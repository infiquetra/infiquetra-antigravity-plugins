# Code Review: feat/port-claude-july-updates Round 4

Date: 2026-07-09

Reviewer: Codex

Target: working tree on `feat/port-claude-july-updates`

Base: `origin/main`

Merge base: `99df140a0860bd8dfe6521d2f782660f4b966348`

Reviewed revision: `99df140a0860bd8dfe6521d2f782660f4b966348` plus staged and unstaged working-tree changes

Plan: `docs/plans/2026-07-08-port-claude-july-updates-plan.md`

Prior review: `docs/code-reviews/2026-07-09-feat-port-claude-july-updates-round-3-code-review.md`

Verdict: BLOCKED

All P1/P2/P3 findings below are required before merge.

## Scope Check

Intent: port the July Claude-plugin delta (`3987510..099ec4c`) into Antigravity-native plugin surfaces, adapting model/tiering, saga outcome, fleet-core, mission-control, validation, and docs without keeping Claude-only runtime assumptions.

Delivered: the working tree contains broad implementation, tests, docs, and plugin-surface updates. Several round-3 findings are fixed, but active runtime docs still point at removed `team-execution` paths, the external-engine documentation remains contradictory, test evidence is partly untracked, and current staged content is not merge-clean.

Scope status: REQUIREMENTS MISSING.

Mergeability note: `HEAD` equals `origin/main` and the branch has zero commits ahead of main. This review therefore covers staged, unstaged, and untracked local state. Untracked files are not part of the mergeable branch until added and committed.

## Findings

### P1

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 1 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/personas/security-reviewer.md:28` | Runtime reviewer personas still instruct workers to load `team-execution/skills/team-execution/references/review-criteria.md`, but this Antigravity repo does not have that path. `SKILL.md:33-34` says the runtime reads personas from `skills/multi-agent-consensus/references/personas/` and then the Antigravity review criteria, so these stale persona prompts are the active surface. `rg` finds the same dead path in multiple runtime personas and `references/consensus-protocol.md:154`. Reviewers spawned from these prompts will either fail to load their rubric or apply a non-existent Claude/team-execution contract. | correctness / agent-contract | 100 | manual |
| 2 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md:250` | The top of the document now says the external-engine worker protocol is planned/deferred, but the body still says "mechanics saga/fleet-core already enforce underneath every chaperone dispatch call." The referenced implementation files are absent: `plugins/saga/references/dispatch-adapter-contract.md`, `plugins/saga/scripts/engine_dispatch.py`, `plugins/saga/scripts/engine_resolver.py`, `plugins/saga/scripts/engine_registry.py`, and `plugins/saga/references/worker-manifest.md`. This leaves an active workflow document with mutually contradictory guidance about whether dispatch enforcement exists. | correctness / docs-contract | 100 | manual |

### P2

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 3 | `plugins/fleet-core/tests/test_fleet_commons.py:1` | Fleet-core now has local tests and `uv run pytest -q plugins/fleet-core tests/test_agent_tier_lint.py` passes, but both `plugins/fleet-core/tests/test_fleet_commons.py` and `tests/test_agent_tier_lint.py` are untracked. If the branch is committed from the current index, the fleet-core test fix and required agent-tier lint do not merge. | testing / merge-verification | 100 | manual |
| 4 | `plugins/fleet-core/references/effort-convention.md:4` | The shared effort convention is still written against `team-execution` runtime surfaces: line 4 names `team-execution` worker tables, line 54 cites `team-execution SKILL.md Step B1`, and line 69 points to an upstream `team-execution/.../worker-manifest.md` that is not present. For an Antigravity port, this keeps the canonical effort contract tied to missing Claude/team-execution mechanics instead of the local `multi-agent-consensus` and deferred external-engine status. | maintainability / docs-contract | 90 | manual |
| 5 | `plugins/saga/scripts/outcome.py:469` | The staged index fails `git diff --cached --check` with trailing whitespace at `plugins/saga/scripts/outcome.py:469,473`, `plugins/saga/scripts/outcome_reconcile.py:167,170,173,178,509`, and `plugins/saga/scripts/run_ledger.py:131`. Full working-tree `git diff --check` passes only because whitespace-clean versions appear to be unstaged. A commit made from the current index would carry whitespace errors and fail a standard diff hygiene gate. | maintainability / merge-verification | 100 | manual |

### P3

| # | File | Issue | Reviewer | Confidence | Route |
|---|------|-------|----------|------------|-------|
| 6 | `plugins/fleet-core/scripts/fleet_commons/effort_rider.py:71` | The scoped Bandit gate still exits nonzero: `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts`. The remaining output includes the new fleet-core assertion at `effort_rider.py:71`, many B101 findings from the untracked fleet-core tests because the scan includes `plugins/fleet-core/tests`, and existing low-severity findings across saga and mission-control. Either the findings need to be fixed, the command/scope needs to exclude tests and use an agreed baseline, or this gate needs an explicit documented reclassification. | security / quality-gate | 90 | manual |

## Round-3 Finding Status

