---
title: Code Review - feat/port-claude-july-updates
date: 2026-07-09
target: working tree on feat/port-claude-july-updates
base: 99df140a0860bd8dfe6521d2f782660f4b966348
plan: docs/plans/2026-07-08-port-claude-july-updates-plan.md
blocked: true
merge_requires: all P1/P2/P3 findings fixed or re-reviewed as intentionally removed
reviewed_revision: 99df140a0860bd8dfe6521d2f782660f4b966348 plus working tree and relevant untracked files
orchestration_mode: team-execution
---

# Code Review - feat/port-claude-july-updates

Scope Check: REQUIREMENTS MISSING

Intent: Port Claude plugin delta `3987510..099ec4c` into the Antigravity plugin repo with explicit direct/adapt/defer handling.

Delivered: Large local working-tree implementation exists, but several planned surfaces are missing or internally inconsistent.

## Blocking Findings

| # | Priority | File | Issue | Confidence | Route |
|---|---|---|---|---:|---|
| 1 | P1 | plugins/fleet-core/scripts/fleet_commons/models.json:4 | Gemini tier defaults are invalid against their own validator. `gemini-3.1-pro` is capped at `medium`, while `tier_policy.json` and mission-control issue stamps emit `gemini-3.1-pro/high`; `ExecutionSpec.validate()` and tier-band parsing reject it. | 100 | manual |
| 2 | P1 | plugins/saga/scripts/execution_spec.py:1937 | Claude tier vocabulary remains in enforcement gates. `SPEND_BASELINE = sonnet/high` and `spend_authority.DEFAULT_SILENT_CEILING` use models absent from the Gemini palette, causing `validate(require_receipts=True)` and default spend authority to raise `ValueError`. | 100 | manual |
| 3 | P1 | plugins/fleet-core/scripts/fleet_commons/effort_rider.py:83 | Planned Gemini thinking payload mapping is not implemented. The plan requires `thinking_level` / `thinkingLevel` with `xhigh` clamped to `high`; the adapter emits `{"thinking": {"effort": effort}}` and passes `xhigh` through. | 100 | manual |
| 4 | P1 | plugins/saga/scripts/execution_spec.py:145 | Team-execution tier enforceability now accepts Gemini `MODELS`, but the packaged resident agents still declare Claude model names (`opus`, `sonnet`, `haiku`), so emitted Gemini tiers can pass validation even though spawned workers cannot honor them. | 100 | manual |
| 5 | P1 | plugins/saga/scripts/execution_spec.py:110 | Verifier panels reference `saga:readonly-verifier`, but `plugins/saga/agents/readonly-verifier.md` is absent and no multi-agent-consensus persona mapping replaces it. The runtime cannot honor the planned read-only verifier guarantee. | 100 | manual |
| 6 | P1 | plugins/saga/hooks/validate_json_hook.py:51 | New hook registrations use Antigravity tool names, but hook scripts still filter Claude tool names such as `Write`, `Edit`, `MultiEdit`, `Agent`, and `Task`; Antigravity `write_to_file`/`invoke_subagent` events pass through unenforced. | 100 | manual |
| 7 | P1 | plugins/saga/scripts/outcome.py:374 | Closed Objective sub-issues are imported into ignored `Node.state`; `derive_states()` explicitly ignores `Node.state`, so closed or not-planned sub-issues can re-enter the ready frontier and dispatch as new work. | 100 | manual |
| 8 | P1 | plugins/saga/scripts/discover_subissues.py:24 | Objective ingestion hard-limits `subIssues(first: 50)` and `trackedIssues(first: 50)` without checking `totalCount`, silently truncating large objectives and dependency edges. | 100 | manual |
| 9 | P1 | plugins/mission-control/scripts/sdlc_manager.py:3291 | Antigravity saga path inference regressed to `.claude/saga/`; `.gemini/saga/` loop-state files now classify as generic local files instead of resume-ready loop state. | 100 | manual |
| 10 | P1 | plugins/mission-control/scripts/sdlc_manager.py:4133 | Vendored mapping fallback points at `infiquetra-claude-plugins` from this Antigravity worktree, so missing external mappings can open the repair PR against the wrong repository. | 100 | manual |
| 11 | P1 | tracked/untracked boundary | Release surface is unsafe to commit as-is. Tracked docs/hooks reference untracked files such as `plugins/saga/commands/tier.md`, hook scripts, `tier_session.py`, and all `plugins/fleet-core/**`; a tracked-only commit would ship broken references. | 100 | manual |

## Required Before Merge Findings

Every finding in this section is required before merge. The P2/P3 labels describe severity and
fix ordering, not deferral permission.

