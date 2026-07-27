# AI Agent Bilingual Handbook MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to implement this plan task by task.
> Every coding/fix brief also requires `$codex-continuation`,
> `omo:programming`, and `superpowers:test-driven-development`.

**Goal:** Add an internal-only LewisDocs `/ai/` handbook that synchronizes the
exact 10 Claude Code and Codex sources into a private `AI_CONTENT_ROOT`, serves
paired English/Chinese pages and two Chinese learning paths, and leaves the
public/default CAD site unchanged.

**Architecture:** Python >=3.11 code parses all external boundaries into frozen
Pydantic models, uses frozen dataclasses internally, fetches through a tuned
`httpx2` client, translates changed Markdown through the single `kimi-k3`
adapter, validates a complete candidate, then performs rollback-protected local
acceptance. Existing CAD preparation runs first; an opt-in final materializer
copies validated private pages into ignored `docs/ai/`, and the existing
VitePress config adds minimal conditional navigation and language switching.

**Tech Stack:** Python >=3.11; uv `0.11.32`; exact runtime dependencies
`pydantic==2.13.4`, `typer==0.27.0`, `rich==15.0.0`,
`httpx2[http2,brotli,zstd]==2.9.1`; exact dev dependencies
`pytest==9.1.1`, `basedpyright==1.39.9`, `ruff==0.16.0`. The existing npm
project remains npm-managed and pins `typescript==7.0.2`,
`@types/node==20.19.43`, and `@biomejs/biome==2.5.5`; VitePress/Vue remain the
only frontend framework.

## Global Constraints

- Normative input:
  `project-docs/07-ai-agent-handbook-spec.md`, exact SHA-256
  `62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`.
  Every task rechecks it before writes.
- Explicit user override: do **not** stage, commit, push, open a PR, deploy, or
  modify remote state. This overrides the commit steps normally suggested by
  `writing-plans`/SDD. Reviews use ignored task reports and owned-path diffs,
  never the index or commits.
- Explicit MVP UI-scope override: preserve the existing VitePress design
  system; do not add or update `DESIGN.md`, Lighthouse/performance-audit
  infrastructure, Playwright, global installs, or score gates. This overrides
  the `omo:frontend` perfection expansion. Retain build, exact
  route/count/link, console/hydration, language-switch, 375/768/1280, CJK, and
  two-independent-visual-oracle verification below.
- `npm run ai:sync` is the only supported AI npm entry. No dynamic inventory,
  Academy, Gemini, offline bundle, Worker, rights/release/seal abstraction,
  scheduled sync, or future-provider framework is allowed.
- Public Git tracks code, tests, synthetic fixtures, and the exact 10-row
  manifest only. It never tracks official English/Chinese full text or the two
  real learning-path full texts. `/.ai-content/`, `/.ai-local/`, `/docs/ai/`,
  and `/.superpowers/sdd/` are ignored.
- `source-ai/sources.yaml` is JSON-compatible YAML and is parsed as JSON by
  Pydantic; PyYAML is not added. No boundary returns a raw dict, `Any`, or
  `object`.
- Boundary records are frozen Pydantic models with `extra="forbid"`; internal
  records are `@dataclass(frozen=True, slots=True)`. `SourceId` is a `NewType`;
  `ErrorCode` is a `StrEnum`; variant handling is exhaustive `match` plus
  `assert_never`.
- Python uses Typer, Rich, pytest, basedpyright `typeCheckingMode="all"`, and
  Ruff `select=["ALL"]`; no argparse, urllib, unittest, mutable boundary model,
  broad exception outside the documented CLI boundary, or type escape hatch.
- New/touched TypeScript has no `any`, assertion, non-null assertion,
  `@ts-ignore`, or `@ts-expect-error`. No Zod is needed because TypeScript does
  not read external files; Python/Pydantic owns manifest/private-content
  boundaries.
- One observable behavior gets one Given/When/Then pytest RED→GREEN cycle.
  Every RED exits through an assertion failure, never import/collection/setup
  failure, and its complete output is saved in the task report. The owner
  writes the behavioral test first; if its module is new, the owner then adds
  only the declared importable signature with a typed, deliberately incorrect
  return before the first run. No behavior is implemented until the assertion
  RED is captured. Native Node tests are additional cross-runtime evidence;
  they never replace the pytest RED for the same launcher/CLI behavior.
- Network tests use `httpx2.MockTransport` or a local HTTP server at the wire
  boundary. No test mocks a whole orchestration service. The Codex HTML fixture
  is invented and minimal, not an official page copy.
- No task calls real Kimi. Task 6 may do so only after the controller confirms
  `MOONSHOT_API_KEY` is process-only, confirms the private root, and explicitly
  authorizes the final real acceptance action.
- Default/public preparation removes stale `docs/ai/`; default/public build and
  search contain no `/ai/`. Internal pages require exact
  `INCLUDE_AI_HANDBOOK=1` and a readable, valid `AI_CONTENT_ROOT`.
- CAD import→rewrite→citation behavior, routes, navigation, search, and derived
  bytes remain regression-protected. Rewrite/citation enumeration excludes
  `docs/ai/**`; materialization is last.
- Current Mac evidence is labelled macOS only. Windows is PASS only after a
  Windows runner executes the stated commands.

## SDD Without Git Staging or Commits

Before Task 1, archive or remove pre-MVP Task 1 brief/report/review artifacts
from current evidence, then create fresh `.superpowers/sdd/task-1/` through
`task-6/` directories as tasks begin. Do not carry forward earlier
snapshot/manifest/review artifacts, and do not create a ledger.

Each task keeps exactly one current `brief.md` and one current `report.md` in
its ignored `.superpowers/sdd/task-N/` directory. The brief fixes scope, owned
paths, behavioral RED, and verification commands. The report records each
declared RED/GREEN/verify command, exit status, and complete output, plus an
owned-path change summary. Capture only the task's owned-path evidence with
`git diff --no-index --binary` against a small pre-task copy when needed, or
the equivalent current working-tree diff/status for tracked, untracked, added,
and deleted owned paths. Never stage or commit to manufacture a diff.

