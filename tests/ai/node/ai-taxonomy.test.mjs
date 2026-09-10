import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import {
  AI_CATEGORIES,
  classifyAiSource,
} from '../../../docs/.vitepress/ai-taxonomy.mjs'

const sources = JSON.parse(
  readFileSync(new URL('../../../source-ai/sources.yaml', import.meta.url), 'utf8'),
)

const sourceById = new Map(sources.map((source) => [source.id, source]))

test('taxonomy assigns every official source to one ordered topic', () => {
  const categoryIds = AI_CATEGORIES.map((category) => category.id)
  assert.equal(new Set(categoryIds).size, categoryIds.length)
  assert.ok(
    AI_CATEGORIES.every(
      (category) => category.labels.en && category.labels['zh-CN'],
    ),
  )

  for (const source of sources) {
    assert.ok(
      categoryIds.includes(classifyAiSource(source)),
      `${source.id} has an unknown category`,
    )
  }

  for (const product of ['claude-code', 'codex']) {
    const represented = new Set(
      sources
        .filter((source) => source.product === product)
        .map(classifyAiSource),
    )
    assert.deepEqual(represented, new Set(categoryIds))
  }
})

test('taxonomy keeps representative reader journeys in stable topics', () => {
  const cases = {
    'claude-code/quickstart': 'start',
    'claude-code/common-workflows': 'workflows',
    'claude-code/desktop': 'clients',
    'claude-code/memory': 'configuration',
    'claude-code/agent-teams': 'agents',
    'claude-code/mcp': 'extensions',
    'claude-code/agent-sdk/overview': 'sdk',
    'claude-code/github-actions': 'automation',
    'claude-code/security': 'security',
    'claude-code/admin-setup': 'enterprise',
    'claude-code/costs': 'models',
    'claude-code/troubleshooting': 'reference',
    'codex/quickstart': 'start',
    'codex/best-practices': 'workflows',
    'codex/app': 'clients',
    'codex/config-file/config-basic': 'configuration',
    'codex/agent-configuration/subagents': 'agents',
    'codex/build-skills': 'extensions',
    'codex/codex-sdk': 'sdk',
    'codex/github-action': 'automation',
    'codex/sandboxing': 'security',
    'codex/enterprise/admin-setup': 'enterprise',
    'codex/models': 'models',
    'codex/reference/troubleshooting': 'reference',
  }

  for (const [sourceId, expected] of Object.entries(cases)) {
    const source = sourceById.get(sourceId)
    assert.ok(source, `${sourceId} is missing from the official manifest`)
    assert.equal(classifyAiSource(source), expected, sourceId)
  }
})
