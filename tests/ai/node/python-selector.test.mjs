import assert from "node:assert/strict"
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { tmpdir } from "node:os"
import { fileURLToPath } from "node:url"
import test from "node:test"

import {
  ensureBootstrap,
  parseLauncherArgs,
  parseProbeOutput,
  runLauncher,
  selectInterpreter,
} from "../../../scripts/run_ai_python.mjs"

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..")
const requirementsPath = resolve(repositoryRoot, "requirements-uv-bootstrap.lock")
const platformUvStdout = process.platform === "win32" ? "\r\n" : "\n"
const uvMetadataArgs = 'from importlib.metadata import version; print(version("uv"))'
const uvMetadataStdout = `0.11.32${platformUvStdout}`
const probeCommand = process.platform === "win32" ? "py" : "python3"
const probePrefix = process.platform === "win32" ? ["-3"] : []
const pythonDirectory = process.platform === "win32" ? "Scripts" : "bin"
const pythonExecutable = process.platform === "win32" ? "python.exe" : "python"

function probe(interpreter) {
  return { status: 0, stdout: JSON.stringify({ executable: interpreter, version: [3, 11, 0] }) }
}

function isPlatformProbe(command, args, script) {
  return (
    command === probeCommand &&
    args.length === probePrefix.length + 2 &&
    probePrefix.every((value, index) => args[index] === value) &&
    args[probePrefix.length] === "-c" &&
    args[probePrefix.length + 1] === script
  )
}

function platformProbeArgs(script) {
  return [...probePrefix, "-c", script]
}

function fakeBootstrapPython(path) {
  const dir = dirname(path)
  mkdirSync(dir, { recursive: true })
  writeFileSync(path, "")
  return path
}

test("parseLauncherArgs accepts only --ai --", () => {
  assert.deepEqual(parseLauncherArgs(["--ai", "--", "-m", "scripts.ai.cli", "sync"]), {
    ai: true,
    target: ["-m", "scripts.ai.cli", "sync"],
  })
  assert.equal(parseLauncherArgs(["--"]), undefined)
  assert.equal(parseLauncherArgs(["--", "-m", "scripts.ai.cli", "sync"]), undefined)
  assert.equal(parseLauncherArgs(["-m", "scripts.ai.cli", "sync"]), undefined)
  assert.equal(parseLauncherArgs(["--ai"]), undefined)
})

test("parseProbeOutput requires absolute interpreter and minimum Python version", () => {
  assert.equal(parseProbeOutput('{"executable": "python3", "version": [3, 11, 0]}'), undefined)
  assert.equal(parseProbeOutput('{"executable": "/usr/bin/python3", "version": [3, 10, 9]}'), undefined)
  assert.deepEqual(parseProbeOutput('{"executable": "/usr/bin/python3", "version": [3, 11, 0]}'), {
    executable: "/usr/bin/python3",
    version: [3, 11, 0],
  })
})

test("selectInterpreter prefers win32 and picks first absolute >=3.11", () => {
  const calls = []
  const selected = selectInterpreter({
    platform: "win32",
    repositoryRoot,
    spawn: (command, args, options) => {
      calls.push([command, args, options?.cwd, options?.shell])
      if (command === "py") {
        return { status: 0, stdout: JSON.stringify({ executable: "python3", version: [3, 11, 0] }) }
      }
      return probe("/absolute/python3")
    },
  })

  assert.equal(selected?.executable, "/absolute/python3")
  assert.equal(selected?.command, "python")
  assert.deepEqual(calls[0][1], ["-3", "-c", "import json,sys;print(json.dumps({'executable':sys.executable,'version':list(sys.version_info[:3])}))"])
  assert.equal(calls[0][2], repositoryRoot)
  assert.equal(calls[0][3], false)
})

