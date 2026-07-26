---
date: 2026-07-26
target: docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md
review_type: requirements-readiness
classification: idea-phase-formal-artifact
reviewed_revision: working-tree-at-aaeac80cce4e20b38c4e98f91f0b9c323ab4339a
external_reviewer: claude-fable-5/max
verdict: ready-for-plan
---

# Antigravity Saga Reliability System Requirements Review

## Readiness Summary

The remediated requirements are ready to drive `/plan`; no P0-P1 findings remain.

The plan must preserve two explicit settlement boundaries: inventory, ranking, and operator approval precede survivor-specific migration units, while the capability doctor precedes runtime-dependent execution design. The document now defines the complete reference route, off-chain obligations, authority hierarchy, canonical evidence, failure behavior, baseline ownership, and release gates without requiring the planner to invent them.

| review-result field | value |
|---|---|
| target path | `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md` |
| reviewed revision | working tree based on `aaeac80cce4e20b38c4e98f91f0b9c323ab4339a`; target is not yet committed |
| blocked status | No |
| raised priorities | P0: 0; P1: 2; P2: 11; P3: 6 |
| remaining priorities | P0: 0; P1: 0; P2: 0; P3: 0 |
| override rationale | None |
| linked source | `docs/ideation/2026-06-27-antigravity-harness-ideation.md` |
| external authority | Advisory and non-gating; every finding independently adjudicated |
| review artifact | `docs/reviews/2026-07-26-antigravity-saga-reliability-system-requirements-review.md` |

## Applied Fixes

Every actionable native, rubric, and Fable finding was fixed in place; one containment-induced Fable claim was dropped after live verification.

| id | priority | source | finding | disposition |
|---|---|---|---|---|
| F01 | P1 | Native + Fable | The reference route omitted the existing hard `/doc-review` gate. | Fixed: `/doc-review` now sits between `/plan` and `/work`, distinct from `/impl-spec`'s internal buildability probe. |
| F02 | P1 | Native + Fable | `/impl-spec` was treated as an on-chain generic phase contrary to its approved profile-backed, off-chain contract. | Fixed: it remains off-chain, writes no Saga tick, commit, or push, requires a folder-contract profile, and passes its promoted spec set to `/plan` for this route. |
| F03 | P2 | Fable | `/resume` was assigned load-bearing behavior even though the current skill is a stub. | Fixed: replacing the stub with R4/R29 reconstruction behavior is explicit first-release scope and a canary obligation. |
| F04 | P2 | Native + Fable | The target did not reconcile `/outcome`'s current leaf scope, branch behavior, GitHub completion authority, or push boundary. | Fixed: the authority hierarchy, current scope gap, working-branch promotion, local commit behavior, and separately authorized pushes are explicit. |
| F05 | P2 | Fable | The review claimed eight cited source paths were absent. | Dropped: all eight exist in the actual worktree; they were intentionally absent from the approval-scoped frozen external workspace. |
| F06 | P2 | Fable | Capability receipts could promote absolute runtime roots and machine identifiers. | Fixed: local-versus-promoted receipt policy, allowed logical roots, redactions, and deterministic rejection rules are explicit. |
| F07 | P2 | Fable | Claude/Codex baseline creation, storage, versioning, and approval had no owner. | Fixed: R55 assigns the plugin maintainer and defines a versioned baseline directory and binding manifest. |
| F08 | P3 | Fable | R1 pointed to six capabilities that the Summary did not enumerate. | Fixed: the Summary names all six. |
| F09 | P3 | Fable | The semantic port ledger had no canonical location or durable format. | Fixed: R9 requires schema-versioned YAML at `docs/ports/<campaign-id>/ledger.yaml`. |
| F10 | P3 | Fable | The rest of the approved 2026-06-11 `/impl-spec` and `/product-review` bundle had no disposition. | Fixed: all `/impl-spec` support surfaces are in scope; `/product-review` and its dispatch entry are explicitly deferred, not superseded. |
| F11 | P3 | Fable | “Strongest safe local probe” was not objectively testable. | Fixed: R20 defines a versioned probe catalog, required fields, evidence shapes, and deterministic coverage. |
| F12 | P3 | Fable | QA and retro were implicitly reclassified from current advisory/off-chain behavior. | Fixed: stored phases and reference obligations are distinguished; QA evidence is fail-closed only for this reference workstream, while retro remains off-chain and Saga-read-only. |
| F13 | P3 | Fable | `AGY`, the Antigravity host, the `agy` CLI, and source `plugins/agy` were ambiguous. | Fixed: a Terminology section distinguishes all three and the requirements use those terms consistently. |
| N01 | P2 | Native | A required obligation could be `degraded` without appearing in the R28 blocker list. | Fixed: required degraded obligations block; only predeclared optional obligations may settle degraded. |
| N02 | P2 | Native | A phase could declare only the strategy that ran and thereby evade multi-strategy coverage. | Fixed: phase-owned minimum coverage comes from the approved baseline and cannot be shrunk by the run manifest. |
| N03 | P2 | Native | “Run with normal changes” did not require blocking CI. | Fixed: R48 makes deterministic conformance checks blocking for scoped changes. |
| N04 | P2 | Native | A success criterion could count a required blocking disposition as release success. | Fixed: required blocking dispositions prevent release; degradation is optional-only. |
| N05 | P2 | Native | Planning could invent survivor-specific scope before the full inventory, ranking, and operator approval. | Fixed: R13, R15, and F1 prohibit migration units, estimates, or sequencing until the survivor set is approved. |
| N06 | P2 | Idea rubric | The document discussed several constraints without naming the binding one. | Fixed: runtime capability proof is the binding constraint and must settle before source, topology, or release planning. |

