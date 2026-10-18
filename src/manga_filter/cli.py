"""manga-filter run IMG... / manga-filter sample DIR --n 12

每张图输出一张对比图：原图 | 亮度基线 | 档位图 | 本方案成品。
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image

from .render import levels_preview, luminance_baseline, render_levels
from .tone import ToneParams, compute_tone

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def load(path: Path, long_side: int) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    s = long_side / max(img.size)
    if s < 1:
        img = img.resize((round(img.width * s), round(img.height * s)), Image.Resampling.LANCZOS)
    return np.asarray(img)


def process(path: Path, out: Path, long_side: int, period: float) -> None:
    rgb = load(path, long_side)
    t0 = time.perf_counter()
    res = compute_tone(rgb, ToneParams())
    ours = render_levels(res.levels, res.lines, period)
    dt = time.perf_counter() - t0
    base = render_levels(luminance_baseline(rgb), res.lines, period)

    gray3 = lambda a: np.repeat(a[..., None], 3, -1)
    row = np.concatenate([rgb, gray3(base), gray3(levels_preview(res.levels)), gray3(ours)], 1)
    out.mkdir(parents=True, exist_ok=True)
    stem = path.stem.replace(".", "_")
    Image.fromarray(row).save(out / f"{stem}_compare.png")
    Image.fromarray(ours).save(out / f"{stem}_manga.png")
    (out / f"{stem}_palette.txt").write_text("\n".join(res.notes), encoding="utf-8")
    print(f"{path.name}: {rgb.shape[1]}x{rgb.shape[0]} {dt:.2f}s")


def main() -> None:
    ap = argparse.ArgumentParser(prog="manga-filter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("images", nargs="+", type=Path)
    s = sub.add_parser("sample")
    s.add_argument("dir", type=Path)
    s.add_argument("--n", type=int, default=12)
    s.add_argument("--seed", type=int, default=0)
    for p in (r, s):
        p.add_argument("-o", "--out", type=Path, default=Path("out"))
        p.add_argument("--long-side", type=int, default=1200)
        p.add_argument("--period", type=float, default=7.0, help="网点周期（像素）")
    a = ap.parse_args()

    if a.cmd == "run":
        paths = a.images
    else:
        files = sorted(f for f in a.dir.iterdir() if f.suffix.lower() in EXTS or f.name.endswith(".webp"))
        paths = random.Random(a.seed).sample(files, min(a.n, len(files)))
    for p in paths:
        try:
            process(p, a.out, a.long_side, a.period)
        except Exception as e:  # noqa: BLE001 原型：单张失败不中断批量
            print(f"{p.name}: FAILED {e!r}")


if __name__ == "__main__":
    main()
