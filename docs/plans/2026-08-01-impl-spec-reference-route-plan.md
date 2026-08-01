---
title: Impl-Spec and Reference Lifecycle Route Implementation Plan
type: feat
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/17
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-impl-spec-reference-route-plan-doc-review.md
---

# Impl-Spec and Reference Lifecycle Route Implementation Plan

## Summary

Deliver `/impl-spec` as a profile-backed, off-chain pipeline for multi-document specification sets.
Add deterministic profile and README-folder-contract validation, the approved six stages, a reusable
buildability-probe result contract, canonical spec-set promotion, and the reference route into
`/plan`. Keep `/product-review` deferred and preserve the later `/doc-review` as the hard readiness
gate on the plan.

## Requirements

R1. `/impl-spec` is a distinct command and skill for profile-backed multi-document spec sets. It is
not a mode of `/spec`, a stored lifecycle phase, or a general requirement for ordinary features.

R2. A closed profile must name a repository-relative spec root and folder-contract README. The README
must provide a parseable folder, required-files, completeness, and optional dependency table. Missing
or malformed profiles and contracts stop as `unavailable`; the skill never invents a layout.

R3. The pipeline has six bounded stages: Research, Author, Assemble, Verify, Review, and
Probe+Remediate. Each stage has explicit entry, output, and exit criteria. A scratch checkpoint under
the ignored runtime root may support recovery but writes no Saga tick.

R4. Authoring follows dependency waves derived from the folder contract. It enforces lifecycle
closure, canonical cross-record rules, and contract-to-prose synchronization before assembly. The
root README is rewritten last.

R5. Native authoring and review require `agy.agent.execution=passed`. When that capability is
`unknown` or `unavailable`, separately isolated sequential document conversations may substitute only
when `agy.sequential.isolation=passed` and each result has its own identity receipt. Failed or unknown
isolation stops the pipeline; same-context roleplay is never independent evidence.

R6. Verification checks every required folder/file, relative link, and cross-document count, plus
applicable contract validators. Security/access-control and consistency/standards reviews must clear
all P0-P3 findings before probing.

R7. Buildability probing receives only the spec set and shared standards. It must enumerate
implementation scope and questions across product, architecture, data, API, and operations. PASS is
valid only when no question meets the boundary test for a spec defect.

R8. Probe remediation fixes the finding class across the spec set and uses a fresh execution each
round. It stops after three failed rounds with explicit unresolved findings.

R9. The complete spec set is content-addressed in a deterministic manifest, promoted through
`artifact_promotion.py` into `docs/specs/`, and handed to `/plan`. The later plan `/doc-review` remains
a separate hard gate.

R10. `/impl-spec` performs no commit, push, PR, issue, board, merge, deployment, or stored Saga-phase
mutation. `/product-review` and its dispatch route remain absent.

## Key Technical Decisions

KTD1. **One small deterministic contract module:** `impl_spec.py` parses a closed JSON profile, a
strict Markdown folder-contract table, dependency waves, completeness, deterministic spec-set
manifests, and buildability-probe JSON. It reads repository files and emits JSON; it does not author
content or invoke Antigravity.

KTD2. **Instructions own the creative pipeline:** `SKILL.md` and its two references own research,
authoring, assembly, review, remediation, interaction mode, and checkpoint behavior. This keeps host
orchestration in Antigravity while making the non-creative gates deterministic.

KTD3. **Use existing receipt contracts:** independent author/reviewer results use the existing
`saga.independent-evidence-receipt.v1`; strategy/probe coverage uses the deliberation receipt; final
promotion uses `saga.artifact-promotion-receipt.v1`. No duplicate execution or settlement schema is
created.

KTD4. **Add one named capability consumer:** `saga.impl-spec` is added to the existing native-agent
fallback mapping. The operator-choice text limits sequential fallback to isolated document
authoring/review for this profile-backed pipeline; it does not authorize code implementation workers
or the full consensus backend.

