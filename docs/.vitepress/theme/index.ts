import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Honeypot from './components/Honeypot.vue'
import OutlineToggle from './components/OutlineToggle.vue'
import Term from './components/Term.vue'
import './custom.css'

const theme: Theme = {
  extends: DefaultTheme,
  // - layout-bottom slot：蜜罐链接（每页都挂）
  //   * 守规矩的爬虫读 robots.txt → 避开 /_honeypot/
  //   * 不读 robots.txt 的爬虫跟 DOM 链接 → 触发 Cloudflare WAF
  //   * 真人用户：定位屏外 + aria-hidden + tabindex=-1，无感
  // - layout-top slot：右上角"折叠本页大纲"按钮，状态写 localStorage
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => h(OutlineToggle),
      'layout-bottom': () => h(Honeypot),
    })
  },
  enhanceApp({ app }) {
    // 全局组件：所有 .md 文件中可直接 `<Term def="...">B-Rep</Term>`
    app.component('Term', Term)
  },
}

export default theme
