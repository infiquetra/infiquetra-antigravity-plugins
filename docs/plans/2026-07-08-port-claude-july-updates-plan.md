---
title: Port Claude Plugin Updates (July 2026) to Antigravity
type: feat
status: active
date: 2026-07-08
origin: /Users/jefcox/.gemini/antigravity-cli/brain/c7e4afd9-1999-42f0-b525-69e03cb79fc1/implementation_plan.md
source_repo: /Users/jefcox/workspace/infiquetra/infiquetra-claude-plugins
source_range: 3987510..099ec4c
target_baseline: 99df140
---

# Port Claude Plugin Updates (July 2026) to Antigravity

## Summary

Port the current Claude plugin delta from `infiquetra-claude-plugins` into this Antigravity-native repository. The source range is `3987510..099ec4c`; `3987510` is the synced commit recorded in this repo's README, and `099ec4c` is the live Claude `main` head verified during review.

This is not a blind file copy. Each source surface must be classified as `direct-port`, `antigravity-adapt`, `metadata-only`, or `blocked/deferred`, then implemented through Antigravity's root `plugin.json`, `agents/`, `commands/`, `skills/`, `config/`, `scripts/`, docs, and tests.

## Problem Frame

Claude plugins and Antigravity plugins use different execution surfaces. Claude workflow `agent(...)` calls, `.claude-plugin` manifests, `team-execution` residents, and Claude-specific tool names cannot be copied directly into Antigravity without changing behavior.

The plan must preserve the useful behavior from the Claude delta while forcing every runtime integration through explicit Antigravity adapters, especially for `invoke_subagent`, `multi-agent-consensus`, root plugin manifests, and local install validation.

## Grounding And Current State

| Item | Verified Value | Notes |
| --- | --- | --- |
| Source repo | `/Users/jefcox/workspace/infiquetra/infiquetra-claude-plugins` | Read-only source. Do not mutate it. |
| Source range | `3987510..099ec4c` | Current Claude delta to port. |
| Target repo baseline | `99df140` | Current Antigravity checkout revision at review time. |
| Prior sync point | `3987510` | Recorded in this repo's README portability matrix. |
| Target dirty state | `.serena/project.yml`, `graphify-out/*`, untracked plan/review docs, untracked `plugins/saga/scripts/completeness_gate.py`, `tests/test_completeness_gate.py` | Do not revert unrelated local state. Treat untracked implementation fragments as out of commit scope until this plan claims them. |

## Requirements

**R1:** Create or update an Antigravity-native `fleet-core` utility plugin so shared tier, effort, cost, retry, and ledger primitives have a real target in this repo.

**R2:** Port run-scoped budget controls, `/tier`, escalation, spend-delta, and tier-default behavior into `saga`, backed by the shared `fleet-core` palette.

**R3:** Adapt the Claude model palette to Antigravity/Gemini model names and payload semantics.

**R4:** Enforce the adapted tier palette in `mission-control` through `executor_profile_lint.py` and issue/profile validation tests.

**R5:** Port verifier panel hardening, including strict verdict shape, visibility requirements, `examined_sha`, reporter identity, fallback attribution, under-strength handling, and malformed-verdict failure.

**R6:** Adapt verifier dispatch to Antigravity. Use `multi-agent-consensus` personas and/or `invoke_subagent`, but do not assume Claude `agent(...)` StructuredOutput enforcement exists.

**R7:** Port outcome DAG and board progression fixes, including cross-repo objective ingestion, `board_progression.py`, `outcome_edges.py`, `outcome_reconcile.py`, and related outcome tests.

**R8:** Port resumable ship/merge primitives and GitHub API fixes where they map to Antigravity, including `ship_ceremony.py`, contents API PUT behavior, label taxonomy validation, repo argument normalization, and bulk `flow set-field`.

**R9:** Replace Claude marketplace work with Antigravity plugin-surface validation. Root `plugins/*/plugin.json`, `scripts/validate_plugins.py`, and `tools/install-plugin.sh` are canonical here; do not introduce a top-level Claude-style `marketplace.json`.

**R10:** Handle subprocess security findings on ported files with scoped Bandit checks. Do not claim the whole repository currently passes `uv run bandit -r plugins/ -q -c pyproject.toml`; it does not.

