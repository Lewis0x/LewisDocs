<script setup lang="ts">
import { useData } from 'vitepress'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  AI_LANGUAGE_EVENT,
  AI_LANGUAGE_STORAGE_KEY,
  readAiLanguage,
  writeAiLanguage,
} from '../../ai-state.mjs'

const { frontmatter } = useData()
type AiLanguage = 'zh-CN' | 'en'

type LanguageOption = {
  code: AiLanguage
  label: string
  href?: string
  current: boolean
  disabled: boolean
}

type LanguageContext =
  | { mode: 'source'; lang: AiLanguage; counterpart?: string }
  | { mode: 'learning' }

const activeLanguage = ref<AiLanguage>('en')

const context = computed<LanguageContext | null>(() => {
  const value: unknown = frontmatter.value
  if (typeof value !== 'object' || value === null) return null
  if ('ai_learning' in value && value.ai_learning === true) {
    return { mode: 'learning' }
  }
  if (!('source_id' in value) || !('lang' in value)) return null
  const lang = value.lang
  if (lang !== 'en' && lang !== 'zh-CN') return null
  const counterpart =
    'ai_counterpart' in value &&
    typeof value.ai_counterpart === 'string' &&
    value.ai_counterpart.trim()
      ? value.ai_counterpart
      : undefined
  return counterpart === undefined
    ? { mode: 'source', lang }
    : { mode: 'source', lang, counterpart }
})

const languageOptions = computed<LanguageOption[] | null>(() => {
  if (context.value === null) return null
  if (context.value.mode === 'learning') {
    return [
      {
        code: 'zh-CN',
        label: '中文',
        current: activeLanguage.value === 'zh-CN',
        disabled: false,
      },
      {
        code: 'en',
        label: 'English',
        current: activeLanguage.value === 'en',
        disabled: false,
      },
    ]
  }

  const { lang, counterpart } = context.value
  const chineseHref = lang === 'zh-CN' ? undefined : counterpart
  const englishHref = lang === 'en' ? undefined : counterpart
  return [
    {
      code: 'zh-CN',
      label: '中文',
      href: chineseHref,
      current: lang === 'zh-CN',
      disabled: lang === 'en' && chineseHref === undefined,
    },
    {
      code: 'en',
      label: 'English',
      href: englishHref,
      current: lang === 'en',
      disabled: false,
    },
  ]
})

const rememberLanguage = (language: AiLanguage) => {
  writeAiLanguage(globalThis.localStorage, language)
}

const selectLearningLanguage = (language: AiLanguage) => {
  if (context.value?.mode !== 'learning') return
  activeLanguage.value = language
  rememberLanguage(language)
  window.dispatchEvent(
    new CustomEvent<AiLanguage>(AI_LANGUAGE_EVENT, { detail: language }),
  )
}

const onStorage = (event: StorageEvent) => {
  if (
    context.value?.mode === 'learning' &&
    event.key === AI_LANGUAGE_STORAGE_KEY &&
    (event.newValue === 'en' || event.newValue === 'zh-CN')
  ) {
    activeLanguage.value = event.newValue
  }
}

onMounted(() => {
  const pageLanguage =
    context.value?.mode === 'source' ? context.value.lang : undefined
  activeLanguage.value = readAiLanguage(
    globalThis.localStorage,
    pageLanguage,
    navigator.language,
  )
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', onStorage)
})
</script>

<template>
  <nav v-if="languageOptions" class="ai-language-switch" aria-label="文档语言">
    <div class="ai-language-switch__group">
      <template v-for="option in languageOptions" :key="option.code">
        <a
          v-if="option.href"
          class="ai-language-switch__item"
          :href="option.href"
          :lang="option.code"
          @click="rememberLanguage(option.code)"
        >
          {{ option.label }}
        </a>
        <button
          v-else-if="context?.mode === 'learning'"
          class="ai-language-switch__item"
          :class="{ 'is-current': option.current }"
          :aria-pressed="option.current"
          :lang="option.code"
          type="button"
          @click="selectLearningLanguage(option.code)"
        >
          {{ option.label }}
        </button>
        <span
          v-else
          class="ai-language-switch__item"
          :class="{
            'is-current': option.current,
            'is-disabled': option.disabled,
          }"
          :aria-current="option.current ? 'page' : undefined"
          :aria-disabled="option.disabled || undefined"
          :lang="option.code"
          :title="option.disabled ? '中文翻译尚未完成' : undefined"
        >
          {{ option.label }}
        </span>
      </template>
    </div>
  </nav>
</template>
