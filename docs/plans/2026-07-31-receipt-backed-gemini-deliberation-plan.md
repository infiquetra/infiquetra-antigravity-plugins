---
title: Receipt-Backed Gemini Deliberation Implementation Plan
type: feat
status: active
date: 2026-07-31
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/19
reviewed: 2026-07-31
review_status: ready
review_artifact: docs/reviews/2026-07-31-receipt-backed-gemini-deliberation-plan-doc-review.md
---

# Receipt-Backed Gemini Deliberation Implementation Plan

## Summary

Add one strict deliberation manifest and one deterministic runtime that validate independently
executed strategies, apply bounded recovery, and preserve disagreement. Declare the approved
minimum coverage for the six Saga phases named by issue #19 without changing their product scope or
building an Antigravity execution engine inside this repository. Export the completed artifact as
`deliberation-receipt` evidence for the existing Saga transition-receipt contract.

## Requirements

R1. A versioned manifest must declare strategy identities, applicability, roles, requested model and
effort, allowed tools, execution bounds, expected result shape, minimum coverage, convergence, and a
bounded recovery policy before results are evaluated.

R2. A result counts as one independent execution. Headings or self-reported personas inside one
result never increase coverage. Proven isolated sequential results may satisfy the same contract as
native agent results.

R3. Receipts must keep requested configuration separate from observed model, effort, tools,
isolation, and worker count. Missing observations remain `unknown`.

R4. Missing, duplicate, malformed, and failed results must follow the declared retry limit. Required
coverage that remains unproven leaves the deliberation incomplete.

R5. Convergence must retain material disagreement, supporting evidence, and adjudication. It may not
replace those facts with only a consensus summary.

R6. The `ideate`, `brainstorm`, `plan`, `doc-review`, `code-review`, and `qa` phase contracts must
declare an approved minimum and an applicability rule that a run cannot silently lower.

R7. Cheap-first escalation must be explicitly allowed by the phase contract and recorded in the
receipt with its triggering evidence.

R8. A completed deliberation receipt must bind into `saga.transition-receipt.v1` as verified
repository evidence with its actual path and digest; it must not define a competing lifecycle
settlement format.

## Key Technical Decisions

KTD1. **Validate evidence; do not dispatch Gemini:** `deliberation.py` will be a standard-library
contract and receipt boundary. Antigravity owns agent or isolated-conversation execution. This keeps
the plugin testable and avoids inventing an unsupported host API.

KTD2. **Use one closed JSON contract:** the manifest schema and Python validator will reject unknown
fields and invalid values. Result receipts use stable strategy and execution identities, so duplicate
coverage cannot be laundered through renamed headings.

KTD3. **Count accepted execution receipts, not prose:** each unique, valid, successful execution may
satisfy at most one required strategy. The runtime reports missing, duplicate, malformed, and failed
strategies separately and applies only the manifest's finite retry allowance.

KTD4. **Keep observations nullable and explicit:** requested values are copied from the contract;
observed fields are populated only from supplied host evidence and otherwise serialize as
`unknown`. Requested model or effort is never promoted into observed evidence.

KTD5. **Preserve convergence inputs:** the final receipt contains accepted results, disagreements,
their evidence references, and the adjudication. A summary is optional and never substitutes for
those records.

KTD6. **Correct the existing host fallback declaration:** add `saga.independent-deliberation` to the
already-defined `agy.sequential.isolation` fallback consumers. Narrow the operator-choice prohibition
so ordinary same-context sequential work remains invalid while separately isolated, receipt-backed
conversations are accepted. No new probe or capability is added.

KTD7. **Keep phase declarations compact:** each covered phase gets a small machine-readable contract
block naming its strategies, minimum, applicability rule, completion quality, and escalation rule.
Existing phase instructions remain authoritative outside that block.

KTD8. **Use the existing Saga evidence adapter:** `transition_receipts.py` will wrap a persisted
deliberation receipt as `EvidenceKind.DELIBERATION_RECEIPT` after validating its schema and digest.
The consensus plugin stays independently packageable and does not import Saga at runtime.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| One response with six headings counts once | U1-U2 | focused fixture test asserts coverage `1/6` |
| Six isolated sequential conversations may satisfy six strategies | U2 | focused fixture test asserts completion with six unique executions |
| Requested and observed facts remain separate | U1-U2 | receipt schema tests preserve `unknown` observations |
| Recovery is bounded and incomplete coverage fails | U2 | duplicate, malformed, failed, and exhausted-retry tests |
| Six phase contracts declare approved minima and applicability | U3 | `test_deliberation_contracts.py` parses every phase block |
| Disagreement, evidence, and adjudication survive convergence | U2 | convergence receipt round-trip test |
| Cheap-first escalation is traceable | U2-U3 | contract authorization and triggering-evidence tests |
| Deliberation binds through the existing transition receipt | U2 | transition-receipt integration test |

