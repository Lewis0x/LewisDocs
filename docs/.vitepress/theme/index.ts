import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Honeypot from './components/Honeypot.vue'
import './custom.css'

const theme: Theme = {
  extends: DefaultTheme,
  // 通过 layout-bottom slot 在每个页面 DOM 树底部插入蜜罐链接：
  //   - 守规矩的爬虫读 robots.txt → 避开 /_honeypot/ → 不被惩罚
  //   - 不读 robots.txt 的爬虫跟 DOM 链接 → 触发 Cloudflare WAF → 进 IP 黑名单
  //   - 真人用户：定位屏外 + aria-hidden + tabindex=-1，无感
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-bottom': () => h(Honeypot),
    })
  },
}

export default theme
