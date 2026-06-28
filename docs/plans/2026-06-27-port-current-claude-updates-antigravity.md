---
title: Port Current Claude Plugin Updates Into Antigravity
type: chore
status: active
date: 2026-06-27
---

# Port Current Claude Plugin Updates Into Antigravity

## Summary

Port the recent `infiquetra-claude-plugins` updates into this Antigravity-native plugin repo. This is not a blind sync. We build an Antigravity-native port, preserving behavior only where Antigravity has a real supported surface, and explicitly classifying anything Claude-only, blocked, or deferred.

The implementation treats `infiquetra-claude-plugins` `2583643..3987510` as the source delta. Antigravity has already ported up through PR #231 (`2583643`), and already cleaned up the legacy plugins prior to Claude doing so.

## Grounding & Truth
- **Source Range (Claude)**: `2583643..3987510`
- **Current Antigravity Baseline SHA**: `be01bd5143afeb4c174b9234afcb4f6c57c62bb7`
- **Dirty State**: Antigravity has modified `.neuralmind/synapses.db`, `graphify-out/graph.json` and untracked `.neuralmind/events.jsonl`. These will be ignored. Claude is clean.

## Delta Inventory & Classification

| Plugin / Surface | Classification | Notes |
| --- | --- | --- |
| `saga` (OutcomeOrchestrator) | `antigravity-adapt` | Port the outcome scripts, tests, and skills to Antigravity. Adapt Claude command references to Antigravity skill semantics. |
| `saga` (Hooks) | `blocked` / `deferred` | Claude's `hooks/` directory (`stale_main`, `pre_push_gate`, etc.) will NOT be ported. `ANTIGRAVITY.md` explicitly lacks hook infrastructure. |
| `mission-control` | `direct-port` | Port board rename ("Jeff Intent" -> "Operations"), null GraphQL node fixes, and mock tests. |
| `team-execution` (Claude) | `antigravity-adapt` | Maps to Antigravity's `multi-agent-consensus`. We will ensure tmux/pane setup guidance is removed and adapt any relevant concurrency/fallback logic. |
| `deploy`, `unifi`, `home-lab-ops` | `metadata-only` | Claude agent model pin updates. Only bump versions if Antigravity behavior changes. |
| Legacy Plugins (`slack`, `pagerduty`, etc.) | `deferred` (already removed) | Claude removed 9 plugins in this delta. Antigravity had already removed them previously. |

## Team-Execution Mapping Evidence
In Antigravity commit `e55e1f2` (`refactor(plugins): migrate team-execution to multi-agent-consensus`), the `team-execution` plugin was explicitly migrated to `multi-agent-consensus`. Claude's `team-execution` updates will thus be adapted into `multi-agent-consensus`.

## Implementation Units

### U1. Source Inventory and Metadata Reconciliation
- Update portability matrix and records to establish the new source range.
- **Files**: `README.md`, docs (if applicable).
- **Tests**: `uv run python scripts/validate_plugins.py`

### U2. Mission Control Port
- Port board rename, GraphQL null handling, and mock tests.
- **Files**: `plugins/mission-control/scripts/*`, `plugins/mission-control/skills/*`.
- **Tests**: `uv run pytest plugins/mission-control/tests -q`

### U3. Saga Core Orchestration Changes
- Port non-outcome engine dependencies (lifecycle storage, execution specs).
- **Files**: `plugins/saga/scripts/saga.py`, `plugins/saga/scripts/execution_spec.py`, etc.
- **Tests**: `uv run pytest plugins/saga/tests -q`

### U4. Saga OutcomeOrchestrator Port
- Port the new OutcomeOrchestrator as Antigravity skills/scripts.
- **Files**: `plugins/saga/skills/outcome/*`, `plugins/saga/scripts/outcome*.py`, adapted tests.
- **Tests**: `uv run pytest tests/test_outcome*.py -q`

### U5. Multi-Agent Consensus (Team Execution) Sync
- Remove stale active tmux/pane guidance and adapt relevant team-execution logic to `multi-agent-consensus`.
- **Files**: `plugins/multi-agent-consensus/*`
- **Tests**: `uv run pytest plugins/multi-agent-consensus/tests -q`

### U6. Documentation Generation and Final Validation
- Regenerate docs, bump versions for plugins with modified behavior, and run comprehensive tests.
- **Files**: `docs/saga/*`, `plugin.json` manifests.
- **Tests**: `uv run pytest -q`, `uv run ruff check`, `uv run bandit -q`.

## Version-Bump Policy
Bump versions only when Antigravity-visible behavior exists and tests pass. Do not bump versions for metadata-only or unexposed changes.