A task is complete when its declared RED was observed, GREEN and verification
commands pass, and its current report/diff evidence is complete; no per-task
review is required. After Task 6, run one fresh GPT-SOL implementation review
and one separate fresh code-quality review over the current complete
implementation diff/equivalent evidence plus all six reports. Findings return
to the owning task for a focused RED/GREEN/verify refresh, followed by both
fresh final reviews. This final code review is separate from Task 6's two visual
oracles.

## External Docs Bound to This Plan

- Moonshot overview: `https://platform.kimi.ai/docs/overview`
- Kimi K3 quickstart:
  `https://platform.kimi.ai/docs/guide/kimi-k3-quickstart`
- Kimi endpoint: `https://api.moonshot.ai/v1/chat/completions`; Bearer key from
  `MOONSHOT_API_KEY`; model `kimi-k3`; translation may set
  `reasoning_effort="low"` and omits temperature, top_p, n, and penalties.
- uv installation:
  `https://github.com/astral-sh/uv/blob/main/docs/getting-started/installation.md`
- httpx2 API:
  `https://github.com/pydantic/httpx2/blob/main/docs/api.md`
- httpx2 transport/resource limits:
  `https://github.com/pydantic/httpx2/blob/main/docs/advanced/transports.md`
  and
  `https://github.com/pydantic/httpx2/blob/main/docs/advanced/resource-limits.md`
- VitePress preview CLI and its only supported preview options:
  `https://vitepress.dev/reference/cli#vitepress-preview`; the pinned local
  1.6.4 `ServeOptions`/implementation is the executable version authority.

---

## Task 1: Contract the scaffold and establish strict uv/TypeScript tooling

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`. Verify spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming`, Python/TypeScript references, and
`superpowers:test-driven-development`. Consume the current scaffold only. Write
only the Files below; preserve all unrelated dirty work.

**Files:**

- Modify: `.gitignore`, `package.json`, `package-lock.json`
- Modify: `project-docs/01-requirements.md`
- Create: `pyproject.toml`, `uv.lock`, `requirements-uv-bootstrap.lock`,
  `biome.json`
- Modify: `tsconfig.json`, `scripts/run_ai_python.mjs`, `scripts/ai/cli.py`
- Modify only to add the package module docstring required by Ruff D104:
  `scripts/ai/__init__.py`
- Create: `docs/.vitepress/vue-shim.d.ts`
- Modify `docs/.vitepress/config.ts` only to remove the two existing assertions
  and change exactly two `self.renderToken(tokens, idx, options, env)` calls to
  `self.renderToken(tokens, idx, options)`; preserve the surrounding
  five-parameter renderer callbacks and five-argument
  `defaultOpen`/`defaultClose` calls.
- Modify: `tests/ai/node/python-selector.test.mjs`
- Create: `tests/ai/test_toolchain.py`
- Delete: `requirements-ai.in`, `requirements-ai.lock`
- Delete: `scripts/ai/command_api.py`
- Delete: `scripts/ai/commands/__init__.py`,
  `scripts/ai/commands/academy_export.py`,
  `scripts/ai/commands/check.py`, `scripts/ai/commands/gate.py`,
  `scripts/ai/commands/generate.py`, `scripts/ai/commands/inventory.py`,
  `scripts/ai/commands/offline.py`, `scripts/ai/commands/rights_enforce.py`,
  `scripts/ai/commands/sync.py`, `scripts/ai/commands/validate.py`
- Delete: `tests/ai/node/cli-dispatch.test.mjs`,
  `tests/ai/node/runtime-types.ts`

**Consumes / produces:** Preserve the HEAD CAD npm command boundary unchanged:
`import`, `rewrite`, `link-citations`, and watermark call their original direct
`python scripts/...` commands. `scripts/run_ai_python.mjs` serves only
`--ai -- <uv-run python argv>` for handbook code; produce a Typer `app` whose
eventual `sync` command is lazily imported. Produce `npm run typecheck`,
`npm run lint:ts`, and the exact uv environment consumed by Tasks 2–6.

- [ ] **RED:** After authoring the single-package bootstrap lock, the controller
  creates an ignored, test-only uv bootstrap with the Session 0 absolute
  Python and the same hash-locked pip argv specified below, then runs
  `uv run --no-project --with pytest==9.1.1 pytest
  tests/ai/test_toolchain.py`. One pytest at a time spawns Node and asserts the
  obsolete scripts, dependency pins, relative-PATH behavior, or bootstrap argv
  is wrong. Append each assertion-failure output to the current Task 1
  `report.md`. Native Node tests repeat the cross-runtime cases after each
  pytest is GREEN.
- [ ] **GREEN runtime:** `pyproject.toml` declares `requires-python=">=3.11"`,
  the four exact runtime dependencies and three exact dev dependencies from
  Tech Stack, and pytest strict mode. `[tool.basedpyright]` sets
  `include=["scripts/ai","tests/ai"]`, Python 3.11, and
  `typeCheckingMode="all"`. `[tool.ruff]` uses valid file globs
  `include=["scripts/ai/**/*.py","tests/ai/**/*.py"]`; Ruff still selects ALL
  with only formatter-conflict and test-specific ignores. These discovery
  scopes exclude preserved legacy CAD Python without weakening checks on
  handbook code/tests. Generate `uv.lock` with
  `<bootstrap-python> -m uv lock --python <absolute-python>` under
  `uv==0.11.32`; never hand-edit it. This is the only application dependency
  lock. `requirements-uv-bootstrap.lock` is a bootstrap supply-chain lock, not
  a second application authority: it contains only `uv==0.11.32` plus every
  supported target wheel SHA-256 and no transitive dependency.
