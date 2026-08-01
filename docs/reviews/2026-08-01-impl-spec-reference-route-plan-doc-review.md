# Impl-Spec and Reference Route Documentation Review

The issue #17 plan adapts the approved 2026 `/impl-spec` design to the current Antigravity receipt,
promotion, and lifecycle contracts without reviving deferred `/product-review` scope.

## Review Result

| Field | Value |
|---|---|
| Target | `docs/plans/2026-08-01-impl-spec-reference-route-plan.md` |
| Reviewed revision | working tree based on `c7fd034` |
| Linked issue | `infiquetra-antigravity-plugins#17` |
| Blocked | no |
| Override | none |

## Applied Fixes

| Priority | Status | Finding | Applied fix |
|---|---|---|---|
| P1 | fixed | The 2026 plan bundled `/product-review`, but the current issue explicitly defers that capability and dispatch entry. | The plan contains only `/impl-spec`, reusable buildability probing, promotion, and the reference route; R10 and the boundaries forbid `/product-review`. |
| P1 | fixed | The old plan treated `define_subagent` as proof of fresh independent execution. | R5 and KTD4 require observed host capability receipts and allow only a narrowly named isolated-sequential document fallback. |
| P1 | fixed | Instruction-only README parsing could not prove that a missing contract stops rather than being invented. | KTD1 and U1 add a deterministic closed profile/table parser and negative fixtures. |
| P1 | fixed | Promoting many files independently did not define when the spec set itself became complete. | KTD5 makes a content-addressed set manifest the final promoted artifact and `/plan` input. |
| P2 | fixed | The old buildability mode described prose output but not a machine-checkable hard verdict. | KTD1 and U1 validate the exhaustive category shape and derive PASS only at zero boundary-test defects. |
| P2 | fixed | Adding a command wrapper without the canonical docs model would leave manuals and visuals stale. | KTD6 and U4 update the existing model and regenerate its current assets. |

## Formal Issue Rubrics

| Rubric | Result | Evidence |
|---|---|---|
| Acceptance criteria clarity | ready | Every issue criterion maps to a unit and decisive test. |
| Devil's advocate | ready | Missing schema, false isolation, partial spec sets, gate collapse, and implicit mutation fail closed. |
| Specification fidelity | ready | The plan retains the six-stage pipeline, profile backing, off-chain behavior, bounded probe, promotion, and later readiness review. |
| Context completeness | ready | Closed dependencies #19, #21, and #23 are consumed through their public receipt contracts. |
| Issue sizing | ready | Four units deliver one command and its deterministic, host, route, and package surfaces. |
| Prerequisite mapping | ready | `/impl-spec` is selected now because all three hard dependencies are merged. |

## Remaining Findings

No P0, P1, P2, or P3 findings remain.

## Residual Risk

The accepted Markdown folder-contract table is intentionally strict. Existing context-library
READMEs with a different shape will return `unavailable` until an explicit profile points at a
compatible contract; the implementation must not add heuristic invention to hide that mismatch.
