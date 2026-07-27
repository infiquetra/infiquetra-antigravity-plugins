---
date: 2026-07-26
topic: antigravity-saga-reliability-system
maturity: requirements-ready
source: docs/ideation/2026-06-27-antigravity-harness-ideation.md - ranked survivors 1-6
---

# Antigravity-Native Saga Reliability System Requirements

## Summary

Build one Antigravity-native reliability system that makes Saga complete a full idea-to-handoff lifecycle through the `agy` CLI and Gemini with observable deliberation, evidence-gated transitions, durable repository artifacts, and release proof. The first release combines all six ideation survivors: the host doctor, semantic port ledger, lifecycle reconciler, Gemini deliberation receipts, artifact promotion transaction, and conformance laboratory. Internal sequencing may vary, but the release is not complete until all six operate together on the reference lifecycle.

## Terminology

- **Antigravity host** means the Gemini-powered Antigravity application/runtime that loads and executes these plugins.
- **`agy` CLI** means the local command-line surface used to invoke or inspect the Antigravity host. A receipt records the `agy` CLI and Antigravity host versions separately when both are observable.
- **Source `plugins/agy`** means the distinct delegation-bridge plugin surface in a sibling source repository. It is not the `agy` CLI and remains outside this release unless the value-and-fit gate separately approves one of its capabilities.

## Problem Frame

The first-generation Antigravity harness established useful commands, routing, review prompts, canaries, and validation. Real `agy` history still shows a different class of failure: a phase may be described without being completed, required viewpoints may collapse into one shallow response, runtime assumptions may exceed what the host proves, and brain artifacts may be treated as durable lifecycle state.

The current Antigravity plugins also trail substantial Claude and Codex evolution. Mechanical file parity would preserve the wrong host assumptions, while selective porting without a complete inventory could silently discard valuable behavior. The needed unit of parity is the user-visible capability, re-expressed through Antigravity terminology, Gemini models, supported agent behavior, and Antigravity storage and validation contracts. Prior Antigravity requirements approved `/impl-spec`, but the current plugin surface does not contain that command or skill, so the reference lifecycle cannot assume it is already available.

Sampled Antigravity runs show that Gemini can perform structured, multi-frame work. The primary gap is therefore not the absence of a good method; it is the lack of enforceable execution topology, honest runtime receipts, canonical promotion, and end-to-end acceptance evidence.

## Key Decisions

**All six capabilities form one first release.** The host doctor, semantic port ledger, lifecycle reconciler, Gemini deliberation receipts, artifact promotion transaction, and conformance laboratory are jointly required. Implementation may proceed in dependency order, but partial delivery does not satisfy release acceptance.

**One complete lifecycle is the release reference.** The required route is `/ideate → /brainstorm → /impl-spec → /plan → /doc-review → /work → /code-review → /qa → /retro or /handoff`. `/outcome` is the durable coordinator around the workstream; `/loop` chooses the next valid obligation, and `/resume` reconstructs interrupted work. Release qualification must exercise `/retro` and produce a valid `/handoff` packet, even though normal completed work may use either terminal route.

**Reference obligations do not silently redefine stored phases.** `/impl-spec` remains an off-chain spec-set engine that writes no Saga tick and performs no commit or push, while `/retro` remains a Saga-read-only terminal learning step; `/outcome` tracks their required artifacts and receipts as obligations rather than inventing stored `lifecycle_phase` values. The reference route extends the approved `/impl-spec` exit by passing its promoted, buildability-probed spec set to `/plan`; its existing direct `/work` exit may remain outside this route. `/qa` remains an invoked acceptance skill, but its evidence is fail-closed for this reference workstream and release canary even where the current general `/loop` route treats QA as advisory.

**Required obligations fail closed.** A phase or outcome workstream cannot claim completion or advance when required evidence is missing. Optional enhancements may degrade only when the degradation is explicit and does not stand in for a required obligation.

**Runtime proof is the binding constraint.** Installed `agy` CLI and Antigravity host versions are evidence, not an allowlist. Source selection, execution topology, and release planning cannot settle until the host doctor proves the capabilities on which they depend; a runtime is supported when its required behavioral probes pass and blocked when a required capability is missing or unproven.

