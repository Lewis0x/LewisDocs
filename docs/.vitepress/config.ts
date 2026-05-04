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
  // GitHub Pages 项目站点 URL = https://<user>.github.io/<repo>/
  // 默认部署到 https://lewis0x.github.io/LewisDocs/，所以 base 必须是 /LewisDocs/
  // 如未来绑定自定义域名（CNAME），把 base 改回 '/'
  base: '/LewisDocs/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  head: [
    ['meta', { name: 'theme-color', content: '#3c8772' }],
  ],

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
