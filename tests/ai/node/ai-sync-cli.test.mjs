import assert from "node:assert/strict"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync } from "node:child_process"
import test from "node:test"

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..")
const launcherPath = resolve(repositoryRoot, "scripts/run_ai_python.mjs")

function invokeCli(args, environment = {}) {
  return invokePython(["-m", "scripts.ai.cli", ...args], environment)
}

function invokePython(args, environment = {}) {
  const env = { ...process.env, ...environment }
  delete env.MOONSHOT_API_KEY
  delete env.VIRTUAL_ENV
  return spawnSync(
    process.execPath,
    [launcherPath, "--ai", "--", ...args],
    { cwd: repositoryRoot, encoding: "utf8", env, shell: false },
  )
}

function normalizeNewlines(value) {
  return value.replaceAll("\r\n", "\n")
}

test("real launcher chain exposes only sync help", () => {
  const result = invokeCli(["--help"])

  assert.equal(result.status, 0)
  assert.match(result.stdout, /\bsync\b/)
  assert.doesNotMatch(result.stdout, /\b(?:validate|check|offline|generate)\b/)
})

test("real launcher chain uses the fixed public content root", () => {
  const result = invokePython(
    [
      "-c",
      "from scripts.ai.sync import _default_options; print(_default_options().content_root)",
    ],
    { AI_CONTENT_ROOT: repositoryRoot },
  )

  assert.equal(result.status, 0)
  assert.equal(
    resolve(normalizeNewlines(result.stdout).trim()),
    resolve(repositoryRoot, "source-ai", "content"),
  )
  assert.doesNotMatch(result.stderr, /Traceback|MOONSHOT_API_KEY|https?:\/\//)
})
