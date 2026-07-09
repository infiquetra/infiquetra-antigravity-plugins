---
title: Code Review Round 3 - feat/port-claude-july-updates
date: 2026-07-09
target: working tree on feat/port-claude-july-updates
reviewed_revision: 99df140a0860bd8dfe6521d2f782660f4b966348 plus working tree
merge_requires: all P1/P2/P3 findings fixed or explicitly re-reviewed as intentionally deferred
orchestration_mode: inline
review_round: 3
blocked: true
---

# Code Review Round 3 - feat/port-claude-july-updates

## Verdict

BLOCKED. The round-2 fixes addressed many real bugs, but the working tree is not merge-ready.
There are still required fixes before merge, and the branch currently has no commits beyond
`origin/main` (`HEAD` and merge-base are both `99df140a0860bd8dfe6521d2f782660f4b966348`).

Scope reviewed: tracked working tree diff against `origin/main`; untracked round-2 review artifact
was noted but not treated as implementation evidence.

## Required Findings

| # | Priority | File | Issue | Confidence | Route |
|---|----------|------|-------|------------|-------|
| 1 | P1 | `plugins/multi-agent-consensus/agents/security-reviewer.md:29` | All 25 multi-agent-consensus agent prompts still identify themselves as `team-execution` agents or point at `team-execution/skills/team-execution/references/...`, which does not exist in this repo. A spawned reviewer can be instructed to load a dead rubric path. | 100 | manual |
| 2 | P1 | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md:12` | The new external-engine worker contract still describes active chaperone dispatch behavior backed by absent/deferred files (`plugins/saga/references/dispatch-adapter-contract.md`, `plugins/saga/scripts/engine_dispatch.py`, `plugins/saga/scripts/engine_resolver.py`, `worker-manifest.md`). `docs/engineering-journal/QUEUED.md:73` says these bridge components were deliberately deferred, so the docs currently claim runnable mechanics that are not present. | 100 | manual |
| 3 | P2 | `plugins/saga/scripts/discover_subissues.py:146` | Nested `trackedIssues` pagination uses the parent objective repo for page 2 instead of the sub-issue's own `repository.nameWithOwner`. Cross-repo sub-issues with more than 50 tracked issues will fetch the wrong issue or fail. Probe recorded `owner=parent repo=repo number=95` for a sub-issue in `other/repo`. | 100 | manual |
| 4 | P2 | `README.md:25` | The portability matrix still claims `deploy` is synced to source commit `099ec4c`, but the source range changes `plugins/deploy/.claude-plugin/plugin.json`, `plugins/deploy/CHANGELOG.md`, and `plugins/deploy/agents/release-orchestrator.md`; the target diff only changes `plugins/deploy/agents/release-orchestrator.md`. | 100 | manual |
| 5 | P2 | `docs/plans/2026-07-08-port-claude-july-updates-plan.md:146` | U1 requires focused tests for the new `plugins/fleet-core` primitives, but the target has no collectable fleet-core tests. `uv run pytest -q plugins/fleet-core` exits 5 with "collected 0 items". | 100 | manual |
| 6 | P2 | `plugins/fleet-core/references/effort-convention.md:16` | The effort convention now claims a required CI lint (`tests/test_agent_tier_lint.py`, `scripts/lint_agent_tiers.py`) and worker-manifest provenance paths, but those files do not exist. Current agent frontmatter is good, but the promised guard against future off-palette `effort:` drift is imaginary. | 100 | manual |
| 7 | P3 | `plugins/fleet-core/scripts/fleet_commons/effort_rider.py:71` | The scoped Bandit command in the verification plan still exits non-zero. The prior high SHA1 issue is fixed, but the gate now fails on low findings and noisy `# nosec` parsing. Either make the scoped command pass with the intended threshold/baseline or explicitly reclassify it as informational. | 90 | manual |

## Round-2 Finding Status

