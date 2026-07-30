---
title: Lifecycle Obligation and Transition Receipt Contracts Implementation Plan
type: feat
status: active
date: 2026-07-30
origin: docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md
deepened: 2026-07-30
reviewed: 2026-07-30
review_status: ready
review_artifact: docs/reviews/2026-07-30-lifecycle-obligation-transition-receipts-plan-doc-review.md
---

# Lifecycle Obligation and Transition Receipt Contracts Implementation Plan

## Summary

Add one versioned lifecycle-obligation contract and one versioned transition-receipt contract to the Saga plugin. The new shared evaluator will decide whether an obligation is satisfied, degraded, or still unsettled from independent evidence, while leaving command routing and full lifecycle integration to later outcome work.

---

## Problem Frame

Saga currently stores lifecycle phase, readiness, and execution state, but it does not have a shared contract for the obligations that permit a transition. A closed GitHub issue or merged PR can therefore be mistaken for proof that implementation, review, quality assurance, or an off-chain ceremony actually occurred. The current stores also lack one durable, versioned receipt that binds inputs, operator decisions, execution evidence, canonical outputs, checks, review findings, and settlement.

GitHub issue #21 owns requirements R25-R28, R30, and R32 from the Antigravity Saga reliability requirements. It establishes the contract consumed later by `/outcome`, `/loop`, `/resume`, artifact promotion, deliberation, and conformance work. It does not own those routing integrations.

---

## Requirements

### Obligation contract

R1. A strict, JSON-compatible `saga.lifecycle-obligation.v1` contract must describe stored lifecycle phases, off-chain `/impl-spec` and `/retro` obligations, required and optional gates, canonical artifacts, checks, quality assurance, reviewers, deliberation and fallback rules, handoffs, and external GitHub facts. Version 1 is the first supported contract: schema-less legacy input, unknown versions, and unknown fields must fail closed with an actionable error. Covers origin R25, R27, and R32.

R2. Every obligation must declare whether it is required or optional before execution. A required obligation may settle only as `satisfied`; an optional obligation may settle as `degraded` only when the contract predeclares that state and names its fallback evidence. Covers origin R25, R28, and acceptance example AE7.

R3. The evaluator must use the closed settlement vocabulary `satisfied`, `unsatisfied`, `degraded`, `unavailable`, and `conflicting`. Missing, contradictory, wrongly scoped, or untrusted evidence must remain distinguishable instead of collapsing into success. Covers origin R26 and R28.

### Evidence and transition receipts

R4. A strict, JSON-compatible `saga.transition-receipt.v1` receipt must bind contract identity, transition identity, evaluated obligation, input references, operator decisions, actual execution receipts, canonical output references, check results, review findings, external facts, and the claimed settlement. Covers origin R26, R27, and R30.

R5. Evidence must carry stable identity, producer, subject, kind, reference, digest, and verification-state fields. Repository evidence must resolve to an existing repository-relative file whose bytes match its digest; an unresolved, missing, or mismatched reference cannot satisfy an obligation. An obligation's own producer statement cannot independently satisfy its execution, review, or quality-assurance gate, and a receipt's claimed settlement cannot override the evaluator's result. Covers origin R28 and acceptance example AE9.

R6. A closed GitHub issue or merged PR is evidence only for its declared external-fact obligation. It cannot satisfy missing repository artifacts, checks, reviews, execution receipts, or off-chain ceremonies. Covers origin R28 and the issue acceptance criteria.

R7. Receipt persistence must be repository-local, atomic, and idempotent. Re-evaluating unchanged inputs must return the existing receipt without adding another file; attempting to reuse a receipt identity for different content must return a conflict. Covers origin R26 and the issue acceptance criteria.

### Compatibility and integration boundary

R8. Stored lifecycle phases remain those defined by `lifecycle_state.py`; `/impl-spec` and `/retro` remain representable off-chain obligations and must not be added as stored phases. Covers origin R25 and R32.

R9. Outcome nodes may refer to an obligation contract and zero or more transition receipts through additive typed fields. Existing outcome specifications without those fields must continue to load and round-trip unchanged. Covers origin R27 and R30.