**R11:** Explicitly classify and defer Claude-only external engine bridges, Codex runner surfaces, and `.claude-plugin` manifest mechanics unless an Antigravity-native equivalent is designed in this plan.

## Delta Inventory And Classification

| Source Surface | Classification | Target Handling |
| --- | --- | --- |
| `plugins/fleet-core/scripts/fleet_commons/*` | `antigravity-adapt` | Add `plugins/fleet-core/` as an Antigravity utility plugin with root `plugin.json`; port shared Python modules and tests. |
| `plugins/fleet-core/.claude-plugin/*` | `blocked/deferred` | Do not port Claude manifests. Replace with root `plugins/fleet-core/plugin.json`. |
| Claude tier palette and `models.json` | `antigravity-adapt` | Rewrite model names and outbound payload mapping for Gemini. Preserve ordering semantics with tests. |
| `effort_rider.py` | `antigravity-adapt` | Keep one effort seam, but emit Gemini `thinking_level` payloads where a real model call exists; use prompt rider only where Antigravity lacks a native effort knob. |
| `cost_weights.py`, `cost_weights.json`, spend envelope, spend authority | `direct-port` with palette adaptation | Port logic and adapt tests to the Gemini palette. |
| `tier_resolver.py`, `tier_policy.json`, `render_tier_table.py` | `antigravity-adapt` | Port resolver semantics and update policy defaults to Gemini tiers. |
| `retry_backoff.py` | `direct-port` | Port as shared fleet primitive; include retry-after clamp tests. |
| `run_ledger.py` | `direct-port` | Port append-only ledger and tests under the Antigravity saga/fleet layout. |
| `saga` `/tier`, `tier_session.py`, tier defaults, team emitter tier handling | `antigravity-adapt` | Port behavior; replace `.claude/saga` local state with the repo's Antigravity local-state convention if present, otherwise document compatibility fallback. |
| `saga` verifier hardening in `execution_spec.py` | `antigravity-adapt` | Rebuild around Antigravity dispatch and validate JSON verdicts in-process after subagent completion. |
| `saga` `readonly-verifier` agent | `antigravity-adapt` | Either add an Antigravity `agents/readonly-verifier.md` or map to `multi-agent-consensus` personas with explicit read-only/worktree limits and tests proving the limits that are actually enforceable. |
| `saga` `check_empty_delivery.py` / `completeness_gate.py` class of fixes | `antigravity-adapt` | Add a unit for completeness/empty-output gates. Existing untracked target files must be reviewed against the source delta before reuse. |
| `saga` outcome DAG files (`outcome_edges.py`, `outcome_reconcile.py`, `board_progression.py`, `outcome.py`, `discover_subissues.py`) | `direct-port` with path adaptation | Port behavior and tests for cross-repo objective ingestion, board progression idempotency, and issue-backed saga ids. |
| `saga` spore, manifest, provenance, gate divergence, status-card files | `antigravity-adapt` | Port only after confirming target references and local-state paths. Add explicit tests or defer individually. |
| `saga` hooks | `antigravity-adapt` or `blocked/deferred` per hook | Target repo has `plugins/saga/hooks/`, but runtime support must be verified. Port only hooks with a proven Antigravity hook consumer. |
| `mission-control` `sdlc_manager.py`, `executor_profile_lint.py`, flow/issue skill changes | `direct-port` with palette adaptation | Port API fixes and tests; adapt palette literals to Gemini names. |
| `scripts/sync_marketplace.py`, `check_release_surface_parity.py`, `tools/release_surface_diff_guard.py` | `antigravity-adapt` | Replace Claude marketplace assumptions with root `plugin.json` and `scripts/validate_plugins.py` checks. |
| `.claude-plugin/marketplace.json` changes | `metadata-only` source lineage, not target runtime | Use only as source evidence for versions and changed plugin set. Do not copy. |
| `plugins/team-execution/*` | `antigravity-adapt` | Map relevant reviewer/validator behavior to `plugins/multi-agent-consensus`; do not create a new `team-execution` plugin unless approved. |
| `plugins/agy/*` | `blocked/deferred` unless directly needed | Antigravity-native `agy` delegation bridges are not part of this port unless separately scoped. |
| `plugins/codex/*`, `engine_bridge_http.py`, Codex runner bridges | `blocked/deferred` | Claude-only or external-engine bridge surfaces; do not port in this plan. |
| `tools/gate-manifest.json` | `antigravity-adapt` | Update only if target tooling uses the same gate manifest. Otherwise defer. |