## Formal Rubric Review

The idea-phase rubric pass is satisfied after remediation; the incentive audit was not applicable to this single-operator internal tool.

| rubric | applicability | score | result |
|---|---|---:|---|
| assumption audit | core | 9 | Load-bearing dependencies are now categorized as validated, testable, historical, or unsatisfied preconditions with a validation response. |
| devil's advocate blueprint | core | 9 | The source ideation preserves rejected alternatives, failure evidence, status quo costs, and explicit no-lift-and-shift constraints. |
| internal consistency | core | 9 | The lifecycle, stored-phase, degraded-state, artifact, and authority contradictions were resolved. |
| problem framing | core | 9 | The operator, observed failure mechanism, counterfactual release risk, and falsification path are specific. |
| alternatives explored | conditional, applied | 9 | The linked ideation artifact compares six survivors against rejected and absorbed alternatives with value-and-fit criteria. |
| binding constraint | conditional, applied | 9 | Runtime proof is named and sequenced first; source selection becomes the next constraint after capability settlement. |
| falsifiability | conditional, applied | 9 | Blocking deterministic checks, capability probes, a live canary, and operator quality comparison define failure conditions. |
| prior art check | conditional, applied | 9 | The requirements engage the first-generation harness, prior port runs, Claude/Codex siblings, and approved unlanded Saga work. |
| stakeholder coverage | conditional, applied | 9 | Operator, maintainer, coordinator, phase, runtime, release reviewer, and mission-control consumer duties and conflicts are explicit. |
| incentive audit | conditional, not applied | N/A | There is no buyer/user, marketplace, or multi-party adoption incentive split in this internal operator workflow. |

## Claude Fable Advisory Review

The governed Fable review completed successfully and remained advisory.

| field | value |
|---|---|
| action | `findings-opinion` |
| provider | Claude CLI `claude-fable-5` |
| effort | `max` |
| mode | read-only `Read,Glob,Grep`; remote-stripped scoped workspace |
| accepted run | `doc-review-20260726-fable-max-r4` |
| wall time | 582.43 seconds |
| typed findings | 13 |
| adjudication | 12 reconciled; 1 dropped; 0 unaccounted |
| evidence artifact SHA-256 | `f4e17ed183e61ebf8a85cbe3a7c65e89da091400873c6b45da4230c92de1551a` |
| authority | non-gating |

The governed path also exposed two source candidates for the later value-and-fit ledger: this target checkout lacks the installed Saga external-action runtime, and the cached Claude adapter's minimal environment omits non-secret user identity variables required for the local Claude profile. Neither candidate is silently added to release scope; both must survive the same inventory and value-and-fit gate as every other source delta.

## Remaining Findings

No actionable findings remain.

| priority | remaining |
|---|---:|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |

## Residual Risk

The requirements review did not execute the future semantic port inventory, deterministic conformance suite, or live `agy`/Gemini lifecycle canary. Raw Antigravity transcript coverage remains incomplete, and the three sibling snapshots must be refreshed at plan execution; the document now treats those as named evidence gates rather than settled facts.
