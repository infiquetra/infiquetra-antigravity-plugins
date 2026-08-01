# Issue #22 Live AGY Canary Code Review

The review covers commit `4bec32dae429bee3adbbbe5d2db588a035cf78f7`, which adds the bounded AGY
release canary, its closed evidence contracts, and the associated documentation.

## Result

No actionable P0, P1, P2, or P3 findings remain. The live run may proceed after the focused checks
and deterministic preflight pass against this commit.

## Applied Findings

| Priority | Finding | Resolution |
|---|---|---|
| P1 | Native AGY plan mode was treated as a read-only security boundary even though the lifecycle must write a durable plan. | Removed native plan mode from only the `live-canary` consumer; retained it for the standalone `saga.plan` consumer and kept sandbox enforcement mandatory. |
| P1 | A run manifest could substitute another repository file for the approved baseline or capability receipt. | Require the exact configured baseline, validate the capability receipt against the current catalog, and re-evaluate the `live-canary` consumer during standalone verification. |
| P1 | The run manifest did not bind the runner implementation that produced it. | Added the runner SHA-256 digest to the closed fixture record and reject stale runner bindings. |
| P1 | Release approval did not require an explicit result for every quality dimension. | Require all five dimensions to be approved, or at least one to be rejected, with a canonical issue #22 decision comment. |
| P2 | A failed phase could consume later model calls before missing output was discovered. | Stop immediately when a phase that owns a canonical artifact produces none. |
| P2 | AGY writes help and plugin-validation output to either standard output or standard error. | Normalize both channels for those bounded observations without retaining them in promoted evidence. |

## Verification Reviewed

- 160 focused tests passed; one unrelated environment-dependent test was skipped.
- The 21-node deterministic conformance selection passed with all 18 scenarios.
- Ruff, mypy, Bandit, and diff whitespace checks passed.
- The controlled preflight passed with AGY 1.1.9, Antigravity 2.3.1, Gemini 3.1 Pro at high
  effort, lifecycle-router execution, conversation resume, plugin checks, and sandbox isolation.

## Residual Risk

The first full live route stopped during `/ideate`; later phases remain unobserved. A replacement run
may stop at another lifecycle gate or produce a mechanically complete but substantively weak result.
The runner stops at the first mechanical failure, and the separate five-dimension operator review
remains release-blocking.

## Live Acceptance Addendum

The first authorized run stopped at `/ideate`: lifecycle-router asked for the seed and repository
paths even though AGY reported the fixture as its working directory. The bounded repair appends the
runtime-only absolute workspace and seed paths to each configured phase instruction. The committed
configuration remains repository-relative and contains no host path. A focused regression test
binds that behavior; no second live run was started by this repair.