R10. The contracts and evaluator must use the Python standard library and repository conventions, remain deterministic and side-effect-free except for the explicit receipt writer, and pass focused tests plus the canonical plugin validator. No new runtime dependency is permitted. Covers origin R30.

---

## Key Technical Decisions

KTD1. **Use strict Python validation over a runtime JSON Schema dependency:** the canonical reference JSON files document the wire contracts, while dataclass constructors and closed allowed-key checks enforce them at runtime. Version 1 is the first supported receipt, so current v1 input is accepted while schema-less legacy and future unknown versions fail closed; future migrations require an explicit upgrader rather than silent reinterpretation. This follows `plugins/saga/scripts/provenance_manifest.py` and avoids promoting the development-only `jsonschema` package into the installed plugin.

KTD2. **Keep obligation settlement separate from lifecycle state:** `lifecycle_obligations.py` owns the five settlement states and validates phase or off-chain obligation kinds against `lifecycle_state.py`. Adding `/impl-spec` or `/retro` to stored lifecycle phases would falsify the existing three-axis state model.

KTD3. **Make evidence authoritative by declared role, scope, verification, and independence:** the evaluator matches evidence to an obligation's required evidence kinds and subject, verifies repository references and digests, and rejects producer overlap where independent execution, review, or quality-assurance evidence is required. External facts carry an explicit verification state; `unknown` or `unavailable` source input cannot satisfy a gate. Free-form notes and a receipt's own settlement claim are never authoritative.

KTD4. **Treat external GitHub state as one evidence category:** issue closure and PR merge facts can satisfy only an obligation explicitly typed `external-github`. They never imply that artifacts, checks, reviews, or ceremonies exist.

KTD5. **Write canonical receipts beneath the outcome artifact tree:** transition receipts live at `docs/outcomes/<outcome-id>/receipts/<receipt-id>.json`, use atomic create-or-compare behavior, and are suitable for Git review. `outcome_store.py` remains a rebuildable cache and `run_ledger.py` remains local telemetry, so neither becomes a second receipt authority.

KTD6. **Add references to outcome nodes without activating the new gate:** `obligation_contract_ref` and `transition_receipt_refs` are optional typed fields in `outcome_spec.Node`. Full completion-barrier and command routing changes remain owned by GitHub issue #14.

KTD7. **Keep the implementation within one planned leaf:** one directly blocking or implementation-caused defect and one targeted recheck are allowed. A second-order workstream, new dependency, public-contract redesign, outcome-edge change, speculative hardening, merge, or deployment requires operator approval.

KTD8. **Derive receipt identity from normalized transition inputs:** the receipt ID is a stable digest of the contract, transition, obligation, decisions, and evidence identities, excluding presentation metadata. The same attempted transition therefore addresses the same file, while different evidence produces a new identity and divergent bytes at an existing identity are a conflict.

---

## High-Level Technical Design

The new modules form a pure contract-and-evaluation layer with one explicit persistence edge.

```text
saga.lifecycle-obligation.v1
        |
        v
strict contract loader -----> evidence matcher -----> computed settlement
                                    ^                         |
                                    |                         v
saga.transition-receipt.v1 --------+------------> validate claimed settlement
                                                              |
                                                              v
                                docs/outcomes/<id>/receipts/<receipt-id>.json

OutcomeSpec.Node
  obligation_contract_ref ----------> contract artifact
  transition_receipt_refs ----------> canonical receipt artifacts
```

An obligation selects one evidence category and may name additional required evidence kinds. Evidence matching is exact by subject and kind. Required independent roles are checked against the obligation producer and against one another where the contract requires distinct producers. The evaluator derives the settlement; the serialized receipt preserves both the claimed and computed values so disagreement is visible as `conflicting`.

The initial obligation kinds are closed:

| obligation kind | what it represents | decisive evidence |
|---|---|---|
| `stored-phase` | a transition in the stored lifecycle state machine | canonical lifecycle-state reference |
| `off-chain-ceremony` | `/impl-spec` or `/retro` completion | canonical ceremony artifact or receipt |
| `gate` | a required or optional decision gate | operator or gate receipt |
| `artifact` | a canonical output exists with expected identity | artifact reference and digest |
| `check` | a named deterministic check ran | execution/check receipt |
| `quality-assurance` | the workstream's declared quality acceptance obligation | independent QA receipt and named results |
| `review` | an independent review occurred | reviewer finding or verdict receipt |
| `deliberation` | required independent deliberation or declared fallback | deliberation receipt or predeclared fallback |
| `handoff` | responsibility transferred with an acknowledged reference | handoff receipt |
| `external-github` | an issue or PR reached a named state | typed GitHub fact |

---

## Requirement and Acceptance Traceability

| requirement | implementation units | decisive proof |
|---|---|---|
| R1-R3 | U1, U2 | strict contract tests cover every obligation kind, state, required/optional rule, unknown key, and unknown schema |
| R4-R6 | U1, U2 | receipt tests bind every evidence category; self-proof, conflicting claims, and GitHub-only false settlement fail |
| R7 | U2 | repeated identical writes return one path; divergent content at the same identity conflicts |
| R8 | U1, U4 | lifecycle phase tests preserve stored and off-chain vocabularies |
| R9 | U3 | old and new outcome specs parse and round-trip; typed refs reject unsafe or malformed values |
| R10 | U1-U4 | focused tests, Ruff, mypy, and the canonical plugin validator pass without a dependency change |

---

## Implementation Units

### U1. Define the lifecycle obligation and receipt wire contracts

Create the closed schemas, typed models, and validation rules that all later evaluation uses.

**Goal:** Establish deterministic loaders and serializers for `saga.lifecycle-obligation.v1` and `saga.transition-receipt.v1`.

**Requirements:** R1-R5, R8, R10; origin R25-R28, R30, R32.

**Dependencies:** None.

**Files:**

- `plugins/saga/references/lifecycle-obligation-contract.md`
- `plugins/saga/references/lifecycle-obligation-schema.json`
- `plugins/saga/references/transition-receipt-schema.json`
- `plugins/saga/scripts/lifecycle_obligations.py`
- `plugins/saga/scripts/transition_receipts.py`
- `plugins/saga/tests/test_lifecycle_obligations.py`
- `plugins/saga/tests/test_transition_receipts.py`
- `plugins/saga/tests/fixtures/lifecycle-obligations/`

**Approach:** Add frozen dataclasses and strict `from_dict`/`to_dict` functions with explicit allowed-key sets, identifier and repository-relative-path validation, closed enums, ordered normalization, and actionable validation errors. Import stored and off-chain phase vocabularies from `lifecycle_state.py` rather than copying them. Keep the reference JSON schemas and runtime validators aligned with shared fixtures, including current v1, schema-less legacy, and future-version cases.

**Patterns to follow:** Mirror the versioned schema, frozen dataclasses, and closed field validation in `plugins/saga/scripts/provenance_manifest.py`. Reuse identifier and repository-path constraints already present in `plugins/saga/scripts/outcome_spec.py`.

**Test scenarios:**

- Happy path: load and round-trip one contract containing every obligation kind and one receipt containing every evidence category; expect byte-stable normalized dictionaries.
- Edge case: model `/impl-spec` and `/retro` as off-chain ceremonies; expect both to validate without appearing in stored lifecycle phases.
- Failure path: supply a schema-less legacy receipt, unknown future schema, unknown field, duplicate obligation ID, absolute path, traversal, invalid digest, invalid state, or required obligation with a degraded fallback; expect a specific validation error.
- Failure path: omit each required receipt evidence category in turn; expect receipt validation to identify the missing category.

**Verification:** Both reference schemas have runtime fixture coverage, all closed vocabularies are tested, and unchanged objects round-trip deterministically.

### U2. Implement settlement evaluation and idempotent receipt persistence

Derive settlement from evidence and persist exactly one canonical receipt for unchanged inputs.

**Goal:** Make required, optional, degraded, unavailable, conflicting, and independent-evidence behavior executable.

**Requirements:** R2-R7, R10; origin R26, R28, R30, AE7, AE9.

**Dependencies:** U1.

**Files:**