- [ ] **GREEN launcher:** Probe candidate argv from repository cwd with:

  ```python
  import json,sys
  print(json.dumps({"executable":sys.executable,"version":list(sys.version_info[:3])}))
  ```

  Require an absolute executable and >=3.11, then discard the candidate prefix
  and reuse that exact executable. First `--ai` creates
  `.ai-local/uv-bootstrap.tmp-<pid>-<nonce>` with
  `<absolute-python> -m venv`, then runs its Python:

  ```text
  -m pip install --require-hashes --only-binary=:all: --no-deps
    -r <absolute-repo>/requirements-uv-bootstrap.lock
  ```

  Run `<tmp-python> -c 'from importlib.metadata import version;
  print(version("uv"))'`, require exact stdout `0.11.32`, then atomically rename
  the temp directory to `.ai-local/uv-bootstrap`. Only reuse an existing
  bootstrap when the same command under its own Python returns that exact
  stdout.
  Missing venv or pip returns stable `AI_PYTHON_VENV_REQUIRED` or
  `AI_PYTHON_PIP_REQUIRED` with the selected interpreter and an actionable
  installation message. A corrupt/wrong-version bootstrap returns
  `AI_UV_BOOTSTRAP_INVALID` with its absolute path and “delete this generated
  directory and retry”; never install over it. After bootstrap, execute:

  ```text
  <bootstrap-python> -m uv run --frozen --python <absolute-python>
    python <target argv>
  UV_PROJECT_ENVIRONMENT=<repo>/.ai-local/venv
  ```

  `uv run` receives `--python <resolved absolute sys.executable>`, repository
  root cwd, `shell:false`, and absolute
  `UV_PROJECT_ENVIRONMENT=<repo>/.ai-local/venv`. Later runs reuse bootstrap
  and project venv. Tests start in a foreign cwd with a relative PATH and prove
  probe/bootstrap/run all use one absolute interpreter; assert exact temp-venv,
  hash-locked pip, both metadata probes' exact `-c 'from importlib.metadata
  import version; print(version("uv"))'` argv and exact stdout `0.11.32`,
  atomic-rename, uv run argv, cwd, shell, and env. Test stable
  venv/pip/corrupt/wrong-version failures. Do not add a CAD/direct, install, or
  requirements mode.
- [ ] **GREEN cleanup:** Keep only npm `ai:sync`, routed through `--ai`; route
  it as `node scripts/run_ai_python.mjs --ai -- -m scripts.ai.cli sync`.
  Restore/preserve exact HEAD commands `python scripts/import_docs.py`,
  `python scripts/rewrite_links.py`, `python scripts/link_citations.py`, and
  `python scripts/watermark.py`; they never use the AI launcher. Delete the
  eight obsolete `ai:*` scripts, dynamic CLI, `requirements-ai.*`, unnecessary
  tests, Workers, Playwright, and tsx. Pin the three allowed TS tools exactly;
  npm remains the package manager. Add the four ignored runtime/review roots.
  Replace old “课程和离线包” wording with fixed 10 bilingual sources and two
  lightweight Chinese learning paths, explicitly not courses/offline packages.
- [ ] **GREEN TS:** Strict `tsconfig.json` includes VitePress config/theme TS
  plus `docs/.vitepress/vue-shim.d.ts`, with `strict`, `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, and no emit. Biome is
  scoped to touched TS/config. Replace the existing `Intl as any` and
  `attrs as any` in `config.ts` through real narrowing, without behavior
  change or other cleanup. The singular owned shim is exactly:

  ```ts
  declare module '*.vue' {
    import type { Component } from 'vue'
    const component: Component
    export default component
  }
  ```

  Installed Markdown-It renderer-rule signatures remain five-parameter, while
  fallback `Renderer.renderToken` uses the installed three-argument API; the
  five-argument `defaultOpen`/`defaultClose` calls remain unchanged. This
  supersedes audit-2 item 6 only for this evidence: plural unowned
  `shims-vue.d.ts` remains deleted, while singular `vue-shim.d.ts` is owned.
- [ ] **Verify / task evidence:**

  ```sh
  node --test tests/ai/node/python-selector.test.mjs
  node scripts/run_ai_python.mjs --ai -- -m pytest tests/ai/test_toolchain.py -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  npm ci --ignore-scripts
  npm run typecheck
  npm run lint:ts
  ```

  Record the owned-path diff/status and complete command outputs in the current
  Task 1 report. No per-task review; do not stage/commit.

## Task 2: Parse the exact sources and normalize nine Markdown plus one HTML response

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`; recheck spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming` Python/httpx2 references, and
`superpowers:test-driven-development`. Consume Task 1 frozen
toolchain/launcher. Write only the Files below; no CLI, translation,
accepted-store, CAD, VitePress, or workflow edit.

**Files:**

- Create: `source-ai/sources.yaml`
- Create: `scripts/ai/types.py`, `scripts/ai/errors.py`
- Create: `scripts/ai/http_client.py`, `scripts/ai/manifest.py`
- Create: `scripts/ai/fetch.py`, `scripts/ai/normalize.py`
- Create: `tests/ai/test_manifest.py`, `tests/ai/test_fetch_normalize.py`
- Create: `tests/ai/fixtures/codex-cli-minimal.html`
- Create: `tests/ai/fixtures/codex-cli-normalized.md`
- Create: `tests/ai/fixtures/codex-cli-normalized.sha256`

**Consumes / produces:**

```python
SourceId = NewType("SourceId", str)
class ErrorCode(StrEnum):
    MANIFEST_INVALID = "MANIFEST_INVALID"
    FETCH_FAILED = "FETCH_FAILED"
    KEY_REQUIRED = "KEY_REQUIRED"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    WRITE_FAILED = "WRITE_FAILED"
