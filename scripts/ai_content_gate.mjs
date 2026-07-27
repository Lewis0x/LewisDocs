import {
  existsSync,
  readdirSync,
  readFileSync,
  rmSync,
} from 'node:fs'
import path from 'node:path'
import { spawnSync as nativeSpawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

export function runGate(command, runtime = {}) {
  const repoRoot = runtime.repoRoot ?? REPO_ROOT
  const env = runtime.env ?? process.env
  const spawnSync = runtime.spawnSync ?? nativeSpawnSync
  const docsAiRoot = path.join(repoRoot, 'docs', 'ai')
  const internal = env.INCLUDE_AI_HANDBOOK === '1'

  if (!internal && command === 'prepare') {
    rmSync(docsAiRoot, { force: true, recursive: true })
    return { signal: null, status: 0 }
  }

  if (!internal && command === 'verify-dist') {
    verifyDefaultDist(path.join(repoRoot, 'docs', '.vitepress', 'dist'))
    return { signal: null, status: 0 }
  }

  if (command !== 'prepare' && command !== 'verify-dist') {
    throw new Error(`unknown AI content gate command: ${command}`)
  }

  const contentRoot = env.AI_CONTENT_ROOT
  if (typeof contentRoot !== 'string' || contentRoot.trim() === '' || !path.isAbsolute(contentRoot)) {
    throw new Error('AI_CONTENT_ROOT must be a nonblank absolute path')
  }
  const moduleName =
    command === 'prepare' ? 'scripts.ai.materialize' : 'scripts.ai.verify_build'
  const result = spawnSync(
    process.execPath,
    ['scripts/run_ai_python.mjs', '--ai', '--', '-m', moduleName],
    {
      cwd: repoRoot,
      env,
      shell: false,
      stdio: 'inherit',
    },
  )
  if (result.error) {
    throw result.error
  }
  return { signal: result.signal, status: result.status }
}

function verifyDefaultDist(distRoot) {
  const aiRoot = path.join(distRoot, 'ai')
  if (existsSync(aiRoot) && readdirSync(aiRoot).length > 0) {
    throw new Error('default build contains dist/ai entries')
  }
  const chunksRoot = path.join(distRoot, 'assets', 'chunks')
  const chunks = findLocalSearchChunks(chunksRoot)
  if (chunks.length !== 1) {
    throw new Error('default build local-search index is missing or ambiguous')
  }
  const source = readFileSync(chunks[0], 'utf8')
  const start = source.indexOf('`')
  const end = source.lastIndexOf('`;')
  if (start < 0 || end <= start) {
    throw new Error('default build local-search index is invalid')
  }
  const rawTemplate = source.slice(start + 1, end)
  const quotedTemplate = `"${rawTemplate.replaceAll('"', '\\"')}"`
  const parsed = JSON.parse(JSON.parse(quotedTemplate))
  if (typeof parsed !== 'object' || parsed === null || typeof parsed.documentIds !== 'object') {
    throw new Error('default build local-search documentIds are invalid')
  }
  for (const route of Object.values(parsed.documentIds)) {
    if (typeof route !== 'string') {
      throw new Error('default build local-search route is invalid')
    }
    if (route === '/ai' || route.startsWith('/ai/')) {
      throw new Error('default build local-search contains an AI route')
    }
  }
}

function findLocalSearchChunks(directory) {
  if (!existsSync(directory)) return []
  const found = []
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const child = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      found.push(...findLocalSearchChunks(child))
    } else if (entry.isFile() && entry.name.startsWith('@localSearchIndex') && entry.name.endsWith('.js')) {
      found.push(child)
    }
  }
  return found.sort()
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
