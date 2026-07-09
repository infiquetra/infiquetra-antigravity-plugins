# Code Review: feat/port-claude-july-updates Round 6

Date: 2026-07-09

Reviewer: Codex

Target: staged working tree on `feat/port-claude-july-updates`

Base: `origin/main`

Merge base: `99df140a0860bd8dfe6521d2f782660f4b966348`

Reviewed revision: `99df140a0860bd8dfe6521d2f782660f4b966348` plus staged changes

Plan: `docs/plans/2026-07-08-port-claude-july-updates-plan.md`

Prior review: `docs/code-reviews/2026-07-09-feat-port-claude-july-updates-round-5-code-review.md`

Verdict: BLOCKED

All P1/P2/P3 findings below are required before merge.

## Scope Check

Intent: port the July Claude-plugin delta (`3987510..099ec4c`) into Antigravity-native
plugin surfaces, adapting fleet-core, saga, mission-control, multi-agent-consensus, validation,
docs, and tests while explicitly deferring Claude-only external-engine bridge surfaces.

Delivered: most prior round-5 blockers are fixed or reclassified with evidence. The exact scoped
production Bandit gate passes, fleet effort docs now match the Gemini payload behavior, and the
external-engine doc no longer claims currently runnable chaperone enforcement as strongly as before.
New residual blockers remain in partial active external-engine code, missing tests for the new
hash-chained run ledger, and metadata/doc portability.

Scope status: REQUIREMENTS MISSING.

Mergeability note: `HEAD` still equals `origin/main` and the branch has zero commits ahead of main.
All implementation changes reviewed here are staged. They must be committed before a PR can merge
this work.

## Findings

### P1

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 1 | `plugins/saga/scripts/execution_spec.py:438` | External-engine routing is partially active even though the bridge was deferred. `Unit.from_dict()` accepts `engine` / `capability` and immediately calls `_validate_external_engine_selector()` (`execution_spec.py:880-884`), which imports `plugins/saga/scripts/engine_registry.py` (`execution_spec.py:438-444`). That file is absent in this port, and a local parse probe for an engine-routed unit raises `FileNotFoundError` before a clean deferred-path `SpecError`. The source inventory confirms the actual bridge files (`engine_registry.py`, `engine_dispatch.py`, `engine_resolver.py`, `dispatch-adapter-contract.md`) were deliberately omitted, while the plan classifies external bridges as blocked/deferred (`docs/plans/2026-07-08-port-claude-july-updates-plan.md:58`, `:83-84`). Any authored engine/capability unit now enters a half-ported runtime path instead of being cleanly rejected or fully supported. | correctness / built-vs-planned | 100 | manual |

Suggested fix: either remove/defer the active `engine`/`capability` spec and emitter paths, or make them fail with a clear `SpecError` saying external-engine dispatch is deferred in Antigravity. If the intent is to support the path now, add the missing registry/dispatch files plus tests that prove the Antigravity dispatch surface is runnable.

### P2

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 2 | `plugins/saga/scripts/run_ledger.py:116` | The new hash-chained run ledger has no direct tests, even though it is a shared state primitive and the staged learning claims "all ledger tests passed" (`docs/engineering-journal/LEARNINGS.md:40`). `append_fact()` now performs the read-compute-write chain under `flock` (`run_ledger.py:116-142`), but `rg` finds no tests calling `RunLedger`, `append_fact()`, `verify_chain()`, `reuse_ratio()`, `last_n_prior()`, or `build_fact()`. A future change can silently break the concurrency/tamper-evidence contract that round-1 finding 16 was about. | testing / reliability | 100 | manual |

Suggested fix: add focused tests for `run_ledger.py`: build/append/read round trip, chain verification, in-place mutation detection, torn trailing line tolerance, numeric rollups, and a concurrent append regression that proves unique `prev_hash` chaining under the lock. Then update the learning entry to cite those tests instead of an uncited manual claim.

### P3

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 3 | `plugins/fleet-core/plugin.json:9` | The newly added Antigravity `fleet-core` manifest points its `repository` to `https://github.com/infiquetra/infiquetra-claude-plugins`. Existing Antigravity plugin manifests in this repo use `https://github.com/infiquetra/infiquetra-antigravity-plugins`, and `README.md` already records Claude as upstream source lineage separately. Leaving the plugin manifest pointed at the source repo will send install/metadata consumers to the wrong canonical plugin repository. | maintainability / metadata | 100 | manual |
| 4 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md:6` | Newly staged docs contain machine-local absolute `file:///Users/jefcox/...` links. The external-engine doc links `QUEUED.md` through an absolute file URL, and `docs/engineering-journal/LEARNINGS.md:34` does the same for `run_ledger.py`. Generated repo docs should use repo-relative links so they survive other worktrees, CI, and another operator machine. | maintainability / docs-portability | 100 | manual |