class Source(BaseModel): ...                 # frozen, extra forbid
class SourceManifest(RootModel[tuple[Source, ...]]): ...
class FetchedPage(BaseModel): ...            # frozen boundary response
@dataclass(frozen=True, slots=True)
class NormalizedPage: source: Source; markdown: str; content_sha256: str
def load_sources(path: Path) -> SourceManifest: ...
def create_http_client(transport: httpx2.BaseTransport | None = None) -> httpx2.Client: ...
def fetch_source(client: httpx2.Client, source: Source) -> FetchedPage: ...
def normalize_source(source: Source, fetched: FetchedPage) -> NormalizedPage: ...
```

The frozen manifest rows are exactly:

```text
claude-code/quickstart | https://code.claude.com/docs/en/quickstart | https://code.claude.com/docs/en/quickstart.md | markdown | Anthropic
claude-code/memory | https://code.claude.com/docs/en/memory | https://code.claude.com/docs/en/memory.md | markdown | Anthropic
claude-code/permissions | https://code.claude.com/docs/en/permissions | https://code.claude.com/docs/en/permissions.md | markdown | Anthropic
claude-code/extensions | https://code.claude.com/docs/en/features-overview | https://code.claude.com/docs/en/features-overview.md | markdown | Anthropic
claude-code/best-practices | https://code.claude.com/docs/en/best-practices | https://code.claude.com/docs/en/best-practices.md | markdown | Anthropic
codex/cli | https://learn.chatgpt.com/docs/codex/cli | https://learn.chatgpt.com/docs/codex/cli | html | OpenAI
codex/prompting | https://learn.chatgpt.com/docs/prompting | https://learn.chatgpt.com/docs/prompting.md | markdown | OpenAI
codex/agents-md | https://learn.chatgpt.com/docs/agent-configuration/agents-md | https://learn.chatgpt.com/docs/agent-configuration/agents-md.md | markdown | OpenAI
codex/approvals-security | https://learn.chatgpt.com/docs/agent-approvals-security | https://learn.chatgpt.com/docs/agent-approvals-security.md | markdown | OpenAI
codex/customization | https://learn.chatgpt.com/docs/customization/overview | https://learn.chatgpt.com/docs/customization/overview.md | markdown | OpenAI
```

Titles in that order are `Claude Code Quickstart`, `Claude Code Memory`,
`Claude Code Permissions`, `Claude Code Features Overview`,
`Claude Code Best Practices`, `Codex CLI`, `Codex Prompting`,
`Codex AGENTS.md`, `Codex Agent Approvals and Security`, and
`Codex Customization Overview`; products/slugs are the two ID components.

- [ ] **RED:** Use behavior-specific pytest cases with distinct mutated inputs
  for duplicate/missing/unknown/empty fields, HTTP URLs, changed frozen URLs,
  wrong format, count !=10, and product split !=5/5. Use
  `httpx2.MockTransport` or a local server for status/content-type/redirect
  host/wire behavior. Every run collects and fails by assertion, not import.
- [ ] **Manifest GREEN:** `sources.yaml` is a JSON array with exactly the spec
  section 5 order, IDs, products, slugs, canonical/fetch HTTPS URLs, formats,
  owners, and non-empty exact titles. Pydantic rejects extra/missing data; a
  frozen expected tuple rejects any non-spec row or URL. Order affects nav
  only, never content comparison.
- [ ] **HTTP GREEN:** Production uses a context-managed `httpx2.Client` with
  `Limits(200,40,30.0)`, split timeout connect/read/write/pool
  `5/30/10/10`, `HTTPTransport(http2=True,retries=3,TCP_NODELAY)`,
  `follow_redirects=True`, and secret-safe event hooks. For each row, derive the
  expected hostname from that frozen `fetch_url` and require the final HTTPS
  response hostname to equal it exactly. RED cross-product redirects
  Claude→Codex and Codex→Claude; both return `FETCH_FAILED`, even though each
  hostname is valid for another manifest row.
- [ ] **Normalizer GREEN:** Nine rows require 2xx and recognizable Markdown
  content type/body, never HTML fallback. Normalize UTF-8/LF/frontmatter/noise
  deterministically while preserving Markdown structure. The HTML path uses
  only `article#mainContent`, requires exactly one readable match, and never
  falls back to a class/body.
- [ ] **Golden fixture:** Invented HTML includes headings, paragraphs, ordered
  and unordered lists, inline code, fenced `pre/code`, links, images, tables,
  and blockquotes plus sibling nav/footer/script noise. Assert complete golden
  Markdown and literal SHA-256; do not copy official page text.
- [ ] **Verify / task evidence:**

  ```sh
  node scripts/run_ai_python.mjs --ai -- -m pytest \
    tests/ai/test_manifest.py tests/ai/test_fetch_normalize.py -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  ```

  Record the owned-path diff/status and complete outputs in the current Task 2
  report. No per-task review, and no request to official sources.

## Task 3: Protect Markdown and translate changed pages through fixed kimi-k3

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`; recheck spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming` Python/httpx2/data-model/error
references, and `superpowers:test-driven-development`. Consume Task 2
`SourceId`, `ErrorCode`, `NormalizedPage`, and client policy. Write only the
Files below; do not read environment keys in pure functions, call real Kimi,
or edit sync, accepted content, CAD, TS, or workflows.

**Files:**

- Create: `scripts/ai/protect.py`, `scripts/ai/kimi.py`
- Create: `tests/ai/test_protect.py`, `tests/ai/test_kimi.py`
- Create: `tests/ai/fixtures/protected-input.md`
- Create: `tests/ai/fixtures/protected-output.md`

**Consumes / produces:**

```python
class KimiRequest(BaseModel): ...            # frozen boundary JSON
class KimiResponse(BaseModel): ...           # frozen choices/message
@dataclass(frozen=True, slots=True)
class ProtectedSpan: placeholder: str; original: str
@dataclass(frozen=True, slots=True)
class ProtectedMarkdown: text: str; spans: tuple[ProtectedSpan, ...]
@dataclass(frozen=True, slots=True)
class TranslationInput: source_id: SourceId; markdown: str; api_key: SecretStr
def protect_markdown(markdown: str) -> ProtectedMarkdown: ...
def restore_and_validate(source: str, protected: ProtectedMarkdown, translated: str) -> str: ...
def translate_markdown(client: httpx2.Client, request: TranslationInput) -> str: ...
```

