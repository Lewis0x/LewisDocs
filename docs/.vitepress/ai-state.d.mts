export type AiLanguage = 'en' | 'zh-CN'

export const AI_LANGUAGE_STORAGE_KEY: 'lewisdocs:ai-language:v1'
export const AI_LANGUAGE_EVENT: 'lewisdocs:ai-language-change'

export function isAiLanguage(value: unknown): value is AiLanguage
export function resolveAiLanguage(input: {
  stored?: unknown
  pageLanguage?: unknown
  browserLanguage?: unknown
}): AiLanguage
export function readAiLanguage(
  storage: Storage | undefined,
  pageLanguage: unknown,
  browserLanguage: unknown,
): AiLanguage
export function writeAiLanguage(
  storage: Storage | undefined,
  language: unknown,
): boolean
