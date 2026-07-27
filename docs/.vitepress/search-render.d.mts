import type { DefaultTheme } from 'vitepress'

export function createSearchRenderer(
  includeAiHandbook: boolean,
): NonNullable<DefaultTheme.LocalSearchOptions['_render']>