**Porting means semantic reimplementation.** The source inventory is exhaustive across relevant Claude and Codex changes, but only operator-approved value-and-fit survivors are implemented. A surviving capability must be expressed through Antigravity-native language, models, effort controls, agents, runtime behavior, artifact rules, and evidence.

**Source package boundaries do not dictate target package boundaries.** Claude `team-execution` is a source capability domain that maps to Antigravity `multi-agent-consensus` under the repository's existing port decision. It does not create a new target plugin merely because the source uses that name.

**Independent perspectives must be independently executed.** One Gemini response impersonating several viewpoints does not satisfy a multi-strategy phase. Antigravity agents are preferred when available; isolated sequential Gemini runs are the valid fallback.

**Repository documents are authoritative.** Antigravity brain and host-local runtime directories are disposable staging or projection surfaces. Phase completion, pause/resume, handoff, and `/outcome` advancement depend on successful promotion into the repository's established `docs/` lifecycle structure.

**Outcome authority is layered rather than competing.** The committed outcome spec remains canonical for graph structure, promoted `docs/` artifacts and receipts govern lifecycle settlement, and GitHub completion events remain canonical only for the external leaf-completion facts they represent. A GitHub completion event without the required linked repository evidence cannot settle a lifecycle obligation.

**Release proof has two layers.** Blocking deterministic conformance checks run for changes to the scoped system. One scripted live `agy`/Gemini canary must complete the reference lifecycle before release and receive both mechanical validation and operator quality sign-off.

**External mutations remain separately authorized.** The reference route ends with a validated mission-control handoff packet. It does not create GitHub issues, change project boards, merge code, or trigger deployment without a separate operator-approved action.

## Actors

A1. **Operator** — initiates or resumes lifecycle work, answers product questions, approves the ranked port survivors, adjudicates unsafe conflicts, and grants separate authority for external mutations.

A2. **Plugin maintainer** — pins comparison snapshots, curates capability classifications, implements approved semantic ports, and maintains deterministic conformance evidence.

A3. **Saga coordinator** — `/outcome`, `/loop`, and `/resume` maintain desired lifecycle state, evaluate evidence, and route each workstream to its earliest unsettled obligation. The first release must replace the current stub-only `/resume` behavior needed by this contract.

A4. **Lifecycle phase** — a Saga skill such as `ideate`, `brainstorm`, `plan`, or `QA` declares its required deliberation, artifacts, checks, and completion evidence.

A5. **Antigravity/Gemini runtime** — supplies the available models, effort controls, agents, tools, conversations, and execution results used by a phase through the Antigravity host and `agy` CLI.

A6. **Release reviewer** — evaluates the live canary's mechanical evidence and judges whether Gemini's result is substantively comparable to the Claude/Codex baseline.

A7. **Mission-control consumer** — accepts a validated handoff packet after the lifecycle completes, but performs remote issue or board mutations only under separate operator authority.

## Requirements

### First-Release Product Contract

R1. The first release must deliver the six coordinated capabilities named in the Summary; none may be declared a later phase of the same release.

R2. The coordinated target surface must cover Saga, `fleet-core`, `mission-control`, and `multi-agent-consensus`, including applicable Claude `team-execution` capabilities mapped into `multi-agent-consensus`.

R3. The release reference lifecycle must provide and cover `/ideate → /brainstorm → /impl-spec → /plan → /doc-review → /work → /code-review → /qa → /retro or /handoff`; `/product-review` is not part of this reference route. `/impl-spec` remains off-chain and must run only for a profile-backed multi-document spec set, perform its own buildability-probe stage, promote its spec set, and hand that set to `/plan`; the later `/doc-review` is the existing hard readiness gate on the resulting plan. Release qualification must exercise `/retro` and validate a `/handoff` packet.

R4. `/outcome` must own durable workstream settlement around the reference lifecycle, while `/loop` and `/resume` must use the same obligations and evidence rather than maintaining competing notions of completion. Because the current `/resume` surface is a stub, delivering the reconstruction and reconciliation behavior required by R4 and R29 is first-release scope rather than an assumed dependency.

R5. The first release must prove one complete reference lifecycle and provide reusable contracts for later application to other Saga routes. It does not need a live acceptance matrix covering every possible route.

