<script setup lang="ts">
// 蜜罐链接：对人类用户不可见（屏外定位 + aria-hidden + tabindex=-1），
// 对扫描 DOM 的爬虫可见。Cloudflare WAF 会把命中 /_honeypot/* 的 IP 加入黑名单。
// 这条规则与 robots.txt 中 Disallow: /_honeypot/ 配合：
//   - 守规矩的爬虫读 robots.txt 后会避开 → 不被惩罚
//   - 不读 / 无视 robots.txt 的爬虫会跟着 DOM 链接掉进陷阱 → 被边缘封禁
import { useData } from 'vitepress'
import { computed } from 'vue'

const { site } = useData()
// 用 base 拼出绝对路径，避免子路径部署时 404
const honeypotUrl = computed(() =>
  (site.value.base?.replace(/\/$/, '') ?? '') + '/_honeypot/do-not-follow.html'
)
</script>

<template>
  <a
    :href="honeypotUrl"
    rel="nofollow noindex noopener"
    aria-hidden="true"
    tabindex="-1"
    class="lewisdocs-honeypot"
    >do-not-follow</a
  >
</template>

<style scoped>
.lewisdocs-honeypot {
  position: absolute;
  left: -9999px;
  top: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
  pointer-events: none;
  /* 防止被键盘 Tab 遍历到 */
  user-select: none;
}
</style>