- [ ] **RED:** One pytest per protected class: fence/language, inline code,
  URL, link target, command/option, environment variable, filename/path,
  product/API/config identifier. Mutation cases remove, duplicate, reorder, or
  invent a placeholder and alter structure. Assert `TRANSLATION_FAILED`.
- [ ] **Protection GREEN:** Replace non-overlapping spans in source order with
  deterministic `⟦LEWISDOCS_0000⟧` tokens. Restore only when every expected
  token occurs exactly once in order and no unknown token exists; compare
  fences byte-for-byte and compare inline-code, URL, link-target, and protected
  literal multisets after restoration.
- [ ] **Adapter GREEN:** POST only to
  `https://api.moonshot.ai/v1/chat/completions` with Bearer `SecretStr`, model
  `kimi-k3`, optional `reasoning_effort="low"`, and messages. Omit temperature,
  top_p, n, and penalties. Parse only `choices[0].message.content` through the
  frozen response model. Terminal/report data contains code/source/status, not
  body, header, key, or full text.
- [ ] **Wire/secret test:** At runtime generate a unique
  `secrets.token_urlsafe(48)` sentinel and pass it only through environment/in
  memory. `MockTransport` calls a redacted constant-time authorization helper
  and records only a boolean; on false, use a fixed failure message with no
  expected/actual operands rather than pytest equality that could expand the
  secret. Scan captured output, saved RED/GREEN reports and task evidence,
  `.ai-local`, all test/temp roots, built `dist`, and the owned-path/current
  working-tree diff for the generated value. No fixed fake key literal is
  stored in Git.
- [ ] **Verify / task evidence:**

  ```sh
  node scripts/run_ai_python.mjs --ai -- -m pytest \
    tests/ai/test_protect.py tests/ai/test_kimi.py -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  ```

  Record the owned-path diff/status and complete outputs in the current Task 3
  report. No per-task review; real Moonshot traffic is forbidden.

## Task 4: Implement the no-op/change transaction, atomic report, and Typer CLI

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`; recheck spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming` Python references, and
`superpowers:test-driven-development`. Consume Tasks 1–3 typed interfaces.
Write only the Files below; do not edit manifest,
fetch/normalization/protection semantics, CAD, VitePress, workflow, or
production fixture prose.

**Files:**

- Create: `scripts/ai/pages.py`, `scripts/ai/snapshot.py`,
  `scripts/ai/sync.py`
- Modify: `scripts/ai/cli.py`
- Create: `tests/ai/test_pages.py`, `tests/ai/test_snapshot.py`,
  `tests/ai/test_sync.py`
- Create: `tests/ai/node/ai-sync-cli.test.mjs`
- Create: `tests/ai/fixture_support.py`
- Create: `tests/ai/fixtures/private-root-template.json`
- Create: `tests/ai/fixtures/manifest-responses.json`

**Consumes / produces:**

```python
class AcceptedPage(BaseModel): ...           # frozen parsed frontmatter/body
class SyncReport(BaseModel): ...             # frozen, secret-free
class SyncOptions(BaseModel): ...            # frozen repo/content/staging paths
@dataclass(frozen=True, slots=True)
class Snapshot: files: tuple[FileDigest, ...]
class ClientFactory(Protocol):
    def __call__(self) -> ContextManager[httpx2.Client]: ...
class Translator(Protocol):
    def __call__(self, client: httpx2.Client, request: TranslationInput) -> str: ...
class FileOps(Protocol): ...                 # exact copy/replace/remove seam
@dataclass(frozen=True, slots=True)
class SyncDeps: client_factory: ClientFactory; translator: Translator; file_ops: FileOps
@dataclass(frozen=True, slots=True)
class AcceptanceRequest: options: SyncOptions; candidate: Path; report: SyncReport
def validate_candidate(root: Path, manifest: SourceManifest) -> None: ...
def tree_snapshot(root: Path) -> Snapshot: ...
def replace_snapshot(request: AcceptanceRequest, file_ops: FileOps) -> None: ...
def run_sync(options: SyncOptions, deps: SyncDeps) -> SyncReport: ...
app: typer.Typer
```

- [ ] **RED:** Separate pytest cycles prove page fields/pairing, explicit
  private-root safety before network, no-op, one-page change, missing key, each
  error code, secret absence, and every write fault. Path REDs cover repository
  root, `source-ai`, `docs`, another tracked/nonignored repository descendant,
  a non-`.ai-content` repository path, and allowed ignored/external roots; a
  rejected path performs zero fetches. `ai-sync-cli.test.mjs` spawns the real
  Node launcher→uv→Typer chain and asserts exit/stdout/report behavior. RED
  outputs are assertion failures saved in the task report.
- [ ] **Pages GREEN:** Deterministic frontmatter has exact spec fields/order.
  English/Chinese pairs share source/product/URL/owner/hash; Chinese has
  `translation_of`, `translation_model="kimi-k3"`,
  `ai_translated=true`, fixed warning, and official attribution. Validate exact
  10 pairs plus the existing two private `learn/` pages, their five links each,
  and no extra managed Markdown. Treat `learn/` as read-only input: sync never
  writes, stages, renames, swaps, or replaces either learning page. Tracked code
  contains only short synthetic fixture prose.
- [ ] **Private-root GREEN:** Before any network, resolve the requested root
  with `resolve(strict=False)` and require an absolute external path or a
  root-anchored ignored `.ai-content/**` path. Reject repository root,
  `source-ai`, `docs`, and every other tracked or nonignored repository
  descendant. Repeat the same resolved-path validation immediately before
  acceptance so path/symlink changes cannot redirect writes.