| # | Priority | File | Issue | Confidence | Route |
|---|---|---|---|---:|---|
| 11 | P2 | README.md:24 | Portability matrix still records `3987510` and does not list `fleet-core`, despite the plan requiring `099ec4c` after the port. | 100 | manual |
| 12 | P2 | plugins/saga/references/saga-spec.md:144 | Docs reference `ship_ceremony.py`, but `plugins/saga/scripts/ship_ceremony.py` was not ported. | 100 | manual |
| 13 | P2 | scripts/validate_plugins.py:85 | Default plugin validation exits ok while new `fleet-core` is missing from the local install; strict mode catches it, default gate does not. | 100 | manual |
| 14 | P2 | plugins/saga/scripts/outcome_reconcile.py:391 | Re-asserting an `external-close` drift calls the close-family writer again; the saga value is `open`, but the op closes instead of reopening. | 100 | manual |
| 15 | P2 | plugins/saga/scripts/outcome_reconcile.py:153 | Equal-timestamp override semantics are documented as override-preferring, but detection accepts any value at the max timestamp, so a reverted board value can be treated as non-drift. | 75 | manual |
| 16 | P2 | plugins/saga/scripts/run_ledger.py:123 | `append_fact()` reads the tail hash before `O_APPEND`; concurrent writers can append two records with the same `prev_hash` and break the chain. | 100 | manual |
| 17 | P2 | plugins/mission-control/scripts/sdlc_manager.py:2519 | `issue_label_remove()` treats every 404 as idempotent success, including wrong repo or wrong issue. | 75 | manual |
| 18 | P2 | plugins/mission-control/skills/issues/SKILL.md:50 | Mission-control skill docs point operators at the Claude plugin checkout and list `infiquetra-claude-plugins` as the common plugin repo. | 100 | manual |
| 19 | P2 | plugins/saga/plugin.json:3 | Saga plugin metadata was not updated for the expanded command surface; docs now declare 21 command files / 20 routable commands. | 75 | manual |
| 20 | P3 | plugins/fleet-core/README.md:16 | Fleet-core docs and metadata still contain Claude-shaped assumptions and repo links. | 100 | manual |
| 21 | P3 | .serena/project.yml:124 | Local/generated churn remains in the diff (`.serena`, `graphify-out` deletions). | 100 | manual |
| 22 | P3 | plugins/fleet-core/scripts/fleet_commons/effort_rider.py:136 | Ruff fails on whitespace-only blank line. | 100 | gated_auto |
| 23 | P3 | docs/engineering-journal/QUEUED.md:72 | `git diff --check` fails on trailing whitespace. | 100 | gated_auto |

## Plan Completion

- U0: PARTIAL. Source range exists, but current implementation misses source files and release assets.
- U1: PARTIAL. `fleet-core` exists but is untracked, has no collected tests under `plugins/fleet-core`, and carries stale Claude docs.
- U2: PARTIAL. Tier/spend code exists, but Gemini palette and spend gates are internally inconsistent.
- U3: PARTIAL. Mission-control tests pass, but Antigravity path and repo fallback regressions remain.
- U4: PARTIAL. Completeness gates exist, but verifier dispatch/isolation is not Antigravity-ready.
- U5: PARTIAL. Outcome tests pass in slices, but objective ingestion and reconcile correctness bugs remain; `ship_ceremony.py` is missing.
- U6: PARTIAL. Manifest/spore/hook files exist, but some hooks are not wired to Antigravity tool names.
- U7: NOT DONE. README portability matrix and release-surface scripts were not updated; validation does not fail default install miss.
- U8: PARTIAL. Deferrals are recorded, but some planned direct/adapt surfaces are missing without clear deferral.

## Checks Run

- `git fetch origin main --quiet`
- `git diff --check 99df140a0860bd8dfe6521d2f782660f4b966348` - failed
- `uv run python scripts/validate_plugins.py --json` - passed with warnings
- `uv run python scripts/validate_plugins.py --json --strict-install` - failed on missing `fleet-core`
- `uv run pytest plugins/mission-control` - passed, 190 tests
- `uv run pytest plugins/saga` - passed, 646 tests
- `uv run pytest plugins/multi-agent-consensus` - passed, 6 tests
- `uv run pytest plugins/fleet-core` - failed, no tests collected
- `uv run pytest` - failed on duplicate `test_completeness_gate.py` module import mismatch
- `uv run ruff check .` - failed on fleet-core whitespace
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts` - failed; one high SHA1 finding plus low baseline/new findings
- `uv run python plugins/saga/scripts/render_docs_visuals.py` - passed

## Verdict

Blocked. This should go back through `/work` before any PR or merge. All P1, P2, and P3 findings
above must be fixed, or re-reviewed and explicitly removed, before merge. The highest-risk clusters
are Gemini tier/payload adaptation, verifier/hook wiring, objective ingestion correctness,
release-boundary tracked/untracked packaging, and the remaining release/documentation/test hygiene
items now marked required before merge.
