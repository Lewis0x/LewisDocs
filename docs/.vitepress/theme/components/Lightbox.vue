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
 * 关键实现细节：
 *   - SVG 用 cloneNode(true) 复制，append 到 stage 容器中（而非 v-html innerHTML）
 *     —— innerHTML 把 SVG 节点当 HTML 解析，丢命名空间 / 不渲染。cloneNode 保留
 *     SVG 节点正确身份。
 *   - SVG 复制后强制 width:100% height:100% style，覆盖 Mermaid 写死的尺寸属性。
 *   - MutationObserver 监听新出现的 .mermaid-diagram svg（Mermaid 在 mount 后才
 *     异步渲染 SVG，必须懒挂 click handler）。
 *   - SSR-safe：所有 DOM 操作只在 onMounted 之后。
 */
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'

const visible = ref(false)
const stageEl = ref<HTMLDivElement | null>(null)
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

function clearStage() {
  if (stageEl.value) stageEl.value.innerHTML = ''
}

function open(node: HTMLImageElement | SVGSVGElement) {
  scale.value = 1
  tx.value = 0
  ty.value = 0
  visible.value = true
  document.body.style.overflow = 'hidden'
  // 等 modal 挂上 DOM 后再插入克隆节点
  nextTick(() => {
    if (!stageEl.value) return
    clearStage()
    const clone = node.cloneNode(true) as HTMLElement | SVGSVGElement
    if (clone instanceof SVGElement) {
      // 覆盖 Mermaid 写死的 width/height 属性，让 SVG 自由缩放到容器
      clone.removeAttribute('width')
      clone.removeAttribute('height')
      clone.setAttribute('preserveAspectRatio', 'xMidYMid meet')
      clone.style.cssText = 'width:90vw;height:85vh;max-width:90vw;max-height:85vh;display:block;'
    } else if (clone instanceof HTMLImageElement) {
      clone.removeAttribute('width')
      clone.removeAttribute('height')
      clone.style.cssText = 'max-width:90vw;max-height:85vh;width:auto;height:auto;display:block;'
      clone.draggable = false
    }
    stageEl.value.appendChild(clone)
  })
}

function close() {
  visible.value = false
  clearStage()
  document.body.style.overflow = ''
}

function onWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = -e.deltaY
  const factor = delta > 0 ? 1.15 : 0.87
  const next = Math.max(0.3, Math.min(8, scale.value * factor))
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
  else if (e.key === '0') { scale.value = 1; tx.value = 0; ty.value = 0 }
  else if (e.key === '+' || e.key === '=') scale.value = Math.min(8, scale.value * 1.2)
  else if (e.key === '-' || e.key === '_') scale.value = Math.max(0.3, scale.value / 1.2)
}

function attach() {
  // 给所有 .vp-doc 内的 img、.mermaid-diagram svg 挂 click handler
  document.querySelectorAll<HTMLImageElement>('.vp-doc img:not([data-lightbox])').forEach((el) => {
    el.dataset.lightbox = '1'
    el.style.cursor = 'zoom-in'
    el.addEventListener('click', (ev) => {
      ev.stopPropagation()
      open(el)
    })
  })
  document.querySelectorAll<SVGSVGElement>('.mermaid-diagram svg:not([data-lightbox])').forEach((el) => {
    el.dataset.lightbox = '1'
    el.style.cursor = 'zoom-in'
    el.addEventListener('click', (ev) => {
      ev.stopPropagation()
      open(el)
    })
  })
}

onMounted(() => {
  attach()
  // Mermaid 在 mount 后异步渲染 SVG；MutationObserver 兜底捕获新增节点
  observer = new MutationObserver(() => {
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
          ref="stageEl"
          class="lewisdocs-lightbox-stage"
          :style="{
            transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
            cursor: dragging ? 'grabbing' : 'grab'
          }"
        ></div>
      </div>
    </transition>
  </Teleport>
</template>

<style>
/* 不 scoped — 让里面的克隆 svg 也能命中 */
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
  display: flex;
  align-items: center;
  justify-content: center;
  /* 使用主题背景变量 → 暗色模式自动用深底而非刺眼白底 */
  background: var(--vp-c-bg, #fff);
  color: var(--vp-c-text-1, #213547);
  border-radius: 4px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
  padding: 12px;
  min-width: 200px;
  min-height: 200px;
}

/* Mermaid SVG 内 nodeLabel 用 currentColor 渲染中文，避免暗色模式下白底白字 */
.lewisdocs-lightbox-stage .nodeLabel,
.lewisdocs-lightbox-stage foreignObject > div {
  color: var(--vp-c-text-1, #213547) !important;
}

.lewisdocs-lightbox-stage > svg,
.lewisdocs-lightbox-stage > img {
  display: block;
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
