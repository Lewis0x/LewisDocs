import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Honeypot from './components/Honeypot.vue'
import OutlineToggle from './components/OutlineToggle.vue'
import Term from './components/Term.vue'
import Lightbox from './components/Lightbox.vue'
import './custom.css'

const theme: Theme = {
  extends: DefaultTheme,
  // - layout-bottom slot：蜜罐 + Lightbox（全页面挂载，监听所有 img / mermaid svg）
  //   * Honeypot：守规矩爬虫绕开、不守规矩爬虫触发 WAF；真人无感
  // - layout-top slot：右上角"折叠本页大纲"按钮，状态写 localStorage
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => h(OutlineToggle),
      'layout-bottom': () => [h(Honeypot), h(Lightbox)],
    })
  },
  enhanceApp({ app }) {
    // 全局组件：所有 .md 文件中可直接 `<Term def="...">B-Rep</Term>`
    app.component('Term', Term)
  },
}

export default theme
