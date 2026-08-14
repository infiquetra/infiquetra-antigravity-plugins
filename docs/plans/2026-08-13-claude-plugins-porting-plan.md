---
title: Claude-to-Antigravity Plugins Porting & Hardening Implementation Plan
type: feat
status: active
date: 2026-08-13
origin: infiquetra-claude-plugins@ff2362843b9202caa07b7a3651c89898f1453231 (local origin/main; per-requirement commits in Sources & Evidence)
source_repo: infiquetra-claude-plugins
reviewed: 2026-08-13
review_status: ready
review_artifact: docs/reviews/2026-08-13-claude-plugins-porting-plan-doc-review.md
---

# Claude-to-Antigravity Plugins Porting & Hardening Implementation Plan

## Summary

Port confirmed Claude-side safety and vocabulary work into this repository, starting from Antigravity `origin/main` (`e0f08ce5a547783db83c8a878971bf35204f287f`), not from the stale local checkout.

The work adds fleet-core schema v2 beside the existing Gemini model registry, ports saga collision/quorum/pre-push/table fixes, ports `team-scaffold`, verifies the already-landed Hermes boundary fixes, and deletes the lease broker after recording the ledger supersede.

---

## Problem Frame

Claude's plugin repository has moved past Antigravity on tier vocabulary, same-wave file collisions, verify-panel severity, pre-push parsing, execution-spec tables, and team scaffolding.

Antigravity already has a committed Hermes profile-evolution plugin and still uses Gemini models, isolated worktrees, and native subagents. A literal copy of Claude's live model list or of the untracked working-tree Hermes copy would destroy that baseline.

---

## Implementation Baseline

Implement against Antigravity local `origin/main` at `e0f08ce5a547783db83c8a878971bf35204f287f`. Local `HEAD` (`ac74786b10d148384b89290aedeadd8e4d4fd4b5`) is twelve commits behind and does not contain the Hermes plugin.

Do not edit the untracked working-tree `plugins/hermes-profile-evolution/` (adapter `timeout=10`). Do not use untracked `docs/ports/2026-07-30-hermes-profile-evolution/`. The committed campaign is `docs/ports/2026-08-01-hermes-profile-evolution/`.

Pin Claude evidence to local `origin/main` at `ff2362843b9202caa07b7a3651c89898f1453231`. Do not pin `541b36b9305c388ad0db304cf59a044d1fd55680`; that commit is `feat(orchestrate): U5` on `feat/orchestrate-u5-completion` and is not an ancestor of Claude `origin/main`. Orchestrate is a non-goal.

---

## Sources & Evidence

Each requirement below is bound to a Claude commit that is an ancestor of Claude `origin/main` (`ff236284`). Ledger reconciliation is noted where the 2026-07-30 saga-reliability campaign is involved.

