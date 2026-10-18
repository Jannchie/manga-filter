"""和全功能 Qwen 版对比：原版仓库 examples/ 里作者放了同一张图的 Qwen-Image 编辑 + Manga Finish 结果，
把原图切出来，跑原版 Lite 和本项目的结合版，与作者的 Qwen 结果并排。
uv run python compare/vs_qwen.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from vs_original import manga_lite, ms  # noqa: E402

from manga_filter.tone import compute_tone  # noqa: E402

EX = Path(__file__).resolve().parents[1] / "ref" / "ComfyUI-MangaScreen" / "examples"
OUT = Path(__file__).parent


def crop(name, x, y, w, h):
    return np.asarray(Image.open(EX / f"{name}.jpg").convert("RGB"))[y : y + h, x : x + w]


def levels(rgb, black=0.20, white=0.70, gamma=1.3):
    g = (rgb.astype(np.float32) / 255) @ np.float32([0.299, 0.587, 0.114])
    g = np.clip((g - black) / (white - black), 0, 1) ** (1 / gamma)
    return (np.repeat(g[..., None], 3, -1) * 255).round().astype(np.uint8)


def hybrid(rgb, extra_pen=None, gray=None):
    """原版 Finish + 本项目的 DoG 细线稿（就是网页调参台的默认管线）"""
    pen = compute_tone(rgb).lines.astype(np.float32)
    if extra_pen is not None:
        pen = np.maximum(pen, extra_pen.astype(np.float32))
    page = ms.finish(levels(rgb) if gray is None else gray, 200, 0.80, 0.30, 0.18, 0.42, 1.0, pen, 0.5, 0.4)
    return np.where(page, 255, 0).astype(np.uint8)


def fit(im, w):
    im = Image.fromarray(im).convert("RGB")
    return np.asarray(im.resize((w, round(im.height * w / im.width)), Image.Resampling.LANCZOS))


def sheet(cols, out, w=470):
    panels = [fit(c, w) for c in cols]
    h = max(p.shape[0] for p in panels)
    panels = [np.pad(p, ((0, h - p.shape[0]), (0, 0), (0, 0)), constant_values=250) for p in panels]
    gap = np.full((h, 12, 3), 250, np.uint8)
    row = panels[0]
    for p in panels[1:]:
        row = np.concatenate([row, gap, p], 1)
    Image.fromarray(row).save(out)
    print(out, row.shape)


if __name__ == "__main__":
    bg = crop("compare_1", 30, 65, 760, 1130)
    sheet([bg, crop("lite_vs_qwen_background", 520, 1648, 470, 699), manga_lite(bg), hybrid(bg)], OUT / "vs-qwen-background.png")
    ch = crop("lite_vs_qwen_character", 30, 100, 400, 595)
    ch2 = cv2.resize(ch, (800, 1190), interpolation=cv2.INTER_CUBIC)  # 示例原图只有 400 宽，放大到 800 再处理
    sheet([ch, crop("lite_vs_qwen_character", 450, 1430, 400, 595), manga_lite(ch2), hybrid(ch2)], OUT / "vs-qwen-character.png", w=400)