## Key Technical Decisions

**KTD1: Source range is explicit.**

Implementation must work from `infiquetra-claude-plugins` range `3987510..099ec4c`, not from a vague "recent updates" description. Start implementation by regenerating a source delta inventory and comparing it to the classification table above.

**KTD2: Add `fleet-core` as an Antigravity utility plugin.**

The target repo does not currently have `plugins/fleet-core`, but the source delta makes `fleet-core` the shared home for tier, effort, retry, ledger, and cost primitives. Create it with root `plugin.json` and no user-facing command requirement unless later units need one.

**KTD3: Gemini effort mapping is an adapter, not a string rename.**

Gemini 3.x uses `thinking_level` values documented as `minimal`, `low`, `medium`, and `high`. The Antigravity adapter must translate internal effort values to outbound payloads as follows:

| Internal Effort | Gemini `thinking_level` | Notes |
| --- | --- | --- |
| `low` | `low` | Lowest ported Claude effort. |
| `medium` | `medium` | Default balanced tier. |
| `high` | `high` | Strong reasoning tier. |
| `xhigh` | `high` plus premium-tier gating/receipt | Gemini has no separate `xhigh`; preserve it only as internal policy semantics, never as an outbound Gemini value. |

For Python Interactions API calls, emit `generation_config: {"thinking_level": "<level>"}`. For JavaScript calls, emit `generationConfig: { thinkingLevel: "<level>" }`. Do not emit legacy `thinking_budget` or both fields in one request.

**KTD4: Verifier StructuredOutput must be enforced by our adapter.**

The plan cannot assume `multi-agent-consensus` natively enforces Claude StructuredOutput schemas. The `saga` adapter must validate every verifier response after completion and hard-fail missing or malformed `refuted`, `upheld`, `examined_sha`, `verifier_identity`, or `fallback_depth` fields where the protocol requires them.

**KTD5: Read-only verifier isolation must be evidence-backed.**

If Antigravity `invoke_subagent` cannot enforce a read-only toolset and disposable worktree, document the weaker guarantee and keep the check as an explicit residual risk. Do not silently claim parity with Claude `readonly-verifier`.

**KTD6: Release validation follows Antigravity surfaces.**

Antigravity validation is `plugins/*/plugin.json`, `scripts/validate_plugins.py`, and symlink installs under `~/.gemini/config/plugins`. Top-level `marketplace.json` generation is not a target unless a separate Antigravity marketplace design is approved.

**KTD7: Bandit is scoped until the baseline is fixed.**

Existing `uv run bandit -r plugins/ -q -c pyproject.toml` fails on the current target baseline. Port work must run Bandit on changed production paths or record a baseline comparison. A full-repo Bandit pass is not an acceptance gate for this plan.

## Implementation Units

### U0. Source Inventory And Preflight

**Goal:** Reproduce the source delta inventory and prove each changed source surface maps to a unit, a deferral, or a metadata-only action.

**Requirements:** R11.

**Files:** No committed code changes expected. Update this plan only if the live source range has changed before implementation starts.

**Approach:** Run `git -C ../infiquetra-claude-plugins diff --name-status 3987510..099ec4c -- plugins/fleet-core plugins/saga plugins/mission-control plugins/team-execution plugins/agy plugins/codex scripts tools` and compare to the classification table.

**Test scenarios:** Inventory has no unclassified source paths in the selected scope.

### U1. Bootstrap Antigravity `fleet-core`

**Goal:** Create a real target for shared fleet primitives.

**Requirements:** R1, R3, R10.

**Files:** `plugins/fleet-core/plugin.json`, `plugins/fleet-core/README.md`, `plugins/fleet-core/scripts/fleet_commons/*`, `plugins/fleet-core/scripts/fleet_commons_shim.py`, focused tests under the repo's existing test layout.

**Approach:** Port shared modules from Claude, remove `.claude-plugin` assumptions, use root `plugin.json`, and adapt model names and effort ceilings to Gemini.

**Test scenarios:** Palette ordering, effort ceiling, `xhigh` clamp/receipt, retry-after clamp, shim resolution, and plugin doctor include `fleet-core`.

### U2. Port Tier, Effort, Spend, And `/tier` Controls