R6. Direct invocation of an individual lifecycle phase may remain available, but it must not claim durable completion, resumability, handoff readiness, or outcome advancement without satisfying the same applicable evidence and promotion obligations.

R7. Release acceptance is all-or-nothing across R1-R6 and the capability groups below, even when implementation is divided into smaller independently testable increments.

### Semantic Port Inventory and Value Gate

R8. Each port campaign must pin the Claude source snapshot, Codex comparison snapshot, and Antigravity target baseline used for its inventory; a release-time refresh must disclose any newer drift.

R9. The ledger must be a committed, schema-versioned YAML artifact at `docs/ports/<campaign-id>/ledger.yaml`. It must inventory every changed capability that could affect the R2 target surface or reference lifecycle, including changes in the corresponding source plugins and shared contracts or tooling, and cluster file- and commit-level changes into semantic capabilities so repeated edits are not mistaken for separate product features.

R10. The inventory must include Codex-only capabilities that Antigravity lacks as well as Claude deltas, with provenance identifying which host or hosts supply each candidate.

R11. Every candidate must record a stable identity, source provenance, user-visible semantic contract, adjacent-plugin dependencies, current Antigravity state, proposed native disposition, value-and-fit assessment, evidence expectation, decision rationale, and revisit trigger.

R12. The value-and-fit assessment must consider operator value, fit with actual Antigravity capabilities, ability to prove the behavior, and ongoing maintenance cost. Ranking must inform the decision without automatically making it.

R13. The operator must explicitly approve the survivor set before implementation scope is considered settled; tooling must not silently discard or approve a candidate. Planning may define the inventory and ranking work before that approval, but it must not commit migration units, estimates, or implementation sequencing for an invented survivor set.

R14. No candidate in the pinned scope may remain unclassified at release. Each must be an approved survivor or an explicit rejection, supersession, metadata-only record, or blocked candidate with rationale.

R15. Every approved survivor must be migrated and receive acceptance evidence. Every non-survivor must remain visible with its rationale and a concrete condition that would justify reconsideration. After approval, the plan must derive migration units and dependency sequencing from the complete survivor set and current capability receipt.

R16. A migrated survivor must preserve its useful semantic outcome through Antigravity-native terminology, Gemini model and effort controls, Antigravity agents or supported fallbacks, host runtime capabilities, canonical artifact behavior, and target-side validation. File copying, prompt renaming, or textual similarity alone cannot satisfy the port.

R17. The target location of a survivor must follow Antigravity's product boundaries rather than the source repository's package layout; specifically, source `team-execution` behavior maps into `multi-agent-consensus` unless a separately approved product decision establishes a new plugin.

R18. Automated drift discovery must be read-only and produce reviewable candidate packets. It may detect changes and suggest clusters, but it cannot assign final semantic value, approve survivors, mutate sibling repositories, or update installed plugins.

### Host Contract and Capability Doctor

R19. A local capability receipt must identify the detected `agy` CLI and Antigravity host versions, logical runtime-root roles, plugin link/load/validation state, supported command flags, model and effort controls, agent execution controls, conversation resume behavior, and any required isolation or sandbox guarantees.

R20. Required capabilities must be proven by the accepted method in a schema-versioned probe catalog at `plugins/fleet-core/references/antigravity-capability-probes.yaml`. Each catalog entry must define the capability identity, requiredness, safe probe method, expected evidence shape, pass/fail/unknown rules, and fallback policy; help text or version strings alone are insufficient when the catalog defines controlled behavioral verification. Unavailable or unobservable capabilities must be reported as such rather than inferred.

R21. A previously unseen `agy` CLI or Antigravity host version must be accepted when its required probes pass. A known version must still be blocked when a required probe fails.

R22. The doctor must distinguish required capabilities from optional enhancements. A missing required capability blocks the affected phase or release canary; an optional capability may produce an explicit degraded receipt and use a declared fallback.

R23. Active prompts, commands, skills, hooks, references, and runbooks must be checked for host-contract violations such as executable `.claude/*` paths, Claude-only interaction or workflow APIs, fixed brain roots, unproven scheduling, or isolation claims stronger than Antigravity can establish. Historical lineage and quoted source evidence must be distinguishable from active runtime instructions.