- `plugins/saga/scripts/lifecycle_obligations.py`
- `plugins/saga/scripts/transition_receipts.py`
- `plugins/saga/tests/test_lifecycle_obligations.py`
- `plugins/saga/tests/test_transition_receipts.py`
- `plugins/saga/tests/test_outcome_completion.py`

**Approach:** Implement an evaluator that returns a typed result and explanation without trusting the receipt's claimed settlement. Required obligations settle only when all declared evidence matches the subject, kind, verification, authority, and independence rules. For repository evidence, a bounded local resolver must prove that the repository-relative path exists as a regular file and its SHA-256 digest matches; external facts must already carry an accepted verification state. Optional obligations may degrade only through their predeclared fallback. Derive receipt identity from normalized transition inputs, then use an atomic create-or-compare writer beneath the canonical outcome receipt directory and reject same-ID divergent content.

**Patterns to follow:** Use the write-once comparison semantics in `plugins/saga/scripts/outcome_store.py`, but write to the tracked outcome artifact tree rather than its Git-common-directory cache. Follow the pure decision/result split in `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py`.

**Test scenarios:**

- Happy path: provide independent execution, check, review, artifact, and operator-decision evidence; expect a required obligation to compute `satisfied`.
- Edge case: re-evaluate and write identical inputs twice; expect the same receipt path and one file.
- Failure path: reuse the receipt ID with changed inputs; expect `conflicting` and no overwrite.
- Failure path: let an obligation producer author its own execution, review, or quality-assurance evidence; expect `unsatisfied`.
- Failure path: reference a missing repository file, a directory, a digest-mismatched file, or an external fact whose source state is `unknown` or `unavailable`; expect the obligation not to settle.
- Failure path: provide a closed GitHub issue or merged PR without required repository evidence; expect the external fact alone to settle only its own obligation.
- Failure path: provide independently verified authorities that assert incompatible facts for the same subject; expect `conflicting`.
- Failure path: claim `satisfied` in a receipt whose evidence computes another state; expect the receipt evaluation to report `conflicting`.
- Degraded path: omit optional primary evidence and provide its exact predeclared fallback; expect `degraded`. The same evidence on a required obligation remains `unsatisfied`.

**Verification:** The evaluator's state is reproducible from serialized inputs, no self-authored assertion crosses an independence gate, and idempotent persistence cannot duplicate or overwrite a receipt.

### U3. Add typed outcome references without changing routing

Let outcome specifications point to the new canonical artifacts while preserving all existing specifications.

**Goal:** Add an additive bridge from outcome nodes to obligation contracts and transition receipts.

**Requirements:** R6, R9, R10; origin R27 and R30.

**Dependencies:** U1, U2.

**Files:**

- `plugins/saga/scripts/outcome_spec.py`
- `plugins/saga/tests/test_outcome_spec.py`
- `plugins/saga/tests/test_outcome_completion.py`

**Approach:** Add optional `obligation_contract_ref` and `transition_receipt_refs` fields to `Node`, validate them as normalized repository-relative paths, serialize them only when present, and leave completion behavior unchanged. Add a conformance fixture proving that a closed GitHub leaf with only an external fact remains unsettled under the contract evaluator.

**Patterns to follow:** Preserve the additive optional-field parsing and deterministic serialization conventions in `plugins/saga/scripts/outcome_spec.py`. Keep the existing completion barrier in `plugins/saga/scripts/outcome_orchestrator.py` intact.

**Test scenarios:**

- Happy path: parse and round-trip a node with one contract reference and multiple receipt references; expect stable ordering and content.
- Compatibility: parse and round-trip existing outcome fixtures without the new fields; expect no output drift.
- Failure path: provide an absolute path, traversal, duplicate receipt reference, or non-string value; expect validation failure.
- Integration: close a GitHub leaf while omitting repository artifact, check, or review evidence; expect the contract evaluator to leave those obligations unsettled without changing current router behavior.

**Verification:** Existing outcome specification tests remain green, new typed references are strict and additive, and no routing or completion code changes.

### U4. Document, version, and validate the shared contract

Publish the contract semantics and record the design boundary for downstream issue work.

**Goal:** Make the new contract discoverable, reviewable, and consumable by later outcome leaves.