Suggested fixes:
- Set `plugins/fleet-core/plugin.json` `repository` to the Antigravity repo. Consider adding a validator warning for plugin manifests whose repository points at `infiquetra-claude-plugins` outside explicit source-lineage docs.
- Replace new `file:///Users/jefcox/...` links with repo-relative Markdown links.

## Round-5 Finding Status

| Round-5 # | Status | Evidence |
|---|---|---|
| 1 | FIXED / superseded | `external-engine-workers.md:213-215` now describes planned/deferred obligations and says they are enforced only once implemented. The stronger remaining issue is now active code partially accepting engine/capability units while the bridge files are absent. |
| 2 | FIXED | `effort-convention.md:54` and `:66-71`, `fleet-core/CHANGELOG.md:80-87`, and `effort_rider.py:68-96` now agree that the `agent` path returns Gemini `generation_config.thinking_level`. |
| 3 | RECLASSIFIED FIXED | The exact plan gate, `uv run bandit -q -c pyproject.toml -ll -r plugins/fleet-core/scripts plugins/saga/scripts plugins/mission-control/scripts`, exits 0. The earlier no-threshold scan still reports low-severity findings, mostly tests, but it is not the plan's required scoped production Bandit gate. |

## Plan-Completion Audit

COMPLETION: PARTIAL.

Done:
- Source range commits `3987510` and `099ec4c` exist in the sibling Claude repo, and the source inventory was regenerated.
- Fleet-core, saga, mission-control, multi-agent-consensus, validation, and docs surfaces are staged.
- Focused and full pytest suites pass.
- Exact scoped production Bandit gate passes.
- Plugin doctor passes in normal and strict installed-state modes.

Partial / Not Done:
- External-engine bridge work is documented as deferred, but active `execution_spec.py` code still partially accepts engine/capability selectors and crashes against absent bridge files.
- The new `run_ledger.py` primitive lacks direct tests for the state and concurrency behavior it introduces.
- Newly staged metadata/docs still contain wrong canonical repository metadata and machine-local absolute links.
- The branch still has zero commits ahead of `origin/main`; staged changes must be committed before merge.

## Checks Run

Pass:
- `git fetch origin main --quiet`
- `git merge-base origin/main HEAD` / `git rev-parse HEAD` / `git rev-parse origin/main`
- `git diff --check $(git merge-base origin/main HEAD)`
- `git diff --cached --check`
- `git diff --check`
- `git -C ../infiquetra-claude-plugins diff --name-status 3987510..099ec4c -- ...`
- `uv run ruff check .`
- `uv run pytest -q plugins/fleet-core tests/test_agent_tier_lint.py` (5 passed)
- `uv run pytest -q plugins/multi-agent-consensus` (6 passed, coverage no-data warning)
- `uv run pytest -q plugins/mission-control` (190 passed)
- `uv run pytest -q plugins/saga` (699 passed, 1 skipped)
- `uv run pytest -q` (932 passed, 1 skipped)
- `uv run python scripts/validate_plugins.py --json`
- `uv run python scripts/validate_plugins.py --strict --json`
- `uv run python scripts/validate_plugins.py --install-dir <empty-dir> --json` (expected warnings, exit 0)
- `uv run python scripts/validate_plugins.py --install-dir <empty-dir> --strict --json` (expected missing-install failure, exit 1)
- `uv run bandit -q -c pyproject.toml -ll -r plugins/fleet-core/scripts plugins/saga/scripts plugins/mission-control/scripts`
- `uv run python plugins/saga/scripts/render_docs_visuals.py`
- Local `discover_subissues.fetch_subissues()` pagination probe with multiple sub-issue pages and tracked-issue pagination (no duplicate tracked nodes)

Informational:
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts` still exits nonzero with low-severity findings only. This is outside the exact required production-path `-ll` gate.

Fail / Blocked:
- Local `execution_spec.ExecutionSpec.from_dict(...)` probe with an engine-routed unit raises `FileNotFoundError` for missing `plugins/saga/scripts/engine_registry.py`.
- No direct tests found for `RunLedger`, `append_fact()`, `verify_chain()`, `reuse_ratio()`, `last_n_prior()`, or `build_fact()`.

## Coverage And Residual Risk

Suppressed findings below confidence threshold: 0.

Untracked files excluded from mergeable evidence before this artifact: none.

Residual risk: this is still a staged pre-commit review. After fixes and commit, rerun the final review
against committed branch diff, not only the index.

## Required Before Merge

1. Resolve the partial external-engine activation: cleanly defer `engine`/`capability` in active code or implement the missing bridge path with tests.
2. Add direct `run_ledger.py` tests and correct the learning entry's validation claim.
3. Fix `fleet-core` plugin metadata to point at the Antigravity repo.
4. Replace newly staged absolute `file:///Users/jefcox/...` links with repo-relative links.
5. Commit the staged branch changes and rerun final checks against the committed branch diff.