- [ ] **No-op/change GREEN:** Fetch/normalize all 10 into `.ai-local`; compare
  English hashes. A complete unchanged snapshot returns 0 and literal
  `no changes` without indexing `MOONSHOT_API_KEY` or calling translator. A
  changed set reads the key once, translates only those pages, reuses unchanged
  bytes, and validates the full 22-page candidate by combining staged `en/` and
  `zh-CN/` with the untouched live `learn/` before acceptance.
- [ ] **Atomic acceptance GREEN:** Acceptance swaps only `en/` and `zh-CN/`,
  then atomically replaces `.ai-local/report.json`; `learn/` is never part of a
  rename. Keep both live trees and the prior report recoverable through
  candidate staging, the two live→backup and two next→live renames, and report
  replacement. Transaction backups are uniquely named, same-root ephemeral
  siblings so renames stay on one filesystem; clean them after both successful
  acceptance and completed rollback. Do not create persistent `.ai-previous`
  state or unspecced previous-snapshot fault modes.

  Inject one-shot failures at every candidate/next write, each of the two
  live→backup renames, each of the two next→live renames, report temp write,
  report `os.replace`, and ephemeral cleanup. Every injected `WRITE_FAILED`
  restores the exact pre-run `en/` tree, `zh-CN/` tree, and prior report, leaves
  `learn/` byte-identical, removes same-root transaction debris, and leaves no
  mixed pair. Crash/power-loss atomicity remains out of MVP.
- [ ] **CLI GREEN:** Typer exposes only `sync`; npm calls it through `--ai`.
  Rich emits a stable JSON/table rendering from `SyncReport`. Exhaustively map
  `ErrorCode` to non-zero status and print only code/source/safe message.
- [ ] **Verify / task evidence:**

  ```sh
  node --test tests/ai/node/python-selector.test.mjs \
    tests/ai/node/ai-sync-cli.test.mjs
  node scripts/run_ai_python.mjs --ai -- -m pytest \
    tests/ai/test_pages.py tests/ai/test_snapshot.py tests/ai/test_sync.py -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  ```

  Compare before/after file digests for every fault and record the owned-path
  diff/status plus complete outputs in the current Task 4 report. No per-task
  review and no real HTTP/Kimi call.

## Task 5: Integrate CAD-last materialization and conditional VitePress UI

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`; recheck spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming` Python/TypeScript references, and
`superpowers:test-driven-development`, then load `omo:frontend` and select its
existing-project/component-system branch. Reuse the current components and
`--vp-*` CSS tokens; the user's narrowed scope forbids a greenfield redesign or
perfection expansion. Do not create/update `DESIGN.md`, add Lighthouse or
performance tooling, add Playwright/global installs, or impose score gates;
this solution introduces no new design token/state. Consume Task 2 manifest
types and Task 4 candidate validation. Write only the Files below; no production
content, workflow, external manifest parsing in TS, or second TS navigation
module.

**Files:**

- Create: `scripts/ai/cad_paths.py`, `scripts/ai/materialize.py`,
  `scripts/ai/verify_build.py`
- Create: `scripts/ai_content_gate.mjs`
- Modify: `scripts/import_docs.py`, `scripts/rewrite_links.py`,
  `scripts/link_citations.py`
- Modify: `package.json`, `package-lock.json`
- Modify: `docs/.vitepress/config.ts`,
  `docs/.vitepress/theme/index.ts`,
  `docs/.vitepress/theme/custom.css`
- Create: `docs/.vitepress/theme/components/AiLanguageSwitch.vue`
- Create: `tests/ai/test_cad_exclusions.py`,
  `tests/ai/test_materialize.py`, `tests/ai/test_verify_build.py`
- Create: `tests/ai/node/ai-content-gate.test.mjs`

**Consumes / produces:**

```python
@dataclass(frozen=True, slots=True)
class MaterializedRoute: source_id: SourceId | None; lang: str; route: str; counterpart: str | None
def iter_cad_markdown(docs_root: Path) -> tuple[Path, ...]: ...
def materialize_ai(options: MaterializeOptions) -> tuple[MaterializedRoute, ...]: ...
def verify_dist(options: VerifyBuildOptions) -> None: ...
```

`cad_paths.py` is justified because both rewrite and citation scripts consume
the same exclusion; import remains its fixed explicit `FILE_MAP`.

- [ ] **RED:** One pytest per observable CAD exclusion, invalid/missing private
  root, exact route, counterpart, learning path, search label, and internal
  dist mode. Native Node tests cover default stale-tree removal, default dist
  rejection, exact opt-in, and subprocess argv. A temp AI sentinel must remain
  byte-exact through rewrite/citation. REDs fail assertions and are saved.
- [ ] **Preparation GREEN:** Set exact order:
  `import → rewrite → link-citations → gate`. Preserve exact direct CAD
  entrypoints `python scripts/import_docs.py`,
  `python scripts/rewrite_links.py`, and
  `python scripts/link_citations.py`. The native Node gate alone removes stale
  `docs/ai` in default mode; only when `INCLUDE_AI_HANDBOOK` equals literal `1`
  does it spawn the existing launcher as
  `node scripts/run_ai_python.mjs --ai -- -m scripts.ai.materialize`. Internal
  materialization requires the root, revalidates all accepted pages, prepares a
  sibling temp tree, and atomically replaces derived `docs/ai`. Derived routes
  are 10
  `/ai/en/<product>/<slug>`, 10 `/ai/zh-CN/<product>/<slug>`, and two
  `/ai/zh-CN/learn/<product>`.
- [ ] **VitePress GREEN:** Modify the actual
  `docs/.vitepress/config.ts` directly. Use the environment flag and a
  readonly, hardcoded route/title list matching the frozen 10-source contract
  to append minimal nav/sidebar; TS reads no file and adds no Zod. Derived page
  frontmatter supplies `ai_counterpart` and `ai_search_label`; titles prefix
  `EN ·` or `中文 ·` for local-search results.
