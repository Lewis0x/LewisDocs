# AI Agent Handbook Acceptance

Status: local MVP acceptance passed on macOS on 2026-07-27.

The synthetic local acceptance suite covers the frozen 10-source manifest, 20
English/Chinese pages, two Chinese learning paths, 22 internal routes,
counterpart links, no-op and one-change synchronization, public error-code and
write-fault behavior, secret-sentinel containment, CAD exclusions, and
default/internal build isolation. Complete command outputs are recorded in
`.superpowers/sdd/task-6/evidence/`.

Automated results:

- Python suite: 189 passed.
- Native Node suite: 27 passed, including four executable local-search
  renderer behavior tests.
- basedpyright: 0 errors, warnings, or notes.
- Ruff, Ruff formatting, TypeScript, Biome, and `git diff --check`: passed.
- Internal synthetic build: 22 HTML routes; `scripts.ai.verify_build` passed.
- Default build: no `docs/ai`, no `dist/ai`, no AI navigation, no AI
  local-search routes, and no implementation-plan search entry.

The only default-build `/ai/` byte hits are explanatory prose in the published
implementation-plan page. The content gate and its regression tests explicitly
allow prose while rejecting handbook routes.

The runtime acceptance tests invoke the safe sync CLI boundary with mock
transport and synthetic roots. They observe all five non-key public error
classes, no-op/changed/failure secret containment, preserved accepted snapshots,
and successful post-failure materialization without contacting Kimi.

## Browser and visual acceptance

- The default and internal builds were exercised in real browsers at
  375×812, 768×900, and 1280×800. The evidence set contains 29 valid PNGs,
  route/layout metrics, console records, and stopped-process receipts.
- Internal EN and ZH permission pages, both five-link learning paths, the
  768px mobile menu, keyboard focus, and exact EN↔ZH counterpart navigation
  passed without horizontal overflow.
- Exact English and Chinese queries visibly selected language-labelled results
  and landed on the matching permission routes. Internal implementation plans
  are excluded from local search.
- The existing BricsCAD page remained usable in both modes; default CAD search
  returned the existing route. Default-mode AI routes returned HTTP 404 at all
  three widths.
- Both browser backends block rendering any HTTP 404 with
  `ERR_BLOCKED_BY_CLIENT`, so the 404 assertion is recorded as raw response
  headers and bodies rather than a fabricated screenshot.
- Browser console warning/error arrays are empty. Preview ports 4173–4177 were
  released, and every receipt records a stopped process.
- Two independent visual gates inspected all 29 images. Their initial
  multi-image preview produced false crop/blank-frame findings; focused
  one-by-one original-pixel rechecks corrected both verdicts to CLEAR.

## Remaining environment-dependent work

- Final implementation/spec gate: CLEAR.
- Final code-quality/security review: CLEAR, with no actionable findings.
- Windows validation: NOT RUN (not executed on a Windows runner).
- Real Kimi sync: NOT RUN (`MOONSHOT_API_KEY` was unavailable; no real
  translation request was sent).
- Remote publication, push, pull request, and deployment: NOT IN SCOPE.