R24. Capability and lint receipts must be safe to preserve. Local diagnostic receipts may retain absolute runtime roots and raw repository-relative paths only in ignored host-local state; promoted receipts must replace them with logical root roles or path digests and must omit usernames, hostnames, credentials, raw private transcript content, and other machine-identifying data. Deterministic validation must reject promoted evidence containing absolute home paths, credential material, or transcript content.

### Proof-Carrying Lifecycle Reconciliation

R25. Each outcome workstream must declare the stored lifecycle phases, off-chain obligations, gates, canonical artifacts, checks, reviewers, deliberation obligations, fallbacks, and handoff state required for settlement. `/impl-spec` and `/retro` remain off-chain obligations rather than stored `lifecycle_phase` values; QA evidence is a required settlement obligation for the reference workstream even where the general `/loop` route remains advisory.

R26. Each attempted transition must produce evidence linking its relevant inputs, operator decisions, actual execution receipts, canonical outputs, checks, review findings, and resulting settlement state.

R27. Settlement must distinguish at least satisfied, unsatisfied, degraded, unavailable, and conflicting obligations so a warning cannot be mistaken for successful completion.

R28. `/outcome` must refuse to advance a workstream when any required obligation is unsatisfied, degraded, unavailable, conflicting, or unsupported by evidence. Only an explicitly optional obligation may settle in a declared degraded state.

R29. `/loop` and the delivered `/resume` implementation must route to the earliest unsettled required obligation. Retrying an already satisfied transition must be safe and must neither duplicate durable artifacts nor skip later obligations.

R30. When runtime narration, transient brain state, GitHub completion events, and canonical repository evidence disagree about lifecycle settlement, promoted repository evidence governs; GitHub remains authoritative only for the external completion fact it records. If automatic reconciliation could overwrite or discard meaningful work, the system must pause for operator adjudication.

R31. `/outcome status` and equivalent summaries must derive completion from the committed outcome spec, linked GitHub completion facts, and settled repository evidence rather than from a model's assertion that a phase ran or a task is done. A GitHub completion event without the evidence required by the workstream contract remains an unsettled lifecycle obligation.

R32. A model-authored statement cannot satisfy its own required execution, review, or quality gate without the independent receipt, check result, artifact, or operator decision named by that gate.

### Receipt-Backed Gemini Deliberation

R33. Before any multi-strategy phase executes, it must declare the required axes or strategies, assigned roles, requested model and effort, allowed tools, execution bounds, expected result shape, convergence rule, and recovery policy. Each phase contract must also carry an approved minimum-coverage or applicability rule derived from the Claude/Codex semantic baseline; a run manifest cannot reduce required coverage merely to match what executed.

R34. Every strategy declared as required must execute independently. Asking one Gemini response to role-play several perspectives in a single context does not count as independent coverage.

R35. Antigravity-native agents should execute independent strategies when the capability doctor proves them available. Otherwise, isolated sequential Gemini runs may satisfy the same semantic requirement when each receives the appropriate bounded context and produces a separate receipt.

R36. Deliberation receipts must distinguish requested configuration from observed execution, including the actual worker count and any model, effort, tool, or isolation facts Antigravity can prove. Unobservable fields must remain explicitly unknown.

R37. Missing, duplicated, malformed, or failed strategy coverage must trigger the declared recovery policy. If required coverage still cannot be proven, the phase remains incomplete.

R38. Convergence must preserve material disagreement, evidence, and adjudication rather than flattening independent results into an unsupported consensus narrative.

R39. Each reference-lifecycle phase must define useful completion quality and minimum deliberation coverage rather than relying on response length or a self-selected strategy count. Examples include retaining operator seeds and applying the approved multi-frame strategy set during ideation, resolving requirements questions during brainstorming, grounding plans in settled requirements, producing evidence-backed review findings, and adjudicating QA failures. Any justified reduction in normally required coverage must be authorized by the phase applicability rule or an explicit operator decision and recorded in the receipt.

R40. Cheap-first model or fanout escalation may remain, but the chosen level must follow the declared phase contract and conformance evidence rather than an unsupported assumption that a cheaper run was sufficient.

