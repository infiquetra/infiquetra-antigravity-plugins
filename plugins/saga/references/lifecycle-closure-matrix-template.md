# Lifecycle Closure Matrix Template

Use one row per stateful entity class. A blank, contradictory, or prose-only cell is a specification
defect. `Not applicable` requires a reason and an invariant that makes the operation impossible.

| Entity class | Origination | Mutation | Revocation or termination | Reads | Events | Audit | Conflict strategy | Retention | Re-grant |
|---|---|---|---|---|---|---|---|---|---|
| `[entity]` | `[creator, preconditions, initial state]` | `[actors, transitions, validation]` | `[actor, terminal state, consequences]` | `[readers, filters, consistency]` | `[published/consumed events and ordering]` | `[who, what, correlation, retention]` | `[winner, concurrency, idempotency]` | `[duration, deletion, legal hold]` | `[whether and how identity/access returns]` |

## Column rules

- **Origination:** name the creator, required inputs, uniqueness rule, initial state, and first
  observable event.
- **Mutation:** list allowed actors, transitions, validation, conditional writes, and rejection
  behavior.
- **Revocation or termination:** define who can end access or state, whether termination is reversible,
  and downstream consequences.
- **Reads:** identify authorized readers, filters, pagination, consistency, and not-found versus
  forbidden behavior.
- **Events:** name every published and consumed event, payload identity, ordering, retry, and
  duplicate handling.
- **Audit:** name actor, action, target, before/after evidence, correlation identity, and retention.
- **Conflict strategy:** state the compare-and-swap, last-write-wins, merge, or rejection rule and its
  observable result.
- **Retention:** define archival, expiration, deletion, tombstones, and legal-hold behavior.
- **Re-grant:** define whether a revoked identity or relationship may return and whether identifiers,
  history, or permissions are reused.

## Closure check

After authoring, sweep every entity row against contracts, endpoint prose, workflows, scenarios, and
operations documents. The same state, actor, error, and event names must appear in every surface. A
matrix cell is not closed merely because it links to a document; the linked rule must exist and agree.