## Implementation Units

### U1. Define and validate the manifest

Create `deliberation-manifest-schema.json` and the typed manifest/result models in
`deliberation.py`. Validate closed fields, unique identifiers, declared strategies, minimum coverage,
finite retry bounds, and allowed execution modes.

Files:

- `plugins/multi-agent-consensus/references/deliberation-manifest-schema.json`
- `plugins/multi-agent-consensus/scripts/deliberation.py`
- `plugins/multi-agent-consensus/tests/test_deliberation.py`

Proof: valid manifests round-trip; unknown fields, duplicate strategies, invalid minima, and unbounded
recovery fail with specific errors.

### U2. Evaluate coverage, recovery, convergence, and receipts

Evaluate supplied execution results without invoking the host. Count independent native-agent or
isolated-sequential executions, distinguish failure classes, expose bounded recovery requests, and
produce a deterministic receipt that keeps requested and observed facts separate. Require material
disagreements and evidence to remain in the convergence record.

Files:

- `plugins/multi-agent-consensus/scripts/deliberation.py`
- `plugins/multi-agent-consensus/tests/test_deliberation.py`
- `plugins/fleet-core/references/antigravity-capability-probes.yaml`
- `plugins/saga/references/operator-choice.md`
- `plugins/saga/scripts/transition_receipts.py`
- `plugins/saga/tests/test_transition_receipts.py`

Proof: the fixture matrix covers one call with six headings, six isolated calls, duplicates,
malformed output, exhausted recovery, unknown model readback, authorized reduced applicability,
preserved disagreement, and cheap-first escalation. A completed receipt also becomes verified
`deliberation-receipt` evidence in a Saga transition receipt without a private settlement state.

### U3. Declare the six Saga phase contracts

Add a compact `saga.deliberation-phase.v1` JSON block to each covered skill. The tests will parse the
blocks and prove that minimum coverage cannot be reduced without the declared applicability rule or
an operator decision.

Files:

- `plugins/saga/skills/ideate/SKILL.md`
- `plugins/saga/skills/brainstorm/SKILL.md`
- `plugins/saga/skills/plan/SKILL.md`
- `plugins/saga/skills/doc-review/SKILL.md`
- `plugins/saga/skills/code-review/SKILL.md`
- `plugins/saga/skills/qa/SKILL.md`
- `plugins/saga/tests/test_deliberation_contracts.py`

Proof: every phase declares strategies, minimum coverage, applicability, useful completion, and
escalation. The declarations agree with the current skill behavior rather than inventing new fanout.

### U4. Document and package the contract

Update the consensus skill, protocol, reviewer registry, plugin metadata, and focused package tests so
the runtime and references ship together. Add only version or formatting test changes caused by this
feature.

Files:

- `plugins/multi-agent-consensus/skills/multi-agent-consensus/SKILL.md`
- `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/consensus-protocol.md`
- `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/reviewer-registry.md`
- `plugins/multi-agent-consensus/README.md`
- `plugins/multi-agent-consensus/CHANGELOG.md`
- `plugins/multi-agent-consensus/plugin.json`
- existing focused package tests when required by the version change

Proof: documentation names the executable contract and does not claim host facts the receipt cannot
prove. The consensus plugin receives the next minor version because it adds a public manifest and
receipt contract.

## Verification

Run narrow checks first:

```bash
uv run pytest plugins/multi-agent-consensus/tests/test_deliberation.py plugins/saga/tests/test_deliberation_contracts.py -q
uv run pytest plugins/multi-agent-consensus/tests plugins/saga/tests/test_transition_receipts.py plugins/saga/tests/test_saga_plugin.py plugins/saga/tests/test_saga_doc_formatting.py -q
uv run ruff check plugins/multi-agent-consensus plugins/saga
uv run mypy plugins/multi-agent-consensus plugins/saga/scripts
python3 scripts/validate_plugins.py
```

One code review and one documentation review will cover the final branch diff. Every actionable
finding will be fixed or explicitly classified as non-actionable with evidence.

## Boundaries

- No new dependency or network client.
- No live Gemini call, installed-plugin mutation, host deployment, or release.
- No changes to canonical artifact promotion, lifecycle routing, or conformance-laboratory behavior
  owned by issues #23, #14, #17, #18, and #22.
- Direct implementation blockers may be corrected only when the change is small and covered by this
  issue's tests. A broader host-contract redesign or second-order workstream requires operator review.
