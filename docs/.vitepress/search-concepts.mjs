export const AI_SEARCH_CONCEPTS = Object.freeze([
  {
    id: 'mcp',
    aliases: ['mcp', 'model context protocol', '模型上下文协议'],
    preferredSources: ['claude-code/mcp', 'codex/mcp'],
  },
  {
    id: 'agents-md',
    aliases: [
      'agents.md',
      'agents md',
      'project instructions',
      'repository instructions',
      '项目指令',
      '仓库指令',
    ],
    preferredSources: ['codex/agents-md'],
  },
  {
    id: 'claude-md',
    aliases: ['claude.md', 'claude md', 'project memory', '项目记忆'],
    preferredSources: ['claude-code/memory'],
  },
  {
    id: 'subagents',
    aliases: ['subagent', 'subagents', 'sub-agent', '子代理', '子智能体'],
    preferredSources: [
      'claude-code/subagents',
      'codex/agent-configuration/subagents',
    ],
  },
  {
    id: 'hooks',
    aliases: ['hook', 'hooks', '钩子', '生命周期钩子'],
    preferredSources: ['claude-code/hooks-guide', 'codex/hooks'],
  },
  {
    id: 'permissions',
    aliases: [
      'permission',
      'permissions',
      'approval',
      'approvals',
      '权限',
      '审批',
    ],
    preferredSources: ['claude-code/permissions', 'codex/approvals-security'],
  },
  {
    id: 'sandbox',
    aliases: ['sandbox', 'sandboxing', '沙箱', '隔离执行'],
    preferredSources: ['claude-code/sandboxing', 'codex/sandboxing'],
  },
  {
    id: 'skills',
    aliases: ['skill', 'skills', '技能'],
    preferredSources: ['claude-code/skills', 'codex/skills-and-plugins'],
  },
  {
    id: 'plugins',
    aliases: ['plugin', 'plugins', '插件'],
    preferredSources: ['claude-code/plugins', 'codex/skills-and-plugins'],
  },
  {
    id: 'ci',
    aliases: ['ci', 'github actions', '持续集成'],
    preferredSources: ['claude-code/github-actions', 'codex/github-action'],
  },
])

export const normalizeSearchText = (text) =>
  String(text)
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\p{P}\p{S}]+/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim()

