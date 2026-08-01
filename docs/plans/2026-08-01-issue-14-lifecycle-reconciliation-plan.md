---
title: Shared Lifecycle Reconciliation Implementation Plan
type: feat
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/14
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-issue-14-lifecycle-reconciliation-plan-doc-review.md
---

# Shared Lifecycle Reconciliation Implementation Plan

## Summary

Make `/outcome`, `/loop`, and `/resume` ask one deterministic function for the earliest required
obligation that repository evidence has not satisfied. Preserve `/outcome`'s existing owner and
manifest checks, keep `/loop`'s current route behavior, and add a read-only `/resume` command-line
entry point. Do not refactor unrelated outcome storage, projection, reporting, GitHub, or Saga-state
modules.

## Requirements

R1. A shared reconciliation result reports whether the workstream is complete and, when it is not,
the earliest unsettled required obligation, its verified settlement state, its declared destination,
and whether operator adjudication is required.

R2. Reconciliation validates the existing lifecycle-obligation contract and transition receipts.
It creates no second schema and treats only `satisfied` as settled.

R3. Required obligations are evaluated in contract order. A valid satisfied receipt preserves
completed work across retries; a conflicting receipt prevents automatic routing even when another
receipt claims satisfaction.

R4. When several non-satisfied receipts exist for one obligation, the result is independent of
receipt order. Conflict has highest precedence, followed by unavailable, degraded, and unsatisfied.
This precedence only selects the reason for stopping; every state still blocks. An unsupported or
unknown settlement value is invalid under the existing closed schema and fails before routing.

R5. `/loop` delegates its existing proof-carrying route to the shared function. Its public helper and
return shape remain compatible.

R6. `/resume` exposes a read-only command-line operation that loads one repository-relative contract
and zero or more repository-relative receipts. It prints the same reconciliation result and never
writes a Saga tick, repository artifact, or remote state. The skill may perform forensic discovery,
but canonical obligations outrank narration, cached phase, and GitHub completion.

R7. `/outcome` retains its leaf-owner and evidence-manifest attestation boundary, then delegates
obligation resolution to the shared function. Its completion barrier includes the shared result in
the verdict and refuses every required state other than `satisfied`.

R8. GitHub facts settle only an obligation whose contract names and verifies that evidence. A closed
issue or merged PR does not settle review, quality assurance, promotion, or another internal gate.

R9. A direct phase invocation remains usable, but without its required canonical evidence and
transition receipt it reconciles as unsettled and cannot support durable completion claims.

R10. Documentation names the shared executable reconciliation path and removes stale claims that
`/resume` is a stub or that committed prose and GitHub can override a conflicting canonical receipt.

## Key Technical Decisions

KTD1. **One new shared module:** `lifecycle_reconciliation.py` owns aggregation, deterministic state
precedence, destination selection, safe repository-reference loading, and a JSON command-line
interface. It imports the existing contract and receipt modules rather than duplicating them.

KTD2. **Thin consumers:** `load_saga_context.py` retains a compatibility wrapper for `/loop`;
`outcome_orchestrator.py` retains its outcome-specific attestation checks and translates the shared
result into a barrier verdict. `/resume` calls the new module directly.

KTD3. **No new durable state:** reconciliation is derived on read. It does not write artifacts,
receipts, ticks, outcome events, GitHub state, or board state. Retrying identical inputs is therefore
idempotent and cannot duplicate canonical content.

KTD4. **Status exposes the shared result without inventing another model:** `outcome.status` adds one
derived-on-read map for proof-carrying nodes by calling the same reconciler. The harvester uses the
same result through its completion barrier. No settlement logic is added to `outcome.py`, and
`outcome_report.py` remains unchanged.

KTD5. **Fixture breadth, implementation restraint:** acceptance scenarios are expressed through
small contract/receipt builders in `test_resume_reconciliation.py` plus focused outcome and loop
assertions. A new fixture directory is unnecessary unless static files make a scenario clearer.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| Resume preserves satisfied work and selects earliest unproven obligation | U1-U2 | focused retry and interrupted-work tests |
| Outcome, loop, and resume agree | U2-U3 | the same contract and receipts are passed through all three consumers |
| Narration or GitHub completion cannot advance internal work | U1-U3 | missing-receipt and wrong-evidence tests |
| Retry creates no duplicate artifact or receipt | U1-U2 | read-only repeat-call and filesystem snapshot assertions |
| Conflict requires operator adjudication | U1-U3 | conflicting receipt test with explicit stop field |
| Direct phase remains non-durable without proof | U1-U2 | no-receipt canonical-output obligation test |
| Command, skill, reference, and agent describe delivered behavior | U4 | plugin validation and documentation tests |

## Implementation Units

### U1. Shared deterministic reconciliation

Create `plugins/saga/scripts/lifecycle_reconciliation.py`. Add an immutable result model, stable state
precedence, obligation-order evaluation, destination selection, repository-relative JSON loading,
and a `reconcile` command-line operation. Invalid paths, contracts, or receipts fail closed with a
non-zero exit and no writes.

### U2. Loop and resume consumers

Turn `load_saga_context.route_earliest_unsettled_required_obligation` into a compatibility wrapper.
Update the resume command, skill, and forensic reference to invoke shared reconciliation before
forensic phase routing. Preserve deep reconstruction only as a discovery aid when no canonical
contract applies.

### U3. Outcome status and completion barrier

After the existing owner and manifest checks in `verified_lifecycle_settlement`, load receipts and
call the shared reconciler. Translate incomplete and conflicting results into an unsatisfied barrier
with the exact obligation, state, destination, and adjudication flag in evidence. Do not change
ordinary GitHub-only leaves. Add the same shared result to `outcome.status` for proof-carrying nodes.

### U4. Documentation, version, and focused acceptance

Update `/outcome`, `/loop`, `/resume`, their shared references, and the lifecycle-router agent. Add
focused cross-consumer tests and bump the Saga plugin to 1.9.0 with a concise changelog entry. Keep
the canonical documentation model unchanged because no command is added or removed.

## Verification

```bash
uv run pytest plugins/saga/tests/test_resume_reconciliation.py plugins/saga/tests/test_loop_routing.py plugins/saga/tests/test_outcome_completion.py -q
uv run pytest plugins/saga/tests/test_saga_plugin.py plugins/saga/tests/test_saga_doc_formatting.py plugins/saga/tests/test_saga_docs_coverage.py -q
uv run ruff check plugins/saga
uv run mypy plugins/saga/scripts
python3 scripts/validate_plugins.py
```

Then run the repository-wide test suite and existing continuous-integration-equivalent checks before
publication.

## Boundaries

- No changes to outcome spec, store, projection, report, GitHub, reconciliation, or lifecycle-state
  modules. `outcome.py` changes only to expose the shared result required by the status acceptance
  criterion.
- No new lifecycle schema, general workflow engine, artifact transaction, dispatcher, or stored phase.
- No direct mutation of canonical artifacts, transition receipts, Saga ticks, GitHub, boards, installed
  plugins, hosts, deployments, or releases.
- One implementation pass, one code review, and one documentation review. Further restructuring
  requires a concrete acceptance failure, not stylistic preference.