KTD5. **Promote the set through a final manifest:** every required document is canonicalized first.
`impl_spec.py` then emits `saga.impl-spec-set.v1` with each repository-relative file and digest. The
manifest is promoted last under `docs/specs/<profile-id>/`, so partial documents alone cannot satisfy
the off-chain obligation.

KTD6. **Update the canonical documentation model:** add `/impl-spec` to the command wrapper, dispatch
table, command manual, lifecycle manual, and documentation model. Regenerate the existing visual
assets mechanically. Do not add `/product-review` anywhere.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| Parse valid profile/README; reject missing contract | U1 | `test_impl_spec.py` valid, missing, malformed, path, and cycle cases |
| Six stages with independent or proven fallback execution | U2-U3 | structural contract tests and capability consumer tests |
| No Saga tick or remote mutation | U2-U3 | skill/source boundary tests |
| Reusable structured buildability verdict | U1-U2 | `test_doc_review_buildability.py` PASS/FAIL and malformed-result cases |
| Promoted set handed to `/plan`; later review retained | U2-U3 | route and documentation-model tests |
| Missing profile prevents invented spec set | U1-U2 | unavailable fixture and hard-stop instructions |
| Command, skill, docs, and dispatch expose only `/impl-spec` | U3-U4 | package and docs coverage tests |

## Implementation Units

### U1. Deterministic profile, folder, manifest, and probe contracts

Create `plugins/saga/scripts/impl_spec.py` and three focused fixture families. The command line will
provide `discover`, `validate`, `manifest`, and `probe-check` read-only operations. The parser accepts
only the documented Markdown table contract and produces dependency waves deterministically.

Proof: focused tests cover a complete profile, missing/unparseable README, invalid paths, missing
files, unknown dependencies, cycles, stable manifests, exhaustive question categories, and the
zero-defect hard verdict.

### U2. Six-stage skill and reusable probe mode

Create the command wrapper, `impl-spec/SKILL.md`, stage reference, authoring prompt, shared
buildability protocol, and lifecycle-closure matrix. Add buildability-probe mode to `/doc-review`
without changing its existing plan/readiness behavior.

Proof: tests require all six stages, their entry/exit rules, a three-round cap, independent execution
receipts, off-chain/no-mutation wording, structured probe output, and preserved doc-review sections.

### U3. Promotion, route, and host-capability integration

Add `impl-spec -> docs/specs` to artifact promotion. Add the `saga.impl-spec` host consumer and narrow
operator-choice exception. Route a promoted spec-set manifest to `/plan`; update `/outcome`, the loop
dispatch table, lifecycle manual, and plan inputs while keeping `/impl-spec` off-chain.

Proof: catalog, artifact-promotion, route, package, and documentation tests prove the new edge and
ensure `/product-review` remains absent.

### U4. Package and documentation model

Update Saga to version 1.8.0, add the command card to the canonical documentation model, update the
manual, and regenerate existing SVG assets. No new visualization or documentation framework is
created.

Proof: Saga package, documentation coverage, formatting, plugin validation, and whole-repository
tests pass.

## Verification

```bash
uv run pytest plugins/saga/tests/test_impl_spec.py plugins/saga/tests/test_doc_review_buildability.py -q
uv run pytest plugins/saga/tests/test_artifact_promotion.py plugins/saga/tests/test_saga_plugin.py plugins/saga/tests/test_saga_doc_formatting.py plugins/saga/tests/test_saga_docs_coverage.py -q
uv run ruff check plugins/saga
uv run mypy plugins/saga/scripts
python3 scripts/validate_plugins.py
```

Then run the repository-wide test, lint, format, type, and security gates before publication.

## Boundaries

- No `/product-review`, product experiment routing, or unrelated `/spec` behavior.
- No live AGY run, installed-plugin mutation, host deployment, release tag, or canary execution.
- No new stored Saga phase, general outcome reconciliation, or conformance-laboratory work owned by
  issues #14, #18, and #22.
- A broader execution backend, host API, or cross-repository schema requires operator review.
