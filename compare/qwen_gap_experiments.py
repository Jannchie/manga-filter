"""针对 Qwen 版的两处差距试轻量替代：
G1 淡边描线：雾中高楼和天空只有很淡的明暗差，按「比周围暗」提不到线。在平滑后的原图上找边缘，
   只留直线段（楼的边、窗格是直的，云的边是弯的）。
G2 暗部层次：暗区里做局部对比度增强（CLAHE），把裙子里略亮的褶皱从实黑里分出来成深网点。
uv run python compare/qwen_gap_experiments.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from vs_qwen import crop, hybrid, levels  # noqa: E402

OUT = Path(__file__).parent


def edge_segments(rgb, k, low=12, high=30, min_len=28, gap=3):
    """G1：Canny（在双边平滑后的 L* 上）→ 概率霍夫直线段，画成 1px 线"""
    lab = cv2.cvtColor(cv2.bilateralFilter(rgb, 9, 40, 7), cv2.COLOR_RGB2LAB)
    edges = cv2.Canny(lab[..., 0], low, high, L2gradient=True)
    segs = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=int(20 * k), minLineLength=int(min_len * k), maxLineGap=int(gap * k))
    out = np.zeros(rgb.shape[:2], np.uint8)
    if segs is not None:
        for x0, y0, x1, y1 in np.asarray(segs).reshape(-1, 4):
            cv2.line(out, (int(x0), int(y0)), (int(x1), int(y1)), 1, 1)
    return out, edges


def dark_detail(rgb, strength=1.0, clip=3.0):
    """G2：Levels 之后，暗区换成 CLAHE 版本（亮区保持不变）"""
    g = levels(rgb)[..., 0]
    eq = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(g)
    w = np.clip((0.45 - g / 255) / 0.3, 0, 1) * strength
    out = (g * (1 - w) + np.maximum(eq, g) * w).round().astype(np.uint8)
    return np.repeat(out[..., None], 3, -1)


if __name__ == "__main__":
    bg = crop("compare_1", 30, 65, 760, 1130)
    qwen = cv2.resize(crop("lite_vs_qwen_background", 520, 1648, 470, 699), (760, 1130), interpolation=cv2.INTER_CUBIC)
    k = bg.shape[1] / 1024
    segs, edges = edge_segments(bg, k)
    base = hybrid(bg)
    g1 = hybrid(bg, extra_pen=segs)
    g2 = hybrid(bg, gray=dark_detail(bg))
    both = hybrid(bg, extra_pen=segs, gray=dark_detail(bg))
    cols = [bg, qwen, base, g1, g2, both]
    rgb3 = lambda a: a if a.ndim == 3 else np.repeat(a[..., None], 3, -1)
    rows = []
    for (y0, y1, x0, x1) in [(0, 520, 0, 760), (820, 1130, 220, 600)]:   # 上半：高楼；下半：裙子
        tiles = [rgb3(c)[y0:y1, x0:x1] for c in cols]
        gap = np.full((y1 - y0, 10, 3), 250, np.uint8)
        r = tiles[0]
        for t in tiles[1:]:
            r = np.concatenate([r, gap, t], 1)
        rows.append(r)
    W = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 14), (0, W - r.shape[1]), (0, 0)), constant_values=250) for r in rows]
    Image.fromarray(np.concatenate(rows, 0)).save(OUT / "qwen-gaps.png")
    Image.fromarray(np.where(edges > 0, 0, 255).astype(np.uint8)).save(OUT / "qwen-gaps-canny.png")
    print("saved", OUT / "qwen-gaps.png")
