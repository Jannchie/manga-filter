# manga-filter

彩色插画转黑白漫画网点，纯机械运算，不用任何学习模型。

主线是 [`web/tone-bench.html`](web/tone-bench.html)：单文件网页，直接用浏览器打开，拖入图片后用滑块实时调参，计算全部在浏览器的 Web Worker 里完成，不依赖 Python。

## 网页调参台

管线移植自 [ashukae/ComfyUI-MangaScreen](https://github.com/ashukae/ComfyUI-MangaScreen) 的 Manga Levels + Manga Finish（MIT，许可证见 [`licenses/`](licenses/)），在它的基础上加了：

- **细线稿**：在原图 L* 上做双尺度 DoG，补回嘴、鼻、浅色轮廓。原版要外接神经网络线稿（Manga Lineart）才有这些线。
- **饱和色提亮**：按 Helmholtz–Kohlrausch 效应调亮高饱和色，红衣服不再压成黑块。
- **暗部分层**（默认关）：大块实黑里较亮的部分改成深网点，适合黑裙子这类深灰布料。
- **淡边描线**（默认关）：Canny 边缘里只留又长又细的直线段，给雾中建筑描轮廓。
- **10 种网点**：圆点、方点、菱形点、链点、平行线、交叉线、波纹线、砂目、同心圆、集中线。
- **出图分辨率独立**：网点间距不足 10 px 时放大出图，圆点才画得圆。

预览可以滚轮缩放、拖动平移，`0` 适应窗口，`1` 为 1:1。

## Python 原型

早期的实验原型，按调色板分档（Lab k-means → 底色 / 阴影配对 → HK 校正明度上的单调分档）：

```sh
uv run manga-filter sample <图片目录> --n 12 -o out
uv run manga-filter run a.png b.jpg -o out
```

`compare/` 下是对比脚本：和原版 Manga-Lite（`vs_original.py`）、和原版作者示例里的 Qwen 版（`vs_qwen.py`、`qwen_*.py`）。原版仓库要先克隆到 `ref/ComfyUI-MangaScreen`。对比图本身不入库。
