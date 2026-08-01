# Saga Reliability Semantic Port Campaign

This campaign reconciles Claude, Codex, and Antigravity Saga-family semantics
without copying source files or selecting migration work.

## Current status

The commit-bound discovery inventory is complete. It contains 1,475 normalized
edit packets: 391 Antigravity current-tree packets, 426 Claude current-tree
packets, 229 Claude history packets, and 429 Codex current-tree packets.

Human curation groups those packets into 80 stable semantic candidates. Every
packet has exactly one candidate owner; unmatched and duplicate ownership are
both zero. On 2026-07-30, Jeff recorded the complete operator decision mapping:
51 `approved-survivor`, 19 `blocked`, 8 `metadata-only`, 1 `rejected`, and 1
`superseded`. The 19 blocked candidates require a host-capability change before
they can be reconsidered.

Both inventory-only and plain validation pass. The maintainer rankings and
proposed dispositions remain review inputs; they do not themselves approve or
reject a candidate.

The campaign has now been deterministically upgraded to
`antigravity.semantic-port-ledger.v2`. Each of the exact 51 approved survivors
has a `migrated` migration object bound to its owned edit-packet set, the current
sanitized host receipt, exact Antigravity target paths, and one positive plus
one negative Pytest node ID. The other 29 decisions are unchanged and carry no
migration data. All 51 migrated rows reference the same canonical evidence
manifest and validation time.

## Pinned planning snapshots

| source | selected surface | planning snapshot |
|---|---|---|
| Claude | `saga`, `fleet-core`, `mission-control`, `team-execution`, and directly consumed shared scripts and tools | `0a572448556252c499752e5132617b4c9aa9c1a5` |
| Codex | `saga`, `fleet-core`, `mission-control`, `verified-workflows`, and current portability manifests | `12b5f2c72ff6954cbdbcda8e93408ab2bc518c45` |
| Antigravity | `saga`, `fleet-core`, `mission-control`, and `multi-agent-consensus` | `45463432612ff271c9a12b02aa1fab9390ba9ac1` |

Claude commit `099ec4c` is only the historical discovery seed. It is not proof
that the target covers every current capability.

At the current refresh, Claude and Codex local `HEAD` matched their local
`origin/main` inventory commits recorded in the ledger. Codex inventory has
advanced from its planning snapshot to
`0c2072446c7e136caa274b5f637ca2c8c03725e4`. Antigravity inventory is bound
to local `origin/main` at `45463432612ff271c9a12b02aa1fab9390ba9ac1`;
its feature `HEAD` is recorded separately in the ledger and is not treated as
target inventory.

## Canonical ledger

The canonical path is:

```text
docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

Version 1 remains accepted as the closed decision-only schema. Version 2
preserves every version 1 field and permits the closed migration object only on
an `approved-survivor` row. The ledger records:

- planning and actual inventory snapshots for all three repositories;
- the exact selected surfaces and historical seeds;
- normalized history and complete current-tree edit packets;
- one stable candidate owner for every packet;
- exact commit/path provenance and the user-visible semantic contract;
- adjacent dependencies and required host capabilities;
- current Antigravity state and proposed Antigravity-native disposition;
- four advisory ranking inputs and later evidence expectations;
- the explicit operator decision state; and
- current release-drift disclosure.

The closed migration mapping is:

```text
docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml
```

Its candidate keys equal the exact 51 approved stable IDs. Each row repeats the
ledger semantic contract byte-for-byte and names a final Antigravity state,
target paths, one positive Pytest node, one negative Pytest node, and explicit
source-to-Antigravity differences. It is an implementation mapping, not a
second decision store.

## Ranking rubric

Each candidate records four visible integer inputs from 1 through 5.

| input | meaning of a higher value |
|---|---|
| operator value | more useful to Jeff's intended Saga workflow |
| Antigravity fit | better fit with existing Antigravity product boundaries |
| proof feasibility | easier to prove deterministically and safely |
| maintenance cost | more expensive to own; sorting therefore treats lower cost as preferable |

The report sorts by operator value, Antigravity fit, proof feasibility, inverse
maintenance cost, and stable candidate ID. This order is advisory. No score,
threshold, total, or report position approves, rejects, hides, or mutates a
candidate.

## Host-receipt binding

The fleet-core doctor is the host contract authority. The ledger retains only:

- the promotable receipt schema;
- the capability-catalog digest;
- the canonical receipt digest; and
- sorted capability ID/state pairs.

Raw paths, hostnames, transcripts, runtime roots, and private diagnostic values
do not enter the ledger. A required capability in `failed`, `unknown`, or
`unavailable` state forces the affected candidate to use Antigravity state
`blocked-by-host` and proposed disposition `blocked`.

## Validation and operator gate

After commit-bound discovery and human semantic curation:

```bash
python3 scripts/port_ledger.py validate --inventory-only \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

python3 scripts/port_ledger.py report \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

Inventory-only validation permits pending decisions before the operator gate. It does not permit
unknown fields, missing snapshots, unsafe paths, missing packets, duplicate
ownership, unmatched drift, incomplete ranking or evidence fields, or an
unsafe host receipt.