// VitePress serializes MiniSearch callbacks into the client bundle. Keep these
// functions closure-free so their source can execute without module bindings.
export function tokenizeAiDocument(text) {
  const concepts = [
    ['mcp', ['mcp', 'model context protocol', '模型上下文协议']],
    [
      'agents-md',
      [
        'agents.md',
        'agents md',
        'project instructions',
        'repository instructions',
        '项目指令',
        '仓库指令',
      ],
    ],
    [
      'claude-md',
      ['claude.md', 'claude md', 'project memory', '项目记忆'],
    ],
    [
      'subagents',
      ['subagent', 'subagents', 'sub-agent', '子代理', '子智能体'],
    ],
    ['hooks', ['hook', 'hooks', '钩子', '生命周期钩子']],
    [
      'permissions',
      ['permission', 'permissions', 'approval', 'approvals', '权限', '审批'],
    ],
    ['sandbox', ['sandbox', 'sandboxing', '沙箱', '隔离执行']],
    ['skills', ['skill', 'skills', '技能']],
    ['plugins', ['plugin', 'plugins', '插件']],
    ['ci', ['ci', 'github actions', '持续集成']],
  ]
  const normalize = (value) =>
    String(value)
      .normalize('NFKC')
      .toLowerCase()
      .replace(/[\p{P}\p{S}]+/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  const splitWords = (value) => {
    if (!value) return []
    if (typeof Intl !== 'undefined' && typeof Intl.Segmenter === 'function') {
      const segmenter = new Intl.Segmenter('zh-CN', { granularity: 'word' })
      return [...segmenter.segment(value)]
        .filter((segment) => segment.isWordLike)
        .map((segment) => segment.segment)
    }
    return value.split(/\s+/u).filter(Boolean)
  }
  const escapePattern = (value) =>
    value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  const normalized = normalize(text)
  const terms = splitWords(normalized)
  for (const [conceptId, aliases] of concepts) {
    if (
      aliases.some((alias) => {
        const normalizedAlias = normalize(alias)
        return new RegExp(
          `(?:^|\\s)${escapePattern(normalizedAlias)}(?=\\s|$)`,
          'u',
        ).test(normalized)
      })
    ) {
      terms.push(`__ai_${conceptId}`)
    }
  }
  return [...new Set(terms)]
}

export function tokenizeAiQuery(text) {
  const concepts = [
    ['mcp', ['mcp', 'model context protocol', '模型上下文协议']],
    [
      'agents-md',
      [
        'agents.md',
        'agents md',
        'project instructions',
        'repository instructions',
        '项目指令',
        '仓库指令',
      ],
    ],
    [
      'claude-md',
      ['claude.md', 'claude md', 'project memory', '项目记忆'],
    ],
    [
      'subagents',
      ['subagent', 'subagents', 'sub-agent', '子代理', '子智能体'],
    ],
    ['hooks', ['hook', 'hooks', '钩子', '生命周期钩子']],
    [
      'permissions',
      ['permission', 'permissions', 'approval', 'approvals', '权限', '审批'],
    ],
    ['sandbox', ['sandbox', 'sandboxing', '沙箱', '隔离执行']],
    ['skills', ['skill', 'skills', '技能']],
    ['plugins', ['plugin', 'plugins', '插件']],
    ['ci', ['ci', 'github actions', '持续集成']],
  ]
  const normalize = (value) =>
    String(value)
      .normalize('NFKC')
      .toLowerCase()
      .replace(/[\p{P}\p{S}]+/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  const splitWords = (value) => {
    if (!value) return []
    if (typeof Intl !== 'undefined' && typeof Intl.Segmenter === 'function') {
      const segmenter = new Intl.Segmenter('zh-CN', { granularity: 'word' })
      return [...segmenter.segment(value)]
        .filter((segment) => segment.isWordLike)
        .map((segment) => segment.segment)
    }
    return value.split(/\s+/u).filter(Boolean)
  }
  const escapePattern = (value) =>
    value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  const normalized = normalize(text)
  const aliases = concepts
    .flatMap(([conceptId, values]) =>
      values.map((value) => [normalize(value), `__ai_${conceptId}`]),
    )
    .sort((left, right) => right[0].length - left[0].length)
  const exact = aliases.find(([alias]) => alias === normalized)
  if (exact !== undefined) return [exact[1]]

  let replaced = ` ${normalized} `
  for (const [alias, token] of aliases) {
    replaced = replaced.replace(
      new RegExp(`\\s${escapePattern(alias)}(?=\\s)`, 'gu'),
      ` ${token}`,
    )
  }
  const terms = replaced
    .trim()
    .replace(/\s+/g, ' ')
    .split(/(__ai_[a-z0-9-]+)/u)
    .flatMap((part) => (part.startsWith('__ai_') ? [part] : splitWords(part)))
    .filter(Boolean)
  return [...new Set(terms)]
}

export const processAiSearchTerm = (term) => {
  const normalized = String(term).toLowerCase().trim()
  return normalized || null
}

export const AI_MINISEARCH_OPTIONS = Object.freeze({
  tokenize: tokenizeAiDocument,
  processTerm: processAiSearchTerm,
})

export const AI_MINISEARCH_SEARCH_OPTIONS = Object.freeze({
  tokenize: tokenizeAiQuery,
  processTerm: processAiSearchTerm,
  fuzzy: (term) =>
    term.startsWith('__ai_') || term.length <= 3 ? false : 0.2,
  prefix: (term) => !term.startsWith('__ai_') && term.length > 3,
  boost: { title: 8, titles: 3, text: 2 },
  boostTerm: (term) => (term.startsWith('__ai_') ? 6 : 1),
  boostDocument: (documentId, term) => {
    const preferredSources = {
      __ai_mcp: ['claude-code/mcp', 'codex/mcp'],
      '__ai_agents-md': ['codex/agents-md'],
      '__ai_claude-md': ['claude-code/memory'],
      __ai_subagents: [
        'claude-code/subagents',
        'codex/agent-configuration/subagents',
      ],
      __ai_hooks: ['claude-code/hooks-guide', 'codex/hooks'],
      __ai_permissions: [
        'claude-code/permissions',
        'codex/approvals-security',
      ],
      __ai_sandbox: ['claude-code/sandboxing', 'codex/sandboxing'],
      __ai_skills: ['claude-code/skills', 'codex/skills-and-plugins'],
      __ai_plugins: ['claude-code/plugins', 'codex/skills-and-plugins'],
      __ai_ci: ['claude-code/github-actions', 'codex/github-action'],
    }
    const preferred = preferredSources[term] ?? []
    let boost = preferred.some((sourceId) =>
      String(documentId).includes(`/${sourceId}`),
    )
      ? 6
      : 1
    let language
    try {
      const value = globalThis.localStorage?.getItem(
        'lewisdocs:ai-language:v1',
      )
      language = value === 'en' || value === 'zh-CN' ? value : undefined
    } catch {
      language = undefined
    }
    if (
      language !== undefined &&
      String(documentId).includes(`/ai/${language}/`)
    ) {
      boost *= 1.5
    }
    return boost
  },
})

export const validateAiSearchConcepts = (sourceIds) => {
  const known = new Set(sourceIds)
  const aliases = new Map()
  for (const concept of AI_SEARCH_CONCEPTS) {
    for (const alias of concept.aliases) {
      const normalized = normalizeSearchText(alias)
      const existing = aliases.get(normalized)
      if (existing !== undefined && existing !== concept.id) {
        throw new Error(`AI search alias collision: ${alias}`)
      }
      aliases.set(normalized, concept.id)
    }
    for (const sourceId of concept.preferredSources) {
      if (!known.has(sourceId)) {
        throw new Error(`Unknown preferred AI search source: ${sourceId}`)
      }
    }
  }
}
