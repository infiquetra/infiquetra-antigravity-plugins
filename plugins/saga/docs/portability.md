# Saga portability

Saga is an Antigravity-native lifecycle system. Repository documents are its
canonical authority. Machine-local state and native brain artifacts are
advisory projections that may help resume work but cannot approve, complete, or
settle it.

## Native execution contract

Saga records exactly two execution backends:

- `inline` for serial work in the current session;
- `multi-agent-consensus` when a passing capability receipt proves native
  independent-agent execution.

An unknown, unavailable, or failed capability is not proof. Saga must not turn
an independence requirement into sequential work.

## Curated source lineage

The documentation model keeps source lineage only as provenance. Every imported
runtime contract is classified before it becomes active Antigravity behavior.

The canonical documentation model also maps every edit packet owned by the
`codex-portability-contracts` ledger candidate. Its exact inventory is 45
packets: 26 adapted, 15 preserved, and 4 shed. Each model entry binds the
packet identifier, Codex source path and commit, Antigravity target boundary,
and cutover classification. This page is the readable summary; the model is
the complete non-lossy packet authority.

The current source binding is Codex local `origin/main` commit
`0c2072446c7e136caa274b5f637ca2c8c03725e4`. All 45 packet identifiers and
their 26 adapted, 15 preserved, and 4 shed classifications remain unchanged.
Seven refreshed packet contents cover version-5 frozen-source checkout and
oracle rules plus their derived references. Those source-runtime rules remain
Codex-specific; Antigravity does not consume them as source-oracle behavior.

| Runtime contract | Antigravity boundary | Classification |
|---|---|---|
| Orchestration backends from historical source runtimes | `references/operator-choice.md` | adapted |
| Plugin dependency resolution for historical source aliases | `scripts/plugin_dependency_resolver.py` | adapted |
| Capability evidence from historical source probes | `scripts/fleet_doctor.py` | adapted |
| Durable artifact authority for historical source brain artifacts | `references/saga-spec.md` | adapted |
| Runtime state projections from historical source state roots | `scripts/reconcile.py` | adapted |
| External action authority for historical source tool calls | `scripts/external_action_contract.py` | adapted |
| Workflow contract package from historical source plugins | `scripts/fleet_commons_shim.py` | shed |

`adapted` means the concept survives behind an Antigravity-native interface.
`preserved` means the contract is host-independent and remains unchanged.
`shed` means Saga consumes the shared contract but does not own or expose the
source package as an active dependency.

## Authority rules

1. Repository `docs/` artifacts are canonical.
2. Brain artifacts are staging inputs only.
3. Machine-local projections are advisory and must reconcile against canonical
   digests before use.
4. External actions require typed intent, authority, and result receipts.
5. Imported evidence keeps its producer and digest provenance.
