<script setup lang="ts">
/**
 * <Term def="术语解释...">B-Rep</Term>
 * <Term def="..." href="/glossary#brep">B-Rep</Term>
 *
 * 行内术语注释 — hover / focus / 触屏 tap 显示定义浮窗。
 *
 * 设计取舍（"克制研究稿" 风格）：
 *   - 视觉：仅一条 1px dashed 下划线 + 主色调；不用图标、不用背景高亮
 *   - 浮窗：浅色卡片，主色边框，固定宽度，**Floating UI 智能反弹** 不会被表格 / 视口边裁
 *   - 触屏：tabindex=0 让 tap 可聚焦
 *   - SSR 友好：浮窗节点初始隐藏，hydration 后挂载
 *   - 可访问性：role=tooltip + aria-describedby
 *
 * 同源策略：行内定义只是"快速预览"；权威定义在 /glossary。
 */
import { ref, useId, type Ref } from 'vue'
import {
  useFloating,
  autoUpdate,
  offset,
  flip,
  shift,
  arrow,
  type Placement,
} from '@floating-ui/vue'

defineProps<{
  /** 浮窗定义文本（短，建议 1-2 句） */
  def: string
  /** 可选：点击跳转目标，通常是 /glossary#anchor */
  href?: string
}>()

const reference: Ref<HTMLElement | null> = ref(null)
const floating: Ref<HTMLElement | null> = ref(null)
const arrowRef: Ref<HTMLElement | null> = ref(null)
const open = ref(false)
const tipId = `term-tip-${useId()}`

const { floatingStyles, middlewareData, placement } = useFloating(reference, floating, {
  placement: 'top' as Placement,
  whileElementsMounted: autoUpdate,
  middleware: [
    offset(8),
    flip({ fallbackPlacements: ['bottom', 'top-start', 'bottom-start', 'top-end', 'bottom-end'] }),
    shift({ padding: 8 }),
    arrow({ element: arrowRef }),
  ],
})

function show() { open.value = true }
function hide() { open.value = false }
</script>

<template>
  <span class="lewisdocs-term">
    <component
      :is="href ? 'a' : 'span'"
      ref="reference"
      class="lewisdocs-term-anchor"
      :href="href"
      tabindex="0"
      role="button"
      :aria-describedby="tipId"
      @mouseenter="show"
      @mouseleave="hide"
      @focusin="show"
      @focusout="hide"
    >
      <slot />
    </component>
    <span
      v-if="open"
      :id="tipId"
      ref="floating"
      class="lewisdocs-term-tip"
      role="tooltip"
      :style="floatingStyles"
      :data-placement="placement"
    >
      {{ def }}
      <span
        ref="arrowRef"
        class="lewisdocs-term-arrow"
        :style="{
          left: middlewareData.arrow?.x != null ? `${middlewareData.arrow.x}px` : '',
          top: middlewareData.arrow?.y != null ? `${middlewareData.arrow.y}px` : '',
        }"
      />
    </span>
  </span>
</template>

<style scoped>
.lewisdocs-term {
  display: inline;
}

.lewisdocs-term-anchor {
  cursor: help;
  text-decoration: underline dashed;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
  text-decoration-color: var(--vp-c-brand-1, #3c8772);
  color: inherit;
}

a.lewisdocs-term-anchor {
  color: inherit;
}

.lewisdocs-term-anchor:hover,
.lewisdocs-term-anchor:focus-visible {
  color: var(--vp-c-brand-1, #3c8772);
  outline: none;
}

.lewisdocs-term-tip {
  width: max-content;
  max-width: min(320px, 80vw);
  padding: 10px 14px;
  background: var(--vp-c-bg-elv, #fff);
  color: var(--vp-c-text-1, #213547);
  border: 1px solid var(--vp-c-divider, rgba(60, 135, 114, 0.3));
  border-left: 3px solid var(--vp-c-brand-1, #3c8772);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  font-size: 13px;
  line-height: 1.55;
  font-weight: normal;
  text-align: left;
  white-space: normal;
  pointer-events: none;
  z-index: 50;
}

.lewisdocs-term-arrow {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--vp-c-bg-elv, #fff);
  border-right: 1px solid var(--vp-c-divider, rgba(60, 135, 114, 0.3));
  border-bottom: 1px solid var(--vp-c-divider, rgba(60, 135, 114, 0.3));
  transform: rotate(45deg);
}
.lewisdocs-term-tip[data-placement^='top'] .lewisdocs-term-arrow {
  bottom: -5px;
}
.lewisdocs-term-tip[data-placement^='bottom'] .lewisdocs-term-arrow {
  top: -5px;
  transform: rotate(225deg);
}

.dark .lewisdocs-term-tip,
.dark .lewisdocs-term-arrow {
  background: var(--vp-c-bg-soft, #1b1b1f);
  color: var(--vp-c-text-1, #fff);
  border-color: var(--vp-c-divider, rgba(94, 165, 142, 0.4));
}

@media print {
  .lewisdocs-term-tip {
    display: none;
  }
  .lewisdocs-term-anchor {
    text-decoration-style: dotted;
  }
}
</style>
