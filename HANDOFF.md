# AI Agent Handbook Handoff

Updated: 2026-07-27

## Current direction

The AI handbook is public LewisDocs content. Its fixed accepted-content directory is:

```text
source-ai/content/
├── en/
│   ├── claude-code/*.md
│   └── codex/*.md
├── zh-CN/
│   ├── claude-code/*.md
│   └── codex/*.md
└── learn/
    └── zh-CN/
        ├── claude-code.md
        └── codex.md
```

`source-ai/content` is intentionally inside the repository and may be committed and
deployed publicly. The earlier private-root and internal-build design is obsolete.

## User entry points

There is one manual synchronization command:

```sh
npm run ai:sync
```

The command always targets `source-ai/content`; callers do not set
`AI_CONTENT_ROOT`. A real update requires `MOONSHOT_API_KEY` in the current process
only when one or more upstream pages changed.

The two learning paths are maintained by the team. Synchronization validates them
but does not overwrite them.

## Build and deployment

AI routes, navigation, language switching, and local search are enabled in the
default public build. There is no `INCLUDE_AI_HANDBOOK` opt-in.

```sh
npm run prepare-content
npm run build
```

Preparation validates `source-ai/content` and derives `docs/ai`. Do not edit or
commit `docs/ai`; it remains generated VitePress input.

`.github/workflows/ai-handbook-sync.yml` is manual-only. It:

1. reads `MOONSHOT_API_KEY` from the repository Actions secret;
2. synchronizes the fixed public content directory;
3. prepares and verifies the complete public site;
4. commits only `source-ai/content` back to the selected branch when bytes changed.

A content commit on `main` then triggers the existing Cloudflare Pages workflow.

## Safety boundaries

- Never write `MOONSHOT_API_KEY` to files, command arguments, logs, or reports.
- Keep `.ai-local/`, `.ai-content/`, `docs/ai/`, build output, and reports untracked.
- Keep synchronization manual; do not add a schedule or PR bot.
- Preserve exact source attribution and paired English/Chinese metadata.
- Do not push, open a PR, trigger Actions, or deploy without explicit user approval.

## Current state

- Branch: `codex/ai-agent-handbook`
- Public learning paths exist under `source-ai/content/learn/zh-CN`.
- The repository Actions secret list includes `MOONSHOT_API_KEY`; its value was
  neither read nor written locally.
- The first real synchronization has not run because the key is stored in GitHub
  Actions rather than the local process.
- The manual workflow must exist on GitHub before it can be dispatched.
- No commit, push, PR, Actions dispatch, or deployment has been performed in this
  handoff session.

## Verification

Windows verification completed on 2026-07-27:

- Node tests: 19 passed.
- Python AI tests: 186 passed, 6 skipped for unavailable Windows symlink/FIFO
  capabilities.
- TypeScript typecheck and Biome lint passed.
- Ruff check and format check passed.
- basedpyright reported 0 errors, 0 warnings, and 0 notes.
- A synthetic accepted corpus completed public preparation, VitePress build,
  watermarking, and exact verification of all 22 AI routes.
- Browser checks confirmed public navigation, five ordered learning-path links,
  Chinese/English switching, and no horizontal overflow at 390 x 844.

Synthetic accepted pages and derived `docs/ai` were removed after verification.
Only the two real learning paths remain under `source-ai/content`.

## Next remote step

After local verification, explicitly approve a push of the feature branch. Then
dispatch **Sync public AI handbook** on that branch. Review the bot-created content
commit and its build before merging to `main`.
