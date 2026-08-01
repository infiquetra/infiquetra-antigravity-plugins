# Lifecycle Obligation and Transition Receipt Contract

Saga uses two versioned JSON-compatible contracts to decide whether a named lifecycle obligation is settled. The contracts record evidence; they do not route commands, dispatch workers, merge PRs, or mutate GitHub.

## Contract identities

| artifact | schema identity | runtime module |
|---|---|---|
| workstream obligation contract | `saga.lifecycle-obligation.v1` | `scripts/lifecycle_obligations.py` |
| attempted transition receipt | `saga.transition-receipt.v1` | `scripts/transition_receipts.py` |

Version 1 is the first supported version. A schema-less record or any unrecognized version fails closed. Future compatibility requires an explicit upgrader; consumers must not silently reinterpret stored fields.

## Lifecycle boundary

The forward workstream contract recognizes the stored phases `ideation`, `brainstorm`, `plan`, `review`, `work`, and `qa`. `/impl-spec` and `/retro` are off-chain obligations and are represented by `off-chain-ceremony` obligations, not by adding stored phases.

The generic Saga envelope retains legacy compatibility outside this contract. Routing and migration of legacy envelopes are deferred to the lifecycle-integration issue.

## Settlement

| state | meaning |
|---|---|
| `satisfied` | every declared primary evidence rule passed |
| `unsatisfied` | required evidence is missing, unverified, wrongly scoped, self-authored, or digest-invalid |
| `degraded` | an optional obligation used its predeclared fallback evidence |
| `unavailable` | the named evidence source is unknown or unavailable |
| `conflicting` | authorities disagree, a producer claim disagrees with computed settlement, or a receipt cannot be reconciled |

A required obligation settles only as `satisfied`. A required obligation cannot declare a degraded fallback. Execution, review, and quality-assurance evidence must be independent of the obligation producer.

## Evidence authority

Every evidence item identifies its role, subject, producer, reference, SHA-256 digest, and verification state. Repository evidence is authoritative only when its normalized repository-relative path resolves to a regular file and the file bytes match the declared digest. External GitHub state is one typed evidence role and can satisfy only an `external-github` obligation.

Independent execution, review, and quality-assurance evidence must reference a closed `saga.independent-evidence-receipt.v1` JSON object. The receipt binds its producer and attester identities, subject, evidence kind, artifact digest, and origin into `receipt_id`. A Saga-host-created receipt is accepted only with a passing `agy.agent.execution` capability. An imported external receipt must carry no host-capability claim and is reported as imported evidence, not as host-created independence.

Free-form narration, a receipt's claimed settlement, issue closure, and PR merge are not aggregate proof of other obligations.

## Transition receipt

Every receipt carries all evidence categories as explicit arrays, even when a category is empty:

- input references;
- operator decisions;
- execution receipts;
- canonical outputs;
- check and quality-assurance results;
- review findings;
- lifecycle, ceremony, deliberation, fallback, and handoff evidence;
- external GitHub facts.

The receipt identity is derived from normalized contract, transition, obligation, attempt, decision, and evidence inputs. Rebuilding unchanged inputs produces the same identity. Canonical receipts live at `docs/outcomes/<outcome-id>/receipts/<receipt-id>.json`; identical writes are idempotent and different bytes at an existing identity are a conflict.

## Integration boundary

Outcome nodes may point to one obligation contract and zero or more transition receipts. Issue #21 adds those references without changing the current completion barrier. `/outcome`, `/loop`, and `/resume` integration is owned by the routing child.

## Installed-plugin command

From a target repository, run `transition_receipts.py build` through the installed Saga plugin with
one explicit contract and one closed evidence JSON object. The complete command and evidence category
shape are documented in `references/live-receipt-commands.md`. The command never infers evidence from
phase narration.
