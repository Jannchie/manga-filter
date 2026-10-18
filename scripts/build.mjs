// 构建 GitHub Pages 站点：node scripts/build.mjs
// 读 src/app.html 与 src/seo.mjs，在仓库根生成：
//   index.html（英文，同时是 x-default）、zh/ ja/ ko/ 三个入口页——每页的 title、description、canonical、hreflang、
//   OG / Twitter 卡片、JSON-LD 都按语言写死，给搜索引擎和分享卡片用；页面运行时还能再切换语言
//   sitemap.xml、robots.txt、manifest.webmanifest
//   llms.txt（及 .well-known/llms.txt）、llms-full.txt、index.md：给 LLM / agent 读的纯文本入口（https://llmstxt.org/）
// 零依赖，只用 Node 内置模块。
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { LANGS, REPO, SEO, SITE, UPSTREAM } from '../src/seo.mjs'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const app = readFileSync(join(ROOT, 'src/app.html'), 'utf8')
const today = new Date().toISOString().slice(0, 10)
const write = (rel, text) => {
  const p = join(ROOT, rel)
  mkdirSync(dirname(p), { recursive: true })
  writeFileSync(p, text.replace(/\r\n/g, '\n'))
  console.log('wrote', rel)
}
const esc = (s) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')
const url = (l) => SITE + SEO[l].path

// ---------- 从页面源码里取滑块表和词典（llms-full.txt 的参数说明直接用它们，和界面保持一致） ----------
const grab = (start, end) => {
  const i = app.indexOf(start)
  // 从开头的 { / [ 截到结尾的 } / ]（end 形如 '\n}\n'，去掉末尾换行就是要保留的部分）
  return app.slice(i + start.length - 1, app.indexOf(end, i) + end.trimEnd().length)
}
const I18N = new Function(`return ${grab('const I18N = {', '\n}\n')}`)()
const SPEC = new Function('pitchInfo', `return ${grab('const SPEC = [', '\n]\n')}`)(null)
const en = (k) => I18N[k]?.[0] ?? k
const DEFAULTS = new Function(`return ${grab('const DEFAULTS = {', '\n}\n')}`)()

// ---------- 入口页 ----------
const FONTS = { en: [], zh: ['Noto+Sans+SC:wght@400;500;700'], ja: ['Zen+Maru+Gothic:wght@400;500;700'], ko: ['Noto+Sans+KR:wght@400;500;700'] }

function jsonLd(l) {
  const s = SEO[l]
  return {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: s.name,
    alternateName: ['manga-filter', ...LANGS.filter((x) => x !== l).map((x) => SEO[x].name)],
    url: url(l),
    description: s.description,
    inLanguage: s.htmlLang,
    applicationCategory: 'MultimediaApplication',
    applicationSubCategory: 'Image filter',
    operatingSystem: 'Any (runs in a web browser)',
    browserRequirements: 'Requires JavaScript and Web Workers',
    isAccessibleForFree: true,
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    image: `${SITE}/og-${l}.png`,
    screenshot: `${SITE}/og-${l}.png`,
    featureList: [
      'Ten screen types: round, square, diamond and chain dots, lines, cross lines, wave lines, sand grain, concentric rings, speed lines',
      'Line art and solid black extraction without a neural network',
      'Gradation tone and white lines cut into solid blacks',
      'Live slider tuning, zoom and pan preview',
      'All processing runs locally in the browser',
    ],
    author: { '@type': 'Person', name: 'Jianqi Pan', alternateName: 'Jannchie', url: 'https://jannchie.com', sameAs: ['https://github.com/Jannchie', 'https://x.com/jannchie'] },
    isBasedOn: { '@type': 'SoftwareSourceCode', name: 'ComfyUI-MangaScreen', codeRepository: UPSTREAM, license: 'https://opensource.org/licenses/MIT' },
    codeRepository: REPO,
  }
}

