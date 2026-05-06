<script setup lang="ts">
/**
 * "本页大纲" 宽度调节器
 *
 * 在大纲（aside）的左边缘放一根 6px 细竖条 → 鼠标拖拽调宽 / 调窄。
 *
 * 行为：
 *   - 默认 224px（VitePress 原值）
 *   - 拖动范围：180px - 560px
 *   - 状态写 localStorage，刷新 / 跨页保留
 *   - mobile (<1280px) 隐藏：VitePress 此时 outline 走下拉菜单
 *   - body.outline-collapsed 时隐藏：折叠态没必要拖
 *
 * 实现：通过 CSS 变量 --lewisdocs-outline-width 暴露给 custom.css，
 * custom.css 用它覆盖 .aside 的 max-width 与 .aside-container 的 width。
 *
 * SSR-safe：所有 DOM 操作都在 onMounted 之后。
 */
import { onMounted, onBeforeUnmount, ref } from 'vue'

const STORAGE_KEY = 'lewisdocs-outline-width'
const DEFAULT_WIDTH = 224
const MIN_WIDTH = 180
const MAX_WIDTH = 560

const width = ref(DEFAULT_WIDTH)
let dragging = false
let dragStartX = 0
let dragStartWidth = 0

function applyWidth(w: number) {
  if (typeof document === 'undefined') return
  document.documentElement.style.setProperty('--lewisdocs-outline-width', w + 'px')
}

function onMouseDown(e: MouseEvent) {
  dragging = true
  dragStartX = e.clientX
  dragStartWidth = width.value
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function onMouseMove(e: MouseEvent) {
  if (!dragging) return
  // 大纲在右侧——鼠标向 LEFT 拖 → 大纲变宽
  const delta = dragStartX - e.clientX
  const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, dragStartWidth + delta))
  width.value = newWidth
  applyWidth(newWidth)
}

function onMouseUp() {
  if (!dragging) return
  dragging = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
  try {
    localStorage.setItem(STORAGE_KEY, String(width.value))
  } catch {
    // ignore
  }
}

function onDoubleClick() {
  // 双击 → 还原默认宽度
  width.value = DEFAULT_WIDTH
  applyWidth(DEFAULT_WIDTH)
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const w = Number(saved)
      if (Number.isFinite(w) && w >= MIN_WIDTH && w <= MAX_WIDTH) {
        width.value = w
      }
    }
  } catch {
    // ignore
  }
  applyWidth(width.value)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<template>
  <div
    class="lewisdocs-outline-resizer"
    @mousedown="onMouseDown"
    @dblclick="onDoubleClick"
    title="拖动调整大纲宽度（双击还原 224px）"
    role="separator"
    aria-orientation="vertical"
  >
    <div class="lewisdocs-outline-resizer-handle"></div>
  </div>
</template>

<style scoped>
/* 6px 宽透明拖拽区，悬停 / 拖动时显示一条 2px 高亮线 */
.lewisdocs-outline-resizer {
  position: fixed;
  top: var(--vp-nav-height, 64px);
  /* 锚在 outline 容器的左边缘——outline 容器在右侧，宽度由 --lewisdocs-outline-width 控制；
   * resizer 应坐在 outline 左边 = 距离屏幕右边 (outline 宽 + 32 padding) px */
  right: calc(var(--lewisdocs-outline-width, 224px) + 32px);
  width: 6px;
  height: calc(100vh - var(--vp-nav-height, 64px));
  z-index: 25;
  cursor: ew-resize;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lewisdocs-outline-resizer-handle {
  width: 2px;
  height: 60px;
  background: transparent;
  border-radius: 1px;
  transition: background 0.15s;
}

.lewisdocs-outline-resizer:hover .lewisdocs-outline-resizer-handle,
.lewisdocs-outline-resizer:active .lewisdocs-outline-resizer-handle {
  background: var(--vp-c-brand-1, #3c8772);
}

/* mobile / 平板 outline 折成下拉菜单，不需要 resizer */
@media (max-width: 1279px) {
  .lewisdocs-outline-resizer {
    display: none;
  }
}

/* outline 折叠态：藏掉 resizer */
:global(body.outline-collapsed) .lewisdocs-outline-resizer {
  display: none;
}
</style>
