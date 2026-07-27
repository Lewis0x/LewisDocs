<script setup lang="ts">
import { useData } from 'vitepress'
import { computed } from 'vue'

const { frontmatter } = useData()

const languageSwitch = computed(() => {
  const value: unknown = frontmatter.value
  if (typeof value !== 'object' || value === null) return null
  if (!('ai_counterpart' in value) || !('lang' in value)) return null

  const counterpart = value.ai_counterpart
  const lang = value.lang
  if (typeof counterpart !== 'string' || !counterpart.trim()) return null
  if (lang === 'en') return { href: counterpart, label: '中文' }
  if (lang === 'zh-CN') return { href: counterpart, label: 'English' }
  return null
})
</script>

<template>
  <nav v-if="languageSwitch" class="ai-language-switch" aria-label="Language">
    <a class="ai-language-switch__link" :href="languageSwitch.href">
      {{ languageSwitch.label }}
    </a>
  </nav>
</template>
