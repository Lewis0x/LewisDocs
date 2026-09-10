import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildLearningSearchMarkdown,
  createSearchRenderer,
} from '../../../docs/.vitepress/search-render.mjs'

const markdown = {
  render(source) {
    return source
  },
}

test('internal AI search replaces the page H1 with its language-labelled title', () => {
  const render = createSearchRenderer(true)
  const source = '# Synthetic claude-code/permissions\n\nSynthetic permissions marker.'
  const rendered = render(
    source,
    {
      relativePath: 'ai/en/claude-code/permissions.md',
      frontmatter: { title: 'EN · Claude Code Permissions' },
    },
    markdown,
  )

  assert.equal(
    rendered,
    '# EN · Claude Code Permissions\n\nSynthetic permissions marker.',
  )
})

test('internal AI search indexes one bilingual canonical learning page', () => {
  const learning = buildLearningSearchMarkdown(
    {
      stages: [
        {
          id: 'mcp',
          source_ids: ['codex/mcp'],
          tasks: [{ id: 'connect-mcp' }],
        },
      ],
    },
    {
      title: 'Codex Learning Path',
      summary: 'Learn safely.',
      stages: { mcp: { title: 'Connect MCP', objective: 'Use read-only tools.' } },
      tasks: {
        'connect-mcp': {
          title: 'Connect a tool',
          instruction: 'Configure it.',
          done_when: 'The tool is read-only.',
        },
      },
    },
    {
      title: 'Codex 学习路径',
      summary: '安全学习。',
      stages: { mcp: { title: '连接 MCP', objective: '使用只读工具。' } },
      tasks: {
        'connect-mcp': {
          title: '连接工具',
          instruction: '完成配置。',
          done_when: '工具保持只读。',
        },
      },
    },
  )
  const render = createSearchRenderer(true, {
    'ai/learn/codex.md': learning,
  })
  const rendered = render(
    '<AiLearningPath product="codex" />',
    {
      relativePath: 'ai/learn/codex.md',
      frontmatter: { ai_learning: true },
    },
    markdown,
  )

  assert.match(rendered, /^# Codex 学习路径 \/ Codex Learning Path/m)
  assert.match(rendered, /## 连接 MCP \/ Connect MCP \{#stage-mcp\}/)
  assert.match(rendered, /codex\/mcp/)
})

test('local search excludes implementation plans and pages opting out', () => {
  const render = createSearchRenderer(true)

  assert.equal(
    render(
      '# AI Agent Bilingual Handbook MVP Implementation Plan',
      {
        relativePath: 'superpowers/plans/2026-07-26-ai-agent-handbook.md',
        frontmatter: {},
      },
      markdown,
    ),
    '',
  )
  assert.equal(
    render(
      '# Hidden',
      {
        relativePath: 'hidden.md',
        frontmatter: { search: false },
      },
      markdown,
    ),
    '',
  )
})

test('default search leaves AI source headings unchanged', () => {
  const render = createSearchRenderer(false)
  const source = '# Synthetic claude-code/permissions\n\nSynthetic permissions marker.'

  assert.equal(
    render(
      source,
      {
        relativePath: 'ai/en/claude-code/permissions.md',
        frontmatter: { title: 'EN · Claude Code Permissions' },
      },
      markdown,
    ),
    source,
  )
})
