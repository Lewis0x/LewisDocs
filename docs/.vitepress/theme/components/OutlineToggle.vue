<script setup lang="ts">
/**
 * 右侧大纲（"本页大纲"）的折叠 / 展开按钮。
 *
 * 行为：
 *   - 浮动在右上角（避免占用正文宽度）
 *   - 点击切换 <body> 上的 .outline-collapsed class
 *   - 状态写入 localStorage，刷新 / 跨页保留
 *   - 折叠后：outline 隐藏，正文 max-width 自动放宽
 *   - 移动端隐藏（<960px 时 VitePress 本来就把 outline 折叠到下拉菜单了）
 *
 * SSR 友好：组件挂载后才读 localStorage，初始 SSR 输出不带状态。
 * 用户首次访问时按 VitePress 默认行为（outline 显示）。
 */
import { onMounted, ref, watch } from 'vue'

const STORAGE_KEY = 'lewisdocs-outline-collapsed'
const isCollapsed = ref(false)

function applyClass(collapsed: boolean) {
  if (typeof document === 'undefined') return
  document.body.classList.toggle('outline-collapsed', collapsed)
}

function toggle() {
  isCollapsed.value = !isCollapsed.value
}

onMounted(() => {
  // 读持久化状态
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === '1') isCollapsed.value = true
  } catch {
    // localStorage 不可用（隐身 / 限制环境），忽略
  }
  applyClass(isCollapsed.value)
})

watch(isCollapsed, (v) => {
  applyClass(v)
  try {
    localStorage.setItem(STORAGE_KEY, v ? '1' : '0')
  } catch {
    // ignore
  }
})
</script>

<template>
  <button
    class="lewisdocs-outline-toggle"
    :class="{ collapsed: isCollapsed }"
    :title="isCollapsed ? '展开本页大纲' : '折叠本页大纲'"
    :aria-label="isCollapsed ? '展开本页大纲' : '折叠本页大纲'"
    :aria-pressed="isCollapsed ? 'false' : 'true'"
    @click="toggle"
  >
    <!-- icon: stacked-list (open) / right-arrow (collapsed) -->
    <svg
      v-if="!isCollapsed"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="14" y2="12" />
      <line x1="3" y1="18" x2="18" y2="18" />
    </svg>
    <svg
      v-else
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  </button>
</template>

<style scoped>
.lewisdocs-outline-toggle {
  position: fixed;
  top: 76px;          /* navbar 高度 + 一点 padding */
  right: 16px;
  z-index: 30;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: var(--vp-c-bg-elv, #fff);
  color: var(--vp-c-text-2, #555);
  border: 1px solid var(--vp-c-divider, rgba(60, 135, 114, 0.25));
  border-radius: 6px;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, transform 0.15s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.lewisdocs-outline-toggle:hover,
.lewisdocs-outline-toggle:focus-visible {
  color: var(--vp-c-brand-1, #3c8772);
  border-color: var(--vp-c-brand-1, #3c8772);
  outline: none;
  transform: translateY(-1px);
}

.lewisdocs-outline-toggle.collapsed {
  /* 折叠态：图标变方向，但按钮不动位置（仍在右上角） */
  color: var(--vp-c-brand-1, #3c8772);
  border-color: var(--vp-c-brand-1, #3c8772);
}

/* 移动端 / 平板：VitePress 本来就把 outline 收成下拉，按钮也不显示 */
@media (max-width: 959px) {
  .lewisdocs-outline-toggle {
    display: none;
  }
}

.dark .lewisdocs-outline-toggle {
  background: var(--vp-c-bg-soft, #1b1b1f);
}
</style>