| Round-2 # | Status | Evidence |
|-----------|--------|----------|
| 1 | FIXED | Terminal-node dispatch probe returned `dispatched []`, states `done`/`rejected`; `outcome.py:831` includes authored terminal nodes in frontier completion input. |
| 2 | PARTIAL | Main and nested pagination now fetch 51 items, but new cross-repo nested pagination bug remains as finding 3. |
| 3 | FIXED | Hook resolves `ANTIGRAVITY_PLUGIN_ROOT` to `plugins/multi-agent-consensus/.../references`. |
| 4 | FIXED | Hook catches `TypeName: self` plus `Role: security-reviewer` and emits advisory. |
| 5 | FIXED | `team_emitter.py:72` no longer emits `team-execution/skills/...` reference rows. |
| 6 | STILL OPEN | External-engine docs still cite absent/deferred implementation files; see finding 2. |
| 7 | PARTIAL | All 25 multi-agent agents now have `effort:`, and spend probes pass; missing lint/manifest docs remain finding 6. |
| 8 | FIXED | `SPEND_BASELINE` is `gemini-3.1-pro/high`; baseline validates without receipts, premium `xhigh` requires justification. |
| 9 | FIXED | `issue_label_remove()` probe no-ops only when issue exists; wrong repo/issue 404 now raises. |
| 10 | FIXED | Delegation audit recognizes `write_to_file`, `replace_file_content`, and `multi_replace_file_content`; probe classifies engine command plus Antigravity write as `fallback_suspected`. |
| 11 | FIXED | Default empty install-dir doctor exits ok with warnings; strict empty install-dir exits 1 with missing-install errors. |
| 12 | STILL OPEN | README deploy sync claim remains false; see finding 4. |
| 13 | PARTIAL | High SHA1 Bandit finding is fixed with `usedforsecurity=False`, but the scoped Bandit gate still exits non-zero; see finding 7. |
| 14 | FIXED | `plugins/mission-control/skills/issues/SKILL.md:97` now documents Gemini tier bands. |
| 15 | PARTIAL | Rejected Claude model names are mostly removed from operator docs, but effort docs still reference missing team-execution paths and missing lint; see finding 6. |
| 16 | FIXED | No `graphify-out` diff remains. |
| 17 | FIXED | `git diff --check` and `uv run ruff check .` both pass. |

## Built vs Planned

Scope Check: REQUIREMENTS MISSING.

Intent: port the Claude plugin delta `3987510..099ec4c` into Antigravity-native plugin surfaces,
adapting runtime paths, validators, tier/spend behavior, outcome flows, and release validation.

Delivered: most saga, mission-control, multi-agent-consensus, and plugin-validator behavior is present
and tested; remaining gaps are the false sync matrix, missing fleet-core direct tests, stale runtime
prompt/reference paths, and docs claiming deferred external-engine mechanics as active.

Completion rollup:

- U0 Source Inventory: PARTIAL. Source comparison was used, but README sync state does not reflect
  missing deploy/saga bridge surfaces.
- U1 Bootstrap fleet-core: PARTIAL. Plugin and scripts exist; focused tests are missing.
- U2 Tier/Effort/Spend: PARTIAL. Behavior probes pass; documented lint and worker-manifest paths are absent.
- U4 Verifier dispatch/completeness: DONE for probed Antigravity tool-name and validation paths.
- U5 Outcome DAG/board/ship: PARTIAL. Main tests pass; cross-repo nested tracked-issue pagination bug remains.
- U6 Manifest/provenance/spore/status/hooks: PARTIAL. Saga tests pass, but external-engine worker docs still
  describe deferred bridge files as active.
- U7 Release validation: PARTIAL. Validator behavior is fixed; deploy matrix still overstates sync.
- U8 Deferred ledger: PARTIAL. QUEUED records external bridge deferral, but runtime docs contradict it.

## Checks Run

- `git fetch origin main --quiet` - passed
- `git status --short --branch` - branch `feat/port-claude-july-updates`; HEAD equals merge-base; working tree carries all implementation changes
- `git diff --stat $(git merge-base origin/main HEAD)` - 131 files, 22093 insertions, 348 deletions
- `git diff --check $(git merge-base origin/main HEAD)` - passed
- `uv run ruff check .` - passed
- `uv run python scripts/validate_plugins.py --json` - passed with existing warnings
- `uv run python scripts/validate_plugins.py --json --strict-install` - passed in current linked install
- `uv run python scripts/validate_plugins.py --json --install-dir <empty>` - passed with missing-install warnings
- `uv run python scripts/validate_plugins.py --json --strict-install --install-dir <empty>` - failed as expected with missing-install errors
- `uv run pytest -q plugins/mission-control` - passed, 190 tests
- `uv run pytest -q plugins/saga` - passed, 699 passed / 1 skipped
- `uv run pytest -q plugins/multi-agent-consensus` - passed, 6 tests
- `uv run pytest -q plugins/fleet-core` - failed, no tests collected
- `uv run pytest -q` - passed, 927 passed / 1 skipped
- `uv run python plugins/saga/scripts/render_docs_visuals.py` - passed
- `uv run bandit -q -c pyproject.toml -r plugins/fleet-core plugins/saga/scripts plugins/mission-control/scripts` - failed, no high issues, low findings remain
- Targeted probes: terminal objective dispatch, sub-issue/tracked pagination, cross-repo tracked pagination, hook registry discovery, `TypeName: self` role matching, spend baseline, `issue_label_remove()` 404 handling, delegation audit Antigravity file tools, source deploy diff comparison, graphify diff absence

## Residual Risk

No live GitHub mutations, deployments, host plugin installs, or Antigravity runtime launches were performed.
The review did not attempt to fix findings. The branch needs a clean staged set and commit after approved
fixes; merging the branch as currently committed would merge nothing.
