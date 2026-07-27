import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { runGate } from '../../../scripts/ai_content_gate.mjs'

function repoFixture() {
  const repoRoot = mkdtempSync(path.join(tmpdir(), 'lewisdocs-ai-gate-'))
  mkdirSync(path.join(repoRoot, 'docs', '.vitepress', 'dist'), { recursive: true })
  return repoRoot
}

function searchChunk(repoRoot, documentIds) {
  const chunk = path.join(
    repoRoot,
    'docs',
    '.vitepress',
    'dist',
    'assets',
    'chunks',
    '@localSearchIndexroot.test.js',
  )
  mkdirSync(path.dirname(chunk), { recursive: true })
  const payload = JSON.stringify({ documentIds, index: [['"', {}]] })
  writeFileSync(chunk, `const t=\`${payload.replaceAll('\\', '\\\\')}\`;export{t as default};\n`)
}

test('default prepare removes stale docs/ai without spawning', () => {
  // Given
  const repoRoot = repoFixture()
  const sentinel = path.join(repoRoot, 'docs', 'ai', 'sentinel.md')
  mkdirSync(path.dirname(sentinel), { recursive: true })
  writeFileSync(sentinel, 'stale\n')
  let spawnCount = 0

  // When
  const result = runGate('prepare', {
    repoRoot,
    env: {},
    spawnSync: () => {
      spawnCount += 1
      return { signal: null, status: 0 }
    },
  })

  // Then
  assert.deepEqual(result, { signal: null, status: 0 })
  assert.equal(spawnCount, 0)
  assert.throws(() => readFileSync(sentinel))
})

for (const value of [undefined, '0', 'true', '01', ' 1 ', ' ']) {
  test(`prepare keeps default mode for non-exact opt-in ${String(value)}`, () => {
    // Given
    const repoRoot = repoFixture()
    const env = value === undefined ? {} : { INCLUDE_AI_HANDBOOK: value }
    let spawnCount = 0

    // When
    runGate('prepare', {
      repoRoot,
      env,
      spawnSync: () => {
        spawnCount += 1
        return { signal: null, status: 0 }
      },
    })

    // Then
    assert.equal(spawnCount, 0)
  })
}

test('internal mode spawns exact native Node launcher contract', () => {
  // Given
  const repoRoot = repoFixture()
  const contentRoot = path.join(repoRoot, '.ai-content', 'qa')
  const env = { INCLUDE_AI_HANDBOOK: '1', AI_CONTENT_ROOT: contentRoot }
  let observed

  // When
  const result = runGate('verify-dist', {
    repoRoot,
    env,
    spawnSync: (command, args, options) => {
      observed = { command, args, options }
      return { signal: null, status: 17 }
    },
  })

  // Then
  assert.deepEqual(result, { signal: null, status: 17 })
  assert.equal(observed.command, process.execPath)
  assert.deepEqual(observed.args, [
    'scripts/run_ai_python.mjs',
    '--ai',
    '--',
    '-m',
    'scripts.ai.verify_build',
  ])
  assert.equal(observed.options.cwd, repoRoot)
  assert.equal(observed.options.shell, false)
  assert.equal(observed.options.stdio, 'inherit')
  assert.equal(observed.options.env, env)
})

test('internal prepare requires nonblank absolute private root before spawning', () => {
  for (const value of [undefined, '', ' ', 'relative/private']) {
    // Given
    const repoRoot = repoFixture()
    const env = {
      INCLUDE_AI_HANDBOOK: '1',
      ...(value === undefined ? {} : { AI_CONTENT_ROOT: value }),
    }
    let spawnCount = 0

    // When / Then
    assert.throws(() =>
      runGate('prepare', {
        repoRoot,
        env,
        spawnSync: () => {
          spawnCount += 1
          return { signal: null, status: 0 }
        },
      }),
    )
    assert.equal(spawnCount, 0)
  }
})

test('internal child signal is returned for CLI propagation', () => {
  // Given
  const repoRoot = repoFixture()
  const env = {
    INCLUDE_AI_HANDBOOK: '1',
    AI_CONTENT_ROOT: path.join(repoRoot, '.ai-content', 'qa'),
  }

  // When
  const result = runGate('prepare', {
    repoRoot,
    env,
    spawnSync: () => ({ signal: 'SIGTERM', status: null }),
  })

  // Then
  assert.deepEqual(result, { signal: 'SIGTERM', status: null })
})

test('default verify-dist parses documentIds and ignores prose plus dist/ai.txt', () => {
  // Given
  const repoRoot = repoFixture()
  const dist = path.join(repoRoot, 'docs', '.vitepress', 'dist')
  writeFileSync(path.join(dist, 'ai.txt'), 'legitimate /ai/ plan prose\n')
  writeFileSync(path.join(dist, 'plan.html'), '<p>/ai/ appears in prose</p>\n')
  searchChunk(repoRoot, { 0: '/comparison#ai-plan' })
  let spawnCount = 0

  // When
  const result = runGate('verify-dist', {
    repoRoot,
    env: {},
    spawnSync: () => {
      spawnCount += 1
      return { signal: null, status: 0 }
    },
  })

  // Then
  assert.deepEqual(result, { signal: null, status: 0 })
  assert.equal(spawnCount, 0)
})

test('default verify-dist rejects dist/ai entries and AI documentIds without spawning', () => {
  for (const mutation of ['entry', 'route']) {
    // Given
    const repoRoot = repoFixture()
    if (mutation === 'entry') {
      const html = path.join(repoRoot, 'docs', '.vitepress', 'dist', 'ai', 'en', 'page.html')
      mkdirSync(path.dirname(html), { recursive: true })
      writeFileSync(html, '<html></html>\n')
      searchChunk(repoRoot, { 0: '/comparison' })
    } else {
      searchChunk(repoRoot, { 0: '/ai/en/codex/cli#section' })
    }
    let spawnCount = 0

    // When / Then
    assert.throws(() =>
      runGate('verify-dist', {
        repoRoot,
        env: {},
        spawnSync: () => {
          spawnCount += 1
          return { signal: null, status: 0 }
        },
      }),
    )
    assert.equal(spawnCount, 0)
  }
})
