import type { DefaultTheme } from 'vitepress'

export function buildLearningSearchMarkdown(
  path: {
    stages: Array<{
      id: string
      source_ids: string[]
      tasks: Array<{ id: string }>
    }>
  },
  en: {
    title: string
    summary: string
    stages: Record<string, { title: string; objective: string }>
    tasks: Record<
      string,
      { title: string; instruction: string; done_when: string }
    >
  },
  zh: {
    title: string
    summary: string
    stages: Record<string, { title: string; objective: string }>
    tasks: Record<
      string,
      { title: string; instruction: string; done_when: string }
    >
  },
): string

export function createSearchRenderer(
  includeAiHandbook: boolean,
  learningPages?: Readonly<Record<string, string>>,
): NonNullable<DefaultTheme.LocalSearchOptions['_render']>