Plain validation requires Jeff's explicit complete mapping for every current
candidate ID. Workflow approval is not candidate approval. The mapping includes
each non-pending state, rationale, and concrete revisit trigger. Decision
recording binds the operator identity and decision time to every row.

The deterministic report shows all 80 candidates, including low-ranked,
metadata-only, superseded, rejected, and host-blocked recommendations. Each row
includes source hosts, all four ranking inputs, the proposed disposition,
current Antigravity state, semantic contract, required host capabilities,
decision rationale, revisit trigger, and version 2 migration state.

## Migration gate

The deterministic upgrade is:

```bash
python3 scripts/port_ledger.py upgrade-v2 \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml \
  docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml
```

It accepts only a valid, fully decided version 1 ledger. It deep-copies the
data, changes only the root schema, and adds a `planned` migration object to
the exact approved ID set. Repeating the upgrade from byte-identical version 1
inputs produces byte-identical output. A version 1 document carrying migration
data and every unknown ledger version fail before the destination is replaced.

The packet-set digest sorts the candidate's unique edit-packet IDs by Unicode
code-point order, encodes them as UTF-8, joins them with a line-feed byte, and
adds one final line feed only for a nonempty set. Carriage returns, line feeds,
invalid Unicode, and duplicate IDs fail.

Migration recording requires the closed canonical JSON evidence manifest:

```bash
python3 scripts/port_ledger.py record-migrations \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml \
  docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml \
  docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json \
  --validated-at 2026-07-30T18:00:00Z
```

The evidence file must use UTF-8 canonical JSON with sorted keys, compact
separators, no byte-order mark, and exactly one terminal line feed. Its content
binds the refreshed source snapshots, selected surfaces, packet content,
operator decisions, sanitized host receipt, generic verification results, exact
candidate targets, and passed positive and negative Pytest outcomes. The
manifest digest is recomputed with `manifest_sha256` omitted.

Recording verifies the complete plan and evidence before constructing a copied
ledger. It rejects partial or extra candidate sets, non-survivors, stale source
or host bindings, failed or skipped nodes, unresolved findings, blocked rows,
unsafe paths, missing target files, and invalid result schemas. Result evidence
does not bind a Codex agent path, attempt, role, profile, workflow graph, plan
byte digest, or custom coverage command. Only after the product evidence passes
does one atomic replacement move every survivor to `migrated` and its declared
final Antigravity state. Any failure leaves the ledger bytes unchanged.

The final delivery gate is:

```bash
python3 scripts/port_ledger.py validate --require-migrated \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

The final `--require-migrated` validation passes with 51 migrated rows and no
planned or partial approved survivor.

## Release refresh

Before release use, repeat the same local read-only comparison:

1. Confirm local `HEAD` equals local `origin/main` in Claude and Codex.
2. Record Antigravity's local `HEAD` separately and bind its inventory and
   release comparison to local `origin/main`.
3. Re-run discovery without fetching or updating refs.
4. Preserve stable candidate ownership for repeated edits.
5. Disclose every new unmatched packet as release drift.
6. Record refreshed snapshots, packet commits, candidate provenance, the full
   sanitized catalog digest, and the full sanitized receipt digest.
7. Compare each candidate's exact ordered packet ID set and the `host`, `path`,
   `change`, `source`, and `content_sha256` fields of its owned packets. Compare
   only the exact capability IDs and states named by that candidate.
8. Return only an affected decided candidate to `pending` when its owned packet
   set or semantic packet content changes, or when a capability it requires
   changes state. Snapshot or packet commit movement alone remains disclosed
   but does not invalidate the decision; provenance refreshes to the current
   commit.
9. Exclude only the seven issue #16 ledger implementation artifacts named in
   the migration plan from source-candidate packets. They are governance
   outputs, not port inputs.

The complete `record-decisions` mapping preserves an existing decision object,
including its operator and timestamp, when `state`, `rationale`, and
`revisit_trigger` are unchanged. It stamps only semantic decision changes. This
allows one explicit redecision without rewriting the other candidate decisions.

The Antigravity refresh to
`45463432612ff271c9a12b02aa1fab9390ba9ac1` changed one owned semantic packet:
`scripts/port_claude_plugin.py` now labels destructive bulk copying as legacy,
warns when invoked, and directs normal campaigns to this semantic ledger. Jeff
reviewed that change and retained `repository-release-validation` as
`metadata-only`; it adds no survivor behavior. Source, packet, and decision
digests in the migration evidence prevent later evidence assembly or migration
recording from silently rewriting any candidate decision. Migration recording
also compares the protected campaign, packet, decision, and candidate data
before accepting the transition.

Discovery may write only this campaign directory. It may not mutate a sibling
repository, installed plugin, user configuration, or host state.

## Boundary with migration issue #15

This campaign remains the semantic decision authority. GitHub issue #15 now
consumes its exact 51 approved stable IDs through the closed migration mapping
and records delivery separately without changing any operator decision.
Blocked, metadata-only, rejected, and superseded candidates remain outside the
migration mapping. Plugin implementation, version changes, full testing,
evidence assembly, and migration recording are complete for issue #15. Issue
#22 release qualification remains separate work.
