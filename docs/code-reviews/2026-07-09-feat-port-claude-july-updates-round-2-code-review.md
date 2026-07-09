---
title: Code Review Round 2 - feat/port-claude-july-updates
date: 2026-07-09
target: staged diff on feat/port-claude-july-updates
base: 99df140a0860bd8dfe6521d2f782660f4b966348
plan: docs/plans/2026-07-08-port-claude-july-updates-plan.md
blocked: true
merge_requires: all P1/P2/P3 findings fixed and re-reviewed before merge
reviewed_revision: 99df140a0860bd8dfe6521d2f782660f4b966348 plus staged index
orchestration_mode: team-execution
review_round: 2
---

# Code Review Round 2 - feat/port-claude-july-updates

Scope Check: REQUIREMENTS MISSING.

Verdict: BLOCKED. The second implementation pass fixed many first-review failures, but the staged diff is not safe to merge. The remaining issues are not just polish: outcome dispatch can re-open terminal work, large objectives still truncate, Antigravity hook/team paths are dead or shape-mismatched, tier effort is still cosmetic in the team path, and multiple required gates are red.

## Required Findings

| # | Priority | File | Issue | Confidence | Route |
|---|---|---|---|---:|---|
| 1 | P1 | `plugins/saga/scripts/outcome.py:831` | Authored terminal Objective nodes still dispatch. `derive_states()` maps `Node.state` `done`/`rejected` correctly, but `_reconcile_once()` builds its ready frontier from success-only store completions. A local probe showed `done` and `rejected` nodes dispatch and then become `dispatched`. | 100 | manual |
| 2 | P1 | `plugins/saga/scripts/discover_subissues.py:24` | Objective ingestion still truncates large graphs. The query uses `subIssues(first: 50)` and `trackedIssues(first: 50)`; `normalize()` only warns on `totalCount > 50` and returns partial DAG data with success. | 100 | manual |
| 3 | P1 | `plugins/saga/hooks/team_spawn_residency_hook.py:177` | The new `invoke_subagent` residency hook does not discover Antigravity registries. It checks `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PROJECT_DIR`, and `plugins/team-execution/...`; the real repo paths are under `plugins/multi-agent-consensus/...`. Normal probe produced no advisory; forced include did. | 100 | manual |
| 4 | P1 | `plugins/saga/hooks/team_spawn_residency_hook.py:244` | Even with a trigger set, the hook checks `Subagents[*].TypeName`; the Antigravity consensus skill instructs `TypeName: "self"` and reviewer identity in `Role`, so real reviewer spawns are missed. | 100 | manual |
| 5 | P1 | `plugins/saga/scripts/team_emitter.py:72` | Generated team artifacts still point to missing `team-execution/skills/team-execution/references/...` paths instead of existing `plugins/multi-agent-consensus/...` references. | 100 | manual |
| 6 | P1 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md:12` | New multi-agent reference docs cite implementation files not present in this staged repo, including `dispatch-adapter-contract.md`, `engine_dispatch.py`, `engine_resolver.py`, `agy_delegate.py`, and `plugins/team-execution/.../worker-manifest.md`. | 100 | manual |
| 7 | P1 | `plugins/saga/scripts/team_emitter.py:289` | Team-execution effort remains unenforceable. The emitter renders `model/effort` as table text, `unenforceable_tier()` only checks the model axis, and the 25 packaged multi-agent agents have `model:` frontmatter but no `effort:` frontmatter. `xhigh` can be emitted without any Gemini payload or rider. | 100 | manual |
| 8 | P1 | `plugins/saga/scripts/execution_spec.py:1937` | Spend baseline is too low for the repo's own default issue bands. Mission-control stamps defect/capability as `gemini-3.1-pro/high`, but `SPEND_BASELINE` and `DEFAULT_SILENT_CEILING` are `gemini-3.5-flash/high`, so normal defect/capability plans are treated as premium and fail `validate(require_receipts=True)` without extra receipts. Error text still names `sonnet`/`opus`/`fable`. | 100 | manual |
| 9 | P2 | `plugins/mission-control/scripts/sdlc_manager.py:2520` | `issue_label_remove()` still treats any 404 as idempotent label absence, including wrong repo or wrong issue. A probe raising `ApiNotFoundError` for a non-existent issue returned `label_remove_noop` instead of failing. | 100 | manual |
| 10 | P2 | `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py:38` | Delegation audit still recognizes only Claude file-tool names. Antigravity `write_to_file` self-edits are not counted as fallback work, so a transcript with engine launch plus Antigravity write classified as `real`. | 100 | manual |
| 11 | P2 | `scripts/validate_plugins.py:160` | Non-strict plugin doctor now errors on missing installs, making the warning-only doctor behavior regress and making clean install-dir probes fail the default `--json` command. Historical harness docs expected missing install dirs to pass with warnings unless strict. | 90 | manual |
| 12 | P2 | `README.md:25` | README claims `deploy` is synced to source commit `099ec4c`, but the staged target diff contains no `plugins/deploy/**` changes while the source range does modify deploy files. This falsely marks an unported surface as synced. | 100 | manual |
| 13 | P2 | `plugins/saga/scripts/board_progression.py:56` | Scoped Bandit still fails on a new high-confidence SHA1 finding in changed code. Either use SHA-256 or mark explicitly non-security with `usedforsecurity=False`/`# nosec` and rationale. | 100 | manual |
| 14 | P3 | `plugins/mission-control/skills/issues/SKILL.md:97` | Operator docs still describe Claude tier bands (`opus/high`, `sonnet/medium`, `sonnet/low`) while implementation stamps Gemini tiers. | 100 | manual |
| 15 | P3 | `plugins/fleet-core/references/effort-convention.md:44` | Fleet-core reference docs still teach rejected Claude model names (`sonnet`, `opus`) even though the staged Gemini palette rejects them. | 100 | manual |
| 16 | P3 | `graphify-out/graph.json:1` | Staged diff deletes tracked generated graphify artifacts even though the plan explicitly excludes reverting `graphify-out/` dirty state from this port. | 100 | manual |
| 17 | P3 | `plugins/saga/scripts/outcome.py:469` | Formatting gates are still red: `git diff --check --cached` and `ruff` report trailing whitespace in `outcome.py`, `outcome_reconcile.py`, and `run_ledger.py`. | 100 | manual |

## Prior Finding Status

Fixed from first review: Gemini model registry accepts produced tier defaults; `effort_rider` emits Gemini `generation_config.thinking_level` and clamps `xhigh` to `high`; `saga:readonly-verifier` now exists; `.gemini/saga` path inference is fixed; mission-control mapping fallback targets `infiquetra-antigravity-plugins`; `ship_ceremony.py` exists; full pytest no longer has the duplicate `test_completeness_gate.py` import mismatch; run-ledger append now locks the read-compute-write cycle; outcome reconcile equal-timestamp override and close-family reassert behavior are fixed.

Still open or replaced by sharper findings: objective terminal ingestion is still unsafe through `_reconcile_once()` dispatch; pagination/truncation is still open; team-execution tier enforceability is still open for effort; hook portability is still open for registry discovery, spawn shape, and delegation audit; `issue_label_remove()` 404 masking is still open; release-boundary cleanup still includes unrelated generated artifacts.

## Checks Run

- `git fetch origin main --quiet`
- `git status --short --branch`
- `git diff --stat 99df140a0860bd8dfe6521d2f782660f4b966348`
- `git diff --name-status 99df140a0860bd8dfe6521d2f782660f4b966348`
- `git diff --cached --name-status 99df140a0860bd8dfe6521d2f782660f4b966348`
- `git diff --check --cached 99df140a0860bd8dfe6521d2f782660f4b966348` - failed on trailing whitespace
- `uv run python scripts/validate_plugins.py --json` - passed with warnings in current local install
- `uv run python scripts/validate_plugins.py --json --strict-install` - passed with warnings in current local install
- `uv run python scripts/validate_plugins.py --json --install-dir <empty-dir>` - failed on missing installs
- `uv run ruff check .` - failed on trailing whitespace
- `uv run pytest plugins/mission-control` - passed, 190 tests
- `uv run pytest plugins/saga` - passed, 699 passed / 1 skipped
- `uv run pytest plugins/multi-agent-consensus` - passed, 6 tests
- `uv run pytest plugins/fleet-core` - failed, no tests collected
- `uv run pytest` - passed, 927 passed / 1 skipped
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts` - failed, including high SHA1 finding in `board_progression.py`
- `uv run python plugins/saga/scripts/render_docs_visuals.py` - passed
- Local probes for Objective terminal dispatch, discovery truncation, hook registry discovery, `TypeName: self` spawn shape, missing reference paths, `issue_label_remove()` 404 masking, Gemini effort payloads, spend baseline behavior, README/source deploy mismatch, and staged graphify deletions
- Independent subagent slices: outcome/reconcile, mission-control/release, hook/team-emitter, and tier/spend

## Notes

The implementation is staged in the index; unstaged implementation diff is empty before this review artifact. The review artifact itself is a new review output and is not evidence that implementation blockers are fixed.