- [ ] **Switch GREEN:** `AiLanguageSwitch.vue` reads
  `frontmatter.ai_counterpart`, renders `中文`/`English`, and renders nothing
  for learning/CAD pages. It never rewrites URL strings. Preserve all existing
  theme components/layout slots and CAD config behavior, using only existing
  components and `--vp-*` tokens.
- [ ] **Build GREEN:** Package scripts are exact at the integration boundary:

  ```text
  import = python scripts/import_docs.py
  rewrite = python scripts/rewrite_links.py
  link-citations = python scripts/link_citations.py
  prepare-content = npm run import && npm run rewrite && npm run link-citations && node scripts/ai_content_gate.mjs prepare
  build = vitepress build docs && python scripts/watermark.py && node scripts/ai_content_gate.mjs verify-dist
  build:no-watermark = vitepress build docs && node scripts/ai_content_gate.mjs verify-dist
  ```

  Default `prepare` performs only native Node deletion of stale `docs/ai`;
  default `verify-dist` performs only native Node inspection and rejects every
  `dist/ai/` path or AI search reference. Neither default gate starts uv,
  touches the network, or invokes the AI launcher. With exact opt-in, the same
  gate alone spawns `node scripts/run_ai_python.mjs --ai -- -m
  scripts.ai.verify_build`; the Python verifier requires exactly 22 AI routes
  and both language labels. Node tests prove default no-spawn and exact internal
  `cwd`, `shell:false`, argv, and exit propagation. Keep `ai:sync` as the only
  `ai:*` npm command. Existing public workflows need no edit.
- [ ] **Verify / task evidence:**

  ```sh
  node scripts/run_ai_python.mjs --ai -- -m pytest \
    tests/ai/test_cad_exclusions.py tests/ai/test_materialize.py \
    tests/ai/test_verify_build.py -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  npm run typecheck
  npm run lint:ts
  node --test tests/ai/node/ai-content-gate.test.mjs
  npm run prepare-content
  npm run build
  ```

  Also expand the synthetic private-root JSON into ignored `.ai-content/qa`,
  run internal prepare/build, and assert 22 routes. Record the owned-path
  diff/status and complete outputs in the current Task 5 report. No per-task
  review; do not edit `.github`.

## Task 6: Verify AC1–AC8 and perform reproducible two-mode browser QA

**Execution envelope:** Work only in
`/Users/lewis/Work/Code.worktrees/lewisdocs-ai-agent-handbook`; recheck spec SHA
`62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1`;
load `$codex-continuation`, `omo:programming`, `omo:visual-qa`, and
`browser:control-in-app-browser`, plus `superpowers:test-driven-development`
only for defect briefs returned to an owning task. Consume all Task 1–5 outputs.
This task is acceptance-only: it may write only the Files/evidence below and
must not modify production, config, lock, or existing tests. A defect returns
to its owning task for a focused RED/GREEN/verify and report refresh. The
existing build/route/link/console/switch/responsive/CJK/two-oracle gate is
sufficient for this manual-trigger MVP; do not expand it into Lighthouse,
performance-score, Playwright, or global-install gates.

**Files:**

- Create: `tests/ai/test_acceptance.py`
- Create: `tests/ai/fixtures/browser-queries.json`
- Create after local acceptance passes:
  `project-docs/08-ai-agent-handbook-acceptance.md`
- Runtime-only: `.superpowers/sdd/task-6/evidence/`, `.ai-local/acceptance/`,
  `.ai-content/acceptance/`

**Consumes / produces:** The acceptance test composes only published interfaces;
it adds no production API. This task does not invent a RED: it runs the frozen
suites/builds/CLI and records observed PASS/FAIL/NOT RUN.

- [ ] **Automated verification:** Prove AC1 exact 10 pairs; AC2 routes,
  pairing/search/learning/CAD; AC3 no-op/no-key/no-call/no-byte-change; AC4 one
  changed pair/nine unchanged; AC5 five public error classes plus all write
  fault points; AC6 runtime-generated sentinel absent everywhere; AC7 CAD
  regression/exclusions; AC8 internal 22/default zero. The acceptance test
  automatically checks every exact AI route, the count of 22, all reciprocal
  source-pair/counterpart links, both learning pages and their five links,
  fixed CAD link/target, and default-build absence from routes, nav, search, and
  generated bytes; visual sampling is not a substitute. Run:

  ```sh
  node --test tests/ai/node/*.test.mjs
  node scripts/run_ai_python.mjs --ai -- -m pytest tests/ai -q
  node scripts/run_ai_python.mjs --ai -- -m basedpyright
  node scripts/run_ai_python.mjs --ai -- -m ruff check scripts/ai tests/ai
  npm run typecheck
  npm run lint:ts
  ```

- [ ] **Fixed browser oracle:** `browser-queries.json` fixes:
  `synthetic permissions marker` → `/ai/en/claude-code/permissions`, `EN`;
  `合成权限标记` → `/ai/zh-CN/claude-code/permissions`, `中文`; and CAD source
  `/platforms/bricscad`, selector
  `a[href="/platforms/autocad#二、api-整体架构-六层金字塔"]`, visible text
  `3.1 §二 API 整体架构：六层金字塔`, target route `/platforms/autocad`, target
  anchor `二、api-整体架构-六层金字塔`.
- [ ] **Automated route inventory:** Internal routes are exactly
  `/ai/{en,zh-CN}/claude-code/{quickstart,memory,permissions,extensions,best-practices}`,
  `/ai/{en,zh-CN}/codex/{cli,prompting,agents-md,approvals-security,customization}`,
  `/ai/zh-CN/learn/claude-code`, and `/ai/zh-CN/learn/codex` (22 total); the
  automated acceptance above covers every route and link.
- [ ] **Sampled capture contract:** At each 375/768/1280 viewport, fresh-capture
  `/ai/en/claude-code/permissions`, its paired
  `/ai/zh-CN/claude-code/permissions`, both Chinese learning paths, and existing
  CAD page `/platforms/bricscad`. On the paired source pages, capture the
  relevant rest/focus/activation/settled language-switch, AI-nav, and bilingual
  search states; verify switches both ways, search activation, no
  console/hydration errors, and natural Chinese wrapping. Default mode
  fresh-captures the same CAD page plus the fixed AI 404 at all three
  viewports. Do not visually capture every AI route.
