<script setup lang="ts">
import { useData } from 'vitepress'
import { computed } from 'vue'
import translationStatus from '../../../ai/translation-status.json'

type AiProduct = 'claude-code' | 'codex'
type AiLanguage = 'en' | 'zh-CN'
type TranslationStatus = { version: 1; source_ids: string[] }

const { frontmatter } = useData()
const translatedSources = new Set(
  (translationStatus as TranslationStatus).source_ids,
)

const context = computed<{
  product: AiProduct
  language: AiLanguage
} | null>(() => {
  const value: unknown = frontmatter.value
  if (typeof value !== 'object' || value === null || !('source_id' in value)) {
    return null
  }
  const product = 'product' in value ? value.product : undefined
  const language = 'lang' in value ? value.lang : undefined
  if (
    (product !== 'claude-code' && product !== 'codex') ||
    (language !== 'en' && language !== 'zh-CN')
  ) {
    return null
  }
  return { product, language }
})

const productHref = (product: AiProduct) => {
  const preferredLanguage =
    context.value?.language === 'zh-CN' &&
    translatedSources.has(`${product}/quickstart`)
      ? 'zh-CN'
      : 'en'
  return `/ai/${preferredLanguage}/${product}/quickstart`
}
</script>

<template>
  <nav v-if="context" class="ai-product-switch" aria-label="AI 产品">
    <a
      v-for="productOption in (['claude-code', 'codex'] as const)"
      :key="productOption"
      :href="productHref(productOption)"
      :class="{ 'is-current': context.product === productOption }"
      :aria-current="context.product === productOption ? 'page' : undefined"
    >
      {{ productOption === 'claude-code' ? 'Claude Code' : 'Codex' }}
    </a>
  </nav>
</template>
