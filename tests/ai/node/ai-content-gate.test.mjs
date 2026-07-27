import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { runGate } from '../../../scripts/ai_content_gate.mjs'

function repoFixture() {
  const repoRoot = mkdtempSync(path.join(tmpdir(), 'lewisdocs-ai-gate-'))
  mkdirSync(path.join(repoRoot, 'docs', '.vitepress', 'dist'), { recursive: true })
  return repoRoot
}

for (const [command, moduleName] of [
  ['prepare', 'scripts.ai.materialize'],
  ['verify-dist', 'scripts.ai.verify_build'],
]) {
  test(`${command} always uses the fixed public content root`, () => {
    const repoRoot = repoFixture()
    const env = {
      KEEP_ME: 'yes',
      AI_CONTENT_ROOT: path.join(repoRoot, 'ignored-override'),
      INCLUDE_AI_HANDBOOK: '0',
    }
    let observed

    const result = runGate(command, {
      repoRoot,
      env,
      spawnSync: (executable, args, options) => {
        observed = { executable, args, options }
        return { signal: null, status: 17 }
      },
    })

    assert.deepEqual(result, { signal: null, status: 17 })
    assert.equal(observed.executable, process.execPath)
    assert.deepEqual(observed.args, [
      'scripts/run_ai_python.mjs',
      '--ai',
      '--',
      '-m',
      moduleName,
    ])
    assert.equal(observed.options.cwd, repoRoot)
    assert.equal(observed.options.shell, false)
    assert.equal(observed.options.stdio, 'inherit')
    assert.deepEqual(observed.options.env, {
      ...env,
      AI_CONTENT_ROOT: path.join(repoRoot, 'source-ai', 'content'),
    })
  })
}

test('child signal is returned for CLI propagation', () => {
  const repoRoot = repoFixture()

  const result = runGate('prepare', {
    repoRoot,
    env: {},
    spawnSync: () => ({ signal: 'SIGTERM', status: null }),
  })

  assert.deepEqual(result, { signal: 'SIGTERM', status: null })
})

test('unknown command is rejected before spawning', () => {
  let spawnCount = 0

  assert.throws(() =>
    runGate('unknown', {
      repoRoot: repoFixture(),
      env: {},
      spawnSync: () => {
        spawnCount += 1
        return { signal: null, status: 0 }
      },
    }),
  )
  assert.equal(spawnCount, 0)
})
