"""档位图 → 二值漫画页：45° 整页对齐网点 + 实黑 + 笔线。"""

from __future__ import annotations

import cv2
import numpy as np

# 各档网点覆盖率：白、浅网点、深网点、黑
COVERAGE = (0.0, 0.18, 0.42, 1.0)


def dot_screen(h: int, w: int, period: float) -> np.ndarray:
    """45° 圆点网屏的点函数，值越大越靠近网点中心。"""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    s = 2 * np.pi / period
    u = (x + y) * s / np.sqrt(2)
    v = (x - y) * s / np.sqrt(2)
    return (np.cos(u) + np.cos(v)) / 2


def ink_for_coverage(spot: np.ndarray, coverage: np.ndarray) -> np.ndarray:
    """按点函数的分位数取阈值，使着墨面积等于覆盖率。"""
    flat = np.sort(spot[: min(spot.shape[0], 512), : min(spot.shape[1], 512)].ravel())
    idx = np.clip(((1 - coverage) * (len(flat) - 1)).astype(int), 0, len(flat) - 1)
    return spot > flat[idx]


def render_levels(levels: np.ndarray, lines: np.ndarray, period: float = 7.0) -> np.ndarray:
    h, w = levels.shape
    cov = np.asarray(COVERAGE, np.float32)[levels]
    ink = ink_for_coverage(dot_screen(h, w, period), cov)
    ink |= levels == 3
    ink |= lines
    return np.where(ink, 0, 255).astype(np.uint8)


def luminance_baseline(rgb: np.ndarray) -> np.ndarray:
    """仿 Manga-Lite：灰度 + 色阶(0.20/0.70, γ1.3)，再按亮度阈值分四档。"""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g = np.clip((g - 0.20) / 0.50, 0, 1) ** (1 / 1.3)
    return np.select([g > 0.80, g > 0.55, g > 0.30], [0, 1, 2], 3).astype(np.int8)


def levels_preview(levels: np.ndarray) -> np.ndarray:
    return np.array([255, 190, 120, 20], np.uint8)[levels]
