export const AI_LANGUAGE_STORAGE_KEY = 'lewisdocs:ai-language:v1'
export const AI_LANGUAGE_EVENT = 'lewisdocs:ai-language-change'

export const isAiLanguage = (value) => value === 'en' || value === 'zh-CN'

export const resolveAiLanguage = ({
  stored,
  pageLanguage,
  browserLanguage,
}) => {
  if (isAiLanguage(stored)) return stored
  if (isAiLanguage(pageLanguage)) return pageLanguage
  return typeof browserLanguage === 'string' &&
    browserLanguage.toLowerCase().startsWith('zh')
    ? 'zh-CN'
    : 'en'
}

export const readAiLanguage = (
  storage,
  pageLanguage,
  browserLanguage,
) => {
  let stored
  try {
    stored = storage?.getItem(AI_LANGUAGE_STORAGE_KEY)
  } catch {
    stored = undefined
  }
  return resolveAiLanguage({ stored, pageLanguage, browserLanguage })
}

export const writeAiLanguage = (storage, language) => {
  if (!isAiLanguage(language)) return false
  try {
    storage?.setItem(AI_LANGUAGE_STORAGE_KEY, language)
    return storage !== undefined
  } catch {
    return false
  }
}
