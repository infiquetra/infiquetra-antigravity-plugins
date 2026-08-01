# Migrate Every Approved Port Survivor Natively

## Purpose

GitHub issue #15 migrates the 51 semantics that Jeff approved in the Saga reliability port
campaign into the Antigravity plugins repository. The work preserves Antigravity-native behavior;
it does not copy another harness's plugin tree or create a `team-execution` plugin.

This plan was simplified after implementation review. The migration gate proves the product and
ledger facts required by issue #15. It does not authenticate a particular Codex session, agent
path, reviewer profile, remediation attempt, plan byte digest, or workflow assignment graph.

## Authoritative inputs

- Semantic decisions: `docs/ports/2026-07-30-saga-reliability/ledger.yaml`
- Exact migration mapping: `docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml`
- Migration evidence: `docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json`
- Product requirements: GitHub issue #15

The ledger contains 80 decided candidates: 51 approved survivors and 29 non-survivors. The
migration plan must contain exactly the 51 approved IDs. Each row repeats the approved semantic
contract and declares target paths, one positive Pytest node, one negative Pytest node, the final
Antigravity state, and intentional differences from the source implementations.

## Acceptance contract

The migration is complete when all of these are true:

1. The ledger validates as complete and fully decided.
2. The migration plan contains exactly one row for each approved survivor and no other candidate.
3. Every declared target path exists within `fleet-core`, `mission-control`,
   `multi-agent-consensus`, `saga`, or the repository `scripts` directory.
4. Every survivor's declared positive and negative Pytest nodes exist and pass.
5. The four affected plugin suites pass.
6. Ruff, mypy, documentation rendering, plugin validation, and the host-contract linter pass.
7. Team execution behavior is owned by `multi-agent-consensus`; no Antigravity
   `team-execution` plugin is created.
8. The Claude and Codex source repositories remain unchanged.
9. Canonical migration evidence binds the current ledger sources, decisions, packets, sanitized
   host receipt, exact candidate mappings, and passed test outcomes.
10. Atomic migration recording moves all 51 approved rows from `planned` to `migrated` without
    changing campaign data, packet ownership, semantic contracts, or operator decisions.

## Implementation scope

### Fleet Core

Provide the shared concurrency, lease, liveness, delegation, evidence, capability, plugin
resolution, Saga acceptance, and workflow compatibility primitives used by the migrated behavior.
Keep host-facing capability observations sanitized and deterministic.

### Mission Control

Align issue, board, label, milestone, metrics, rollout, and executor-profile behavior with the
approved semantic contracts. Preserve the repository's existing command and skill boundaries.

### Multi-Agent Consensus

Own the approved team-execution and application-security review behavior. Do not add a separate
Antigravity `team-execution` plugin.

### Saga

Complete the approved lifecycle, evidence, handoff, orchestration, reconciliation, promotion,
pulse, review, documentation, and safety behavior. Keep unavailable Antigravity host capabilities
explicit rather than claiming unsupported execution.

## Migration evidence

The evidence manifest uses the closed
`antigravity.semantic-port-migration-evidence.v1` schema and canonical JSON bytes. It must contain:

- the exact sorted 51 candidate IDs;
- current source snapshot, selected-surface, packet-content, decision, and operator-gate bindings;
- the exact sanitized host receipt stored in the ledger;
- one or more generic completed verification results with passing checks and no unresolved
  findings;
- accepted reviewer results when a review result is included;
- per-candidate target paths and positive and negative node IDs equal to the migration plan;
- passing outcomes for every mapped node; and
- a recomputed manifest digest.

Result identity is deliberately generic. The gate does not require agent paths, attempt IDs,
roles, model profiles, reviewer score matrices, declared workflow write sets, or a custom coverage
command. Candidate evidence must reference verification results that exist and pass.

## Source refresh policy

Source repositories are read-only. Use local `HEAD` and local `origin/main`; do not fetch, pull,
checkout, or rewrite refs.

A changed owned packet set or changed owned packet content invalidates the affected candidate's
decision. Snapshot or commit movement alone updates provenance without invalidating unchanged
semantics. Only capability states required by a candidate can invalidate that candidate. The seven
issue #16 governance outputs named by the campaign remain excluded from source packets.

## Boundaries

Do not mutate sibling repositories, installed plugins, user configuration, host state, or
`.serena/project.yml`. Do not deploy or release as part of issue #15. Correct product defects and
test failures tied to the 51 migrations, but stop for approval before adding a new product surface,
dependency, schema, external action, or unrelated cleanup.

## Verification

```bash
python3 scripts/port_ledger.py validate \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

uv run pytest --collect-only -q \
  $(python3 scripts/port_ledger.py test-nodes \
    docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml)

uv run pytest \
  plugins/saga/tests \
  plugins/fleet-core/tests \
  plugins/mission-control/tests \
  plugins/multi-agent-consensus/tests -q

uv run python plugins/saga/scripts/render_docs_visuals.py --check
uv run ruff check plugins scripts
uv run mypy plugins scripts
python3 scripts/validate_plugins.py \
  --capability-profile repository-validation \
  --observe-host \
  --json
```

After the evidence manifest is current:

```bash
python3 scripts/port_ledger.py record-migrations \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml \
  docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml \
  docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json \
  --validated-at <UTC timestamp>

python3 scripts/port_ledger.py validate --require-migrated \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

## Closeout

Perform one code review and one documentation review. Resolve every actionable P0 through P3
finding or explain why it is not actionable. Then commit the issue-scoped changes, open and merge
the PR when checks pass, confirm issue #15 and the Operations board are closed, return to current
`main`, and remove the merged feature branch. Release qualification remains separate work.
