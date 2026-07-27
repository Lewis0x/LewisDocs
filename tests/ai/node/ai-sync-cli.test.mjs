import assert from "node:assert/strict"
import { existsSync, readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync } from "node:child_process"
import test from "node:test"

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..")
const launcherPath = resolve(repositoryRoot, "scripts/run_ai_python.mjs")

function invokeCli(args, environment = {}) {
  const env = { ...process.env, ...environment }
  delete env.MOONSHOT_API_KEY
  delete env.VIRTUAL_ENV
  return spawnSync(
    process.execPath,
    [launcherPath, "--ai", "--", "-m", "scripts.ai.cli", ...args],
    { cwd: repositoryRoot, encoding: "utf8", env, shell: false },
  )
}

test("real launcher chain exposes only sync help", () => {
  const result = invokeCli(["--help"])

  assert.equal(result.status, 0)
  assert.match(result.stdout, /\bsync\b/)
  assert.doesNotMatch(result.stdout, /\b(?:validate|check|offline|generate)\b/)
})

test("real launcher chain rejects repository content root before network or report write", () => {
  const reportPath = resolve(repositoryRoot, ".ai-local", "report.json")
  const before = existsSync(reportPath) ? readFileSync(reportPath) : undefined
  const result = invokeCli(["sync"], { AI_CONTENT_ROOT: repositoryRoot })
  const after = existsSync(reportPath) ? readFileSync(reportPath) : undefined

  assert.equal(result.status, 6)
  assert.equal(result.stdout, "code=VALIDATION_FAILED source_id=- message=validation failed\n")
  assert.doesNotMatch(result.stderr, /Traceback|MOONSHOT_API_KEY|https?:\/\//)
  assert.deepEqual(after, before)
})