| Requirement | Upstream source | Verified content |
|---|---|---|
| R1, R2 | `13b02343` feat(fleet-core): authoritative tier vocabulary and per-vendor effort application (#715), 2026-08-13 | Additive `schema_version` 2 keys `execution_classes`, `scalar_efforts`, `root_orchestration_profiles`. Live Claude `models` stay `fable`/`opus`/`sonnet`/`haiku` and are not the portable subset. Class names are `review-max`, `review-high`, `test-medium`, `scan-low`, `monitor-low`, `work-high`, `work-medium`. `resolve_for_runtime` / `adapt_runtime_argv` plus collapse `muse`/`grok` `max→xhigh` and `agy` `max`/`xhigh→high`. |
| R3 | `b3c13006` feat(saga): halt when concurrent units declare the same file (#671/#673), 2026-07-27 | `wave_file_conflicts` / `assert_no_wave_file_conflicts` in `execution_spec.py`, concurrent-writer section in `spec_table.py`, plan-skill splitting rule, `tests/test_wave_file_conflicts.py`. |
| R4 | `f0ca9a47` merge feat/686-verify-panel-severity-axis, 2026-08-03 | Severity axis `refuted_deliverable` (gating) vs `advisory_corrections` (non-gating). Declared quorum floor is `n // 2 + 1`, not `ceil(n / 2)`. |
| R5 | `fe3bf9f3` fix(saga): pre-push gate parses the git invocation, not the command text (#663/#670), 2026-07-27 | `shlex` tokenizer with `punctuation_chars=True` in `hooks/pre_push_gate_hook.py`. |
| R6 | `faecb8a3` feat(saga): render the execution-spec approval table at every backend approval (#668/#669), 2026-07-27 | New `scripts/spec_table.py` and `tests/test_spec_table.py`. |
| R7 | `f218f615` feat(team-scaffold): emit collection deploy harness, 2026-06-08 | `plugins/home-lab-ops/skills/team-scaffold/` including `scripts/tests/`. |
| R8 | Already on Antigravity `origin/main`: `18eaa18` port, `83a1f5a` (#38) timeout 20→45, reply limits in `tests/test_hermes_profile_evolution.py`. Claude sources `b53827bb` (#709) and `440b3208` remain the producer-side evidence. | `SUBPROCESS_TIMEOUT_SECONDS = 45` (producer network bound is 30). Reply validation rejects whitespace-only content and messages above the fixture `max_characters` of 16384. |
| R9 | `e2ba7db5` feat(fleet-core,saga,team-execution): delete lease broker and orphan evidence, add re-add guard (#684/#703), 2026-08-07 | Deletes the two modules and adds `tests/test_no_lease_broker_readd.py`. Antigravity counterparts live under `plugins/fleet-core/`. |

Upstream commit order on 2026-07-27: `faecb8a3` (R6) precedes `b3c13006` (R3), so the `spec_table.py` port lands before the collision-guard unit. `b3c13006` (R3) precedes `f0ca9a47` (R4), so the collision-guard edit of `execution_spec.py` lands before the severity-axis edit.

---

## Requirements

### `fleet-core` Tier Vocabulary & Execution Classes

R1. Add schema version 2 keys `execution_classes`, `scalar_efforts`, and `root_orchestration_profiles` to `plugins/fleet-core/scripts/fleet_commons/models.json`. Update the Gemini `models` catalog to include `gemini-3.1-pro`, `gemini-3.7-flash`, `gemini-3.6-flash`, and `gemini-3.5-flash` with their respective effort ceilings and rank orderings, alongside existing `efforts` (`low`, `medium`, `high`, `xhigh`). Do not replace them with Claude's live `fable`/`opus`/`sonnet`/`haiku` list.

R2. Add `resolve_for_runtime()` and `adapt_runtime_argv()` in `plugins/fleet-core/scripts/fleet_commons/tier_resolver.py` beside the existing `resolve()` API. Collapse `grok` and `muse` `max` to `xhigh`, and `agy` `max` and `xhigh` to `high`. Return structured `RuntimeResolution` objects. Existing `resolve()` callers stay on Gemini `models` / `efforts`.

### `saga` Safety & Review Hardening

R3. Implement concurrent file collision halting in `plugins/saga/scripts/execution_spec.py` (`wave_file_conflicts` / `assert_no_wave_file_conflicts`) so same-wave units that declare the same file path halt with an actionable error. Surface the collision in `plugins/saga/scripts/spec_table.py` and document the same-file splitting rule in the `plan` skill.

R4. Harden refute-N verify panels in `plugins/saga/scripts/execution_spec.py` by adding the `refuted_deliverable` / `advisory_corrections` severity axis and replacing the even-N fail-open floor. Antigravity today uses `floor = (n + 1) // 2` (`ceil(n/2)`). Upstream's declared floor is `n // 2 + 1`.

R5. Fix pre-push git invocation parsing in `plugins/saga/hooks/pre_push_gate_hook.py` to inspect structured command argv rather than the current regex over the raw command string.

R6. Port the execution-spec approval table module `plugins/saga/scripts/spec_table.py` and render it at every backend approval point that has a structured spec artifact. In Antigravity that is the outcome dispatch surface: `render_outcome` (the native `--outcome` mode) renders the approval table from the committed `docs/outcomes/<id>/outcome-spec.json` before `approve` and each `advance` dispatch wave. Plan step 5 and work-before-execution keep their existing approval surfaces (the plan's own unit tables) and never author an `ExecutionSpec` (plan skill 5.2a guard); the Claude-source `render` path stays test-covered for ported parity.

### Ecosystem Plugins & Skills

R7. Port the `team-scaffold` deterministic generator skill from upstream into `plugins/home-lab-ops/skills/team-scaffold/` so Antigravity can create `infiquetra/team-*` repositories, Ansible harnesses, and vault wiring.

R8. Keep the Hermes adapter subprocess timeout at 45 seconds so the producer's 30-second network request can finish, and keep reply validation that rejects whitespace-only messages and messages above 16,384 characters. This is already true on Antigravity `origin/main`; do not regress it.

### Architecture Alignment & Legacy Cleanup

R9. Retire legacy `lease_broker.py` and `orphan_evidence.py` from `fleet-core`, leaving outcome concurrency on the worktree registry (`plugins/saga/scripts/outcome_worktrees.py`). Record the superseding decision on the 2026-07-30 saga-reliability campaign ledger: both `concurrency-lease-policy` and `orphan-evidence-attestation` were approved survivors with `antigravity_state: present` at 2026-07-30T21:51Z, and their revisit trigger ("Reassess when source snapshots drift") is met by upstream `e2ba7db5` (2026-08-07).

R10. Verify that quality guards, doctor checks (`scripts/validate_plugins.py --strict-install`), and test suites pass.

---

## Key Technical Decisions

KTD1. **Schema v2 is additive on the Gemini registry.** Import Claude #715's portable subset (`execution_classes`, `scalar_efforts`, `root_orchestration_profiles`) and the six-runtime resolver. Update the Gemini models catalog with `gemini-3.1-pro`, `gemini-3.7-flash`, `gemini-3.6-flash`, and `gemini-3.5-flash`. Do not import Claude's live `models`/`efforts` (`fable`/`opus`/`sonnet`/`haiku`) and do not import Codex's `lineage_models`/`lineage_efforts` key layout. Existing `resolve()` callers and `tier_palette.MODELS` stay on Gemini.

KTD2. **Worktree registry over file leases.** Antigravity concurrency relies on isolated git worktrees (`outcome_worktrees.py`) and explicit unit dependency graphs. `lease_broker.py` is deleted after the ledger supersede in U7.

KTD3. **Native subagent protocol for consensus.** Review panels stay on Antigravity's native `invoke_subagent` and the `multi-agent-consensus` plugin rather than external CLI multiplexing.

KTD4. **`origin/main` is the implementation tree.** Inventory, file lists, and "already present" claims bind to Antigravity `origin/main` and Claude `origin/main`. Working-tree untracked files and feature-branch HEADs are not sources.

---

## Implementation Units

### U1. `fleet-core` Tier Vocabulary v2 & Execution-Class Resolver

Add schema v2 beside the Gemini registry and add the per-runtime resolver.

**Goal:** Upgrade model definitions and tier resolution without replacing Gemini models.

**Requirements:** R1, R2

**Dependencies:** None.

**Files:**

- `plugins/fleet-core/scripts/fleet_commons/models.json`
- `plugins/fleet-core/scripts/fleet_commons/tier_resolver.py`
- `plugins/fleet-core/scripts/fleet_commons/tier_palette.py`
- `plugins/fleet-core/scripts/fleet_commons/cost_weights.json` (gemini-3.7/3.6-flash rows)
- `plugins/fleet-core/tests/test_fleet_core_execution_classes.py` (new; Antigravity keeps fleet-core tests under the plugin, not repo-root `tests/`)

**Approach:** Copy the portable v2 objects and `resolve_for_runtime` / `adapt_runtime_argv` from Claude `13b02343`. Leave `resolve()`, `ROLE_TIER_ALIASES`, and `models`/`efforts` in place. Use the upstream class names, not invented aliases.

**Patterns to follow:** `plugins/fleet-core/scripts/fleet_commons/tier_resolver.py` `resolve()` and `Resolution`; Claude `plugins/fleet-core/scripts/fleet_commons/tier_resolver.py` at `13b02343`.

**Test scenarios:**

- Happy path: resolve `review-max`, `review-high`, and `work-high` for `agy`, `claude`, and `codex`; verify mapped models and collapsed efforts (`agy` cannot emit `max` or `xhigh`).
- Edge: resolve `muse`/`grok` with preferred effort `max` and expect `xhigh`.
- Error: unknown execution class or invalid runtime raises `TierResolverError` / `KeyError` with a descriptive message.
- Non-regression: `resolve()` still returns Gemini models from the existing `tier_policy.json` work-shape registry.

**Verification:** `uv run pytest plugins/fleet-core/tests/test_fleet_core_execution_classes.py plugins/fleet-core/tests/test_fleet_commons.py tests/test_agent_tier_lint.py` passes.

### U2. `saga` Pre-Push Git Invocation Parsing & Execution-Spec Table Rendering

Replace the pre-push regex and add the approval table module.

**Goal:** Eliminate false positives and false negatives in git pre-push gates, and render execution-spec approval tables.

**Requirements:** R5, R6

**Dependencies:** None.

**Files:**

- `plugins/saga/hooks/pre_push_gate_hook.py`
- `plugins/saga/scripts/spec_table.py` (new module port, plus the native `--outcome` renderer)
- `plugins/saga/skills/outcome/SKILL.md` (approval-table step at `approve`/`advance` dispatch)
- `tools/gate-manifest.json` (single-source gate manifest the hook reads)
- `plugins/saga/tests/test_pre_push_gate.py` (new)
- `plugins/saga/tests/test_spec_table.py` (new)

**Approach:** Replace `_is_git_push_command`'s regex with the upstream `shlex` tokenizer (`punctuation_chars=True`, git global opts with values skipped). Port `spec_table.py` from `faecb8a3`, add the native `--outcome` renderer (`render_outcome` over `outcome-spec.json`), and wire it into the `outcome` skill at the `approve`/`advance` dispatch points. Plan step 5 and work-before-execution keep their existing approval surfaces and never author an `ExecutionSpec`.

**Patterns to follow:** Claude `plugins/saga/hooks/pre_push_gate_hook.py` at `fe3bf9f3`; current Antigravity hook's silent-on-pass / exit-2 contract.

**Test scenarios:**

- Happy path: structured `git push origin main` is detected and the gate runs.
- Edge: `git -C /repo push` is a push; `git commit -m 'git push'` is not; `echo 'git push'` is not.
- Error: `git push&&echo ok` still counts as a push (plain `shlex.split` would miss it).
- Happy path: an execution-spec approval table renders on backend approval transitions.
- Happy path: `spec_table.py --outcome` renders the node/flags/sandbox approval table from an `outcome-spec.json`, with destructive and gated nodes named in approval warnings.

**Verification:** `uv run pytest plugins/saga/tests/test_pre_push_gate.py plugins/saga/tests/test_spec_table.py` passes.

### U3. `saga` Refute-N Verify Panel Severity Axis & Even-N Quorum Fix

Harden verify-panel math after the collision-guard edit of the same file.

**Goal:** Stop even-N fail-open and split gating findings from advisory ones.

**Requirements:** R4

**Dependencies:** U4 (same file `execution_spec.py`; upstream `b3c13006` precedes `f0ca9a47`).

**Files:**

- `plugins/saga/scripts/execution_spec.py`
- `plugins/saga/tests/test_verify_panel_severity_axis.py` (new; shipped name — the upstream `test_saga_execution_spec.py`/`test_workflow_emitter.py` split was not adopted)

**Approach:** Port the `#686` severity axis and change the declared quorum floor from `(n + 1) // 2` to `n // 2 + 1`. Keep `_emit_panel_reconciliation` as the single emitter.

**Patterns to follow:** current `_emit_panel_reconciliation` in `plugins/saga/scripts/execution_spec.py`; Claude reconciliation after `f0ca9a47`.

**Test scenarios:**

- Happy path: even panel (2 pass, 2 fail) does not fail-open; declared floor for `n=4` is 3.
- Happy path: `refuted_deliverable` gates; `advisory_corrections` do not.
- Error: a malformed verifier payload without both required arrays is treated as missing, not as an accept.

**Verification:** `uv run pytest plugins/saga/tests/test_verify_panel_severity_axis.py` passes.

### U4. `saga` Concurrency Safety — Halt on Concurrent File Collisions

Prevent same-wave units from writing the same declared file.

**Goal:** Halt emission when same-wave `Unit.files` overlap.

**Requirements:** R3

**Dependencies:** U2 (`spec_table.py` module port; upstream #668 precedes #671).

**Files:**

- `plugins/saga/scripts/execution_spec.py`
- `plugins/saga/scripts/team_emitter.py`
- `plugins/saga/skills/plan/SKILL.md` (same-file splitting rule, Step 5)
- `plugins/saga/tests/test_wave_file_conflicts.py` (new)
- `plugins/saga/tests/test_spec_table.py` (concurrent-writer safety section)

**Approach:** Port `wave_file_conflicts` / `assert_no_wave_file_conflicts` and call them from emit paths. Add the concurrent-writer section to the table from U2.

**Patterns to follow:** Claude `b3c13006`; existing Antigravity `Unit.files` on `execution_spec.py`.

**Test scenarios:**

- Happy path / error: two same-wave units with overlapping declared files halt with a conflict error naming each pair and shared path.
- Happy path: two same-wave units with disjoint declared files emit without error.

**Verification:** `uv run pytest plugins/saga/tests/test_wave_file_conflicts.py plugins/saga/tests/test_spec_table.py` passes.

### U5. `home-lab-ops` `team-scaffold` Skill Port

Port the deterministic team-repo generator.

**Goal:** Provide Antigravity with automated team repository and deployment scaffolding.

**Requirements:** R7

**Dependencies:** None.

**Files:**

- `plugins/home-lab-ops/skills/team-scaffold/SKILL.md`
- `plugins/home-lab-ops/skills/team-scaffold/references/`
- `plugins/home-lab-ops/skills/team-scaffold/scripts/`
- `plugins/home-lab-ops/skills/team-scaffold/scripts/tests/` (upstream tests live here; `plugins/home-lab-ops/tests/` does not exist on `origin/main`)
- `plugins/home-lab-ops/skills/team-scaffold/specs/`

**Approach:** Port the skill tree from Claude `f218f615` / current Claude `origin/main`. Keep tests inside the skill package.

**Patterns to follow:** existing `plugins/home-lab-ops/skills/*` layout; Claude `plugins/home-lab-ops/skills/team-scaffold/`.

**Test scenarios:**

- Happy path: `team-scaffold validate-spec` on a golden team spec produces a valid skeleton and Ansible harness.
- Error: an invalid or incomplete spec returns clear validation errors.

**Verification:** the skill-local tests under `plugins/home-lab-ops/skills/team-scaffold/scripts/tests/` pass.

### U6. `hermes-profile-evolution` Boundary Non-Regression

Confirm the already-landed timeout and reply bounds; do not re-port the plugin.

**Goal:** Keep the committed adapter's 45-second subprocess bound and 16,384-character reply limits.

**Requirements:** R8

**Dependencies:** None. Requires the Implementation Baseline: work from `origin/main`, not the untracked working-tree copy.

**Files:**

- `plugins/hermes-profile-evolution/scripts/profile_request.py` (read/verify; no functional change expected)
- `tests/test_hermes_profile_evolution.py` (read/verify existing cases)
- `docs/ports/2026-08-01-hermes-profile-evolution/receipt.yaml` (committed campaign; do not revive `docs/ports/2026-07-30-hermes-profile-evolution/`)

**Approach:** On `origin/main`, `SUBPROCESS_TIMEOUT_SECONDS = 45` and `test_adapter_timeout_does_not_preempt_the_producer_transport` already asserts `45 > 30`. Reply limits are already enforced (`content.strip()` and `test_reply_uses_producer_limit_and_rejects_secret_message`). If those assertions still pass, this unit is done.

**Patterns to follow:** committed `plugins/hermes-profile-evolution/` on `origin/main`, not the untracked working-tree tree.

**Test scenarios:**

- Test expectation: none as new coverage — re-run the existing origin/main tests named above. Add a test only if a rebase dropped `SUBPROCESS_TIMEOUT_SECONDS == 45` or the 16,384 / whitespace-only checks.

**Verification:** `uv run pytest tests/test_hermes_profile_evolution.py` passes on the `origin/main` plugin, and the untracked `timeout=10` copy is not what shipped.

### U7. Lease Broker Unwinding & Worktree Registry Alignment

Delete the unused lease modules and record the ledger supersede.

**Goal:** Remove `lease_broker.py` and `orphan_evidence.py` now that no production `.py` imports them.

**Requirements:** R9

**Dependencies:** None (upstream `e2ba7db5` was self-contained; Antigravity production scripts do not `load("lease_broker")` or `load("orphan_evidence")`).

**Files:**

- Remove `plugins/fleet-core/scripts/fleet_commons/lease_broker.py`
- Remove `plugins/fleet-core/scripts/fleet_commons/orphan_evidence.py`
- Remove `plugins/fleet-core/tests/test_lease_broker.py` and `plugins/fleet-core/tests/test_orphan_evidence.py`
- Add `plugins/fleet-core/tests/test_output_attestation.py` (the orphan-fencing coverage refactor, upstream `tests/test_output_attestation.py`)
- Add `plugins/fleet-core/tests/test_no_lease_broker_readd.py`
- Update `plugins/fleet-core/tests/test_concurrency_policy.py` and `plugins/fleet-core/tests/test_host_contract_lint.py`
- Update `plugins/fleet-core/references/antigravity-host-contract-surfaces.json`
- Update `docs/ports/2026-07-30-saga-reliability/ledger.yaml` with the superseding decision for `concurrency-lease-policy` and `orphan-evidence-attestation`

**Approach:** Delete the two modules and the tests that load them. Update host-contract and concurrency tests that assert those paths. Add the re-add guard. Record the ledger supersede in the same unit so the plan is not the only decision record.

**Patterns to follow:** Claude `e2ba7db5`; existing `plugins/saga/scripts/outcome_worktrees.py`.

**Test scenarios:**

- Happy path: saga outcome / worktree tests run without `lease_broker`.
- Non-regression: a re-add of `lease_broker.py` or `orphan_evidence.py` fails the new guard test.

**Verification:** `uv run pytest plugins/fleet-core/tests/test_no_lease_broker_readd.py plugins/fleet-core/tests/test_concurrency_policy.py plugins/fleet-core/tests/test_host_contract_lint.py plugins/saga/tests/test_outcome_worktrees.py` passes.

### U8. Verification, Conformance, & Quality Guards

End-to-end verification across the repository.

**Goal:** Prove the ported units pass the repo doctor and the full test suite.

**Requirements:** R10

**Dependencies:** U1–U7.

**Files:**

- `docs/engineering-journal/LEARNINGS.md`
- `docs/engineering-journal/DECISIONS.md`

**Approach:** Run the same doctor invocation the Verification section names. Record the port decisions and the `origin/main` baseline in the journal.

**Patterns to follow:** existing journal entry format in those two files.

**Test scenarios:**

- Run `uv run python scripts/validate_plugins.py --strict-install` and expect status ok.
- Run `uv run pytest` and expect a full pass (no new failures).

**Verification:** both commands above are green on the implementation tree.

---

## Scope Boundaries

### Explicit Non-Goals

- **`orchestrate` plugin:** held off per operator direction while still under active upstream development. Do not take files from `541b36b9` / `feat/orchestrate-u5-completion`.
- **`house-style` output styles:** not ported (Antigravity presentation is `GEMINI.md` / `ANTIGRAVITY.md`).
- **`redis-channel`:** not ported (Antigravity uses native agent messaging).
- **`agy` / `codex` delegation plugins:** not ported (Antigravity is already the native host runtime).
- **Replacing Gemini models with Claude live vocabulary:** out of scope; see KTD1.
- **Re-porting `hermes-profile-evolution` from the untracked working tree:** out of scope; see U6.

---

## Risks & Dependencies

| Risk | Mitigation |
|---|---|
| Local checkout is behind `origin/main` and has a stale untracked Hermes tree | Implementation Baseline: start from `e0f08ce`; ignore untracked `plugins/hermes-profile-evolution/` |
| Claude feature-branch HEAD is not `origin/main` | Pin `ff236284`; exclude orchestrate |
| Blind copy of Claude `models.json` breaks `tier_palette.MODELS` and `CHEAP_MODELS` | R1/KTD1 keep Gemini `models`/`efforts` |
| U3 and U4 share `execution_spec.py` | U3 depends on U4 |
| R9 still recorded as approved-survivor in the saga-reliability ledger | U7 updates `docs/ports/2026-07-30-saga-reliability/ledger.yaml` |
| Claude `origin/main` moves before implementation | Re-pin the Sources table before `/work` |

---

## Verification & Test Plan

1. **Unit tests:** `uv run pytest` across all new and updated plugin test files listed in U1–U7.
2. **Doctor check:** `uv run python scripts/validate_plugins.py --strict-install`.
3. **Engineering journal:** record the porting decisions, the `origin/main` baseline, and the R9 ledger supersede.
