---
title: Canonical Artifact Promotion Implementation Plan
type: feat
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/23
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-canonical-artifact-promotion-plan-doc-review.md
---

# Canonical Artifact Promotion Implementation Plan

## Summary

Add one local-only promotion transaction that copies a staged lifecycle document into an approved
repository `docs/` location, binds it to an existing Saga transition receipt, and writes a
deterministic promotion receipt. An unchanged retry is idempotent. A predecessor mismatch preserves
the canonical document and a repository conflict copy, then returns `conflicting` for operator
adjudication.

## Requirements

R1. Canonical lifecycle documents must resolve inside an approved repository `docs/` family. The
target and every existing parent must be ordinary paths, not symlinks.

R2. Promotion must bind the source phase, logical staging role, staged and predecessor digests,
canonical target, transition receipt path and digest, historical-import state, and final settlement
in a closed, versioned receipt.

R3. A successful first write and an unchanged retry must produce the same canonical document,
promotion identity, and receipt path without duplicate state or ledger entries.

R4. If the current canonical digest differs from the caller's expected predecessor, promotion must
not overwrite it. The staged candidate must be preserved under the outcome conflict directory, the
receipt must be `conflicting`, and operator adjudication must be required.

R5. Content sanitization must run before any repository write and reject absolute home paths,
credential-shaped values, private hostnames, and transcript payload markers without echoing unsafe
content in errors.

R6. A historical brain-only import may preserve content and source provenance, but its promotion
receipt must not claim execution, review, quality-assurance, or operator evidence that was not
supplied as verified repository references.

R7. Explicit abandonment is valid only for unfinished exploration. It must report that the work is
not phase-complete, resumable, handoffable, or outcome-settled and must write no canonical artifact.

R8. Promotion performs local file operations only. It must not run Git, GitHub, deployment, or other
remote commands. An optional runtime projection is a disposable pointer to canonical evidence.

## Key Technical Decisions

KTD1. **One new standard-library module:** `artifact_promotion.py` owns validation, sanitization,
write-once helpers, promotion and conflict receipts, and terminal abandonment. It does not add a
database, transaction manager, network client, or dependency.

KTD2. **Recoverable two-file transaction:** the canonical document is created write-once before the
receipt. The document alone never settles the obligation. If receipt persistence is interrupted, an
unchanged retry recognizes the canonical digest and completes the same deterministic receipt.

KTD3. **Conflict copies are repository evidence:** a predecessor mismatch keeps the existing target
unchanged and creates a content-addressed candidate under
`docs/outcomes/<outcome>/conflicts/`. The receipt names both digests and requires an operator
decision; no timestamp or file length chooses a winner.

KTD4. **Consume existing transition receipts:** the module parses and validates
`saga.transition-receipt.v1`, requires it to resolve inside the repository, and binds its digest. It
does not introduce another lifecycle evaluator or change issue #21's state vocabulary.

KTD5. **Keep evidence claims closed:** callers may bind only explicit repository references for
`execution`, `review`, `qa`, and `operator` evidence. Historical imports serialize absent kinds as
absent and remain `unsatisfied` until their declared required evidence is present.

KTD6. **Do not retrofit unrelated stores:** the promotion receipt is the durable provenance record.
`provenance_manifest.py`, `run_ledger.py`, `outcome_store.py`, and `lifecycle_state.py` remain
unchanged because their existing responsibilities do not improve this transaction.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| Canonical document plus receipt are required | U1 | first-promotion and interrupted-retry tests |
| Unchanged retries create no duplicate state | U1 | stable identity and single receipt-path assertions |
| Divergent predecessor preserves both sides | U1 | conflict-copy and no-overwrite test |
| Brain-only imports cannot fabricate evidence | U1 | historical-import negative tests |
| Terminal no-save is narrow and non-settling | U1 | abandonment validation and no-write tests |
| Unsafe paths and promoted content fail closed | U1-U2 | path, symlink, credential, hostname, home-path, and transcript fixtures |
| No remote mutation occurs | U1 | source audit and monkeypatched command-boundary test |

## Implementation Units

### U1. Implement the promotion contract and transaction

Create the closed receipt model and local transaction in
`plugins/saga/scripts/artifact_promotion.py`, with the operator contract in
`plugins/saga/references/artifact-promotion-contract.md`.

The transaction will validate the transition receipt first, sanitize staged bytes, resolve the
target, compare predecessor state, create either the canonical artifact or conflict copy write-once,
persist the deterministic receipt, and optionally write a disposable projection pointer.

Proof: `test_artifact_promotion.py` covers successful promotion, idempotent retry, partial recovery,
conflict preservation, historical import, abandonment, invalid paths, sanitization, missing
transition evidence, and local-only mutation.

### U2. Bind lifecycle skills and package the feature

Add a short canonical-promotion rule to the nine lifecycle artifact-producing skills named in issue
#23. Update Saga package metadata and its changelog to version 1.7.0. Extend existing packaging and
documentation-contract tests without changing phase behavior.

Proof: package tests require the new module and contract; skill tests require repository authority
and prevent brain/runtime paths from claiming durable completion.

## Verification

Run narrow checks first:

```bash
uv run pytest plugins/saga/tests/test_artifact_promotion.py -q
uv run pytest plugins/saga/tests/test_saga_plugin.py plugins/saga/tests/test_saga_doc_formatting.py -q
uv run ruff check plugins/saga/scripts/artifact_promotion.py plugins/saga/tests/test_artifact_promotion.py
uv run mypy plugins/saga/scripts/artifact_promotion.py
python3 scripts/validate_plugins.py
```

Then run the whole repository test suite and the repository-wide lint, formatting, type, and
security gates before publication.

## Boundaries

- No remote mutation, host deployment, installed-plugin change, release tag, or new dependency.
- No lifecycle routing, run-ledger, outcome-store, or general manifest redesign.
- No attempt to make local files resistant to a malicious same-user process; the contract prevents
  accidental overwrite, path escape, partial settlement, and privacy promotion.
- Any requirement for a new cross-process database, distributed lock, or remote artifact service
  requires operator review rather than expansion of this issue.