| Round-3 # | Status | Evidence |
|---|---|---|
| 1 | STILL OPEN | Top-level agent prompts were adjusted, but the runtime persona prompts under `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/personas/` still cite the dead `team-execution/skills/team-execution/references/review-criteria.md` path. |
| 2 | STILL OPEN | `external-engine-workers.md:3-6` adds a planned/deferred disclaimer, but `external-engine-workers.md:250-252` still claims the mechanics are already enforced while the referenced bridge files are absent. |
| 3 | FIXED | A direct fetch probe returned `blocked_by_count 51`, `last_blocked_by {'number': 51, 'repo': 'other/repo'}`, and the second tracked page call used `owner=other`, `repo=repo`, `number=95`. |
| 4 | FIXED IN WORKING TREE | `README.md:25` now marks `deploy` synced to `099ec4c`; `plugins/deploy/plugin.json:3`, `plugins/deploy/CHANGELOG.md:3-5`, and `plugins/deploy/agents/release-orchestrator.md:5-6` carry the expected deploy update. Note: the deploy file changes are currently unstaged. |
| 5 | PARTIAL | Fleet-core tests pass locally, but the new test files are untracked and therefore not mergeable yet. |
| 6 | PARTIAL | The lint reference now names `tests/test_agent_tier_lint.py`, but that lint file is untracked and `effort-convention.md` still contains active `team-execution` runtime references. |
| 7 | STILL OPEN | The scoped Bandit command still exits 1. |

## Plan-Completion Audit

COMPLETION: PARTIAL.

Done:
- Fleet-core plugin and shared primitives exist in the working tree.
- Mission-control and saga tests pass.
- Cross-repo nested tracked-issue pagination is fixed in code and by direct probe.
- README sync matrix is corrected in the working tree.
- Current linked plugin validation passes.

Partial / Not Done:
- Active multi-agent reviewer runtime prompts are not fully Antigravity-native.
- External-engine documentation is still contradictory about deferred vs enforced mechanics.
- Fleet-core and agent-tier tests are not mergeable until tracked and committed.
- Staged index is not whitespace-clean.
- Scoped Bandit gate remains nonzero without a baseline, scope adjustment, or documented reclassification.
- The branch has no commits ahead of `origin/main`; merge truth cannot be proven until intended staged, unstaged, and untracked changes are reconciled into commits.

## Checks Run

Pass:
- `git fetch origin main --quiet`
- `git rev-parse HEAD` / `git merge-base origin/main HEAD` / `git rev-list --count origin/main..HEAD`
- `git diff --check $(git merge-base origin/main HEAD)`
- `git diff --check`
- `uv run ruff check .`
- `uv run pytest -q plugins/mission-control` (190 passed)
- `uv run pytest -q plugins/saga` (699 passed, 1 skipped)
- `uv run pytest -q plugins/multi-agent-consensus` (6 passed)
- `uv run pytest -q plugins/fleet-core tests/test_agent_tier_lint.py` (5 passed; includes untracked files)
- `uv run pytest -q` (932 passed, 1 skipped; includes untracked files)
- `uv run python scripts/validate_plugins.py --json`
- `uv run python scripts/validate_plugins.py --strict --json`
- `uv run python scripts/validate_plugins.py --install-dir /tmp/empty-antigravity-install --json` (non-strict missing install accepted with warnings)
- `uv run python scripts/validate_plugins.py --install-dir /tmp/empty-antigravity-install --strict --json` (expected failure for missing install)
- `uv run python plugins/saga/scripts/render_docs_visuals.py`
- Direct nested tracked-issue pagination probe

Fail:
- `git diff --cached --check`
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts`

## Coverage And Residual Risk

Suppressed findings below confidence threshold: 0.

Untracked files excluded from mergeable evidence until added: `docs/code-reviews/2026-07-09-feat-port-claude-july-updates-round-2-code-review.md`, `docs/code-reviews/2026-07-09-feat-port-claude-july-updates-round-3-code-review.md`, `plugins/fleet-core/tests/test_fleet_commons.py`, `tests/test_agent_tier_lint.py`.

Residual risk: because this branch has no commits ahead of `origin/main`, a final pre-merge review must be repeated after the intended files are staged and committed. Current passing tests prove the local working tree, not the mergeable branch.

## Required Before Merge

1. Replace all runtime persona and consensus-protocol references to `team-execution/skills/team-execution/references/review-criteria.md` with the local Antigravity review-criteria path, and rerun the multi-agent-consensus tests plus the relevant prompt/lint check.
2. Make `external-engine-workers.md` internally consistent: either reduce it to clearly deferred design notes, or add the missing implementation files and tests that prove the mechanics are real.
3. Add/commit the new fleet-core and agent-tier lint tests, then rerun the focused and full pytest commands.
4. Rewrite `effort-convention.md` so the canonical contract names Antigravity-native runtime surfaces and explicitly marks deferred/external-engine surfaces as non-runnable.
5. Reconcile staged vs unstaged content and make `git diff --cached --check` pass.
6. Resolve or explicitly baseline/reclassify the scoped Bandit findings, then rerun the scoped Bandit gate.
7. Commit the intended branch changes and rerun the final review checks against the committed branch diff.