**Requirements:** R1, R8, R10; origin R25, R30, and R32.

**Dependencies:** U1-U3.

**Files:**

- `plugins/saga/README.md`
- `plugins/saga/CHANGELOG.md`
- `plugins/saga/plugin.json`
- `docs/engineering-journal/DECISIONS.md`
- `plugins/saga/tests/test_saga_plugin.py`

**Approach:** Document contract identity, settlement rules, receipt location, and integration limits; record the Key Technical Decisions in the engineering journal; and bump the Saga plugin minor version because the plugin gains a new public contract. Repair only version assertions directly affected by that bump.

**Patterns to follow:** Use the current Saga README contract tables, Keep a Changelog structure, semantic versioning convention, and dated engineering-journal entries.

**Test scenarios:**

- Integration: load the packaged plugin and resolve both new reference schemas; expect packaged paths and the declared version to agree.
- Compatibility: run the canonical plugin validator; expect no package, manifest, or reference errors.
- Documentation: compare README state names and paths with the executable constants; expect exact agreement.

**Verification:** The plugin package exposes the references, changelog and manifest agree, the journal records the decisions, and canonical validation passes.

---

## Sequencing and Checkpoints

The implementation is one issue and one draft PR, with independently reviewable unit commits when the changes are ready to publish.

1. U1 establishes the schema vocabulary and must pass its focused tests before evaluator work.
2. U2 implements settlement and persistence against U1 and must pass both new test modules.
3. U3 adds only the additive outcome-specification bridge and must pass the existing outcome test group.
4. U4 updates documentation and packaging, then runs the full issue verification set.

If implementation exposes a directly blocking or implementation-caused defect, fix at most one such defect and run one targeted recheck. Record any further incidental finding without expanding this leaf.

---

## Reviewability and Delivery Boundary

The selected destination is a draft PR. Autonomous work may create the leaf branch, commits, push, and draft PR for GitHub issue #21. Merge, deployment, parent-outcome closure, new outcome edges, and work outside this issue's declared contract require operator approval.

The selected execution backend is inline because the four units share a compact schema vocabulary and edit overlapping Saga modules. This avoids coordination overhead and does not weaken the independent review evidence required by the contract itself.

---

## Prerequisite and Unlock Map

The host capability contract prerequisite is already merged; this leaf defines the stable boundary consumed by the remaining reconciliation work.

| relationship | issue or PR | effect on this plan |
|---|---|---|
| completed prerequisite | GitHub issue #20 and PR #24 | supplies the capability-receipt state semantics; no implementation wait remains |
| coordinated peer | GitHub issue #19 | artifact promotion will later produce canonical output evidence matching this contract |
| coordinated peer | GitHub issue #23 | conformance work will later produce and validate reference receipts |
| directly unlocked | GitHub issue #14 | may integrate the evaluator into `/outcome`, `/loop`, and `/resume` routing |
| directly unlocked | GitHub issues #17, #18, and #22 | may consume the contract for conformance, port reconciliation, and handoff behavior |

No external service, infrastructure, credential, deployment, or specialist prerequisite is required for this issue.

---

## Risks and Dependencies

| risk or dependency | consequence | mitigation |
|---|---|---|
| runtime and reference schemas drift | consumers accept a contract the docs reject, or vice versa | use shared fixtures and assert schema identities and closed vocabularies in focused tests |
| self-authored evidence is accidentally trusted | a leaf can certify its own execution, review, or quality assurance | require declared evidence roles and producer independence; compute settlement instead of trusting a claim |
| receipt persistence becomes a second mutable state store | resume behavior diverges across machines | keep canonical receipts tracked and write-once; leave local telemetry and cache modules unchanged |
| additive node fields activate routing prematurely | issue #21 absorbs work owned by issue #14 | change only parsing and serialization; assert that completion routing remains unchanged |
| version test drift exposes older unrelated assertions | broad cleanup distracts from the contract | repair only assertions directly invalidated by this version bump; record any further mismatch as an incidental finding |

---

## Alternatives Considered