### Canonical Artifact Promotion

R41. A lifecycle phase or off-chain reference obligation cannot be treated as durably complete, paused for later resumption, handed off, or advanced by `/outcome` until its authoritative artifact and settlement evidence are promoted into the repository's established `docs/` structure on the current outcome or work branch. Promotion does not imply merge to the repository's integration branch.

R42. Antigravity brain directories and other host-local Saga directories must be treated as disposable staging or projection surfaces. They may contain working material and pointers to canonical artifacts, but they must not become the only authoritative state for a durable lifecycle.

R43. Promotion must preserve enough provenance to connect the canonical artifact to its source phase, predecessor state, relevant input and output identities, and transition receipt.

R44. Promotion must not silently overwrite conflicting canonical work or leave a partially advanced lifecycle. A failed or ambiguous promotion blocks the transition and preserves both sides for reconciliation.

R45. Existing brain-only artifacts may be imported as staged candidates, but the import must not displace a canonical document without explicit conflict handling and must not retroactively fabricate missing execution evidence.

R46. An explicitly abandoned, unfinished exploration may remain disposable. It cannot be represented as phase-complete, resumable, handoffable, or settled by `/outcome`.

### Conformance and Release Qualification

R47. Raw `agy` transcripts and histories used to discover scenarios must remain local and uncommitted. Repository fixtures must minimize and sanitize the behavior needed for regression coverage.

R48. Changes to the scoped reliability system must pass blocking deterministic CI checks covering the versioned capability-probe catalog, capability classification, host-contract linting, required-versus-optional behavior, transition settlement, retry/resume, deliberation receipts, artifact promotion, promoted-evidence sanitization, conflict handling, and external-mutation boundaries.

R49. Before release, one scripted live `agy`/Gemini canary must execute the complete reference lifecycle in a controlled fixture repository and produce the expected canonical documents, deliberation receipts, transition evidence, outcome state, and handoff packet. The fixture must contain the profile and README folder contract required by the approved multi-document `/impl-spec` capability, and `/plan` must consume the promoted spec set it produces.

R50. Mechanical canary validation must prove that every required phase, off-chain obligation, and strategy ran, the `/doc-review` hard gate and QA acceptance obligation settled, canonical artifacts were promoted, delivered `/resume` behavior was exercised, and no unsupported capability was reported as proven.

R51. The release reviewer must also confirm that the live Gemini output is substantively comparable to operator-approved Claude/Codex baseline artifacts for the same fixture, using depth, evidence use, seed retention, adjudication, and lifecycle completeness. Strategy counts and artifact presence alone are insufficient, and the baseline hosts do not need to be rerun for every Antigravity release.

R52. A failed deterministic check, failed live canary, or withheld operator quality sign-off blocks release. Release evidence must record the observed runtime capabilities, `agy` CLI and Antigravity host versions, model and effort information observable from the host, and the exact source snapshots assessed.

R53. The first release does not require a broad model, version, or lifecycle-route matrix. The live canary qualifies the capability-probed runtime and reference route actually tested.

R54. The live canary and normal lifecycle must stop at a validated mission-control handoff packet unless the operator separately authorizes remote changes. Local fixture branches, canonical promotion, and local outcome-spec commits may be required by the controlled workflow, but `git push`, pull-request creation or merge, GitHub issue creation, board mutation, and deployment are not implicit acceptance steps.

R55. The plugin maintainer must produce and version the Claude and Codex comparison artifacts from the same fixture under `docs/conformance/baselines/<fixture-id>/`. A baseline manifest must bind the fixture revision, semantic-contract version, source snapshots, artifact identities, and operator approval; R51 may reuse the baseline only while those bindings remain unchanged.

## Key Flows

F1. **Port-candidate reconciliation.** The maintainer pins Claude, Codex, and Antigravity snapshots; inventories and clusters every scoped delta in the canonical ledger; records the three-way semantic comparison; ranks candidates; and presents the complete list for operator approval. Only after approval does the plan settle migration units, estimates, and dependency sequencing from the survivor set and current capability receipt; all other candidates retain explicit dispositions and revisit triggers. **Covers R8-R18.**

