"""和原版 ComfyUI-MangaScreen 对比：原版 Manga-Lite（Manga Levels → Manga Finish，无外接线稿）
与本项目的亮度基线、调色板分档。

原版只依赖 numpy / OpenCV，torch 只用来包装 ComfyUI 的张量；这里给一个空壳 torch 模块，直接调用它的 finish()。
uv run python compare/vs_original.py
"""

import importlib.util
import sys
import types
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from manga_filter.cli import load
from manga_filter.render import luminance_baseline, render_levels
from manga_filter.tone import compute_tone

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "ref" / "ComfyUI-MangaScreen" / "__init__.py"
IMAGES = Path("E:/pictoria/server/illustration/images")
OUT = ROOT / "compare"

sys.modules.setdefault("torch", types.ModuleType("torch"))
spec = importlib.util.spec_from_file_location("mangascreen", REF)
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)


def manga_lite(rgb: np.ndarray) -> np.ndarray:
    """原版 Manga-Lite 默认参数：Levels(0.20 / 0.70 / γ1.3) → Finish(200 线, 白 0.80, 黑 0.30, 18% / 42%, 渐变 1.0, 白线 0.4)"""
    g = (rgb.astype(np.float32) / 255) @ np.float32([0.299, 0.587, 0.114])
    g = np.clip((g - 0.20) / 0.50, 0, 1) ** (1 / 1.3)
    g8 = (np.repeat(g[..., None], 3, -1) * 255).round().astype(np.uint8)
    page = ms.finish(g8, 200, 0.80, 0.30, 0.18, 0.42, 1.0, None, 0.30, 0.4)
    return np.where(page, 255, 0).astype(np.uint8)


def main(names: list[str]) -> None:
    rows = []
    for name in names:
        rgb = load(next(IMAGES.glob(name + ".*")), 1200)
        lines = compute_tone(rgb).lines
        panels = [
            rgb,
            manga_lite(rgb),
            render_levels(luminance_baseline(rgb), lines),
        ]
        h = 760
        ims = [Image.fromarray(p).convert("RGB") for p in panels]
        ims = [im.resize((round(im.width * h / im.height), h), Image.Resampling.LANCZOS) for im in ims]
        row = Image.new("RGB", (sum(im.width for im in ims) + 16 * (len(ims) - 1), h), (250, 250, 247))
        x = 0
        for im in ims:
            row.paste(im, (x, 0))
            x += im.width + 16
        rows.append(row)
        # 原图分辨率的单张，方便放大看网点
        Image.fromarray(manga_lite(rgb)).save(OUT / f"orig-lite_{name}.png")
    W = max(r.width for r in rows)
    sheet = Image.new("RGB", (W, sum(r.height for r in rows) + 24 * (len(rows) - 1)), (250, 250, 247))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 24
    sheet.save(OUT / "vs-original.png")
    print(OUT / "vs-original.png", sheet.size)


if __name__ == "__main__":
    main(sys.argv[1:] or [
        "GkcW3bUXsAALnUe",
        "de3c927f2fbd4102cc56f710946f6abc",
        "d87bd2b9142628475ed685689ecefcdd",
        "5ae326d4905b3df6a1e9e3fb988cd1e9",
    ])
