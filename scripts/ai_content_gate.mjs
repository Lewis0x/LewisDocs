import path from 'node:path'
import { spawnSync as nativeSpawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

export function runGate(command, runtime = {}) {
  const repoRoot = runtime.repoRoot ?? REPO_ROOT
  const env = runtime.env ?? process.env
  const spawnSync = runtime.spawnSync ?? nativeSpawnSync

  if (command !== 'prepare' && command !== 'verify-dist') {
    throw new Error(`unknown AI content gate command: ${command}`)
  }

  const moduleName =
    command === 'prepare' ? 'scripts.ai.materialize' : 'scripts.ai.verify_build'
  const childEnv = {
    ...env,
    AI_CONTENT_ROOT: path.join(repoRoot, 'source-ai', 'content'),
  }
  const result = spawnSync(
    process.execPath,
    ['scripts/run_ai_python.mjs', '--ai', '--', '-m', moduleName],
    {
      cwd: repoRoot,
      env: childEnv,
      shell: false,
      stdio: 'inherit',
    },
  )
  if (result.error) {
    throw result.error
  }
  return { signal: result.signal, status: result.status }
}

function runCli() {
  try {
    const result = runGate(process.argv[2])
    if (result.signal !== null) {
      process.kill(process.pid, result.signal)
      return
    }
    process.exitCode = result.status ?? 1
  } catch (error) {
    const message = error instanceof Error ? error.message : 'AI content gate failed'
    process.stderr.write(`${message}\n`)
    process.exitCode = 1
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runCli()
}
