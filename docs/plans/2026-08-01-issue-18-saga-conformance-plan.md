---
title: Deterministic Saga Conformance Laboratory Implementation Plan
type: feat
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/18
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-issue-18-saga-conformance-plan-doc-review.md
---

# Deterministic Saga Conformance Laboratory Implementation Plan

## Summary

Build a small conformance index over the deterministic contract tests already delivered by issues
#14 through #23. Each sanitized scenario names its requirement, expected observable result, and exact
pytest validator. One repository script validates the closed metadata, privacy boundary, fixture and
baseline digests, then runs the selected validators in one subprocess. Add one blocking CI job. Do
not add transcript replay, model calls, a second contract evaluator, or a generalized test framework.

## Requirements

R1. Raw Antigravity transcripts, histories, brain artifacts, usernames, hostnames, absolute home
paths, prompts, and credentials remain outside tracked repository content. The ignored local discovery
root is `.conformance-local/`.

R2. Each committed scenario is a closed JSON object with a stable identifier, fixture identifier and
revision, requirement identifiers, scenario class, a single exact pytest node, a plain-language
observable, an expected zero exit code, and explicit sanitized/no-raw-source declarations.

R3. The reference-lifecycle fixture lists every scenario in deterministic order and binds its
profile-backed `/impl-spec` profile and README folder contract by repository-relative path and SHA-256
digest. Referencing the existing implementation-spec fixture avoids a second copy.

R4. Failure scenarios cover stale or falsely narrated state, conflicting canonical documents,
unavailable required capabilities, active Claude-only APIs, mismatched receipts, missing strategy
coverage, and unauthorized external mutation. Success scenarios cover the probe catalog,
required/optional capability behavior, host lint, settlement, retry/resume, deliberation, promotion,
sanitization, and external-mutation authority.

R5. `scripts/saga_conformance.py verify --fixture reference-lifecycle` validates all metadata and
digests, rejects private content without echoing it, and executes all exact pytest nodes in one bounded
subprocess. It never invokes `agy`, Gemini, Claude, Codex, or a network service.

R6. The verifier accepts only pytest node identifiers under the repository's plugin test trees. It
does not accept shell, arbitrary arguments, globs, environment changes, or external paths.

R7. A baseline manifest binds fixture revision and digest, the semantic-contract version/path/digest,
Claude and Codex source snapshot commits, both artifact paths and identities, and operator approval.
The approval carries a binding digest over every reusable field, so any changed binding invalidates
reuse.

R8. Claude and Codex baseline artifacts use the same closed semantic summary contract over the same
reference fixture. They record depth, evidence use, seed retention, adjudication, and lifecycle
completeness without claiming that artifact presence alone proves quality.

R9. Baseline candidate files may be prepared autonomously, but `approval.state=approved` and its
binding digest are recorded only after Jeff reviews the candidates. This is the issue's one required
operator-quality gate.

R10. A dedicated CI job runs fixture verification and baseline validation after a normal dependency
install. The publish job depends on it, and no live model call occurs in ordinary CI.

## Key Technical Decisions

KTD1. **Compose existing tests:** scenario validators are exact pytest node identifiers. The lab
indexes semantic intent and proves coverage without reproducing capability, receipt, deliberation,
promotion, reconciliation, or external-action logic.

KTD2. **JSON in the requested manifest path:** `manifest.yaml` contains strict JSON, which is valid
YAML while remaining parseable with the Python standard library. No new YAML or schema dependency is
added.

KTD3. **One verifier, two commands:** `verify` validates a named fixture and runs its nodes;
`validate-baseline` validates the manifest, binding digest, referenced digests, approval, and closed
artifact shape. There is no generator or transcript-ingestion command.

KTD4. **Reuse the promotion privacy boundary:** the verifier calls Saga's existing promoted-content
sanitizer, then adds closed-key checks for prompt/history/brain/operator fields that do not belong in
scenario or baseline contracts. Errors name the file and rule class, never the rejected value.

KTD5. **One reference fixture:** the first release supports only `reference-lifecycle`. Scenario files
are individually minimized, but a fixture index owns their order and digest set. Adding a second
fixture requires an explicit later change.

KTD6. **Leave `review_canary.py` alone:** it scores saved review prose and does not own lifecycle
contracts or baseline binding. Issue #22 can consume both tools during live qualification without
coupling them here.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| Every scenario carries requirement and observable validator | U1-U2 | closed-schema and mutation tests |
| Sanitization rejects private content | U1-U2 | field, path, host, credential, prompt, and transcript negative tests |
| Reference fixture verifies without AGY or Gemini | U1-U2 | injected subprocess assertion plus real command run |
| Baseline binds all required identities and approval | U3 | digest drift and approval-state tests |
| Required checks are blocking in CI | U4 | workflow structure test and `conformance` publish dependency |
| Eight named failure classes are covered | U1-U2 | exact required scenario-ID set assertion |
| Raw discovery artifacts remain untracked | U4 | `.conformance-local/` ignore assertion and clean status check |

## Implementation Units

### U1. Closed scenario and fixture corpus

Add a `reference-lifecycle` index and minimized scenario JSON files under
`plugins/saga/tests/fixtures/conformance/`. Bind existing `/impl-spec` profile/folder-contract inputs
by digest. Add a short scenario catalog under `docs/conformance/scenarios/` that explains the privacy
and semantic-predicate rules without copying fixture bodies.

### U2. Deterministic verifier and tests

Add `scripts/saga_conformance.py` and `plugins/saga/tests/test_conformance_scenarios.py`. Validate
closed keys, identifiers, path containment, digests, sanitization, required scenario coverage, and
subprocess boundaries. Batch exact test nodes into one `python -m pytest -q` call.

### U3. Version-bound baseline candidates

Add one Claude and one Codex semantic baseline artifact plus `manifest.yaml` under
`docs/conformance/baselines/reference-lifecycle/`. Bind the current fixture, requirements contract,
source snapshots, artifact identities, and approval payload. Stop for Jeff's review before recording
approved state and binding digest.

### U4. Blocking CI and package documentation

Ignore `.conformance-local/`, add the dedicated conformance CI job, and make publishing depend on it.
Bump Saga to 1.10.0 with a concise changelog entry and package assertions for the conformance script
and fixture.

## Verification

```bash
python3 scripts/saga_conformance.py verify --fixture reference-lifecycle
python3 scripts/saga_conformance.py validate-baseline docs/conformance/baselines/reference-lifecycle/manifest.yaml
uv run pytest plugins/saga/tests/test_conformance_scenarios.py -q
uv run pytest plugins/fleet-core/tests/test_antigravity_capabilities.py plugins/fleet-core/tests/test_host_contract_lint.py plugins/multi-agent-consensus/tests/test_deliberation.py -q
uv run ruff check scripts/saga_conformance.py plugins
uv run ruff format --check scripts/saga_conformance.py plugins
uv run mypy scripts/saga_conformance.py plugins/saga/scripts
python3 scripts/validate_plugins.py
```

Then run the whole repository suite and existing CI-equivalent checks before publication.

## Boundaries

- No raw transcript/history/brain collection, minimizer, replay engine, or committed discovery input.
- No live AGY, Gemini, Claude, or Codex calls; issue #22 owns live qualification.
- No aggregate quality score, prose golden file, or automatic operator approval.
- No duplicated lifecycle schemas or validators; exact existing pytest nodes remain authoritative.
- No changes to `review_canary.py`, contract runtimes, plugin installation, hosts, deployment, or
  release tags.
- One implementation pass, one code review, and one documentation review. Additional machinery needs
  a failed acceptance criterion, not a preference for a broader laboratory.
