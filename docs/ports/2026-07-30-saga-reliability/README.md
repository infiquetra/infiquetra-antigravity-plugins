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

## Pinned planning snapshots

| source | selected surface | planning snapshot |
|---|---|---|
| Claude | `saga`, `fleet-core`, `mission-control`, `team-execution`, and directly consumed shared scripts and tools | `0a572448556252c499752e5132617b4c9aa9c1a5` |
| Codex | `saga`, `fleet-core`, `mission-control`, `verified-workflows`, and current portability manifests | `12b5f2c72ff6954cbdbcda8e93408ab2bc518c45` |
| Antigravity | `saga`, `fleet-core`, `mission-control`, and `multi-agent-consensus` | `6565ddbafb12e794104bdd11e52596bcc993febd` |

Claude commit `099ec4c` is only the historical discovery seed. It is not proof
that the target covers every current capability.

At discovery time, Claude and Codex local `HEAD` matched their local
`origin/main` commits shown above. Antigravity inventory is bound to local
`origin/main` at `6565ddbafb12e794104bdd11e52596bcc993febd`; its feature
`HEAD` is recorded separately in the ledger and is not treated as target
inventory.

## Canonical ledger

The canonical path is:

```text
docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

The ledger uses schema `antigravity.semantic-port-ledger.v1`. It records:

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
decision rationale, and revisit trigger.

## Release refresh

Before release use, repeat the same local read-only comparison:

1. Confirm local `HEAD` equals local `origin/main` in Claude and Codex.
2. Record Antigravity's local `HEAD` separately and bind its inventory and
   release comparison to local `origin/main`.
3. Re-run discovery without fetching or updating refs.
4. Preserve stable candidate ownership for repeated edits.
5. Disclose every new unmatched packet as release drift.
6. Compare refreshed snapshots, packet content identities, selected surfaces,
   and required host-capability evidence with the existing ledger.
7. Return every affected decided candidate to `pending` if any snapshot or
   semantic input changes, even when its stable candidate and packet IDs are
   unchanged. Re-enter the operator gate before those decisions can become
   authoritative again.

A refresh whose source evidence is byte-identical preserves existing decision
authority. A changed snapshot or semantic input always requires renewed
operator review; candidate-set changes are not the only gate trigger.

Discovery may write only this campaign directory. It may not mutate a sibling
repository, installed plugin, user configuration, or host state.

## Boundary with migration issue #15

This campaign creates and decides the semantic candidate set. It does not
create migration units, estimates, sequencing, dependency order, source
changes, plugin installs, version bumps, or outcome edges.

Only the 51 approved survivors in a fully decided ledger with zero unmatched
packets unlock later migration planning in GitHub issue #15. That planning
permission does not authorize migration units, estimates, sequencing, code, or
implementation. Blocked candidates require a host-capability change before
reconsideration. Later work consumes the approved stable candidate IDs and the
current sanitized host-capability binding.
