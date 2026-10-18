"""拼两张对比图：原型（插画 → 漫画）与 my-home 沙盘（黑白漫画系列预设）。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from manga_filter.cli import load
from manga_filter.render import luminance_baseline, render_levels
from manga_filter.tone import ToneParams, compute_tone

OUT = Path("E:/code/manga-filter/compare")
IMAGES = Path("E:/pictoria/server/illustration/images")
SHOTS = Path("C:/Users/Jannchie/AppData/Local/Temp/claude/C--Users-Jannchie/ba62519d-609e-4783-8ac4-d84cae564e7a/scratchpad/shots-v2")
FONT = "C:/Windows/Fonts/msyh.ttc"
BOLD = "C:/Windows/Fonts/msyhbd.ttc"
BG, INK, MUTED, RULE = (250, 250, 247), (28, 28, 30), (110, 110, 115), (220, 220, 214)
GAP, PAD = 12, 40
OLD = ToneParams(line_scales=((3.0, 7.0, 65.0),), line_min_area=12, detail_gain=0)


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def fit_box(im, w, h):
    """等比缩进 w×h 的格子，居中，空白处填底色"""
    s = min(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.Resampling.LANCZOS)
    cell = Image.new("RGB", (w, h), BG)
    cell.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return cell


def captioned(im, text):
    """左上角贴一个标签"""
    im = im.copy()
    d = ImageDraw.Draw(im)
    f = font(26, True)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((12, 12, 12 + tw + 24, 12 + 44), radius=8, fill=(255, 255, 255), outline=RULE, width=2)
    d.text((24, 17), text, font=f, fill=INK)
    return im


def grid(rows, col_labels, title, subtitle, out, row_h, cell_w):
    """rows: [(section 或 None, label, [panels])]，每个面板放进 cell_w×row_h 的格子"""
    n = max(len(r[2]) for r in rows)
    label_w = 210
    W = PAD * 2 + label_w + cell_w * n + GAP * (n - 1)
    head_h = 150 if col_labels else 110
    sec_h = 56
    H = PAD + head_h + sum(row_h + GAP + (sec_h if r[0] else 0) for r in rows) + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((PAD, PAD), title, font=font(40, True), fill=INK)
    d.text((PAD, PAD + 58), subtitle, font=font(22), fill=MUTED)
    for i, lab in enumerate(col_labels):
        tw = d.textlength(lab, font=font(22, True))
        d.text((PAD + label_w + i * (cell_w + GAP) + (cell_w - tw) / 2, PAD + head_h - 40), lab, font=font(22, True), fill=INK)
    y = PAD + head_h
    for section, label, panels in rows:
        if section:
            d.line((PAD, y + 14, W - PAD, y + 14), fill=RULE, width=2)
            d.text((PAD, y + 20), section, font=font(22, True), fill=MUTED)
            y += sec_h
        d.multiline_text((PAD, y + 6), label, font=font(20), fill=INK, spacing=6)
        for i, p in enumerate(panels):
            sheet.paste(fit_box(p, cell_w, row_h), (PAD + label_w + i * (cell_w + GAP), y))
        y += row_h + GAP
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out, sheet.size)


def proto(name, crop=None):
    """原图 | 亮度基线 | 旧版（纯调色板分档）| 新版（双尺度提线 + 细节回填）；crop=(x0, y0, x1, y1) 取局部"""
    rgb = load(next(IMAGES.glob(name + ".*")), 1200)
    new, old = compute_tone(rgb), compute_tone(rgb, OLD)
    panels = [rgb, render_levels(luminance_baseline(rgb), new.lines), render_levels(old.levels, old.lines), render_levels(new.levels, new.lines)]
    ims = [Image.fromarray(a).convert("RGB") for a in panels]
    return [im.crop(crop) for im in ims] if crop else ims


proto_rows = [
    ("适合：平涂、线稿清晰", "黑发涂实黑\n皮肤与高光留白", proto("GkcW3bUXsAALnUe")),
    (None, "同上，脸部局部\n新版补回嘴与睫毛\n虹膜层次仍是基线好", proto("GkcW3bUXsAALnUe", (230, 300, 500, 560))),
    (None, "红衣进浅网点\n基线压成黑块", proto("de3c927f2fbd4102cc56f710946f6abc")),
    (None, "浅底色留白\n深尾巴实黑", proto("d87bd2b9142628475ed685689ecefcdd")),
    (None, "蓝色袜子与裙子\n分到不同档", proto("a9d644ecaa292d3d0f4488ec17c464ae")),
    ("局限：高饱和、厚涂、夜景、复杂背景", "高饱和背景\n两者都偏乱", proto("9df6c1e37c188eb322e8cacd7b86369d")),
    (None, "厚涂夜景\n偏黑、丢细节\n基线更好", proto("5ae326d4905b3df6a1e9e3fb988cd1e9")),
    (None, "复杂背景\n碎块多", proto("efd4670f04fda43509481d8903943caf")),
]
grid(
    proto_rows,
    ["原图", "亮度基线（仿 Manga-Lite）", "旧版：纯调色板分档", "新版：+ 双尺度提线、细节回填"],
    "彩色插画 → 黑白漫画：纯机械方案",
    "调色板分档 + 底色/阴影配对 + HK 校正明度，无学习模型；新版补回被调色板吞掉的小细节。基线与新版共用新线稿",
    OUT / "prototype.png",
    row_h=560,
    cell_w=420,
)


def shot(look, t, text):
    return captioned(Image.open(SHOTS / f"{look}-{t}.png").convert("RGB").crop((0, 20, 880, 720)), text)


home_rows = [
    (None, "", [shot("none", 14, "原样"), shot("manga", 14, "黑白漫画"), shot("manga-coarse", 14, "粗网点漫画")]),
    (None, "", [shot("manga-hatch", 14, "排线漫画"), shot("manga-ink", 14, "墨线稿"), shot("manga", 21, "黑白漫画 · 21:00")]),
]
grid(
    home_rows,
    [],
    "my-home 沙盘：黑白漫画系列",
    "材质直接输出档位与法线：固有色定底色档，阴影再深一档，法线夹角大处补转折线；四个预设只换画法",
    OUT / "my-home.png",
    row_h=560,
    cell_w=704,
)