test("ensureBootstrap reuses only matching uv bootstrap and rejects mismatched uv version", () => {
  const root = mkdtempSync(join(tmpdir(), "task1-bootstrap-"))
  const bootstrapPath = resolve(root, ".ai-local", "uv-bootstrap")
  const bootstrapPython = resolve(bootstrapPath, pythonDirectory, pythonExecutable)
  fakeBootstrapPython(bootstrapPython)

  const healthy = ensureBootstrap({
    interpreter: "/absolute/python3",
    repositoryRoot: root,
    requirementsPath,
    spawn: (command, args) => {
      if (command === bootstrapPython && args[0] === "-c" && args[1] === uvMetadataArgs) {
        return { status: 0, stdout: uvMetadataStdout }
      }
      return { status: 1, stdout: "" }
    },
  })
  assert.equal(healthy.status, "ready")

  const invalidOutputs = [
    ` ${uvMetadataStdout}`,
    `${uvMetadataStdout} `,
    `${uvMetadataStdout}${platformUvStdout}`,
    `${uvMetadataStdout}extra`,
  ]
  for (const output of invalidOutputs) {
    const invalid = ensureBootstrap({
      interpreter: "/absolute/python3",
      repositoryRoot: root,
      requirementsPath,
      spawn: (command, args) => {
        if (command === bootstrapPython && args[0] === "-c" && args[1] === uvMetadataArgs) {
          return { status: 0, stdout: output }
        }
        return { status: 1, stdout: "" }
      },
    })
    assert.equal(invalid.status, "invalid")
    assert.equal(invalid.path, bootstrapPath)
  }

  rmSync(root, { recursive: true, force: true })
})

test("ensureBootstrap creates same-root temporary bootstrap, runs hash-locked pip, and renames atomically", () => {
  const root = mkdtempSync(join(tmpdir(), "task1-bootstrap-create-"))
  const calls = []
  let tempPath

  const result = ensureBootstrap({
    interpreter: "/absolute/python3",
    repositoryRoot: root,
    requirementsPath,
    spawn: (command, args, options) => {
      calls.push([command, args, options?.cwd, options?.shell])

      if (
        (command === "/absolute/python3" || command === "python3" || command === "py") &&
        args[0] === "-m" &&
        args[1] === "venv"
      ) {
        tempPath = args[2]
        fakeBootstrapPython(resolve(tempPath, pythonDirectory, pythonExecutable))
        return { status: 0 }
      }

      const tempPython = resolve(tempPath, pythonDirectory, pythonExecutable)
      if (command === tempPython) {
        if (args[0] === "-m" && args[1] === "pip" && args[2] === "--version") {
          return { status: 0, stdout: "pip 24.0.0" }
        }
        if (
          args[0] === "-m" &&
          args[1] === "pip" &&
          args[2] === "install" &&
          args[3] === "--require-hashes" &&
          args[4] === "--only-binary=:all:" &&
          args[5] === "--no-deps" &&
          args[6] === "-r" &&
          args[7] === requirementsPath
        ) {
          return { status: 0 }
        }
        if (args[0] === "-c" && args[1] === uvMetadataArgs) {
          return { status: 0, stdout: uvMetadataStdout }
        }
      }

      return { status: 1, stdout: "" }
    },
  })

  assert.equal(result.status, "ready")
  const finalPath = result.path
  const tempPattern = /uv-bootstrap\.tmp-[0-9]+-[a-f0-9]+$/
  assert.match(tempPath, tempPattern)
  assert.equal(tempPath.endsWith("uv-bootstrap"), false)
  assert.equal(resolve(root, ".ai-local", "uv-bootstrap"), finalPath)

  const venvCall = calls.find(
    (entry) =>
      (entry[0] === "/absolute/python3" || entry[0] === "python3" || entry[0] === "py") &&
      entry[1][0] === "-m" &&
      entry[1][1] === "venv",
  )
  assert.equal(venvCall?.[1][2] === tempPath, true)
  assert.equal(venvCall?.[2], root)
  assert.equal(venvCall?.[3], false)

  const installCall = calls.find(
    (entry) =>
      entry[1][0] === "-m" &&
      entry[1][1] === "pip" &&
      entry[1][2] === "install" &&
      entry[1][3] === "--require-hashes" &&
      entry[1][4] === "--only-binary=:all:" &&
      entry[1][5] === "--no-deps",
  )
  assert.equal(installCall?.[1][6], "-r")
  assert.equal(installCall?.[1][7], requirementsPath)
  assert.equal(installCall?.[0], resolve(tempPath, pythonDirectory, pythonExecutable))

  const uvCheckCall = calls.find((entry) => entry[1][0] === "-c" && entry[1][1] === 'from importlib.metadata import version; print(version("uv"))')
  assert.equal(uvCheckCall?.[0], resolve(tempPath, pythonDirectory, pythonExecutable))
  assert.equal(existsSync(tempPath), false)
  rmSync(root, { recursive: true, force: true })
})