- [ ] **Preview process contract:** Local VitePress 1.6.4 `serve(options)`
  accepts only root/base/port and ignores hostname input, matching the official
  `ServeOptions`; do not use an npm wrapper or invent another option. Preflight
  each fixed port, then call Node `spawn` with `process.execPath`, absolute
  `node_modules/vitepress/bin/vitepress.js`, and argv
  `preview docs --port 4173 --base /` for default or
  `preview docs --port 4174 --base /` for internal, repository cwd, and
  `shell:false`. Probe `http://127.0.0.1:<port>/` until ready. After captures,
  terminate and wait for that actual Node child PID, then prove the port is
  released before continuing; never run both previews concurrently.
- [ ] **Default browser run:** Build with no opt-in, start the 4173 process
  above, prove CAD nav/search/link/backlink and fixed `/ai/...` 404 with no AI
  nav/search hit, and produce the fresh default sample set.
- [ ] **Internal browser run:** Expand the synthetic ignored root, prepare/build
  with `AI_CONTENT_ROOT=<absolute ignored root>` and exact
  `INCLUDE_AI_HANDBOOK=1`, start the 4174 process above, and produce the complete
  internal sample/state set against that same current build.
- [ ] **Visual dual oracle:** Validate capture signatures, dimensions, freshness,
  and complete sampled page/state inventory, then dispatch two independent
  read-only reviewers concurrently over the same evidence:
  design-system/functional integrity and visual-fidelity/CJK precision. Any
  finding returns to its owner and invalidates affected evidence. The final
  approving round requires both reviewers to return fresh PASS on the complete
  representative sample set from the same current build; automated route tests
  or an earlier-build verdict never self-certify visual PASS. Record automated
  outputs, preview lifecycle receipts, sample inventory, and both oracle
  verdicts in the current Task 6 report/evidence.
- [ ] **Optional real final sync:** Only after explicit controller confirmation
  of process-only key, intended private root with two private learning pages,
  and authorization, run `npm run ai:sync` twice. First may fetch/translate;
  second must be real no-op. Otherwise record `NOT RUN` and do not claim real
  content acceptance. No push/deploy follows.
- [ ] **Final implementation/code gates:** Any failure is routed to its Task
  1–5 owner; Task 6 does not patch production. After the acceptance suite and
  visual oracles pass, one fresh GPT-SOL performs the final implementation
  review and one separate fresh reviewer performs the final code-quality review
  over the current complete implementation diff/equivalent evidence and six
  task reports. Findings require owner fix, affected verification/report
  refresh, and both fresh final reviews. The acceptance report distinguishes
  macOS default/internal, sampled manual browser QA, Windows, real Kimi, and
  remote publication (`NOT IN SCOPE`). Do not stage/commit/push/PR/deploy.

## Dependency and AC Matrix

```text
1 strict runtime/tooling → 2 manifest/fetch/normalize → 3 protected Kimi
→ 4 no-op/atomic acceptance/CLI → 5 CAD/VitePress integration → 6 acceptance
```

| Coverage | Owner | Evidence |
|---|---|---|
| Spec §1–4, §14 public/private scope | 1, 4–6 | sole command, ignored private content, public default off |
| §5–7 / AC1 exact sources | 2, 4, 6 | frozen 10-row manifest and 10 validated pairs |
| §8–10 / AC2 pages, learning, routes, switch, search | 4–6 | pair/frontmatter validators and browser oracle |
| §11.1–11.2 / AC3–AC5 sync transaction | 4, 6 | no-op, one change, failure/rollback matrix |
| §11.3 normalization | 2 | 9 Markdown wire tests and one full HTML golden |
| §11.4 / AC7 CAD order | 5, 6 | shared exclusion, sentinel, CAD browser result |
| §12 Kimi / AC6 secrets | 3, 4, 6 | fixed adapter, protected spans, dynamic sentinel |
| §13 errors | 2–4 | exhaustive `ErrorCode`, safe Typer/Rich output |
| §15 security | 2–6 | redirect host, secret scan, no public full text |
| §16 AC1–AC8 / §17 completion | 6 | full automated + two-mode manual evidence |
| §18 deferred inputs | 6 | explicit key/root authorization gate and accurate NOT RUN |

## Plan Self-Check

```sh
test "$(shasum -a 256 project-docs/07-ai-agent-handbook-spec.md | awk '{print $1}')" = \
  "62afc39b3da75307a897e5cd2e6170bd6c80d800b2482707f66c4ab68d743da1"
test "$(rg -c '^## Task [1-6]:' docs/superpowers/plans/2026-07-26-ai-agent-handbook.md)" = 6
test "$(wc -l < docs/superpowers/plans/2026-07-26-ai-agent-handbook.md)" -le 900
! rg -n -e 'TO''DO' -e 'TB''D' -e 'implement ''later' -e 'similar to ''Task' \
  docs/superpowers/plans/2026-07-26-ai-agent-handbook.md
rg -n 'pydantic==2.13.4|typer==0.27.0|rich==15.0.0|httpx2.*2.9.1|uv==0.11.32' \
  docs/superpowers/plans/2026-07-26-ai-agent-handbook.md
rg -n 'AC1|AC2|AC3|AC4|AC5|AC6|AC7|AC8|config.ts|4173|4174' \
  docs/superpowers/plans/2026-07-26-ai-agent-handbook.md
shasum -a 256 docs/superpowers/plans/2026-07-26-ai-agent-handbook.md
wc -l -c docs/superpowers/plans/2026-07-26-ai-agent-handbook.md
```

Final handoff reports plan SHA/line/byte counts, six tasks, self-check results,
preserved unrelated dirty files, and confirms no stage/commit/push/PR/deploy or
derived-content command occurred.
