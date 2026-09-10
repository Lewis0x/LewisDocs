import type { Options, SearchOptions } from 'minisearch'

export type AiSearchConcept = Readonly<{
  id: string
  aliases: readonly string[]
  preferredSources: readonly string[]
}>

export const AI_SEARCH_CONCEPTS: readonly AiSearchConcept[]
export const AI_MINISEARCH_OPTIONS: Readonly<
  Pick<Options, 'tokenize' | 'processTerm'>
>
export const AI_MINISEARCH_SEARCH_OPTIONS: Readonly<SearchOptions>
export function normalizeSearchText(text: unknown): string
export function tokenizeAiDocument(text: string): string[]
export function tokenizeAiQuery(text: string): string[]
export function processAiSearchTerm(term: unknown): string | null
export function validateAiSearchConcepts(sourceIds: Iterable<string>): void