test("ensureBootstrap rejects non-exact uv output for fresh bootstrap creation", () => {
  const invalidOutputs = [
    ` ${uvMetadataStdout}`,
    `${uvMetadataStdout} `,
    `${uvMetadataStdout}${platformUvStdout}`,
    `${uvMetadataStdout}extra`,
  ]

  for (const output of invalidOutputs) {
    const root = mkdtempSync(join(tmpdir(), "task1-bootstrap-fresh-invalid-"))
    let tempPath

    const result = ensureBootstrap({
      interpreter: "/absolute/python3",
      repositoryRoot: root,
      requirementsPath,
      spawn: (command, args) => {
        if (
          (command === "/absolute/python3" || command === "python3" || command === "py") &&
          args[0] === "-m" &&
          args[1] === "venv"
        ) {
          tempPath = args[2]
          fakeBootstrapPython(resolve(tempPath, pythonDirectory, pythonExecutable))
          return { status: 0 }
        }

        const temporaryPython = tempPath === undefined ? undefined : resolve(tempPath, pythonDirectory, pythonExecutable)
        if (command === temporaryPython) {
          if (args[0] === "-m" && args[1] === "pip" && args[2] === "--version") {
            return { status: 0, stdout: "pip 24.0.0" }
          }
          if (
            args[0] === "-m" &&
            args[1] === "pip" &&
            args[2] === "install" &&
            args[3] === "--require-hashes" &&
            args[4] === "--only-binary=:all:" &&
            args[5] === "--no-deps" &&
            args[6] === "-r" &&
            args[7] === requirementsPath
          ) {
            return { status: 0 }
          }
          if (args[0] === "-c" && args[1] === uvMetadataArgs) {
            return { status: 0, stdout: output }
          }
        }

        return { status: 1, stdout: "" }
      },
    })

    assert.equal(result.status, "invalid")
    assert.equal(existsSync(resolve(root, ".ai-local", "uv-bootstrap")), false)
    assert.equal(result.path, tempPath)
    assert.equal(existsSync(tempPath), false)
    rmSync(root, { recursive: true, force: true })
  }
})

test("runLauncher enforces --ai --, passes exact uv args, cwd, shell, and env", () => {
  const root = mkdtempSync(join(tmpdir(), "task1-launcher-"))
  const bootstrapPath = resolve(root, ".ai-local", "uv-bootstrap")
  const bootstrapPython = resolve(bootstrapPath, pythonDirectory, pythonExecutable)
  const legacy = runLauncher(["--", "-m", "scripts.ai.cli", "sync"], {
    repositoryRoot: root,
    spawn: () => ({ status: 0 }),
    writeError: () => {},
  })
  assert.equal(legacy, 2)

  const empty = runLauncher(["--ai", "--"], {
    repositoryRoot: root,
    spawn: () => ({ status: 0 }),
    writeError: () => {},
  })
  assert.equal(empty, 2)

  assert.equal(bootstrapPath, resolve(root, ".ai-local", "uv-bootstrap"))
  rmSync(root, { recursive: true, force: true })
})

