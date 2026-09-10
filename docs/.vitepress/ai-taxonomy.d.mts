export type AiTaxonomySource = {
  product: 'claude-code' | 'codex'
  slug: string
  title: string
  section: string
}

export type AiCategory = {
  id: string
  label: string
  labels: {
    en: string
    'zh-CN': string
  }
}

export const AI_CATEGORIES: readonly AiCategory[]

export function classifyAiSource(source: AiTaxonomySource): string