F2. **Outcome start and capability negotiation.** The operator starts or resumes an outcome workstream. The Saga coordinator obtains a current capability receipt, checks required host contracts, establishes the reference obligations, and either routes to the earliest valid phase or blocks with the missing capability and remedy. **Covers R19-R32.**

F3. **Multi-strategy phase execution.** A lifecycle phase declares its deliberation topology, dispatches each independent strategy through proven Antigravity agents or isolated sequential runs, compares requested and observed execution, recovers missing coverage, adjudicates the results, and promotes the canonical artifact before settlement. **Covers R33-R46.**

F4. **Interrupted or falsely completed work.** `/resume` compares canonical documents and receipts with the desired outcome state. It preserves already settled obligations, rejects unsupported completion narration, and returns to the earliest missing or conflicting requirement without duplicating prior durable work. **Covers R25-R32, R41-R46.**

F5. **Artifact conflict.** Promotion finds both new staged material and a divergent canonical document. The phase preserves both, leaves the transition unsettled, and requests operator adjudication instead of selecting the newest timestamp or overwriting either artifact. **Covers R30, R41-R46.**

F6. **Release qualification.** Blocking deterministic checks first prove the state and failure contracts. A fresh profile-backed fixture repository then runs the complete `agy`/Gemini reference lifecycle, stops at the mission-control handoff packet, validates mechanical evidence against the versioned Claude/Codex baseline manifest, and receives operator quality sign-off before release. **Covers R47-R55.**

## Acceptance Examples

AE1. **Trigger:** A newer, previously unlisted `agy` CLI or Antigravity host version is installed and all required catalog probes pass. **Expected:** The capability receipt records the new version and the lifecycle proceeds without a version-list update. **Covers R19-R22.**

AE2. **Trigger:** Antigravity exposes an agent command but the controlled probe cannot prove independent agent execution. **Expected:** Phases requiring independence use the declared isolated sequential fallback or remain blocked; the receipt does not claim agent execution. **Covers R20-R22, R35-R37.**

AE3. **Trigger:** A Claude/Codex delta is inventoried but scores poorly for operator value and Antigravity fit. **Expected:** It remains visible, the operator explicitly rejects it, and its rationale and revisit trigger are recorded; no implementation is required. **Covers R9-R15.**

AE4. **Trigger:** An approved survivor is copied with executable `.claude/agy` paths and Claude-only workflow language. **Expected:** Host-contract validation fails, and the survivor cannot be marked migrated until the behavior is re-expressed and proven through Antigravity-native surfaces. **Covers R16, R23.**

AE5. **Trigger:** The approved `ideate` phase contract requires six applicable strategies, but a run declares or executes only one Gemini call and its response contains six headings. **Expected:** The manifest cannot shrink the requirement to one, independent coverage is one of six, recovery is attempted, and ideation remains incomplete if the other five runs cannot be proven. **Covers R33-R39.**

AE6. **Trigger:** Antigravity cannot run agents concurrently, but it can start isolated bounded Gemini conversations. **Expected:** Each declared strategy runs sequentially with a separate receipt; the phase may complete after all required coverage and convergence checks pass. **Covers R34-R38.**

AE7. **Trigger:** A phase produces a polished artifact only inside an Antigravity brain directory. **Expected:** `/outcome` does not advance, and `/loop` routes to canonical promotion under `docs/`. **Covers R28-R31, R41-R43.**

AE8. **Trigger:** Promotion encounters a canonical document changed by another session. **Expected:** Neither version is overwritten, the transition remains conflicting, and the operator receives the evidence needed to reconcile it. **Covers R30, R44-R45.**

AE9. **Trigger:** Runtime narration says code review and QA completed, but only the work artifact and code-review request exist. **Expected:** `/resume` preserves completed work and routes to the earliest unproven review obligation rather than retro or handoff. **Covers R25-R32.**

AE10. **Trigger:** The live canary completes all reference phases and generates valid receipts, but the operator judges the Gemini requirements and review materially shallower than the Claude/Codex baseline. **Expected:** Release remains blocked despite mechanical success. **Covers R49-R52.**

AE11. **Trigger:** The live canary reaches `retro/handoff`. **Expected:** It creates and validates the handoff packet without creating a GitHub issue, changing a board, merging code, or deploying. **Covers R49, R54.**

