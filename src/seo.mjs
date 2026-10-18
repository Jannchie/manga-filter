// 各语言的 SEO 文案：入口页里写死的 meta、页面运行时切换语言时同步的 <head>、llms.txt 都用这一份
export const SITE = 'https://jannchie.github.io/manga-filter'
export const REPO = 'https://github.com/Jannchie/manga-filter'
export const UPSTREAM = 'https://github.com/ashukae/ComfyUI-MangaScreen'

// path：入口页相对站点根的路径；英文版放在根上，同时是 x-default
export const SEO = {
  en: {
    path: '/',
    htmlLang: 'en',
    ogLocale: 'en_US',
    name: 'Manga Tone Bench',
    title: 'Manga Tone Bench · Free manga screentone filter that runs in your browser',
    description:
      'Turn a color illustration into a black-and-white manga page with screentone. Ten screen types, line art, solid blacks and gradation, tuned live with sliders. Free, no sign-up, no AI model, and images never leave your browser.',
    keywords: 'manga filter, screentone, halftone, manga converter, illustration to manga, black and white manga, comic tone, online tool',
    ogImageAlt: 'Manga Tone Bench: a color anime illustration on the left and the same picture as a black-and-white manga page with screentone on the right',
    noscript: 'Please enable JavaScript to use this tool.',
  },
  zh: {
    path: '/zh/',
    htmlLang: 'zh-CN',
    ogLocale: 'zh_CN',
    name: '漫画网点调参台',
    title: '漫画网点调参台 · 彩色插画转黑白漫画网点的在线工具',
    description:
      '把彩色插画转成带网点的黑白漫画：10 种网点、线稿、实黑与渐变网点，拖动滑块实时调整。免费、无需注册、不用 AI 模型，图片只在你的浏览器里处理。',
    keywords: '漫画滤镜,网点,网点纸,半调,插画转漫画,黑白漫画,漫画化,在线工具',
    ogImageAlt: '漫画网点调参台：左边是彩色动漫插画，右边是同一张图转成的带网点黑白漫画',
    noscript: '请启用 JavaScript 后使用。',
  },
  ja: {
    path: '/ja/',
    htmlLang: 'ja',
    ogLocale: 'ja_JP',
    name: '漫画トーン調整台',
    title: '漫画トーン調整台 · カラーイラストをモノクロ漫画のトーンに変換するオンラインツール',
    description:
      'カラーイラストを、スクリーントーンを貼ったモノクロ漫画に変換します。10 種類の網、線画、ベタ、グラデーショントーンをスライダーでリアルタイムに調整。無料・登録不要・AI モデル不使用で、画像はブラウザの外に出ません。',
    keywords: '漫画フィルター,スクリーントーン,網点,ハーフトーン,イラスト 漫画化,モノクロ漫画,トーン,オンラインツール',
    ogImageAlt: '漫画トーン調整台：左はカラーのアニメ風イラスト、右は同じ絵をトーン入りのモノクロ漫画にしたもの',
    noscript: 'JavaScript を有効にしてご利用ください。',
  },
  ko: {
    path: '/ko/',
    htmlLang: 'ko',
    ogLocale: 'ko_KR',
    name: '만화 톤 조정대',
    title: '만화 톤 조정대 · 컬러 일러스트를 흑백 만화 스크린톤으로 바꾸는 온라인 도구',
    description:
      '컬러 일러스트를 스크린톤이 들어간 흑백 만화로 바꿉니다. 10가지 망, 선화, 먹칠, 그러데이션 톤을 슬라이더로 실시간 조정합니다. 무료, 가입 불필요, AI 모델 미사용이며 이미지는 브라우저 밖으로 나가지 않습니다.',
    keywords: '만화 필터,스크린톤,망점,하프톤,일러스트 만화화,흑백 만화,톤,온라인 도구',
    ogImageAlt: '만화 톤 조정대: 왼쪽은 컬러 애니메이션풍 일러스트, 오른쪽은 같은 그림을 스크린톤이 들어간 흑백 만화로 바꾼 것',
    noscript: 'JavaScript를 켠 뒤 사용해 주세요.',
  },
}
export const LANGS = Object.keys(SEO)
