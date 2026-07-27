import { randomBytes } from "node:crypto"
import { existsSync, mkdirSync, renameSync, rmSync } from "node:fs"
import { spawnSync } from "node:child_process"
import { dirname, isAbsolute, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const launcherPath = fileURLToPath(import.meta.url)
const defaultRepositoryRoot = resolve(dirname(launcherPath), "..")
const probeScript =
  "import json,sys;print(json.dumps({'executable':sys.executable,'version':list(sys.version_info[:3])}))"
const uvProbeScript = 'from importlib.metadata import version; print(version("uv"))'
export const requirementsFile = "requirements-uv-bootstrap.lock"
export const usage = "Usage: node scripts/run_ai_python.mjs --ai -- <python arguments...>\n"
const minimumVersion = [3, 11]
const requiredUvVersion = "0.11.32"
const requiredUvVersionStdout = `${requiredUvVersion}${process.platform === "win32" ? "\r\n" : "\n"}`

function isMinimumVersion(version) {
  return (
    Array.isArray(version) &&
    version.length >= 2 &&
    Number.isInteger(version[0]) &&
    Number.isInteger(version[1]) &&
    (version[0] > minimumVersion[0] ||
      (version[0] === minimumVersion[0] && version[1] >= minimumVersion[1]))
  )
}

export function candidatesForPlatform(platform = process.platform) {
  return platform === "win32" ? [["py", "-3"], ["python"]] : [["python3"], ["python"]]
}

export function isAbsoluteInterpreter(value) {
  return typeof value === "string" && isAbsolute(value)
}

export function parseProbeOutput(payload) {
  const parsed = JSON.parse(payload)
  if (
    parsed == null ||
    typeof parsed !== "object" ||
    typeof parsed.executable !== "string" ||
    !isAbsoluteInterpreter(parsed.executable) ||
    !isMinimumVersion(parsed.version)
  ) {
    return undefined
  }
  return parsed
}

export function selectInterpreter({
  platform = process.platform,
  repositoryRoot = defaultRepositoryRoot,
  spawn = spawnSync,
  writeError = (message) => process.stderr.write(message),
} = {}) {
  const commands = candidatesForPlatform(platform)
  for (const [command, ...prefix] of commands) {
    const probe = spawn(command, [...prefix, "-c", probeScript], {
      cwd: repositoryRoot,
      shell: false,
      encoding: "utf8",
    })
    if (probe.status !== 0) {
      continue
    }
    try {
      const payload = parseProbeOutput(probe.stdout)
      if (payload !== undefined) {
        return { command, prefix, executable: payload.executable, version: payload.version }
      }
    } catch {
      continue
    }
  }
  writeError("AI_PYTHON_311_REQUIRED\n")
  return undefined
}

function bootstrapDirectory(repositoryRoot) {
  return join(repositoryRoot, ".ai-local", "uv-bootstrap")
}

function temporaryBootstrapPath(repositoryRoot) {
  const nonce = randomBytes(4).toString("hex")
  return join(repositoryRoot, ".ai-local", `uv-bootstrap.tmp-${process.pid}-${nonce}`)
}

function bootstrapPythonPath(baseDirectory) {
  return join(baseDirectory, process.platform === "win32" ? "Scripts" : "bin", process.platform === "win32" ? "python.exe" : "python")
}

function bootstrapMissingVenvMessage(interpreter) {
  return `AI_PYTHON_VENV_REQUIRED: ${interpreter}\nPlease install a Python version with the stdlib venv module.\n`
}

function bootstrapMissingPipMessage(interpreter) {
  return `AI_PYTHON_PIP_REQUIRED: ${interpreter}\nPlease ensure this interpreter has pip installed.\n`
}

function bootstrapInvalidMessage(bootstrapPath) {
  return `AI_UV_BOOTSTRAP_INVALID: ${bootstrapPath}\n(delete this generated directory and retry)\n`
}

function isBootstrapUvValid({ pythonPath, spawn }) {
  const uvCheck = spawn(pythonPath, ["-c", uvProbeScript], {
    encoding: "utf8",
    shell: false,
  })
  if (uvCheck.status !== 0) {
    return false
  }

  return uvCheck.stdout === requiredUvVersionStdout
}

function ensureExistingBootstrap({
  bootstrapPython,
  spawn,
}) {
  if (!existsSync(bootstrapPython)) {
    return { status: "invalid", path: dirname(bootstrapPython) }
  }

  if (!isBootstrapUvValid({ pythonPath: bootstrapPython, spawn })) {
    return { status: "invalid", path: dirname(bootstrapPython) }
  }

  return { status: "ready", path: dirname(bootstrapPython) }
}

function removeTempBootstrap(path) {
  rmSync(path, { recursive: true, force: true })
}

export function ensureBootstrap({
  interpreter,
  repositoryRoot,
  requirementsPath,
  spawn = spawnSync,
}) {
  const bootstrapPath = bootstrapDirectory(repositoryRoot)
  const bootstrapPython = bootstrapPythonPath(bootstrapPath)

  if (existsSync(bootstrapPath)) {
    const bootstrapStatus = ensureExistingBootstrap({
      bootstrapPython,
      spawn,
    })
    if (bootstrapStatus.status === "ready") {
      return { status: "ready", path: bootstrapPath }
    }
    return {
      status: bootstrapStatus.status,
      path: bootstrapPath,
    }
  }

  const tempPath = temporaryBootstrapPath(repositoryRoot)
  const tempPython = bootstrapPythonPath(tempPath)

  const create = spawn(interpreter, ["-m", "venv", tempPath], {
    cwd: repositoryRoot,
    shell: false,
    encoding: "utf8",
  })
  if (create.status !== 0) {
    removeTempBootstrap(tempPath)
    return { status: "missing-bootstrap-venv", path: tempPath }
  }

  const pipVersion = spawn(tempPython, ["-m", "pip", "--version"], {
    cwd: repositoryRoot,
    shell: false,
    encoding: "utf8",
  })
  if (pipVersion.status !== 0) {
    removeTempBootstrap(tempPath)
    return { status: "missing-bootstrap-pip", path: tempPath }
  }

  const install = spawn(
    tempPython,
    ["-m", "pip", "install", "--require-hashes", "--only-binary=:all:", "--no-deps", "-r", requirementsPath],
    {
      cwd: repositoryRoot,
      shell: false,
      encoding: "utf8",
    },
  )
  if (install.status !== 0) {
    removeTempBootstrap(tempPath)
    return { status: "invalid", path: tempPath }
  }

  const uvCheck = spawn(tempPython, ["-c", uvProbeScript], {
    cwd: repositoryRoot,
    shell: false,
    encoding: "utf8",
  })
  if (uvCheck.status !== 0 || uvCheck.stdout !== requiredUvVersionStdout) {
    removeTempBootstrap(tempPath)
    return { status: "invalid", path: tempPath }
  }

  try {
    mkdirSync(dirname(bootstrapPath), { recursive: true })
    renameSync(tempPath, bootstrapPath)
  } catch {
    removeTempBootstrap(tempPath)
    return { status: "invalid", path: tempPath }
  }

  return { status: "ready", path: bootstrapPath }
}

export function parseLauncherArgs(argumentsFromShell) {
  if (argumentsFromShell[0] === "--ai" && argumentsFromShell[1] === "--" && argumentsFromShell.length > 2) {
    return { ai: true, target: argumentsFromShell.slice(2) }
  }
  return undefined
}

function runTarget({
  command,
  args,
  cwd,
  projectRoot,
  spawn = spawnSync,
  writeError = (message) => process.stderr.write(message),
}) {
  const result = spawn(command, args, {
    cwd,
    shell: false,
    stdio: "inherit",
    encoding: "utf8",
    env: {
      ...process.env,
      UV_PROJECT_ENVIRONMENT: resolve(projectRoot, ".ai-local", "venv"),
    },
  })
  if (result.error !== undefined) {
    writeError(`AI_PYTHON_TARGET_SPAWN_ERROR: ${result.error.message}\n`)
    return 1
  }
  if (result.signal !== undefined && result.signal !== null) {
    writeError(`AI_PYTHON_TARGET_SIGNAL: ${result.signal}\n`)
    return 1
  }
  return result.status ?? 1
}

function runWithBootstrap({
  bootstrapPath,
  interpreter,
  target,
  repositoryRoot,
  spawn = spawnSync,
  writeError = (message) => process.stderr.write(message),
}) {
  const bootstrapPython = bootstrapPythonPath(bootstrapPath)
  return runTarget({
    command: bootstrapPython,
    args: ["-m", "uv", "run", "--frozen", "--python", interpreter, "python", ...target],
    cwd: repositoryRoot,
    projectRoot: repositoryRoot,
    spawn,
    writeError,
  })
}

export function runLauncher(
  argumentsFromShell,
  {
    platform = process.platform,
    repositoryRoot = defaultRepositoryRoot,
    spawn = spawnSync,
    writeError = (message) => process.stderr.write(message),
    ensure = ensureBootstrap,
  } = {},
) {
  const parsed = parseLauncherArgs(argumentsFromShell)
  if (parsed === undefined || parsed.target.length === 0) {
    writeError(usage)
    return 2
  }

  const selected = selectInterpreter({
    platform,
    repositoryRoot,
    spawn,
    writeError,
  })
  if (selected === undefined) {
    return 1
  }

  const bootstrap = ensure({
    interpreter: selected.executable,
    repositoryRoot,
    requirementsPath: resolve(repositoryRoot, requirementsFile),
    spawn,
  })

  if (bootstrap.status !== "ready") {
    if (bootstrap.status === "missing-bootstrap-venv") {
      writeError(bootstrapMissingVenvMessage(selected.executable))
      return 1
    }
    if (bootstrap.status === "missing-bootstrap-pip") {
      writeError(bootstrapMissingPipMessage(selected.executable))
      return 1
    }
    writeError(bootstrapInvalidMessage(bootstrap.path))
    return 1
  }

  return runWithBootstrap({
    bootstrapPath: bootstrap.path,
    interpreter: selected.executable,
    target: parsed.target,
    repositoryRoot,
    spawn,
    writeError,
  })
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === launcherPath) {
  process.exitCode = runLauncher(process.argv.slice(2))
}
