<script setup lang="ts">
/**
 * Lightbox / 放大镜
 *
 * 给所有 <img> 与 Mermaid SVG 加 "点击放大" 行为：
 *   - 点击图片 → 弹出全屏遮罩层 + 居中放大原图
 *   - 滚轮缩放（鼠标位置为中心），按住鼠标拖动平移
 *   - ESC / 遮罩层空白处点击 / 关闭按钮 → 收回
 *   - 移动端：双指捏合缩放（pinch-to-zoom）
 *
 * 实现要点：
 *   - 不修改原 markdown，运行时用 MutationObserver 监听 .vp-doc 内
 *     新出现的 img / .mermaid-diagram svg，自动挂 click handler
 *   - 复用一个全局 modal DOM 节点，避免每张图重复挂载
 *   - SSR-safe：所有 DOM 操作都在 onMounted 之后
 */
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'

const visible = ref(false)
const srcImg = ref<string>('')              // 当前展示的 image src（普通图片用）
const srcSvg = ref<string>('')              // 当前展示的 SVG outerHTML（Mermaid 用）
const scale = ref(1)
const tx = ref(0)
const ty = ref(0)
const dragging = ref(false)
let dragStartX = 0
let dragStartY = 0
let dragStartTx = 0
let dragStartTy = 0
let lastTouchDist = 0
let observer: MutationObserver | null = null
let routeWatchInterval: number | null = null
let lastPath = ''

function open(src: string, svgHtml?: string) {
  srcImg.value = svgHtml ? '' : src
  srcSvg.value = svgHtml || ''
  scale.value = 1
  tx.value = 0
  ty.value = 0
  visible.value = true
  document.body.style.overflow = 'hidden'
}

function close() {
  visible.value = false
  document.body.style.overflow = ''
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = -e.deltaY
  const factor = delta > 0 ? 1.15 : 0.87
  const next = Math.max(0.3, Math.min(8, scale.value * factor))
  // 缩放以鼠标位置为锚点
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const mx = e.clientX - rect.left - rect.width / 2
  const my = e.clientY - rect.top - rect.height / 2
  const ratio = next / scale.value
  tx.value = mx - (mx - tx.value) * ratio
  ty.value = my - (my - ty.value) * ratio
  scale.value = next
}

function onMouseDown(e: MouseEvent) {
  if (e.button !== 0) return
  dragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragStartTx = tx.value
  dragStartTy = ty.value
  e.preventDefault()
}

function onMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  tx.value = dragStartTx + (e.clientX - dragStartX)
  ty.value = dragStartTy + (e.clientY - dragStartY)
}

function onMouseUp() {
  dragging.value = false
}

function onTouchStart(e: TouchEvent) {
  if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX
    const dy = e.touches[0].clientY - e.touches[1].clientY
    lastTouchDist = Math.hypot(dx, dy)
  } else if (e.touches.length === 1) {
    dragging.value = true
    dragStartX = e.touches[0].clientX
    dragStartY = e.touches[0].clientY
    dragStartTx = tx.value
    dragStartTy = ty.value
  }
}

function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX
    const dy = e.touches[0].clientY - e.touches[1].clientY
    const dist = Math.hypot(dx, dy)
    if (lastTouchDist) {
      const factor = dist / lastTouchDist
      scale.value = Math.max(0.3, Math.min(8, scale.value * factor))
    }
    lastTouchDist = dist
  } else if (e.touches.length === 1 && dragging.value) {
    tx.value = dragStartTx + (e.touches[0].clientX - dragStartX)
    ty.value = dragStartTy + (e.touches[0].clientY - dragStartY)
  }
}

function onTouchEnd() {
  dragging.value = false
  lastTouchDist = 0
}

function onKeyDown(e: KeyboardEvent) {
  if (!visible.value) return
  if (e.key === 'Escape') close()
  else if (e.key === '0') {
    scale.value = 1
    tx.value = 0
    ty.value = 0
  } else if (e.key === '+' || e.key === '=') {
    scale.value = Math.min(8, scale.value * 1.2)
  } else if (e.key === '-' || e.key === '_') {
    scale.value = Math.max(0.3, scale.value / 1.2)
  }
}

