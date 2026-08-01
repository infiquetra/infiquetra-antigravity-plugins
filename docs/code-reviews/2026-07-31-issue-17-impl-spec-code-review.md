# Issue 17 Impl-Spec Code Review

The issue #17 implementation adds the profile-backed `/impl-spec` route without changing stored Saga
phases or introducing remote mutation.

## Review Result

| Field | Value |
|---|---|
| Scope | Issue #17 changes on `feat/issue-17-impl-spec-route` |
| Base | `c7fd034` on `main` |
| Excluded | Operator-owned `.serena/project.yml` |
| Verdict | ready |
| Unresolved P0-P3 findings | none |

## Applied Findings

| Priority | Status | Finding | Repair |
|---|---|---|---|
| P1 | fixed | The first draft did not explain how authors could validate staged documents without writing canonical `docs/specs/` content before the promotion transaction. | The skill now requires an ignored mirrored workspace. Stages 2 through 6 operate only there, and promotion is the first canonical write. Structural tests preserve that boundary. |
| P2 | fixed | A folder contract could repeat the same required file, producing duplicate manifest rows and ambiguous completeness evidence. | The parser now rejects duplicate required files per folder and has a negative test. |
| P2 | fixed | The first focused tests proved the deterministic parser and verdict, but did not directly preserve every six-stage, independence, routing, and no-product-review instruction. | Structural acceptance tests now cover the stage sequence, native or isolated fallback, three-round cap, staging boundary, promotion, `/plan`, later `/doc-review`, and absent `/product-review` route. |

## Verification

- Repository tests: 1,589 passed, one intentionally skipped.
- Ruff: clean across the repository.
- MyPy: clean across 229 source files.
- Bandit: clean for the four changed Python modules.
- Plugin validation: passed; Saga exposes 22 skills and 24 commands, with zero unresolved host-contract findings.
- `git diff --check`: clean.

## Residual Risk

The folder-contract parser intentionally accepts one exact Markdown table shape. Repositories with a
different README format stop as unavailable; this is the issue's fail-closed behavior, not an
automatic schema-conversion feature.
