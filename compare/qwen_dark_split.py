"""G2 第二版：暗区内部再分一次档（模仿 Qwen 版的黑裙子：受光处深网点、下摆阴影实黑）。
大块实黑区域里，在色阶前的灰度上做 Otsu 二分；两类明度差够大时，较亮的一类抬到深网点档。
uv run python compare/qwen_dark_split.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from vs_qwen import crop, hybrid, levels  # noqa: E402

OUT = Path(__file__).parent


def dark_split(rgb, bp=0.30, mid=0.55, min_area=3000, min_gap=0.035):
    """返回给 Finish 的灰度图：大块暗区里较亮的一类抬到 (bp, mid) 之间"""
    k = rgb.shape[1] / 1024
    raw = (rgb.astype(np.float32) / 255) @ np.float32([0.299, 0.587, 0.114])
    g = levels(rgb)[..., 0].astype(np.float32) / 255
    dark = (cv2.GaussianBlur(g, (0, 0), 2 * k) < bp).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, connectivity=4)
    rs = cv2.GaussianBlur(raw, (0, 0), 2.5 * k)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < min_area * k * k:
            continue
        m = lab == i
        v = rs[m]
        t, _ = cv2.threshold((v * 255).astype(np.uint8)[:, None], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        t /= 255
        lo, hi = v[v <= t], v[v > t]
        if len(lo) == 0 or len(hi) == 0 or hi.mean() - lo.mean() < min_gap or len(hi) < 0.15 * len(v):
            continue
        up = m & (rs > t)
        g[up] = np.maximum(g[up], (bp + mid) / 2)
    g8 = (g * 255).round().astype(np.uint8)
    return np.repeat(g8[..., None], 3, -1)


if __name__ == "__main__":
    bg = crop("compare_1", 30, 65, 760, 1130)
    qwen = cv2.resize(crop("lite_vs_qwen_background", 520, 1648, 470, 699), (760, 1130), interpolation=cv2.INTER_CUBIC)
    base, split = hybrid(bg), hybrid(bg, gray=dark_split(bg))
    y0, y1, x0, x1 = 820, 1130, 220, 600
    rgb3 = lambda a: a if a.ndim == 3 else np.repeat(a[..., None], 3, -1)
    tiles = [rgb3(c)[y0:y1, x0:x1] for c in (bg, qwen, base, split)]
    gap = np.full((y1 - y0, 10, 3), 250, np.uint8)
    row = tiles[0]
    for t in tiles[1:]:
        row = np.concatenate([row, gap, t], 1)
    Image.fromarray(row).resize((row.shape[1] * 2, row.shape[0] * 2), Image.Resampling.NEAREST).save(OUT / "qwen-dark-split.png")
    Image.fromarray(split).save(OUT / "qwen-dark-split-full.png")
    print("saved")
