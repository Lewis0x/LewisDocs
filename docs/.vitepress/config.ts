import { withMermaid } from 'vitepress-plugin-mermaid'

// 中文分词器：使用浏览器原生 Intl.Segmenter
// 支持的浏览器：Chrome 87+, Firefox 125+, Safari 14.1+, Edge 87+
const chineseTokenize = (text: string) => {
  if (typeof text !== 'string') return [text]
  const lower = text.toLowerCase()

  if (typeof Intl !== 'undefined' && (Intl as any).Segmenter) {
    const segmenter = new (Intl as any).Segmenter('zh-CN', { granularity: 'word' })
    const tokens: string[] = []
    for (const seg of segmenter.segment(lower)) {
      const t = seg.segment.trim()
      if (t) tokens.push(t)
    }
    return tokens
  }

  // 服务端构建（Node.js）或老浏览器：退化为按空格/标点分词
  return lower.split(/[\s、：，。；！？/\(\)（）]+/).filter(Boolean)
}

export default withMermaid({
  title: '通用 CAD 平台 API 设计哲学',
  description: '8 个主流 CAD 平台的 API 设计深度剖析、横向对比、理论框架',
  lang: 'zh-CN',
  // 部署目标：Cloudflare Pages，根路径 → base = '/'
  // 如回退到 GH Pages 子路径 https://lewis0x.github.io/LewisDocs/，改回 '/LewisDocs/'
  base: '/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  // 反爬声明式信号（详见 project-docs/02-design.md ADR-009）：
  //   - 拒绝所有合规通用爬虫 + 搜索引擎索引
  //   - 显式列出已知 AI / RAG 抓取器
  //   - referrer no-referrer 减少出站隐私泄露
  //   - generator 用空字符串覆盖（transformHead 兜底再删一遍）
  head: [
    ['meta', { name: 'theme-color', content: '#3c8772' }],
    ['meta', { name: 'robots', content: 'noindex,nofollow,noarchive,nosnippet,noimageindex,nocache' }],
    ['meta', { name: 'googlebot', content: 'noindex,nofollow,noarchive' }],
    ['meta', { name: 'bingbot', content: 'noindex,nofollow' }],
    ['meta', { name: 'GPTBot', content: 'noindex' }],
    ['meta', { name: 'OAI-SearchBot', content: 'noindex' }],
    ['meta', { name: 'ChatGPT-User', content: 'noindex' }],
    ['meta', { name: 'ClaudeBot', content: 'noindex' }],
    ['meta', { name: 'anthropic-ai', content: 'noindex' }],
    ['meta', { name: 'Claude-Web', content: 'noindex' }],
    ['meta', { name: 'Google-Extended', content: 'noindex' }],
    ['meta', { name: 'Applebot-Extended', content: 'noindex' }],
    ['meta', { name: 'CCBot', content: 'noindex' }],
    ['meta', { name: 'Bytespider', content: 'noindex' }],
    ['meta', { name: 'PerplexityBot', content: 'noindex' }],
    ['meta', { name: 'Amazonbot', content: 'noindex' }],
    ['meta', { name: 'Diffbot', content: 'noindex' }],
    ['meta', { name: 'cohere-ai', content: 'noindex' }],
    ['meta', { name: 'referrer', content: 'no-referrer' }],
    ['meta', { name: 'generator', content: '' }],
  ],

  // 删除 VitePress 默认注入的 generator 指纹（把版本号送出去太傻）
  transformHead({ assets, head }) {
    return head.filter(
      ([tag, attrs]) =>
        !(tag === 'meta' && (attrs as any)?.name === 'generator' && (attrs as any)?.content?.startsWith('VitePress')),
    )
  },

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '理论框架', link: '/theory' },
      { text: '横向对比', link: '/comparison' },
      {
        text: '厂商深度',
        items: [
          { text: 'AutoCAD ObjectARX', link: '/platforms/autocad' },
          { text: 'CATIA CAA RADE', link: '/platforms/catia' },
          { text: 'Siemens NX', link: '/platforms/nx' },
          { text: 'Onshape', link: '/platforms/onshape' },
          { text: 'MicroStation + iTwin', link: '/platforms/microstation' },
          { text: 'SolidWorks', link: '/platforms/solidworks' },
          { text: 'SketchUp', link: '/platforms/sketchup' },
          { text: 'FreeCAD', link: '/platforms/freecad' },
        ],
      },
      { text: '术语表', link: '/glossary' },
    ],

    sidebar: [
      {
        text: '系列总览',
        items: [
          { text: '总目录与导读', link: '/' },
          { text: '理论框架（顶层）', link: '/theory' },
          { text: '横向对比（全景矩阵）', link: '/comparison' },
        ],
      },
      {
        text: '厂商深度剖析',
        collapsed: false,
        items: [
          { text: '3.1 AutoCAD ObjectARX', link: '/platforms/autocad' },
          { text: '3.2 CATIA CAA RADE', link: '/platforms/catia' },
          { text: '3.3 Siemens NX (NX Open)', link: '/platforms/nx' },
          { text: '3.4 Onshape (REST + FeatureScript)', link: '/platforms/onshape' },
          { text: '3.5 MicroStation + iTwin', link: '/platforms/microstation' },
          { text: '3.6 SolidWorks', link: '/platforms/solidworks' },
          { text: '3.7 SketchUp Ruby', link: '/platforms/sketchup' },
          { text: '3.8 FreeCAD', link: '/platforms/freecad' },
        ],
      },
      {
        text: '工具',
        items: [
          { text: '术语表（Glossary）', link: '/glossary' },
        ],
      },
    ],

    outline: {
      level: [2, 3],
      label: '本页大纲',
    },

    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },

    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '目录',
    darkModeSwitchLabel: '深色模式',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    lastUpdatedText: '最后更新',

    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: '搜索文档',
                buttonAriaLabel: '搜索文档',
              },
              modal: {
                noResultsText: '未找到相关结果',
                resetButtonTitle: '清除查询条件',
                footer: {
                  selectText: '选择',
                  navigateText: '切换',
                  closeText: '关闭',
                },
              },
            },
          },
        },
        miniSearch: {
          options: {
            tokenize: chineseTokenize,
            processTerm: (term: string) => term.toLowerCase().trim(),
          },
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, text: 2, titles: 1 },
          },
        },
      },
    },
  },

  markdown: {
    lineNumbers: false,
    // ⚠️ 不要设 `anchor.permalink: false` — VitePress local search 的 splitPageIntoSections
    // 通过 heading 内的 <a href="#…">  锚点切分文档，禁掉 permalink 会导致整个搜索索引为空。
    // 默认 permalink 是 true（hover 显示 # 链接），保留即可。
    config(md) {
      // 把每个 <table> 包一层 .table-scroll-wrapper：
      //   - wrapper 提供 overflow-x: auto（横向滚动条挂在 wrapper 上）
      //   - 内部 table 保持 display:table（原生），width: max-content（按内容自然宽）
      //   - 让 thead 的 position: sticky 能正确以"页面视口"为参照（display:block 的 table 会
      //     因为自己创建滚动容器而把 sticky 锚到 table 内部，与"页面下滚时表头吸顶"的 UX 相悖）
      const defaultOpen =
        md.renderer.rules.table_open ||
        ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options, env))
      const defaultClose =
        md.renderer.rules.table_close ||
        ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options, env))
      md.renderer.rules.table_open = (tokens, idx, options, env, self) =>
        '<div class="table-scroll-wrapper">' +
        defaultOpen(tokens, idx, options, env, self)
      md.renderer.rules.table_close = (tokens, idx, options, env, self) =>
        defaultClose(tokens, idx, options, env, self) + '</div>'
    },
  },

  // Mermaid 配置：跟随 VitePress 主题切换深浅色
  mermaid: {
    theme: 'default',
    themeVariables: {
      fontFamily: 'inherit',
    },
  },
  mermaidPlugin: {
    class: 'mermaid-diagram',
  },
})