**Goal:** Move tier mechanics into `saga` using the new `fleet-core` primitives.

**Requirements:** R2, R3.

**Files:** `plugins/saga/commands/tier.md`, `plugins/saga/scripts/execution_spec.py`, `plugins/saga/scripts/tier_session.py`, `plugins/saga/scripts/tier_defaults.py`, `plugins/saga/scripts/spend_authority.py`, `plugins/saga/scripts/effort_ledger.py`, `plugins/saga/scripts/team_emitter.py`, related docs/tests.

**Approach:** Preserve Claude behavior where it is backend-independent, adapt local state paths to Antigravity, and prove every outbound Gemini payload uses KTD3 mapping.

**Test scenarios:** Existing saga tests pass; new tests cover `/tier` ceiling, per-unit override, escalation gate, spend delta, budget warning/HALT, and Gemini payload mapping.

### U3. Port Mission-Control Profile And GitHub API Fixes

**Goal:** Bring mission-control validation and GitHub API fixes current with the Claude range.

**Requirements:** R4, R8, R10.

**Files:** `plugins/mission-control/scripts/sdlc_manager.py`, `plugins/mission-control/scripts/executor_profile_lint.py`, `plugins/mission-control/scripts/fleet_commons_shim.py`, `plugins/mission-control/skills/flow/SKILL.md`, `plugins/mission-control/skills/issues/SKILL.md`, related tests.

**Approach:** Port repo argument normalization, PUT contents API behavior, label taxonomy validation, bulk `flow set-field`, and profile linting against the Gemini palette.

**Test scenarios:** `uv run pytest plugins/mission-control` plus focused tests for invalid model rejection, `gemini-3.5-flash`/`gemini-3.1-pro` acceptance, PUT contents API, label cap validation, and bulk field updates.

### U4. Port Verifier Hardening And Completeness Gates

**Goal:** Make Antigravity verifier panels fail loudly on incomplete, malformed, under-strength, or unverifiable outputs.

**Requirements:** R5, R6, R10.

**Files:** `plugins/saga/scripts/execution_spec.py`, `plugins/saga/scripts/completeness_gate.py` or source-equivalent gate module, `plugins/saga/agents/readonly-verifier.md` if supported, `plugins/multi-agent-consensus/*` only where the adapter needs persona mapping, related tests.

**Approach:** Build an Antigravity verifier adapter that spawns the selected reviewer persona, captures the response, validates the strict verdict object, records reporter identity/fallback depth, and fails on missing required fields. Review existing untracked target `completeness_gate.py` before reuse; do not assume it matches the source delta.

**Test scenarios:** Refuted/upheld verdict handling, missing `examined_sha`, missing reporter identity, malformed JSON, empty delivery, under-strength quorum, fallback attribution, and prompt tool-name translation (`Bash` -> `run_command`, `Edit` -> `replace_file_content`, `Write` -> `write_to_file`, `MultiEdit` -> `multi_replace_file_content`).

### U5. Port Outcome DAG, Board Progression, And Ship Ceremony

**Goal:** Bring outcome progression and ship/merge support current.

**Requirements:** R7, R8, R10.

**Files:** `plugins/saga/scripts/board_progression.py`, `plugins/saga/scripts/outcome.py`, `plugins/saga/scripts/outcome_edges.py`, `plugins/saga/scripts/outcome_reconcile.py`, `plugins/saga/scripts/outcome_github.py`, `plugins/saga/scripts/ship_ceremony.py`, related docs/tests.

**Approach:** Port source behavior with Antigravity path and command adaptations. Keep GitHub mutations behind existing CLI/test seams; no live GitHub mutation during implementation unless explicitly approved.

**Test scenarios:** Cross-repo objective ingestion, board-sync comment idempotency, issue-backed saga id emission, outcome edge validation, reconciliation, and ship ceremony transition persistence.

### U6. Port Manifest, Provenance, Spore, Status, And Hook Surfaces

**Goal:** Capture support files from the source range that are easy to miss but affect runtime safety.

**Requirements:** R5, R7, R10, R11.

**Files:** `plugins/saga/scripts/manifest_reader.py`, `manifest_store.py`, `provenance_manifest.py`, `saga_spore.py`, `status_card.py`, `gate_divergence_reader.py`, hook files only after runtime verification, related references/tests.