test("runLauncher resolves one absolute interpreter through real probe->bootstrap->uv-run from foreign cwd", () => {
  const root = mkdtempSync(join(tmpdir(), "task1-launcher-real-"))
  const foreignCwd = mkdtempSync(join(tmpdir(), "task1-launcher-foreign-"))
  const probeScript =
    "import json,sys;print(json.dumps({'executable':sys.executable,'version':list(sys.version_info[:3])}))"
  const bootstrapPath = resolve(root, ".ai-local", "uv-bootstrap")
  const bootstrapPython = resolve(bootstrapPath, pythonDirectory, pythonExecutable)
  const interpreter = "/absolute/python3"
  const calls = []
  const uvProbeVersions = []
  const uvProbeArgs = []
  let tempPath
  let firstRun = 0
  let secondRun = 0
  let firstMessage = ""
  let secondMessage = ""

  const spawn = (command, args, options) => {
    calls.push([command, args, options])
    if (isPlatformProbe(command, args, probeScript)) {
      return probe(interpreter)
    }
    if (command === interpreter && args[0] === "-m" && args[1] === "venv") {
      tempPath = args[2]
      fakeBootstrapPython(resolve(tempPath, pythonDirectory, pythonExecutable))
      return { status: 0 }
    }

    const temporaryPython = tempPath === undefined ? undefined : resolve(tempPath, pythonDirectory, pythonExecutable)
    if (command === temporaryPython) {
      if (args[0] === "-m" && args[1] === "pip" && args[2] === "--version") {
        return { status: 0, stdout: "pip 24.0.0" }
      }
      if (
        args[0] === "-m" &&
        args[1] === "pip" &&
        args[2] === "install" &&
        args[3] === "--require-hashes" &&
        args[4] === "--only-binary=:all:" &&
        args[5] === "--no-deps" &&
        args[6] === "-r" &&
        args[7] === resolve(root, "requirements-uv-bootstrap.lock")
      ) {
        return { status: 0 }
      }
      if (args[0] === "-c" && args[1] === uvMetadataArgs) {
        uvProbeVersions.push("0.11.32")
        uvProbeArgs.push(args)
        return { status: 0, stdout: uvMetadataStdout }
      }
    }

    if (command === bootstrapPython && args[0] === "-c" && args[1] === uvMetadataArgs) {
      uvProbeVersions.push("0.11.32")
      uvProbeArgs.push(args)
      return { status: 0, stdout: uvMetadataStdout }
    }
    if (command === bootstrapPython && args[0] === "-m" && args[1] === "uv") {
      return { status: 0 }
    }
    return { status: 0 }
  }

  const originalCwd = process.cwd()
  const originalPath = process.env.PATH
  process.chdir(foreignCwd)
  process.env.PATH = "."
  try {
    firstRun = runLauncher(["--ai", "--", "-m", "scripts.ai.cli", "sync"], {
      repositoryRoot: root,
      spawn,
      writeError: (text) => {
        firstMessage += text
      },
    })
    secondRun = runLauncher(["--ai", "--", "-m", "scripts.ai.cli", "sync"], {
      repositoryRoot: root,
      spawn,
      writeError: (text) => {
        secondMessage += text
      },
    })
  } finally {
    process.chdir(originalCwd)
    if (originalPath === undefined) {
      delete process.env.PATH
    } else {
      process.env.PATH = originalPath
    }
  }

  assert.equal(firstRun, 0)
  assert.equal(secondRun, 0)
  assert.equal(firstMessage, "")
  assert.equal(secondMessage, "")

  const probeCall = calls.find((entry) => isPlatformProbe(entry[0], entry[1], probeScript))
  assert.equal(probeCall?.[0], probeCommand)
  assert.equal(probeCall?.[2]?.cwd, root)
  assert.equal(probeCall?.[2]?.shell, false)
  assert.deepEqual(probeCall?.[1], platformProbeArgs(probeScript))

  assert.notEqual(tempPath, undefined)
  const tempPattern = /uv-bootstrap\.tmp-[0-9]+-[a-f0-9]+$/
  assert.match(tempPath, tempPattern)
  assert.equal(dirname(tempPath), resolve(root, ".ai-local"))

  const venvCall = calls.find(
    (entry) => entry[0] === interpreter && entry[1][0] === "-m" && entry[1][1] === "venv",
  )
  assert.equal(venvCall?.[1][2], tempPath)
  assert.equal(venvCall?.[2]?.cwd, root)
  assert.equal(venvCall?.[2]?.shell, false)

  const installCall = calls.find((entry) => entry[1][0] === "-m" && entry[1][1] === "pip" && entry[1][2] === "install")
  assert.deepEqual(installCall?.[1], [
    "-m",
    "pip",
    "install",
    "--require-hashes",
    "--only-binary=:all:",
    "--no-deps",
    "-r",
    resolve(root, "requirements-uv-bootstrap.lock"),
  ])
  assert.equal(installCall?.[0], resolve(tempPath, pythonDirectory, pythonExecutable))

  assert.equal(uvProbeVersions.length, 2)
  assert.deepEqual(uvProbeVersions[0], "0.11.32")
  assert.deepEqual(uvProbeVersions[1], "0.11.32")
  assert.deepEqual(uvProbeArgs[0], ["-c", uvMetadataArgs])
  assert.deepEqual(uvProbeArgs[1], ["-c", uvMetadataArgs])

  const uvRunCall = calls.find((entry) => entry[0] === bootstrapPython && entry[1][0] === "-m" && entry[1][1] === "uv")
  assert.deepEqual(uvRunCall?.[1], [
    "-m",
    "uv",
    "run",
    "--frozen",
    "--python",
    interpreter,
    "python",
    "-m",
    "scripts.ai.cli",
    "sync",
  ])
  assert.equal(uvRunCall?.[1][5], interpreter)
  assert.equal(uvRunCall?.[2]?.cwd, root)
  assert.equal(uvRunCall?.[2]?.shell, false)
  assert.equal(uvRunCall?.[2]?.env?.UV_PROJECT_ENVIRONMENT, resolve(root, ".ai-local", "venv"))

  assert.equal(existsSync(bootstrapPath), true)
  assert.equal(bootstrapPath, resolve(root, ".ai-local", "uv-bootstrap"))
  assert.equal(existsSync(tempPath), false)
  rmSync(root, { recursive: true, force: true })
  rmSync(foreignCwd, { recursive: true, force: true })
})

