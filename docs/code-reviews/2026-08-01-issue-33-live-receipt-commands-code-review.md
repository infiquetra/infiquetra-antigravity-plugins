---
title: Issue 33 Live Receipt Commands Code Review
type: code-review
status: complete
date: 2026-08-01
target: working tree after 6a56697d10739b5a6266a99b6032b643054cd16b
verdict: approved
---

# Issue 33 Live Receipt Commands Code Review

## Verdict

APPROVED. The repair is limited to command adapters around the existing receipt contracts, installed
plugin discovery instructions, and the controlled issue #22 fixture. No actionable P0 through P3
finding remains after one remediation pass and one targeted recheck.

## Review scope

- Deliberation receipt command and write-once persistence.
- Transition receipt command and typed evidence loading.
- Artifact promotion command and staged-file containment.
- Installed-plugin command instructions across the reference lifecycle.
- Bound live-canary obligation contract, phase prompt, artifact and receipt discovery.
- Package versions, host-contract annotations, tests, and operator boundaries.

## Findings and disposition

| Priority | Status | Finding | Resolution |
|---|---|---|---|
| P1 | fixed | `ObligationContract.from_dict()` raises the base `ObligationError`, which the first transition command caught only as its narrower `TransitionReceiptError` subclass. A malformed contract could therefore print a traceback. | The command now catches the contract base error and returns sanitized exit status 2. A subprocess regression test proves no traceback escapes. |
| P1 | fixed | The phase prompt initially assigned every route item a transition obligation. `/resume` has no artifact obligation, so the prompt named a nonexistent `resume` obligation. | Receipt instructions are appended only for phases in the artifact map. A regression assertion keeps `/resume` receipt-free. |
| P2 | fixed | The first skill snippets contained shell angle-bracket placeholders. Copying them literally could invoke redirection rather than the helper. | Skills now run only safe helper-existence checks and direct the worker to the shared reference containing every required flag and input shape. |
| P2 | fixed | Receipt discovery matched filename text, but canonical receipt identities are hashes stored below typed receipt directories. Valid command output would remain invisible. | The collector now recognizes canonical deliberation, transition, and promotion directories while retaining legacy filename patterns. The no-remote integration test proves all three groups are found. |
| P2 | fixed | The live canary artifact map omitted `docs/work-sessions/`, even though `/work` is an artifact-producing reference phase. | `work` now participates in artifact binding and in the exact ten-obligation contract validation. |
| P3 | fixed | Legitimate edits to four historically annotated skills invalidated their whole-file digest allowlist entries. | The allowlist source digests were refreshed without changing the historical line digests or classification. The host-contract validator reports zero unresolved findings. |

## Checks reviewed

- Full repository test suite: 1,634 passed, 1 skipped.
- Receipt, canary, schema, package, formatting, and host-contract selection: 250 passed, 1 skipped.
- Targeted post-remediation receipt, canary, and host-contract checks: 105 passed.
- Ruff lint and format: passed.
- mypy: passed.
- Bandit: changed executable files passed with no findings. The repository-wide scan remains noisy
  with pre-existing assertions and findings outside this defect's executable diff.
- Antigravity plugin doctor: passed; installed-link warnings are expected because development remains
  in the isolated issue worktree under the explicit no-install boundary.

## Residual risk

Deterministic tests prove that the installed-plugin command contract can create and discover the full
receipt chain. They do not prove that the live Antigravity worker will follow the revised instructions.
That remaining risk is exactly what the separately approved replacement canary must test after the
new plugin bytes are installed.
