"""彩色插画 → 漫画明度档位图（纯机械，无学习模型）。

流程：
1. 提线：比周围暗的细笔画单独成层，不参与调色板。
2. 调色板：Lab 空间 k-means，像素归入最近色，众数滤波合并碎块。
3. 阴影配对：相邻、同色相、更暗的颜色判为某底色的阴影层。
4. 底色分档：按感知明度排序，枚举单调分档，最小化代价。
5. 阴影层 = 父底色档位 + 1。
6. 细节回填：像素比所在色块明显更暗 / 更亮时（超过死区），按差值压深 / 提亮档位，
   保住嘴、眼中高光、衣褶这类被调色板和众数滤波吞掉的小细节。
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import cv2
import numpy as np
from scipy import ndimage
from skimage import color

# 档位：0 白，1 浅网点，2 深网点，3 黑
LEVELS = 4


@dataclass
class ToneParams:
    k: int = 12  # 调色板颜色数
    # 笔线：每个尺度 (高斯 σ, 比周围暗多少 L*, 笔线本身 L* 上限)。细尺度抓嘴、睫毛这类淡而细的线
    line_scales: tuple[tuple[float, float, float], ...] = ((1.2, 6.0, 90.0), (3.0, 7.0, 65.0))
    line_min_area: int = 4
    mode_size: int = 7  # 众数滤波窗口，合并碎块
    # 阴影配对
    shadow_dl: tuple[float, float] = (4.0, 45.0)
    shadow_hue_deg: float = 40.0
    shadow_adj_ratio: float = 0.2
    # 分档代价
    w_distinct: float = 4.0  # 相邻异色同档的惩罚
    w_dark_area: float = 0.6  # 大面积深色的惩罚
    skin_white: bool = True
    # 细节回填：死区（V 单位）与增益，增益 0 即纯调色板分档
    detail_dead: float = 8.0
    detail_gain: float = 1.0


@dataclass
class ToneResult:
    levels: np.ndarray  # HxW int8，0..3
    lines: np.ndarray  # HxW bool
    labels: np.ndarray  # HxW int，调色板编号
    palette_lab: np.ndarray  # Kx3
    palette_level: np.ndarray  # K
    parent: np.ndarray  # K，阴影层的父底色编号，底色为 -1
    skin: np.ndarray  # K bool
    notes: list[str] = field(default_factory=list)


def hk_lightness(lab: np.ndarray) -> np.ndarray:
    """Helmholtz–Kohlrausch 校正明度（Fairchild & Pirrotta）：高饱和色看起来更亮。"""
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a))
    return L + (2.5 - 0.025 * L) * (0.116 * np.abs(np.sin(np.radians((h - 90) / 2))) + 0.085) * C


def extract_lines(L: np.ndarray, p: ToneParams) -> np.ndarray:
    lines = np.zeros(L.shape, bool)
    for sigma, contrast, max_l in p.line_scales:
        darker = cv2.GaussianBlur(L, (0, 0), sigma) - L
        lines |= (darker > contrast) & (L < max_l)
    _, cc, stats, _ = cv2.connectedComponentsWithStats(lines.astype(np.uint8), connectivity=8)
    keep = stats[:, cv2.CC_STAT_AREA] >= p.line_min_area
    keep[0] = False
    return keep[cc]


def mode_filter(labels: np.ndarray, k: int, size: int) -> np.ndarray:
    votes = np.stack(
        [cv2.boxFilter((labels == i).astype(np.float32), -1, (size, size)) for i in range(k)]
    )
    return votes.argmax(0)


def build_palette(lab: np.ndarray, mask: np.ndarray, p: ToneParams) -> tuple[np.ndarray, np.ndarray]:
    pix = lab[mask].astype(np.float32)
    rng = np.random.default_rng(0)
    sample = pix[rng.choice(len(pix), size=min(len(pix), 120_000), replace=False)]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, _, centers = cv2.kmeans(sample, p.k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    d = ((lab[..., None, :].astype(np.float32) - centers[None, None]) ** 2).sum(-1)
    return d.argmin(-1), centers


def adjacency(labels: np.ndarray, k: int) -> np.ndarray:
    adj = np.zeros((k, k), np.int64)
    for a, b in ((labels[:, :-1], labels[:, 1:]), (labels[:-1], labels[1:])):
        diff = a != b
        np.add.at(adj, (a[diff], b[diff]), 1)
    return adj + adj.T


def is_skin(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab[:, 0], lab[:, 1], lab[:, 2]
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a))
    return (L > 55) & (C > 6) & (C < 45) & (h > 20) & (h < 75) & (a > 3)


def find_shadows(lab, area, adj, skin, p: ToneParams) -> np.ndarray:
    k = len(lab)
    C = np.hypot(lab[:, 1], lab[:, 2])
    h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1]))
    perim = adj.sum(1) + 1e-9
    parent = np.full(k, -1)
    for j in range(k):
        best, best_score = -1, 0.0
        for i in range(k):
            if i == j:
                continue
            dl = lab[i, 0] - lab[j, 0]
            if not (p.shadow_dl[0] <= dl <= p.shadow_dl[1]):
                continue
            if C[i] > 8 and C[j] > 8:
                dh = abs((h[i] - h[j] + 180) % 360 - 180)
                if dh > p.shadow_hue_deg:
                    continue
            elif (C[i] > 8) != (C[j] > 8) and not skin[i]:
                # 有彩底色配灰阴影不常见，肤色例外（灰紫阴影）
                continue
            elif C[i] <= 8 and C[j] <= 8 and dl < 12:
                # 两块都是灰：明度差小的多半是两种不同的浅色（白底与米色衣服），不是阴影
                continue
            ratio = adj[i, j] / perim[j]
            if ratio < p.shadow_adj_ratio or area[j] > area[i] * 1.5:
                continue
            if ratio > best_score:
                best, best_score = i, ratio
        parent[j] = best
    # 断开环，并把链压到最终的底色
    for j in range(k):
        seen, cur = {j}, j
        while parent[cur] >= 0:
            if parent[cur] in seen:
                parent[j] = -1
                break
            cur = parent[cur]
            seen.add(cur)
    return parent


def target_level(v: np.ndarray) -> np.ndarray:
    """感知明度 → 连续档位。V≥82 全白，V≤35 全黑（漫画里深发、深衣直接涂黑）。"""
    return np.clip((82.0 - v) / (82.0 - 35.0) * (LEVELS - 1), 0, LEVELS - 1)


def assign_bases(bases, v, area, adj, de, fixed, p: ToneParams) -> dict[int, int]:
    """在底色上枚举单调分档（越暗档位不降），最小化代价。"""
    free = [i for i in bases if i not in fixed]
    free.sort(key=lambda i: -v[i])
    t = target_level(v)
    area_frac = area / area.sum()
    best, best_cost = None, np.inf
    n = len(free)
    # 三个切点把有序列表切成四段
    for cuts in itertools.combinations_with_replacement(range(n + 1), LEVELS - 1):
        lv = dict(fixed)
        bounds = (0, *cuts, n)
        for level in range(LEVELS):
            for idx in range(bounds[level], bounds[level + 1]):
                lv[free[idx]] = level
        cost = 0.0
        for i in bases:
            w = 0.3 + area_frac[i] * 10
            cost += w * (lv[i] - t[i]) ** 2 + p.w_dark_area * area_frac[i] * lv[i]
        for i, j in itertools.combinations(bases, 2):
            if lv[i] == lv[j] and adj[i, j] > 0:
                cost += p.w_distinct * min(de[i, j] / 30, 1.0) * adj[i, j] / adj.sum() * 50
        if cost < best_cost:
            best, best_cost = lv, cost
    return best


def compute_tone(rgb: np.ndarray, p: ToneParams | None = None) -> ToneResult:
    p = p or ToneParams()
    smooth = cv2.bilateralFilter(rgb, 7, 30, 5)
    lab = color.rgb2lab(smooth).astype(np.float32)
    # 提线用原图：双边滤波会把一两像素宽的淡线抹掉
    lines = extract_lines(color.rgb2lab(rgb)[..., 0].astype(np.float32), p)

    labels, centers = build_palette(lab, ~lines, p)
    # 笔线像素取最近的非笔线像素的颜色编号
    _, (iy, ix) = ndimage.distance_transform_edt(lines, return_indices=True)
    labels = labels[iy, ix]
    labels = mode_filter(labels, p.k, p.mode_size)

    k = p.k
    area = np.bincount(labels.ravel(), minlength=k).astype(np.float64)
    pal = np.array([lab[labels == i].mean(0) if area[i] else centers[i] for i in range(k)])
    adj = adjacency(labels, k)
    v = hk_lightness(pal)
    skin = is_skin(pal) if p.skin_white else np.zeros(k, bool)
    de = np.linalg.norm(pal[:, None] - pal[None], axis=-1)

    parent = find_shadows(pal, area, adj, skin, p)
    bases = [i for i in range(k) if parent[i] < 0 and area[i] > 0]
    fixed = {i: 0 for i in bases if skin[i]}
    lv = assign_bases(bases, v, area, adj, de, fixed, p)

    palette_level = np.zeros(k, np.int8)
    for i in range(k):
        root = i
        while parent[root] >= 0:
            root = parent[root]
        if root == i:
            palette_level[i] = lv.get(i, 3)
        else:
            # 阴影至少比底色深一档；本身就很暗的阴影按自己的明度走
            own = int(np.round(target_level(v[i : i + 1])[0]))
            palette_level[i] = min(max(lv[root] + 1, own), LEVELS - 1)

    notes = [
        f"#{i:02d} L={pal[i,0]:5.1f} V={v[i]:5.1f} area={area[i]/area.sum():5.1%} "
        f"lv={palette_level[i]} parent={parent[i]:2d}{' skin' if skin[i] else ''}"
        for i in np.argsort(-v)
    ]
    levels = palette_level[labels].astype(np.float32)
    if p.detail_gain > 0:
        d = v[labels] - hk_lightness(lab)
        d = np.sign(d) * np.maximum(np.abs(d) - p.detail_dead, 0)
        levels += p.detail_gain * d * (LEVELS - 1) / (82.0 - 35.0)
    levels = np.clip(np.round(levels), 0, LEVELS - 1).astype(np.int8)
    return ToneResult(levels, lines, labels, pal, palette_level, parent, skin, notes)