test("runLauncher emits stable errors from real ensureBootstrap failure branches", () => {
  const root = mkdtempSync(join(tmpdir(), "task1-launcher-errors-"))
  const binDir = process.platform === "win32" ? "Scripts" : "bin"
  const probeScript =
    "import json,sys;print(json.dumps({'executable':sys.executable,'version':list(sys.version_info[:3])}))"
  const runWithError = (repositoryRoot, spawn) => {
    const messages = []
    const status = runLauncher(["--ai", "--", "-m", "scripts.ai.cli", "sync"], {
      repositoryRoot,
      spawn,
      writeError: (text) => {
        messages.push(text)
      },
    })
    return { status, message: messages.join("") }
  }

  const corruptRoot = mkdtempSync(join(tmpdir(), "task1-launcher-corrupt-"))
  const corruptPath = resolve(corruptRoot, ".ai-local", "uv-bootstrap")
  mkdirSync(corruptPath, { recursive: true })
  const corruptResult = runWithError(corruptRoot, (command, args) => {
    if (isPlatformProbe(command, args, probeScript)) {
      return probe("/absolute/python3")
    }
    return { status: 0 }
  })
  assert.equal(corruptResult.status, 1)
  assert.equal(
    corruptResult.message,
    `AI_UV_BOOTSTRAP_INVALID: ${corruptPath}\n(delete this generated directory and retry)\n`,
  )

  const missingVenvRoot = mkdtempSync(join(tmpdir(), "task1-launcher-missing-venv-"))
  const missingVenvResult = runWithError(missingVenvRoot, (command, args) => {
    if (isPlatformProbe(command, args, probeScript)) {
      return probe("/absolute/python3")
    }
    if (command === "/absolute/python3" && args[0] === "-m" && args[1] === "venv") {
      return { status: 1 }
    }
    return { status: 0 }
  })
  assert.equal(missingVenvResult.status, 1)
  assert.equal(
    missingVenvResult.message,
    "AI_PYTHON_VENV_REQUIRED: /absolute/python3\nPlease install a Python version with the stdlib venv module.\n",
  )

  const missingPipRoot = mkdtempSync(join(tmpdir(), "task1-launcher-missing-pip-"))
  let tempPath
  const missingPipResult = runWithError(missingPipRoot, (command, args) => {
    if (isPlatformProbe(command, args, probeScript)) {
      return probe("/absolute/python3")
    }
    if (command === "/absolute/python3" && args[0] === "-m" && args[1] === "venv") {
      tempPath = args[2]
      fakeBootstrapPython(resolve(tempPath, pythonDirectory, pythonExecutable))
      return { status: 0 }
    }
    if (command === resolve(tempPath, binDir, pythonExecutable) && args[0] === "-m" && args[1] === "pip" && args[2] === "--version") {
      return { status: 1, stdout: "" }
    }
    return { status: 0 }
  })
  assert.equal(missingPipResult.status, 1)
  assert.equal(
    missingPipResult.message,
    "AI_PYTHON_PIP_REQUIRED: /absolute/python3\nPlease ensure this interpreter has pip installed.\n",
  )

  const wrongUvRoot = mkdtempSync(join(tmpdir(), "task1-launcher-wrong-uv-"))
  const wrongUvPath = resolve(wrongUvRoot, ".ai-local", "uv-bootstrap")
  const wrongUvPython = resolve(wrongUvPath, pythonDirectory, pythonExecutable)
  fakeBootstrapPython(wrongUvPython)
  const wrongUvResult = runWithError(wrongUvRoot, (command, args) => {
    if (isPlatformProbe(command, args, probeScript)) {
      return probe("/absolute/python3")
    }
    if (command === wrongUvPython && args[0] === "-c" && args[1] === 'from importlib.metadata import version; print(version("uv"))') {
      return { status: 0, stdout: "0.11.31\n" }
    }
    return { status: 0 }
  })
  assert.equal(wrongUvResult.status, 1)
  assert.equal(
    wrongUvResult.message,
    `AI_UV_BOOTSTRAP_INVALID: ${wrongUvPath}\n(delete this generated directory and retry)\n`,
  )

  rmSync(root, { recursive: true, force: true })
  rmSync(corruptRoot, { recursive: true, force: true })
  rmSync(missingVenvRoot, { recursive: true, force: true })
  rmSync(missingPipRoot, { recursive: true, force: true })
  rmSync(wrongUvRoot, { recursive: true, force: true })
})