AE12. **Trigger:** A useful regression case contains private paths, prompt history, or operator content in a raw transcript. **Expected:** The raw transcript remains local; the committed scenario contains only the minimized sanitized behavior and expected outcome. **Covers R24, R47.**

AE13. **Trigger:** A required host capability is reported as degraded even though an optional fallback succeeds. **Expected:** The affected phase and release remain blocked; only an obligation declared optional before execution may settle as degraded. **Covers R22, R27-R28.**

AE14. **Trigger:** The canary promotes evidence and commits its outcome spec on a local fixture branch, then reaches a command that would push or open a pull request. **Expected:** Local settlement remains valid, but the remote mutation does not occur without separate operator authorization. **Covers R41, R54.**

AE15. **Trigger:** The canary fixture lacks the folder-contract README required by the `/impl-spec` profile. **Expected:** `/impl-spec` remains unavailable, `/plan` does not invent the missing spec set, and release qualification blocks with the missing fixture contract. **Covers R3, R20, R49-R50.**

## Success Criteria

- Every capability in the pinned Claude/Codex comparison scope has an operator-approved disposition; no source delta disappears through omission.
- Every approved survivor is implemented as an Antigravity-native behavior and carries target-side acceptance evidence.
- No required lifecycle obligation can be marked complete or advanced by `/outcome` without its named evidence.
- Every independently required Gemini strategy has a distinct observed receipt or leaves the phase incomplete.
- Every durable reference-lifecycle artifact is authoritative under `docs/`, with runtime staging state pointing back to it.
- Every active runtime surface in the scoped plugins passes the host-contract check; a required blocking disposition prevents release, while only an explicitly optional capability may carry a degraded disposition supported by proven Antigravity capabilities.
- Blocking deterministic conformance checks pass, and one live `agy`/Gemini reference lifecycle passes both mechanical validation and operator quality review.
- The live lifecycle reaches a validated mission-control handoff packet without unauthorized external mutation.
- A planner can derive implementation sequencing and technical design without inventing port-selection policy, lifecycle completion behavior, artifact authority, release gates, or external-action boundaries.

## Scope Boundaries

**In scope:**

- All six capabilities from the source ideation artifact as one coordinated first release.
- Saga-centered behavior across `fleet-core`, `mission-control`, and `multi-agent-consensus`.
- Claude `team-execution` and Codex-only capabilities as provenance-bearing inputs to the value-and-fit inventory.
- Delivery of the previously approved but currently absent `/impl-spec` capability, its `/doc-review` buildability-probe mode, its shared support references, and its off-chain dispatch integration required by the reference lifecycle.
- The single reference lifecycle, `/outcome` coordination, and the `/loop`/`/resume` reconciliation implementation required to replace the current `/resume` stub.
- Capability negotiation, independent Gemini deliberation, canonical artifact promotion, sanitized regression scenarios, and one live release canary.

**Deferred beyond the first release:**

- Live qualification matrices across every Gemini model, `agy` CLI or Antigravity host version, plugin route, and operating environment.
- Re-running the Claude and Codex baseline lifecycle for every Antigravity release when the approved fixture and semantic baseline have not changed.
- Additional end-to-end reference routes after the shared contracts prove reusable.
- Generalized transcript collection or replay infrastructure beyond the bounded conformance fixtures and release canary.
- Operator dashboards beyond the inspectable receipts and status required for this release.
- The separately approved `/product-review` capability and its dispatch-table entry; this release neither implements nor supersedes that deferred capability.

**Out of scope:**

- `/product-review` implementation or use in the reference lifecycle.
- Mechanical parity, file-for-file copying, and implementing candidates rejected by the approved value-and-fit gate.
- A new Antigravity `team-execution` plugin without a separate product decision.
- A host-neutral intermediate representation or shared cross-host runtime.
- Global use of the highest-cost model or consensus for every task.
- Automatic GitHub issue creation, board changes, merge, deployment, or other remote mutation.
- Claiming schedule, isolation, sandbox, model, effort, or agent behavior that the installed Antigravity runtime cannot prove.
- General code-quality cleanup unrelated to an approved survivor or the conformance needed for this release.