**Approach:** Port surfaces only when their target consumers exist. For each hook, prove the target repo/runtime actually invokes it; otherwise classify the hook as deferred in the implementation notes.

**Test scenarios:** Manifest read/write, provenance receipt validation, spore round trip, status card rendering, gate divergence reading, and no hook drift in `scripts/validate_plugins.py`.

### U7. Release Surface And Validation Adaptation

**Goal:** Replace Claude marketplace assumptions with Antigravity validation and install checks.

**Requirements:** R9, R10.

**Files:** `README.md` portability matrix, `scripts/validate_plugins.py` if needed, `tools/install-plugin.sh` if needed, `tools/release_surface_diff_guard.py`, `scripts/check_release_surface_parity.py`, `scripts/sync_marketplace.py` only if retained as an Antigravity-compatible generator.

**Approach:** Validate root `plugin.json` files directly. Update the portability matrix to record source commit `099ec4c` for modified plugins. Do not generate or require top-level `marketplace.json`.

**Test scenarios:** `uv run python scripts/validate_plugins.py --json`, install-surface checks, no stale `.claude-plugin` references in current Antigravity specs, and portability matrix reflects the new source commit after all units land.

### U8. Deferred Surface Ledger

**Goal:** Prevent accidental partial ports of Claude-only or out-of-scope surfaces.

**Requirements:** R11.

**Files:** Plan/work-session notes and, if convention exists, engineering journal queued/deferred entry.

**Approach:** Record each deferred surface with rationale: external HTTP bridge, Codex runner, Claude `.claude-plugin` manifests, unapproved `agy` delegation bridge, and any hook without proven Antigravity runtime support.

**Test scenarios:** Final diff contains no accidental `plugins/codex`, Claude manifest, or external HTTP bridge port unless explicitly re-scoped.

## Verification Plan

Run checks in this order, tightening from scoped to broad:

1. `uv run python scripts/validate_plugins.py --json`
2. `uv run pytest plugins/mission-control`
3. `uv run pytest plugins/saga`
4. `uv run pytest plugins/multi-agent-consensus`
5. `uv run pytest` after unit-level tests pass
6. `uv run ruff check .`
7. Scoped Bandit over changed production paths, for example `uv run bandit -q -c pyproject.toml -ll -r plugins/fleet-core/scripts plugins/saga/scripts plugins/mission-control/scripts`
8. Full `uv run bandit -r plugins/ -q -c pyproject.toml` only as informational until the existing baseline is fixed
9. `uv run python plugins/saga/scripts/render_docs_visuals.py`

Known baseline from review:

| Command | Current Result | Use In This Plan |
| --- | --- | --- |
| `uv run pytest plugins/mission-control` | Passes, 176 tests | Required after mission-control changes. |
| `uv run pytest plugins/saga` | Passes, 399 passed / 1 skipped | Required after saga changes. |
| `uv run python scripts/validate_plugins.py --json` | Passes with an existing `unifi` empty-agent warning | Required after plugin-surface changes. |
| `uv run ruff check .` | Passes | Required before final review. |
| `uv run pytest plugins/fleet-core` | Fails because the directory does not exist | Becomes valid only after U1 creates `fleet-core`. |
| `uv run bandit -r plugins/ -q -c pyproject.toml` | Fails on existing baseline findings | Informational unless baseline config is fixed. |

## Scope Boundaries

Out of scope unless explicitly approved:

- OpenAI-compatible HTTP bridge and Codex runner delegation.
- New `plugins/codex` plugin in Antigravity.
- New `plugins/agy` bridge work beyond direct verifier/tier dependencies.
- Claude `.claude-plugin` manifests or top-level `marketplace.json`.
- Live GitHub mutations, deployments, installed plugin changes, or host syncs.
- Reverting unrelated dirty state in `.serena/`, `graphify-out/`, or untracked implementation fragments.

## Handoff Gate

Before `/work` starts, the implementer must confirm:

1. The source range is still `3987510..099ec4c`, or update this plan and re-review.
2. Every source path in the regenerated inventory is represented by a unit, metadata-only action, or explicit deferral.
3. The `fleet-core` utility plugin target is accepted.
4. Gemini `thinking_level` mapping follows KTD3.
5. Verifier structured verdict enforcement is implemented in Antigravity-owned code, not assumed from `multi-agent-consensus`.