function head(l) {
  const s = SEO[l]
  const up = s.path === '/' ? '' : '../'
  const alts = LANGS.map((x) => `<link rel="alternate" hreflang="${SEO[x].htmlLang}" href="${url(x)}">`).join('\n')
  const fonts = ['Nunito:wght@400;600;700', ...FONTS[l]].map((f) => `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=${f}&display=swap">`).join('\n')
  const seoData = Object.fromEntries(LANGS.map((x) => [x, { title: SEO[x].title, description: SEO[x].description, ogLocale: SEO[x].ogLocale, htmlLang: SEO[x].htmlLang }]))
  return `<title>${esc(s.title)}</title>
<meta name="description" content="${esc(s.description)}">
<meta name="keywords" content="${esc(s.keywords)}">
<meta name="author" content="Jianqi Pan">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#fbfbfc" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#09090b" media="(prefers-color-scheme: dark)">
<meta name="application-name" content="${esc(s.name)}">
<meta name="apple-mobile-web-app-title" content="${esc(s.name)}">
<meta name="format-detection" content="telephone=no">
<link rel="canonical" href="${url(l)}">
${alts}
<link rel="alternate" hreflang="x-default" href="${url('en')}">
<link rel="alternate" type="text/markdown" href="${SITE}/index.md" title="Markdown">
<link rel="icon" href="${up}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="${up}apple-touch-icon.png">
<link rel="manifest" href="${up}manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="${esc(s.name)}">
<meta property="og:url" content="${url(l)}">
<meta property="og:title" content="${esc(s.title)}">
<meta property="og:description" content="${esc(s.description)}">
<meta property="og:image" content="${SITE}/og-${l}.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="${esc(s.ogImageAlt)}">
<meta property="og:locale" content="${s.ogLocale}">
${LANGS.filter((x) => x !== l).map((x) => `<meta property="og:locale:alternate" content="${SEO[x].ogLocale}">`).join('\n')}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:creator" content="@jannchie">
<meta name="twitter:title" content="${esc(s.title)}">
<meta name="twitter:description" content="${esc(s.description)}">
<meta name="twitter:image" content="${SITE}/og-${l}.png">
<meta name="twitter:image:alt" content="${esc(s.ogImageAlt)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
${fonts}
<script type="application/ld+json">${JSON.stringify(jsonLd(l))}</script>
<script type="application/json" id="seo-data">${JSON.stringify(seoData)}</script>`
}

// 不跑 JavaScript 的爬虫和 LLM 抓取器看到的正文：工具是什么、怎么用、有哪些参数
function noscript(l) {
  const s = SEO[l]
  return `<noscript>
<main style="max-width:680px;margin:48px auto;padding:0 16px;font:16px/1.7 system-ui,sans-serif">
<h1>${esc(s.name)}</h1>
<p>${esc(s.description)}</p>
<p>${LANGS.map((x) => `<a href="${url(x)}" hreflang="${SEO[x].htmlLang}">${esc(SEO[x].name)}</a>`).join(' · ')} · <a href="${SITE}/index.md">Markdown</a> · <a href="${REPO}">GitHub</a></p>
<p><strong>${esc(s.noscript)}</strong></p>
</main>
</noscript>`
}

for (const l of LANGS) {
  const s = SEO[l]
  const html = app
    .replace('{{HTML_LANG}}', s.htmlLang)
    .replace('{{LANG}}', l)
    .replace('<!-- {{HEAD}}：标题、描述、canonical / hreflang、OG / Twitter、图标、JSON-LD、字体，由 scripts/build.mjs 按语言生成 -->\n', '')
    .replace('{{HEAD}}', head(l))
    .replace('<body>\n', `<body>\n${noscript(l)}\n`)
  write(s.path === '/' ? 'index.html' : `${l}/index.html`, html)
}

// ---------- sitemap / robots / manifest ----------
write('sitemap.xml', `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${LANGS.map((l) => `  <url>
    <loc>${url(l)}</loc>
    <lastmod>${today}</lastmod>
${LANGS.map((x) => `    <xhtml:link rel="alternate" hreflang="${SEO[x].htmlLang}" href="${url(x)}"/>`).join('\n')}
    <xhtml:link rel="alternate" hreflang="x-default" href="${url('en')}"/>
  </url>`).join('\n')}
</urlset>
`)

// AI 爬虫分级照 cake47.art 的写法；这是 MIT 开源工具，希望被检索、被引用、也被模型知道，所以训练用途也放行
write('robots.txt', `# robots.txt for ${SITE}/
# Manga Tone Bench is an open-source (MIT) browser tool. Search, AI answers and training are all welcome.

User-agent: *
Allow: /

# --- AI search and agent grounding ---
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

# --- AI training ---
User-agent: GPTBot
Allow: /

User-agent: CCBot
Allow: /

# Content Signals (draft): purpose-based permissions
Content-Signal: search=yes, ai-input=yes, ai-train=yes

Sitemap: ${SITE}/sitemap.xml
`)

