# Code Review: feat/port-claude-july-updates Round 5

Date: 2026-07-09

Reviewer: Codex

Target: staged working tree on `feat/port-claude-july-updates`

Base: `origin/main`

Merge base: `99df140a0860bd8dfe6521d2f782660f4b966348`

Reviewed revision: `99df140a0860bd8dfe6521d2f782660f4b966348` plus staged changes

Plan: `docs/plans/2026-07-08-port-claude-july-updates-plan.md`

Prior review: `docs/code-reviews/2026-07-09-feat-port-claude-july-updates-round-4-code-review.md`

Verdict: BLOCKED

All P1/P2/P3 findings below are required before merge.

## Scope Check

Intent: port the July Claude-plugin delta (`3987510..099ec4c`) into Antigravity-native plugin surfaces, adapting model/tiering, saga outcome, fleet-core, mission-control, validation, and docs without keeping Claude-only runtime assumptions.

Delivered: the staged tree now includes all prior untracked tests and review artifacts, and the index is clean for whitespace. Runtime reviewer persona paths are fixed. Remaining issues are concentrated in deferred external-engine documentation, fleet-core effort contract drift, and the still-red scoped Bandit gate.

Scope status: REQUIREMENTS MISSING.

Mergeability note: `HEAD` still equals `origin/main` and the branch has zero commits ahead of main. All reviewed implementation changes are staged, with no unstaged or untracked files. The branch still needs an actual commit before it can merge these changes.

## Findings

### P1

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 1 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md:213` | The external-engine doc still contradicts its own deferred disclaimer. Line 6 says the protocol is deferred and the bridge files are not present or runnable, but lines 213-219 say the mechanics are "now backed" by always-on `saga`/`fleet-core` enforcement and that enforcement already runs under every chaperone dispatch. The referenced dispatch files are still missing (`dispatch-adapter-contract.md`, `engine_dispatch.py`, `engine_resolver.py`, `engine_registry.py`, `worker-manifest.md`). This can lead an implementer to rely on non-existent runtime enforcement. | correctness / docs-contract | 100 | manual |

### P2

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 2 | `plugins/fleet-core/references/effort-convention.md:54` | The fleet effort contract still describes the `agent` path as an `EFFORT_RIDER` prompt proxy with no real knob, and line 69 still points to an upstream `team-execution/.../worker-manifest.md`. The implementation and tests now do the opposite for `agent`: `effort_rider.py:84-96` returns a Gemini `generation_config.thinking_level` payload, and `test_fleet_commons.py:53-60` asserts that behavior. The shared contract, changelog, and module docstring must match the actual Gemini payload contract and Antigravity-native surfaces. | maintainability / docs-contract | 100 | manual |

### P3

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 3 | `plugins/fleet-core/tests/test_fleet_commons.py:21` | The scoped Bandit gate still exits nonzero: `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts`. Current output has no high-severity findings, but it still reports 47 low findings, including B101 from the newly tracked fleet-core tests because the scan path includes `plugins/fleet-core/tests`. Fix the issues, exclude/baseline test paths, or explicitly document the accepted baseline for this scoped gate. | security / quality-gate | 90 | manual |

## Round-4 Finding Status

| Round-4 # | Status | Evidence |
|---|---|---|
| 1 | FIXED | Runtime personas and `consensus-protocol.md` now point to `multi-agent-consensus/skills/multi-agent-consensus/references/review-criteria.md`; no `team-execution/skills/team-execution/references/review-criteria.md` matches remain. |
| 2 | STILL OPEN | Top disclaimer says deferred, but `external-engine-workers.md:213-219` still claims existing runtime enforcement. |
| 3 | FIXED | `plugins/fleet-core/tests/test_fleet_commons.py` and `tests/test_agent_tier_lint.py` are now tracked, and the focused pytest command passes. |
| 4 | PARTIAL | `effort-convention.md` changed some `team-execution` wording, but still points to `team-execution/.../worker-manifest.md` and contradicts the actual `agent` payload behavior. |
| 5 | FIXED | `git diff --cached --check`, full diff check, and unstaged diff check all pass. |
| 6 | STILL OPEN | Scoped Bandit still exits 1. |

## Plan-Completion Audit

COMPLETION: PARTIAL.

Done:
- Fleet-core plugin, primitives, and tests are now tracked in the staged diff.
- Runtime multi-agent persona review-criteria paths now target local Antigravity docs.
- Cross-repo nested tracked-issue pagination remains fixed by direct probe.
- README deploy sync and deploy plugin metadata are staged.
- Whitespace hygiene gates pass for cached, unstaged, and full working-tree diffs.

Partial / Not Done:
- External-engine worker docs still mix deferred/non-runnable status with active-enforcement claims.
- Fleet-core effort docs/changelog/docstrings do not match the actual Gemini payload behavior.
- Scoped Bandit gate remains nonzero without a baseline, exclusion, or accepted-risk note.
- The branch still has zero commits ahead of `origin/main`; staged changes must be committed before merge.

## Checks Run

Pass:
- `git fetch origin main --quiet`
- `git rev-parse HEAD` / `git merge-base origin/main HEAD` / `git rev-list --count origin/main..HEAD`
- `git diff --check $(git merge-base origin/main HEAD)`
- `git diff --cached --check`
- `git diff --check`
- `uv run ruff check .`
- `uv run pytest -q plugins/fleet-core tests/test_agent_tier_lint.py` (5 passed)
- `uv run pytest -q plugins/mission-control` (190 passed)
- `uv run pytest -q plugins/saga` (699 passed, 1 skipped)
- `uv run pytest -q plugins/multi-agent-consensus` (6 passed)
- `uv run pytest -q` (932 passed, 1 skipped)
- `uv run python scripts/validate_plugins.py --json`
- `uv run python scripts/validate_plugins.py --strict --json`
- `uv run python scripts/validate_plugins.py --install-dir /tmp/empty-antigravity-install --json` (non-strict missing install accepted with warnings)
- `uv run python scripts/validate_plugins.py --install-dir /tmp/empty-antigravity-install --strict --json` (expected failure for missing install)
- `uv run python plugins/saga/scripts/render_docs_visuals.py`
- Direct nested tracked-issue pagination probe

Fail:
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts`

## Coverage And Residual Risk

Suppressed findings below confidence threshold: 0.

Untracked files excluded from mergeable evidence: none.

Residual risk: this is still a staged pre-commit review. After committing, rerun the final review checks against the committed branch diff before opening or merging a PR.

## Required Before Merge

1. Make `external-engine-workers.md` internally consistent: either keep it as clearly deferred design notes throughout, or add the missing implementation files and tests proving enforcement exists.
2. Update fleet-core effort docs/changelog/docstrings to match the actual `generation_config.thinking_level` payload behavior and remove/replace stale `team-execution` worker-manifest references.
3. Resolve, exclude, baseline, or explicitly reclassify the scoped Bandit findings, then rerun the scoped Bandit command.
4. Commit the staged branch changes and rerun the final review checks against the committed branch diff.