- **Use `jsonschema` at plugin runtime:** rejected because it is not an installed Saga runtime dependency and strict repository patterns already exist in Python.
- **Store receipts in `outcome_store.py`:** rejected because that store is explicitly rebuildable host-local cache, while transition receipts are canonical review evidence.
- **Append transition receipts to `run_ledger.py`:** rejected because the run ledger is telemetry and has different retention and authority semantics.
- **Replace the current outcome completion barrier now:** rejected because routing integration belongs to GitHub issue #14 and would exceed this leaf.
- **Treat GitHub closure or PR merge as aggregate proof:** rejected because it cannot establish artifacts, checks, review independence, or off-chain ceremonies.

---

## Scope Boundaries

### In Scope

- Versioned lifecycle-obligation and transition-receipt contracts.
- Strict stdlib runtime validation and deterministic serialization.
- Independent-evidence settlement evaluation.
- Atomic, idempotent canonical receipt persistence.
- Additive outcome-node references.
- Focused conformance tests, documentation, journal entry, and Saga plugin versioning.

### Deferred to Follow-Up Work

- Full `/outcome`, `/loop`, and `/resume` routing through the evaluator: GitHub issue #14.
- Artifact promotion transactions and compensating rollback: GitHub issue #19.
- Gemini deliberation routing and fallback execution: GitHub issue #16.
- Reference lifecycle and failure-injection conformance laboratory: GitHub issues #17 and #23.
- Cross-runtime port-ledger reconciliation: GitHub issue #18.

### Non-Goals

- Adding `/impl-spec` or `/retro` to stored lifecycle phases.
- Treating model narration, free-form notes, warnings, degradation, GitHub closure, or PR merge as aggregate lifecycle proof.
- Allowing an execution producer to satisfy its own independent review or quality-assurance obligation.
- Adding a runtime dependency, remote service, database, credential flow, deployment, or production mutation.
- Implementing speculative security hardening beyond strict parsing, safe repository-relative paths, atomic writes, and plausible personal-harness trust boundaries.

---

## Validation Plan

Run the narrowest checks after each unit, then the issue-level set:

```bash
uv run pytest -q \
  plugins/saga/tests/test_lifecycle_obligations.py \
  plugins/saga/tests/test_transition_receipts.py

uv run pytest -q \
  plugins/saga/tests/test_outcome_spec.py \
  plugins/saga/tests/test_outcome_store.py \
  plugins/saga/tests/test_outcome_completion.py \
  plugins/saga/tests/test_run_ledger.py \
  plugins/saga/tests/test_saga_plugin.py

uv run ruff check \
  plugins/saga/scripts/lifecycle_obligations.py \
  plugins/saga/scripts/transition_receipts.py \
  plugins/saga/scripts/outcome_spec.py \
  plugins/saga/tests/test_lifecycle_obligations.py \
  plugins/saga/tests/test_transition_receipts.py \
  plugins/saga/tests/test_outcome_spec.py \
  plugins/saga/tests/test_outcome_completion.py \
  plugins/saga/tests/test_saga_plugin.py

uv run mypy \
  plugins/saga/scripts/lifecycle_obligations.py \
  plugins/saga/scripts/transition_receipts.py \
  plugins/saga/scripts/outcome_spec.py

uv run python scripts/validate_plugins.py
```

The issue is ready for review when the focused tests prove every settlement and persistence rule, existing outcome tests show no compatibility regression, documentation matches the executable vocabulary, and the canonical plugin validator passes.

---

## Sources / Research

- `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`
- `plugins/saga/docs/lifecycle.md`
- `plugins/saga/docs/state-readiness.md`
- `plugins/saga/references/execution-spec.md`
- `plugins/saga/scripts/lifecycle_state.py`
- `plugins/saga/scripts/outcome_spec.py`
- `plugins/saga/scripts/outcome_store.py`
- `plugins/saga/scripts/outcome_orchestrator.py`
- `plugins/saga/scripts/provenance_manifest.py`
- `plugins/saga/scripts/run_ledger.py`
- `plugins/saga/tests/test_outcome_completion.py`
- `docs/engineering-journal/DECISIONS.md`
- `docs/engineering-journal/LEARNINGS.md`
