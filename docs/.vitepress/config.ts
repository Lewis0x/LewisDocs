import { existsSync, readFileSync } from 'node:fs'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { AI_CATEGORIES, classifyAiSource } from './ai-taxonomy.mjs'
import {
  AI_MINISEARCH_OPTIONS,
  AI_MINISEARCH_SEARCH_OPTIONS,
  validateAiSearchConcepts,
} from './search-concepts.mjs'
import {
  buildLearningSearchMarkdown,
  createSearchRenderer,
} from './search-render.mjs'

type AiSource = {
  id: string
  product: 'claude-code' | 'codex'
  slug: string
  title: string
  section: string
}

type AiLanguage = 'en' | 'zh-CN'
type LearningPath = Parameters<typeof buildLearningSearchMarkdown>[0]
type LearningCopy = Parameters<typeof buildLearningSearchMarkdown>[1]

const sourceManifest = JSON.parse(
  readFileSync(new URL('../../source-ai/sources.yaml', import.meta.url), 'utf8'),
) as AiSource[]

const readChineseTitle = (source: AiSource) => {
  const url = new URL(
    `../../source-ai/content/zh-CN/${source.product}/${source.slug}.md`,
    import.meta.url,
  )
  if (!existsSync(url)) return undefined
  const match = /^title:\s*(.+)$/mu.exec(readFileSync(url, 'utf8'))
  return match?.[1]?.trim()
}

const AI_SOURCES = sourceManifest.map((source) => {
  const chineseTitle = readChineseTitle(source)
  return {
    ...source,
    translated: chineseTitle !== undefined,
    chineseTitle,
  }
})

validateAiSearchConcepts(AI_SOURCES.map((source) => source.id))

const escapeHtml = (value: string) =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')

const aiSourceRoute = (
  source: (typeof AI_SOURCES)[number],
  language: AiLanguage,
) =>
  `/ai/${
    language === 'zh-CN' && source.translated ? 'zh-CN' : 'en'
  }/${source.product}/${source.slug}`

const aiRouteForId = (sourceId: string, language: AiLanguage) => {
  const source = AI_SOURCES.find((candidate) => candidate.id === sourceId)
  if (source === undefined) {
    throw new Error(`Unknown AI source route: ${sourceId}`)
  }
  return aiSourceRoute(source, language)
}

const aiSidebarTitle = (
  source: (typeof AI_SOURCES)[number],
  language: AiLanguage,
) => {
  if (language === 'en') return escapeHtml(source.title)
  if (source.translated) {
    return escapeHtml(source.chineseTitle ?? source.title)
  }
  return `${escapeHtml(source.title)} <span class="ai-sidebar-fallback">EN</span>`
}

const aiProductSidebar = (
  product: AiSource['product'],
  language: AiLanguage,
) => {
  const sources = AI_SOURCES.filter((source) => source.product === product)
  return [
    {
      text: product === 'claude-code' ? 'Claude Code' : 'Codex',
      items: [
        {
          text: language === 'zh-CN' ? '学习路径' : 'Learning path',
          link: `/ai/learn/${product}`,
        },
      ],
    },
    ...AI_CATEGORIES.map((category) => ({
      text: category.labels[language],
      collapsed: true,
      items: sources
        .filter((source) => classifyAiSource(source) === category.id)
        .map((source) => ({
          text: aiSidebarTitle(source, language),
          link: aiSourceRoute(source, language),
        })),
    })).filter((category) => category.items.length > 0),
  ]
}

const readLearningJson = <T,>(name: string) =>
  JSON.parse(
    readFileSync(
      new URL(`../../source-ai/learning/${name}.json`, import.meta.url),
      'utf8',
    ),
  ) as T

const AI_LEARNING_SEARCH_PAGES = Object.fromEntries(
  (['claude-code', 'codex'] as const).map((product) => {
    const path = readLearningJson<LearningPath>(`${product}.path`)
    const en = readLearningJson<LearningCopy>(`${product}.en`)
    const zh = readLearningJson<LearningCopy>(`${product}.zh-CN`)
    return [
      `ai/learn/${product}.md`,
      buildLearningSearchMarkdown(path, en, zh),
    ]
  }),
)

const CAD_SIDEBAR = [
  {
    text: '附录：CAD API 设计哲学',
    items: [
      { text: '总目录与导读', link: '/appendix/cad' },
      { text: '理论框架（顶层）', link: '/theory' },
      { text: '横向对比（全景矩阵）', link: '/comparison' },
    ],
  },
  {
    text: '横向研究',
    items: [{ text: 'UI 框架研究', link: '/ui-frameworks' }],
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
      { text: '3.9 BricsCAD (BRX + Qt/QML)', link: '/platforms/bricscad' },
    ],
  },
  {
    text: '工具',
    items: [{ text: '术语表（Glossary）', link: '/glossary' }],
  },
]

const renderAiSearch = createSearchRenderer(true, AI_LEARNING_SEARCH_PAGES)

export default withMermaid({
  title: 'LewisDocs AI 教程及文档',
  description: 'Claude Code 与 OpenAI Codex 官方教程、参考文档和中文学习路径',
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
    return head.filter(([tag, attrs]) => {
      if (tag !== 'meta' || attrs === null || typeof attrs !== 'object') {
        return true
      }

      return !(
        'name' in attrs &&
        attrs.name === 'generator' &&
        'content' in attrs &&
        typeof attrs.content === 'string' &&
        attrs.content.startsWith('VitePress')
      )
    })
  },

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      {
        text: 'Claude Code',
        items: [
          { text: '学习路径', link: '/ai/learn/claude-code' },
          {
            text: '快速入门',
            link: aiRouteForId('claude-code/quickstart', 'zh-CN'),
          },
          {
            text: '文档概览',
            link: aiRouteForId('claude-code/overview', 'zh-CN'),
          },
        ],
      },
      {
        text: 'Codex',
        items: [
          { text: '学习路径', link: '/ai/learn/codex' },
          {
            text: '快速入门',
            link: aiRouteForId('codex/quickstart', 'zh-CN'),
          },
          {
            text: '文档概览',
            link: aiRouteForId('codex/overview', 'zh-CN'),
          },
        ],
      },
      {
        text: '附录',
        items: [
          { text: 'CAD API 设计哲学', link: '/appendix/cad' },
          { text: '理论框架', link: '/theory' },
          { text: '横向对比', link: '/comparison' },
          { text: 'UI 框架研究', link: '/ui-frameworks' },
          { text: '术语表', link: '/glossary' },
        ],
      },
    ],

    sidebar: {
      '/ai/en/claude-code/': aiProductSidebar('claude-code', 'en'),
      '/ai/zh-CN/claude-code/': aiProductSidebar('claude-code', 'zh-CN'),
      '/ai/en/codex/': aiProductSidebar('codex', 'en'),
      '/ai/zh-CN/codex/': aiProductSidebar('codex', 'zh-CN'),
      '/appendix/': CAD_SIDEBAR,
      '/theory': CAD_SIDEBAR,
      '/comparison': CAD_SIDEBAR,
      '/ui-frameworks': CAD_SIDEBAR,
      '/platforms/': CAD_SIDEBAR,
      '/glossary': CAD_SIDEBAR,
    },

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
          options: AI_MINISEARCH_OPTIONS,
          searchOptions: AI_MINISEARCH_SEARCH_OPTIONS,
        },
        _render: renderAiSearch,
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
        ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))
      const defaultClose =
        md.renderer.rules.table_close ||
        ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options))
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