function attach() {
  // 给所有 .vp-doc 内的 img、.mermaid-diagram svg 挂 click handler
  document.querySelectorAll<HTMLElement>('.vp-doc img:not([data-lightbox])').forEach((el) => {
    el.dataset.lightbox = '1'
    el.style.cursor = 'zoom-in'
    el.addEventListener('click', (ev) => {
      ev.stopPropagation()
      const img = el as HTMLImageElement
      if (img.src) open(img.src)
    })
  })
  document.querySelectorAll<SVGSVGElement>('.mermaid-diagram svg:not([data-lightbox])').forEach((el) => {
    el.dataset.lightbox = '1'
    el.style.cursor = 'zoom-in'
    el.addEventListener('click', (ev) => {
      ev.stopPropagation()
      // 把当前 SVG 的 outerHTML 喂给 modal —— 全屏放大版
      open('', el.outerHTML)
    })
  })
}

function detach() {
  // 不需要主动 detach（页面切换时 .vp-doc 内容会被重建）
  // 但要在路由切换后重新 attach
}

onMounted(() => {
  attach()
  // VitePress 单页路由切换时不会触发 mounted；用 MutationObserver 兜底
  observer = new MutationObserver(() => {
    // debounce: 让 DOM 稳定后再扫
    requestAnimationFrame(attach)
  })
  observer.observe(document.body, { childList: true, subtree: true })
  window.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<template>
  <Teleport to="body">
    <transition name="lewisdocs-lightbox">
      <div
        v-if="visible"
        class="lewisdocs-lightbox-overlay"
        @click.self="close"
        @wheel="onWheel"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
        @touchstart.passive="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
        @touchcancel="onTouchEnd"
        role="dialog"
        aria-modal="true"
        aria-label="图像放大查看"
      >
        <button
          class="lewisdocs-lightbox-close"
          @click.stop="close"
          aria-label="关闭"
          title="关闭 (Esc)"
        >
          ×
        </button>
        <div class="lewisdocs-lightbox-hint">
          滚轮缩放 · 拖动平移 · Esc 关闭 · 0 还原
        </div>
        <div
          class="lewisdocs-lightbox-stage"
          :style="{
            transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
            cursor: dragging ? 'grabbing' : 'grab'
          }"
        >
          <img v-if="srcImg" :src="srcImg" alt="" draggable="false" />
          <div v-else-if="srcSvg" v-html="srcSvg" />
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style>
/* 不 scoped — 让里面的 svg 命中 */
.lewisdocs-lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  user-select: none;
}

.lewisdocs-lightbox-stage {
  transform-origin: center center;
  transition: transform 0.05s linear;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lewisdocs-lightbox-stage img,
.lewisdocs-lightbox-stage svg {
  max-width: 95vw;
  max-height: 90vh;
  width: auto;
  height: auto;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
}

.lewisdocs-lightbox-close {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 1;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.lewisdocs-lightbox-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.lewisdocs-lightbox-hint {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  background: rgba(0, 0, 0, 0.4);
  padding: 6px 14px;
  border-radius: 16px;
  pointer-events: none;
}

/* 入场 / 退场动画 */
.lewisdocs-lightbox-enter-active,
.lewisdocs-lightbox-leave-active {
  transition: opacity 0.2s;
}
.lewisdocs-lightbox-enter-from,
.lewisdocs-lightbox-leave-to {
  opacity: 0;
}

/* 鼠标在正文图上变 zoom-in，提示可点击 */
.vp-doc img[data-lightbox],
.mermaid-diagram svg[data-lightbox] {
  cursor: zoom-in;
  transition: filter 0.15s;
}
.vp-doc img[data-lightbox]:hover,
.mermaid-diagram svg[data-lightbox]:hover {
  filter: brightness(0.97);
}
</style>
