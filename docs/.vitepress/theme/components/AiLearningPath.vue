<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  AI_LANGUAGE_EVENT,
  readAiLanguage,
} from '../../ai-state.mjs'
import claudeEnJson from '../../../../source-ai/learning/claude-code.en.json'
import claudePathJson from '../../../../source-ai/learning/claude-code.path.json'
import claudeZhJson from '../../../../source-ai/learning/claude-code.zh-CN.json'
import codexEnJson from '../../../../source-ai/learning/codex.en.json'
import codexPathJson from '../../../../source-ai/learning/codex.path.json'
import codexZhJson from '../../../../source-ai/learning/codex.zh-CN.json'
import manifestRaw from '../../../../source-ai/sources.yaml?raw'
import translationStatus from '../../../ai/translation-status.json'

type AiLanguage = 'en' | 'zh-CN'
type AiProduct = 'claude-code' | 'codex'
type LearningTask = { id: string; kind: 'practice' | 'verify' }
type LearningStage = {
  id: string
  source_ids: string[]
  tasks: LearningTask[]
}
type LearningPathData = {
  version: 1
  product: AiProduct
  stages: LearningStage[]
}
type StageCopy = { title: string; objective: string; risk: string }
type TaskCopy = { title: string; instruction: string; done_when: string }
type LearningCopy = {
  version: 1
  product: AiProduct
  title: string
  summary: string
  stages: Record<string, StageCopy>
  tasks: Record<string, TaskCopy>
}
type SourceRow = { id: string; title: string }
type TranslationStatus = { version: 1; source_ids: string[] }

const props = defineProps<{ product: AiProduct }>()

const bundles = {
  'claude-code': {
    path: claudePathJson as LearningPathData,
    en: claudeEnJson as LearningCopy,
    'zh-CN': claudeZhJson as LearningCopy,
  },
  codex: {
    path: codexPathJson as LearningPathData,
    en: codexEnJson as LearningCopy,
    'zh-CN': codexZhJson as LearningCopy,
  },
} as const

const sources = new Map(
  (JSON.parse(manifestRaw) as SourceRow[]).map((source) => [
    source.id,
    source,
  ]),
)
const translatedSources = new Set(
  (translationStatus as TranslationStatus).source_ids,
)

const bundle = computed(() => bundles[props.product])
const path = computed(() => bundle.value.path)
const language = ref<AiLanguage>('en')
const copy = computed(() => bundle.value[language.value])

const labels = computed(() =>
  language.value === 'zh-CN'
    ? {
        stageNavigation: '阶段导航',
        jumpToStage: '跳转到阶段',
        recommended: '推荐阅读',
        practice: '实践',
        verify: '验证',
        doneWhen: '完成标准',
        risk: '权限与风险',
        fallback: '英文回退',
      }
    : {
        stageNavigation: 'Stage navigation',
        jumpToStage: 'Jump to stage',
        recommended: 'Recommended reading',
        practice: 'Practice',
        verify: 'Verify',
        doneWhen: 'Done when',
        risk: 'Permissions and risk',
        fallback: 'English fallback',
      },
)

const sourceTarget = (sourceId: string) => {
  const useChinese =
    language.value === 'zh-CN' && translatedSources.has(sourceId)
  return {
    href: `/ai/${useChinese ? 'zh-CN' : 'en'}/${sourceId}`,
    fallback: language.value === 'zh-CN' && !useChinese,
    title: sources.get(sourceId)?.title ?? sourceId,
  }
}

const jumpToStage = (event: Event) => {
  const stageId = (event.target as HTMLSelectElement).value
  if (!stageId) return
  const target = document.getElementById(`stage-${stageId}`)
  target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  history.replaceState(null, '', `#stage-${stageId}`)
}

const onLanguageChange = (event: Event) => {
  const next = (event as CustomEvent<AiLanguage>).detail
  if (next === 'en' || next === 'zh-CN') language.value = next
}

const onStorage = (event: StorageEvent) => {
  if (event.key !== 'lewisdocs:ai-language:v1') return
  if (event.newValue === 'en' || event.newValue === 'zh-CN') {
    language.value = event.newValue
  }
}

onMounted(() => {
  language.value = readAiLanguage(
    globalThis.localStorage,
    undefined,
    navigator.language,
  )
  window.addEventListener(AI_LANGUAGE_EVENT, onLanguageChange)
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  window.removeEventListener(AI_LANGUAGE_EVENT, onLanguageChange)
  window.removeEventListener('storage', onStorage)
})
</script>

<template>
  <main class="ai-learning" :lang="language">
    <header class="ai-learning__header">
      <p class="ai-learning__eyebrow">
        {{ product === 'claude-code' ? 'Claude Code' : 'Codex' }}
      </p>
      <h1>{{ copy.title }}</h1>
      <p class="ai-learning__summary">{{ copy.summary }}</p>
    </header>

    <label class="ai-learning__mobile-nav">
      <span>{{ labels.jumpToStage }}</span>
      <select @change="jumpToStage">
        <option value="">{{ labels.jumpToStage }}</option>
        <option v-for="stage in path.stages" :key="stage.id" :value="stage.id">
          {{ copy.stages[stage.id]?.title }}
        </option>
      </select>
    </label>

    <div class="ai-learning__layout">
      <nav class="ai-learning__stage-nav" :aria-label="labels.stageNavigation">
        <p>{{ labels.stageNavigation }}</p>
        <ol>
          <li v-for="(stage, index) in path.stages" :key="stage.id">
            <a :href="`#stage-${stage.id}`">
              <span>{{ index + 1 }}</span>
              {{ copy.stages[stage.id]?.title }}
            </a>
          </li>
        </ol>
      </nav>

      <div class="ai-learning__stages">
        <section
          v-for="(stage, index) in path.stages"
          :id="`stage-${stage.id}`"
          :key="stage.id"
          class="ai-learning__stage"
        >
          <div class="ai-learning__stage-heading">
            <span>{{ index + 1 }}</span>
            <div>
              <h2>{{ copy.stages[stage.id]?.title }}</h2>
            </div>
          </div>
          <p class="ai-learning__objective">
            {{ copy.stages[stage.id]?.objective }}
          </p>

          <div class="ai-learning__reading">
            <h3>{{ labels.recommended }}</h3>
            <ul>
              <li v-for="sourceId in stage.source_ids" :key="sourceId">
                <a :href="sourceTarget(sourceId).href">
                  {{ sourceTarget(sourceId).title }}
                </a>
                <span
                  v-if="sourceTarget(sourceId).fallback"
                  class="ai-learning__fallback"
                >
                  EN · {{ labels.fallback }}
                </span>
              </li>
            </ul>
          </div>

          <div class="ai-learning__tasks">
            <article
              v-for="task in stage.tasks"
              :key="task.id"
              class="ai-learning__task"
              :data-task-id="task.id"
            >
              <span class="ai-learning__task-body">
                <span class="ai-learning__task-kind">
                  {{ labels[task.kind] }}
                </span>
                <strong>{{ copy.tasks[task.id]?.title }}</strong>
                <span>{{ copy.tasks[task.id]?.instruction }}</span>
                <span class="ai-learning__done-when">
                  <b>{{ labels.doneWhen }}:</b>
                  {{ copy.tasks[task.id]?.done_when }}
                </span>
              </span>
            </article>
          </div>

          <p class="ai-learning__risk">
            <strong>{{ labels.risk }}:</strong>
            {{ copy.stages[stage.id]?.risk }}
          </p>
        </section>
      </div>
    </div>
  </main>
</template>
