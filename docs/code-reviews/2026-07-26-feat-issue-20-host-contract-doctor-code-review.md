---
title: Issue 20 Antigravity Host Contract And Capability Doctor Code Review
date: 2026-07-26
target: feat/issue-20-host-contract-doctor
base: origin/main
plan: docs/plans/2026-07-26-antigravity-host-contract-capability-doctor-plan.md
reviewed_revision: 8ed9cdc4141125b1e1a57ce6befcc088718473cc
result: approved
scope_check: clean
---

# Issue 20 Code Review

Scope Check: CLEAN

Verdict: APPROVED. No required-before-merge findings remain.

The implementation delivers the versioned capability catalog and receipt,
bounded probe registry, local diagnostic boundary, active and comparison
host-contract scanner, canonical doctor integration, Saga consumer gates, and
Antigravity-native interaction/state corrections required by issue #20.

## Plan Completion

| Unit | Status | Evidence |
|---|---|---|
| U1 Capability contract | DONE | Closed catalog, schemas, state vocabulary, logical roots, and requested/observed facts are implemented and validated. |
| U2 Bounded probes | DONE | Registered passive and controlled probes fail closed without arbitrary execution. |
| U3 Privacy boundary | DONE | Promotable receipts are closed and non-echoing; rich diagnostics remain ignored, bounded, retained, and purgeable. |
| U4 Host-contract linter | DONE | Canonical active and comparison surfaces produce digest-only findings with narrow content-addressed exceptions. |
| U5 Instruction remediation | DONE | Active Saga interaction and Workflow routing use Antigravity-native language and capability gates. |
| U6 Runtime remediation | DONE | Antigravity state roots, scheduling, isolation, and adjacent runtime assumptions are corrected or gated. |
| U7 Doctor integration | DONE | The canonical validator reports catalog, capability, privacy, and host-contract status and fails required consumers closed. |
| U8 Consumer proof | DONE | Saga adapters consume the shared receipt semantics without translating states. |

## Reviewer Disposition

- Privacy reviewer role digest
  `ac4851075886bfc86fe9103043671463aa88eee81e93f19863c71a9eb359aae9`:
  APPROVE at `8ed9cdc`; 193 focused tests passed and injected traversal
  failures did not echo private paths.
- Devil's advocate reviewer role digest
  `573d1ac6590f0ce85c533b2922e48545b9f81a7b68022f012e2a6ab49a21c1ae`:
  APPROVE at `8ed9cdc`; selector, active traversal, comparison traversal,
  doctor JSON, and human output all failed closed without raw path disclosure.
- All earlier capability, authorization, selector, exception-binding,
  diagnostics, version-normalization, and comparison-corpus findings are
  resolved.
- The concurrent same-user diagnostic-directory replacement proposal is
  non-actionable for this local trust boundary: that principal already has
  direct access to the ignored diagnostic state, while descriptor-relative
  POSIX handling would add portability cost without changing access.

## Checks

- Focused capability, host-contract, and doctor suites: 193 passed.
- Full pytest: 1243 passed, one skipped.
- Ruff lint and format: passed across 165 files.
- Mypy: passed for the changed fleet-core and doctor surfaces.
- Bandit medium/high scan excluding tests: passed.
- Canonical doctor: catalog, capability, receipt privacy, and host contract
  passed; 95 classified findings, zero errors, zero unresolved findings.
- `git diff --check`: passed.

## Residual Risk

- No live AGY host observation was performed. Repository validation correctly
  records host-only capabilities as unavailable; live qualification belongs to
  the separate canary issue.
- The one skipped Saga plugin test is pre-existing and unrelated.

## Required Before Merge

None.