## Dependencies / Assumptions

The release depends on a small set of explicit, evidence-bearing assumptions.

| assumption or dependency | current status | required validation or response |
|---|---|---|
| Claude, Codex, and Antigravity repositories are available at immutable snapshots. The July 25 scan observed Claude `b464d090`, Codex `f79f141`, and Antigravity `aaeac80`. | Testable; historical observations may drift. | Refresh and pin all three revisions during inventory and release qualification. |
| The recorded Antigravity sync point is `099ec4c`. | Validated historical marker, not an authoritative delta. | Let the complete ledger establish the release delta. |
| Claude `team-execution` maps to Antigravity `multi-agent-consensus`. | Validated by existing repository decisions. | Preserve the mapping while value-and-fit decides which source capabilities survive. |
| `/impl-spec` was approved as an off-chain, profile-backed multi-document engine but is absent from the current command and skill surfaces. | Validated implementation gap. | Deliver the capability, buildability-probe support, and dispatch integration without converting it into a stored Saga phase. |
| Current orchestration does not satisfy the reference contract: `/resume` is a stub, general `/loop` treats QA and retro as advisory, and `/outcome` currently coordinates execution leaves rather than the full idea-to-handoff obligation set. | Validated implementation gap. | Deliver R4/R29 reconstruction and the R25 reference-workstream obligation semantics; do not treat current routing as sufficient. |
| Antigravity provides enough bounded execution and conversation control for the live canary. | Testable and unproven until the host doctor runs. | Prove it through the R20 catalog; leave unavailable capabilities unavailable. |
| Complete raw `agy` assistant/tool transcripts are not available. | Validated evidence limitation. | Begin with available summaries, histories, brain artifacts, and operator corrections; add minimized scenarios when better evidence appears. |
| A valid local `agy`/Gemini environment is available for qualification. | Testable release precondition. | Run the capability doctor before the live canary; normal deterministic tests require no live model call. |
| Operator-approved Claude/Codex baseline artifacts exist for the shared fixture. | Required precondition, not assumed complete. | Produce the R55 manifest before the first live qualification and invalidate it when any binding changes. |
| `scripts/validate_plugins.py` is the canonical repository plugin validator. | Validated current contract. | Extend behavioral truth through the host doctor without replacing package validation. |

## Sources / Research

- `docs/ideation/2026-06-27-antigravity-harness-ideation.md` — six ranked survivors, transcript evidence, runtime scan, and cross-host source comparison.
- `docs/brainstorms/2026-06-27-antigravity-harness-requirements.md` — shipped first-generation harness boundary.
- `docs/brainstorms/2026-06-11-impl-spec-and-product-review-requirements.md` and `docs/plans/2026-06-11-impl-spec-product-review-plan.md` — approved `/impl-spec` behavior and the current unlanded implementation plan.
- `STRATEGY.md` — Antigravity-native orchestration direction and plugin portfolio.
- `README.md` — recorded per-plugin source sync points and canonical target plugin names.
- `.agents/skills/port-claude-plugins/SKILL.md` — current port workflow and `team-execution` mapping.
- `docs/plans/2026-06-27-port-current-claude-updates-antigravity.md` — established `team-execution` to `multi-agent-consensus` decision.
- `docs/plans/2026-07-08-port-claude-july-updates-plan.md` and `docs/reviews/2026-07-08-port-claude-july-updates-plan-review.md` — prior semantic classifications, host-adaptation constraints, and review findings.
- `docs/engineering-journal/QUEUED.md` — recorded post-sync Claude drift and deferred team-execution capabilities.
- `docs/FULL_REPO_CODE_REVIEW.md` — prior repository review and the boundary of its semantic prompt/reference coverage.
- `plugins/saga/skills/ideate/SKILL.md`, `plugins/saga/skills/loop/SKILL.md`, `plugins/saga/skills/resume/SKILL.md`, and `plugins/saga/skills/outcome/SKILL.md` — current lifecycle, deliberation, and coordination contracts.
- `plugins/saga/references/saga-spec.md` — current lifecycle phase and durable state contract.
- `scripts/validate_plugins.py` and `scripts/review_canary.py` — existing deterministic plugin and review validation surfaces.
