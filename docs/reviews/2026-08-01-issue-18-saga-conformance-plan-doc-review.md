# Deterministic Saga Conformance Laboratory Plan Documentation Review

The issue #18 plan turns the existing deterministic reliability contracts into one privacy-safe,
blocking conformance index without creating another evaluator for those contracts.

## Review Result

| Field | Value |
|---|---|
| Target | `docs/plans/2026-08-01-issue-18-saga-conformance-plan.md` |
| Reviewed revision | working tree based on `4bf7e23` |
| Linked issue | `infiquetra-antigravity-plugins#18` |
| Blocked | no |
| Override | none |

## Applied Findings

| Priority | Status | Finding | Applied fix |
|---|---|---|---|
| P1 | fixed | A new scenario runner could duplicate the contract logic already covered by roughly 1,600 repository tests. | KTD1 limits validators to exact existing pytest nodes; the new code owns metadata, privacy, binding, and orchestration only. |
| P1 | fixed | Automatically marking generated Claude/Codex summaries operator-approved would fabricate the human quality judgment required by R55. | R9 and U3 introduce one explicit Jeff review gate before approval state and binding digest are recorded. |
| P1 | fixed | Invoking arbitrary commands from fixture metadata would turn committed scenarios into a CI code-execution interface. | R6 permits only closed plugin-test pytest node identifiers and one fixed subprocess vector. |
| P1 | fixed | Reusing a baseline after editing its fixture, contract, snapshots, or artifacts could silently compare different work. | R7 binds every reusable identity into one approval digest and makes drift invalid. |
| P2 | fixed | Full prose snapshots would fail on harmless wording and reward artifact presence rather than behavior. | R2, R4, and R8 use semantic predicates and closed summaries for the five quality dimensions. |
| P2 | fixed | A transcript minimizer would create a new private-data processing surface outside the acceptance need. | KTD3 and the boundaries omit ingestion/generation; curation remains local and the committed boundary only validates sanitized outputs. |
| P2 | fixed | Changing `review_canary.py` would couple a review-output scorer to lifecycle settlement and baseline identity. | KTD6 leaves it unchanged for issue #22 to compose later. |

## Formal Issue Rubrics

| Rubric | Result | Evidence |
|---|---|---|
| Acceptance criteria clarity | ready | Each issue criterion maps to a bounded unit and a decisive command or mutation test. |
| Devil's advocate | ready | Private content, drift, arbitrary commands, nondeterminism, stale approval, and proxy scoring fail closed. |
| Specification fidelity | ready | R47, R48, R55, F6 inputs, and AE12 are represented without absorbing live-canary scope. |
| Context completeness | ready | The plan composes all closed dependency contracts and the existing implementation-spec fixture. |
| Issue sizing | ready | One verifier, one fixture index, minimized scenario metadata, one baseline, and one CI job form the complete deterministic layer. |
| Prerequisite mapping | ready | Issues #14 through #23 are closed and their public tests are available as validators. |

## Remaining Findings

No P0, P1, P2, or P3 findings remain.

## Residual Risk

The first fixture's Claude and Codex baselines will be sanitized semantic summaries rather than raw
model transcripts. That is intentional for privacy and deterministic reuse, but Jeff must confirm
that the summaries retain enough depth to serve issue #22's later substantive comparison.