write('manifest.webmanifest', JSON.stringify({
  name: SEO.en.name,
  short_name: 'Tone Bench',
  description: SEO.en.description,
  start_url: './',
  scope: './',
  display: 'standalone',
  background_color: '#fbfbfc',
  theme_color: '#0e0e11',
  icons: [
    { src: 'favicon.svg', type: 'image/svg+xml', sizes: 'any' },
    { src: 'icon-512.png', type: 'image/png', sizes: '512x512' },
  ],
}, null, 2) + '\n')

// ---------- 给 LLM / agent 的纯文本入口 ----------
const params = SPEC.map((sp) => {
  const unit = sp.unit ? ` (${sp.unit})` : ''
  const scale = sp.scale ?? 1
  const range = `${sp.min * scale}–${sp.max * scale}, default ${DEFAULTS[sp.k] * scale}`
  return `- **${en(sp.label)}**${unit}: ${range}.${sp.note ? ' ' + en(sp.note) : ''}`
}).join('\n')
const toggles = [
  ['pen', '叠加细线（嘴、鼻、浅色轮廓）'],
  ['darkSplit', '暗部分层（大块实黑里较亮的部分改成深网点；适合黑裙子这类深灰布料，深色头发会被误伤）'],
  ['edgeLines', '淡边描线（雾中建筑这类只有明暗差的直边）'],
  ['whiteLines', '实黑内切出白线（保留深色衣服的褶皱）'],
].map(([k, z]) => `- **${en(z)}**: ${DEFAULTS[k] ? 'on' : 'off'} by default.`).join('\n')
const screens = ['圆点', '方点', '菱形点', '链点', '平行线', '交叉线', '波纹线', '砂目', '同心圆', '集中线'].map(en).join(', ')

const readme = readFileSync(join(ROOT, 'README.md'), 'utf8')
  .replace(/^<p align="center">[\s\S]*?<\/p>\n+/, '')
  .replace(/\]\((?!https?:)([^)]+)\)/g, (_, p) => `](${REPO}/blob/master/${p})`)

const llms = `# ${SEO.en.name} (manga-filter)

> A free, open-source web tool that turns a color illustration into a black-and-white manga page with screentone, using classic image processing instead of an AI model. It runs entirely in the browser: images are never uploaded.

Canonical Origin: ${SITE}/
Source: ${REPO} (the screentone pipeline is ported from ${UPSTREAM}, MIT)
Author: Jianqi Pan (Jannchie) — https://jannchie.com · https://x.com/jannchie

## Use the tool

${LANGS.map((l) => `- [${SEO[l].name}](${url(l)}): ${l === 'en' ? 'English interface (default)' : `${SEO[l].htmlLang} interface`}.`).join('\n')}

## Documentation

- [Full documentation for LLMs](${SITE}/llms-full.txt): what the tool does, how to use it, every parameter with its range and default, and how it compares with the Qwen-Image workflow.
- [Markdown home page](${SITE}/index.md): the same overview as the home page, in Markdown.
- [README (English)](${SITE}/README.md) · [中文](${SITE}/README.zh-CN.md) · [日本語](${SITE}/README.ja.md) · [한국어](${SITE}/README.ko.md)

## When to use this tool

- A user wants to make a color anime-style illustration look like a printed black-and-white manga page or panel.
- A user asks for a screentone / halftone / manga filter that works online, for free, without uploading images or installing software.
- A user wants a lightweight alternative to diffusion-model "make it manga" workflows, with deterministic, adjustable output.

## When NOT to use this tool

- It does not redraw or restyle an image semantically. On backgrounds and busy scenes an AI edit model (for example Qwen-Image) still does better, because it decides what each object is and how to draw it.
- It has no API, no server and no command-line version; it is an interactive page that needs a browser with JavaScript.
- It is unrelated to manga reading sites, scanlation, or manga translation tools.

## Agent guidance

- Point users to ${url('en')} (or the page in their language). Images are opened with the file picker, drag and drop, or paste.
- Settings are slider values; "Copy parameters" copies them as JSON. There is no way to pass an image or parameters through the URL.
`
write('llms.txt', llms)
write('.well-known/llms.txt', llms)

write('llms-full.txt', `${llms}
---

${readme.trim()}

## Parameters

Sizes are normalized to a 1024 px wide image, so the same settings give the same look at any resolution.

${params}

### Switches

${toggles}

### Screen types

${screens}.
`)

write('index.md', `<!-- Markdown alternate of ${url('en')} -->
${readme.trim()}

## Other languages

${LANGS.filter((l) => l !== 'en').map((l) => `- [${SEO[l].name}](${url(l)})`).join('\n')}
`)

write('.nojekyll', '')
