import assert from 'node:assert/strict'
import test from 'node:test'

import { createSearchRenderer } from '../../../docs/.vitepress/search-render.mjs'

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

test('internal AI search labels learning pages without frontmatter titles', () => {
  const render = createSearchRenderer(true)
  const rendered = render(
    '# Claude Code 学习路径\n\n推荐阅读顺序',
    {
      relativePath: 'ai/zh-CN/learn/claude-code.md',
      frontmatter: {},
    },
    markdown,
  )

  assert.equal(rendered, '# 中文 · Claude Code 学习路径\n\n推荐阅读顺序')
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
