# Issue 18 Deterministic Saga Conformance Code Review

This review covers the issue #18 conformance verifier, fixture corpus, baseline binding, tests, CI,
and package changes.

## Review Result

| Field | Value |
|---|---|
| Target | `feat/issue-18-saga-conformance` working tree |
| Base | `4bf7e23` |
| Linked issue | `infiquetra-antigravity-plugins#18` |
| Blocked | no |
| Override | none |

## Applied Findings

| Priority | Status | Finding | Applied fix |
|---|---|---|---|
| P1 | fixed | Scenario metadata and fixture revision could remain unchanged while an exact pytest validator or static input changed underneath them. | The fixture now binds every deduplicated validator source and static input by repository-relative path and SHA-256 digest; every scenario reference must belong to one of those tables. |
| P1 | fixed | Treating the generated Claude/Codex summaries as approved would fabricate the operator-quality judgment required by R55. | The manifest remained `pending` until Jeff approved the summaries; it now binds that approval to the exact fixture, contract, source snapshots, and artifacts. |
| P1 | fixed | A general command field in scenario metadata could turn the fixture corpus into a CI command-execution surface. | The closed validator accepts only exact plugin-test pytest nodes and executes one fixed `uv run --frozen python -m pytest ... -q` vector without a shell. |
| P2 | fixed | The first subprocess vector used the invoking system Python, so the documented `python3` command missed dependencies installed in the repository environment. | The verifier now enters the locked uv environment through a fixed vector; the documented command passes from a normal shell and in CI. |
| P2 | fixed | Fixture and baseline validation could echo private content through parser or sanitizer errors. | Errors report only the contract field or privacy rule class; tests inject private paths and fields and assert the rejected value is absent. |
| P2 | fixed | A stale or invented approval reference could satisfy a non-empty-string check. | Approval now requires a UTC timestamp, the operator role, a canonical issue or issue-comment URL, and the binding digest. |
| P2 | fixed | A baseline could omit one substantive comparison dimension while retaining valid artifact files. | Both artifacts use a closed five-dimension contract for depth, evidence use, seed retention, adjudication, and lifecycle completeness. |

## Acceptance Evidence

- The reference fixture indexes 18 scenarios and executes 21 deterministic pytest cases in one
  subprocess.
- Required success and failure scenario identifiers are exact and closed.
- Fixture, scenario-set, validator-source, input-source, semantic-contract, provider-snapshot, and
  artifact identities are digest-bound.
- Private fields and promoted-content hazards fail before scenario execution or baseline reuse.
- The verifier exposes no model, network, arbitrary shell, or transcript-ingestion command.
- CI has a separate conformance job, and plugin publishing depends on it.

## Remaining Findings

No code P0, P1, P2, or P3 findings remain. Jeff approved the baseline summaries, and the manifest
records the canonical approval reference and binding digest.

## Residual Risk

An exact pytest node remains a semantic validator maintained by humans. The source digest makes any
change invalidate the approved fixture, but review is still required to decide whether an updated test
preserves the intended operator correction before increasing the fixture revision.
