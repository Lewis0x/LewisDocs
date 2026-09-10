import assert from 'node:assert/strict'
import test from 'node:test'

import MiniSearch from 'minisearch'

import {
  AI_MINISEARCH_OPTIONS,
  AI_MINISEARCH_SEARCH_OPTIONS,
  AI_SEARCH_CONCEPTS,
  normalizeSearchText,
  tokenizeAiDocument,
  tokenizeAiQuery,
  validateAiSearchConcepts,
} from '../../../docs/.vitepress/search-concepts.mjs'

test('search aliases normalize to one concept token', () => {
  for (const concept of AI_SEARCH_CONCEPTS) {
    const expected = `__ai_${concept.id}`
    for (const alias of concept.aliases) {
      assert.deepEqual(tokenizeAiQuery(alias), [expected], alias)
    }
  }
  assert.deepEqual(tokenizeAiQuery('model'), ['model'])
  assert.deepEqual(tokenizeAiQuery('context'), ['context'])
  assert.equal(tokenizeAiQuery('代理').some((term) => term.startsWith('__ai_')), false)
})

test('multiword queries replace the longest alias span and keep other terms', () => {
  const terms = tokenizeAiQuery('configure Model Context Protocol safely')
  assert.ok(terms.includes('__ai_mcp'))
  assert.ok(terms.includes('configure'))
  assert.ok(terms.includes('safely'))
  assert.equal(terms.includes('model'), false)
  assert.equal(terms.includes('context'), false)
})

test('document tokenizer keeps ordinary terms and appends concept tokens', () => {
  const terms = tokenizeAiDocument('Use AGENTS.md for repository instructions')
  assert.ok(terms.includes('agents'))
  assert.ok(terms.includes('__ai_agents-md'))
  assert.equal(normalizeSearchText('ＡＧＥＮＴＳ．ＭＤ'), 'agents md')
})

test('MiniSearch callbacks survive VitePress-style function serialization', () => {
  const revive = (callback) => Function(`return (${callback.toString()})`)()
  const documentTokenizer = revive(AI_MINISEARCH_OPTIONS.tokenize)
  const queryTokenizer = revive(AI_MINISEARCH_SEARCH_OPTIONS.tokenize)
  const boostDocument = revive(AI_MINISEARCH_SEARCH_OPTIONS.boostDocument)

  assert.ok(
    documentTokenizer('Model Context Protocol').includes('__ai_mcp'),
  )
  assert.deepEqual(queryTokenizer('模型上下文协议'), ['__ai_mcp'])
  assert.equal(boostDocument('/ai/en/claude-code/mcp', '__ai_mcp'), 6)
})

test('concept validation rejects unknown preferred sources', () => {
  const allPreferred = new Set(
    AI_SEARCH_CONCEPTS.flatMap((concept) => concept.preferredSources),
  )
  assert.doesNotThrow(() => validateAiSearchConcepts(allPreferred))
  assert.throws(() => validateAiSearchConcepts([]), /Unknown preferred/)
})

test('real MiniSearch ranking promotes preferred concept sources', () => {
  const index = new MiniSearch({
    fields: ['title', 'titles', 'text'],
    storeFields: ['title', 'titles'],
    ...AI_MINISEARCH_OPTIONS,
  })
  const conceptDocuments = AI_SEARCH_CONCEPTS.map((concept) => ({
    id: `/ai/en/${concept.preferredSources[0]}`,
    title: concept.aliases[0],
    titles: ['AI handbook'],
    text: concept.aliases.join(' '),
  }))
  index.addAll([
    ...conceptDocuments,
    {
      id: '/ai/en/claude-code/model-config',
      title: 'Model context configuration',
      titles: ['Claude Code'],
      text: 'Model context configuration and settings',
    },
  ])

  for (const concept of AI_SEARCH_CONCEPTS) {
    const preferredId = `/ai/en/${concept.preferredSources[0]}`
    for (const alias of concept.aliases) {
      const results = index.search(alias, AI_MINISEARCH_SEARCH_OPTIONS)
      assert.ok(results.length > 0, alias)
      assert.equal(results[0]?.id, preferredId, alias)
    }
  }

  assert.equal(
    index.search('model', AI_MINISEARCH_SEARCH_OPTIONS)[0]?.id,
    '/ai/en/claude-code/model-config',
  )
  assert.equal(
    index.search('context', AI_MINISEARCH_SEARCH_OPTIONS)[0]?.id,
    '/ai/en/claude-code/model-config',
  )
})
