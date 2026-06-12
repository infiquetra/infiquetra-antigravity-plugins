---
date: 2026-06-11
topic: impl-spec-and-product-review
maturity: requirements-ready
source: docs/ideation/2026-06-11-saga-vecu-port-spec-methodology.md — Workstream 1 (M1, M2, M3, S2, S4, A2, A3) and Workstream 2 (S1)
---

# Implementation Spec Pipeline and Product Review

## Summary

Add two new saga skills and supporting infrastructure to the Infiquetra saga plugin: `/impl-spec` for authoring comprehensive, buildable multi-document spec sets in context-library repos using a 6-stage pipeline with parallel subagent authoring and a bounded probe-remediation loop; and `/product-review` for deciding whether to prototype or experiment before committing to a full spec-and-build. A buildability probe mode is added to `/doc-review` as a composable quality gate.

## Problem Frame

The Infiquetra saga plugin handles feature-level specs well through `/spec` (convergent WHAT-interrogation). But context-library repos (campps-context-library, mimir-context-library, and future ones) produce multi-document spec sets — service implementations with architecture, API contracts, data models, workflows, and operational runbooks spanning 5-25K lines across 8+ folders. The current `/spec` skill is not designed for this: it produces a single-document feature spec, has no parallel authoring capability, no cross-document consistency enforcement, and no buildability probe.

The campps identity-access service spec ran through 10 probe rounds (~$1.3K in tokens) before the method was refined. With class-closure disciplines moved to authoring time, subsequent specs are expected to converge in 1-3 rounds at roughly a third of the cost. The method works, but it exists only as prose in a narrative doc and manual operator prompts — not as an executable saga skill.

Separately, the saga lifecycle has no "should we experiment first?" gate. Ideas flow from `/ideate` through `/brainstorm` to `/spec` or `/plan` without a structured decision point for whether empirical validation should precede a full build commitment.

## Key Decisions

**D1. `/impl-spec` is a new skill, not a mode of `/spec`.** The existing `/spec` stays WHAT-only for feature specs. `/impl-spec` runs the full 6-stage pipeline for multi-document spec sets. This avoids a monolithic skill (the vecu `/work-loop` at 621 lines is the cautionary example) and keeps each skill focused.

**D2. Generalized method, project-specific schema.** `/impl-spec` implements the 6-stage pipeline (research → author → verify → review → probe+remediate) as a reusable method. The folder contract — which folders to author, which files each folder must contain, and what "complete" means — is discovered by scanning the target directory's README for a folder contract table. No CAMPPS structure is baked into the skill.

**D3. Schema discovery, not configuration.** The skill scans the target directory for an existing spec-schema README (like campps' `06-service-implementations/README.md`) and derives the folder structure and completeness checklist from it. No machine-readable YAML/JSON spec schema is required. This keeps the barrier low for existing context-libraries.

**D4. Buildability probe lives in `/doc-review`, composed by `/impl-spec`.** The probe mode is a reusable capability of `/doc-review`, independently callable on any spec set. `/impl-spec` auto-invokes it as Stage 6. This means manually-written specs benefit from the probe too.

**D5. Probe freshness via `define_subagent`.** The campps probe protocol requires a fresh agent with no authoring context. In Antigravity, `define_subagent` creates a purpose-built probe agent type; `invoke_subagent` creates a conversation with clean context. The probe's system prompt includes the protocol rules (forced enumeration, boundary test, hard verdict) as first-class instructions.

**D6. Configurable interaction model.** The operator chooses autonomous or interactive mode at invocation. Autonomous runs stages 1-6 with minimal gates. Interactive pauses at each stage for operator input (research brief decisions, closure matrix review, finding triage, boundary-test failure answers). Mixable per spec per the campps recommendation: autonomous for mechanically constrained specs, interactive for judgment-heavy ones.

**D7. `/product-review` is independent from `/impl-spec`.** They serve different use cases: `/product-review` is for new product bets ("should we prototype first?"); `/impl-spec` is for known services that need thorough specs. They rarely overlap.

**D8. Shared reference docs for reusable quality primitives.** The boundary test protocol, lifecycle closure matrix template, and probe protocol live as reference docs in `saga/references/` that multiple skills can load. Consistent with how `saga/references/formatting-style.md` already works.

## Actors

A1. **Operator** — the human using saga skills interactively. Makes product decisions at gates, answers boundary-test failures in interactive mode, chooses autonomous vs interactive, selects the spec target.

A2. **Orchestrator agent** — the main saga agent running `/impl-spec`. Manages the 6-stage pipeline, dispatches subagents, consolidates results, handles remediation.

A3. **Authoring subagents** — spawned by the orchestrator in parallel waves. Each authoring subagent writes one folder's documents. Wave 1 agents are independent; Wave 2 agents read Wave 1 output from disk.

A4. **Probe subagent** — a purpose-built fresh-context agent spawned via `define_subagent`. Receives only the spec folder set and shared standards. Produces the implementation breakdown, assumptions-and-questions enumeration, and boundary-test classifications. Has no knowledge of the authoring process.

A5. **Remediation subagents** — spawned when the probe finds defects. Fix the *class* each finding represents across the entire folder set, not just the cited line.

## Requirements

### `/impl-spec` skill

R1. The skill runs the 6-stage pipeline: Research → Author (parallel waves) → Assemble → Verify → Review → Probe+Remediate. Each stage is a named phase in the SKILL.md with clear entry/exit criteria.

R2. Stage 1 (Research) compiles a grounding brief before authoring begins: settled decisions with sources, entity and endpoint inventories implied by existing docs, cross-spec obligations from already-shipped specs, divergences between the spec directory and reality, and open questions each with a recommended resolution and cost-of-deciding-wrong.

R3. Stage 2 (Author) dispatches authoring subagents in dependency waves. Wave 1 agents (folders with no cross-folder dependencies) run in parallel via a single `invoke_subagent` call. Wave 2 agents (folders that depend on Wave 1 output) launch after all Wave 1 agents complete, reading Wave 1 output from disk. The folder sets and wave ordering are derived from the discovered spec schema. If the schema README does not declare inter-folder dependencies, all folders default to Wave 1 (fully parallel).

R4. Stage 2 enforces three class-closure disciplines as authoring deliverables, not afterthoughts: (a) a lifecycle closure matrix for stateful specs — every entity class × origination/mutation/revocation/reads/events/audit/retention, with no blank or contradictory cells; (b) cross-record interaction rules referenced from a canonical source, not re-derived per spec; (c) contract↔prose synchronization — every field, enum, and error code exists in both contract files and prose, checked both directions.

R5. Stage 3 (Assemble) rewrites the service/spec-set README last, as the root contract. READMEs written first drift; written last they index reality.

R6. Stage 4 (Verify) runs all scriptable checks before any review: completeness checklist audit against the discovered spec schema, link resolution for every relative link, cross-document count consistency (entities, events, endpoints quoted identically everywhere). Additional validators (OpenAPI validation, Mermaid rendering) run when applicable contract files are present.

R7. Stage 5 (Review) runs at least two review lenses before the probe: a security/access-control lens and a consistency/standards-alignment lens. P0/P1 findings from review are fixed before the probe runs.

R8. Stage 6 (Probe+Remediate) invokes `/doc-review`'s buildability-probe mode. If the probe returns FAIL, the skill spawns remediation subagents that fix the *class* each finding represents (sweep the pattern folder-wide, update the closure matrix), then re-invokes the probe with a fresh subagent. Bounded at 3 rounds. If round 3 still fails, findings escalate to the operator with the residue.

R9. The operator chooses autonomous or interactive mode at invocation. In autonomous mode, stages 1-6 run with minimal gates (only the probe-failure escalation at round 3 is a hard gate). In interactive mode, every stage pauses for operator input: the operator decides research brief open questions (Stage 1), skims the closure matrix (Stage 2), triages review findings (Stage 5), and answers boundary-test failures from the probe (Stage 6).

R10. Schema discovery: the skill reads the target directory's README (or a spec-standard README the operator points to) and derives the folder contract (which folders, which files per folder, completeness criteria). It does not require a separate machine-readable schema file.

R11. The skill is off-chain (does not write saga ticks) and does not commit or push. Its output is the spec folder set on disk, ready for the operator to commit. The planning phase should consider a lightweight progress checkpoint (scratch file, not saga) so a crashed session can resume mid-pipeline rather than restart from Stage 1.

### `/product-review` skill

R12. The skill is an off-chain advisory gate for deciding whether to prototype/experiment before committing to a full spec-and-build. It is callable from anywhere in the saga lifecycle.

R13. Per idea or proposal under review, the skill: (a) names the riskiest assumption — the one that, if wrong, wastes the most invested work; (b) designs the smallest build-to-learn experiment that would validate or falsify that assumption; (c) sets a measurable success threshold with a concrete pass/fail criterion; (d) runs a premise check — is the assumption already validated by existing evidence, code, or data?

R14. The skill routes to one of three outcomes: (a) *experiment* — the assumption is unvalidated and worth testing, routes to `/plan` with an experiment-scoped plan; (b) *full build* — the assumption is already validated or the risk is acceptably low, routes to `/brainstorm`; (c) *park* — the idea is not worth the experiment cost right now, records the deferral with a "worth it when" trigger.

R15. The skill accepts input from any lifecycle point: a `/ideate` survivor, a `/brainstorm` output, a direct operator ask, or an issue reference. It does not require a specific upstream artifact.

R16. The skill requires a concrete pass/fail threshold before routing to experiment. An idea without a measurable success criterion cannot proceed to experiment — it stays in the review until one is defined.

### Buildability probe mode in `/doc-review`

R17. `/doc-review` gains a "buildability probe" mode, invocable independently or by `/impl-spec` Stage 6. The mode is triggered when: (a) the operator explicitly requests it, (b) `/impl-spec` invokes it, or (c) the target is classified as a multi-document spec set.

R18. The probe spawns a fresh subagent via `define_subagent` + `invoke_subagent`. The subagent receives only the spec folder set and shared standards (no authoring context, no prior probe artifacts, no remediation notes). The system prompt includes the probe protocol as first-class instructions.

R19. The probe subagent produces a single artifact with: (a) an implementation breakdown — repos, stacks/modules, every endpoint, every data entity, every event published/consumed, a test plan; (b) an exhaustive assumptions-and-questions list enumerated per category (product, architecture, data, API, operations) — empty categories are declared explicitly; (c) per-question boundary-test classification with reasoning.

R20. The boundary test is: "If two reasonable implementers could answer differently and the difference is visible in API behavior, data shape, or user experience, it is a spec defect." Questions that pass the boundary test are spec defects. Method names, internal code organization, and operational configuration are execution-time discoveries, not defects.

R21. The probe verdict is PASS only at zero boundary-test defects. The spec gets fixed, never the probe. The probe artifact is committed as `docs/reviews/YYYY-MM-DD-<subject>-buildability-probe[-rN].md`.

### Shared reference docs

R22. A `saga/references/buildability-probe-protocol.md` reference doc captures: the boundary test definition, the probe input constraints (exactly what the probe subagent receives), the forced enumeration requirement, the per-question classification protocol, and the hard verdict rule. `/impl-spec` and `/doc-review` both load this reference.

R23. A `saga/references/lifecycle-closure-matrix-template.md` reference doc provides the entity × lifecycle-operation matrix template with column definitions (origination, mutation, revocation/termination, reads, events, audit, LWW verdict/conflict strategy, retention, re-grant rules) and the rule that a blank or contradictory cell is a defect. `/impl-spec` loads this during Stage 2 authoring.

### Lifecycle integration

R24. Both `/impl-spec` and `/product-review` are added to the `/loop` dispatch table as routable commands. `/impl-spec` accepts `spec-ready` or `requirements-ready` maturity input and produces spec folder sets. `/product-review` accepts any maturity input and produces `experiment-ready` or `full-build-ready` routing decisions.

R25. The lifecycle routing chain is updated: `/ideate` or `/brainstorm` can route to `/product-review`. `/product-review` can route to `/plan` (experiment) or `/brainstorm` (full build). `/impl-spec` can route to `/doc-review` (probe) and `/work` (build from the spec).

## Key Flows

F1. **Full autonomous `/impl-spec` run.** **Trigger:** Operator invokes `/impl-spec` on a context-library spec directory in autonomous mode. **Steps:** (1) Skill scans target README for folder contract. (2) Stage 1: research subagent compiles grounding brief, skill auto-decides open questions based on available evidence. (3) Stage 2: Wave 1 authoring subagents run in parallel (one per independent folder), Wave 2 subagents run after Wave 1 completes. Class-closure disciplines enforced. (4) Stage 3: README assembled from authored content. (5) Stage 4: mechanical verification runs. (6) Stage 5: security + consistency review subagents run, P0/P1 auto-remediated. (7) Stage 6: `/doc-review` probe mode invoked with fresh subagent. If FAIL, remediation subagents fix the class, re-probe. Bounded at 3 rounds. **Covers R1, R2, R3, R4, R5, R6, R7, R8, R9.**

F2. **Interactive `/impl-spec` run.** Same as F1 but: after Stage 1, operator reviews the research brief and decides each open question. After Stage 2, operator skims the lifecycle closure matrix. After Stage 5, operator triages review findings (P0/P1 must be fixed; P2/P3 operator decides). After Stage 6 probe failure, operator answers each boundary-test defect (product fork: operator decides; spec mechanics: delegates the fix; disagrees with classification: overrules in writing). **Covers R9.**

F3. **Independent buildability probe.** **Trigger:** Operator invokes `/doc-review` on a multi-document spec set and selects probe mode, or `/doc-review` auto-classifies the target as probe-eligible. **Steps:** (1) Probe subagent defined with protocol rules. (2) Subagent spawned with exactly the spec inputs. (3) Subagent produces the artifact. (4) Findings surfaced to operator. **Covers R17, R18, R19, R20, R21.**

F4. **`/product-review` experiment routing.** **Trigger:** Operator invokes `/product-review` on an idea, brainstorm output, or issue reference. **Steps:** (1) Skill identifies the riskiest assumption. (2) Skill designs the smallest validation experiment. (3) Skill proposes a measurable threshold. (4) Premise check: is the assumption already validated? (5) Route: experiment → `/plan` with experiment scope; validated → `/brainstorm`; not worth it → park with "worth it when." **Covers R12, R13, R14, R15, R16.**

## Acceptance Examples

AE1. **Schema discovery from an existing context-library.** Given the campps-context-library with `platform-specs/06-service-implementations/README.md` containing the folder contract table, `/impl-spec` parses the table and derives: 8 folders (architecture, api, models, specifications, workflows, scenarios, integrations, operations), required files per folder (e.g. `service-architecture.md`, `multi-region.md`, `security-architecture.md` for architecture/), and completeness criteria (e.g. "OpenAPI 3.1 validates; every endpoint appears in endpoint-specifications.md"). The operator does not need to create a separate schema file. **Covers R10.**

AE2. **Probe catches a boundary-test defect, remediation fixes the class.** The probe surfaces: "Unlisted service calls — does the API return 401 or 403? Two defensible readings exist in the docs; the difference is on the wire." This is classified as a defect (boundary test: two implementers could answer differently, visible in API behavior). Remediation subagent: (a) decides 403 (or escalates to operator in interactive mode), (b) sweeps every endpoint doc for the same ambiguity, (c) updates the authorization table, (d) updates the error catalog. Re-probe with a fresh subagent confirms the class is closed. **Covers R4, R8, R20, R21.**

AE3. **`/product-review` parks an idea.** Operator asks `/product-review` about a notification system. Riskiest assumption: "users will actually read and act on notifications" — no existing evidence of notification engagement. Smallest experiment: instrument a manual email notification for 2 weeks, track open and action rates. Threshold: ≥30% open rate and ≥10% action rate within 48 hours. Premise check: no existing data. Route: the experiment cost (2 weeks of manual emails) is disproportionate to the current priority. Park with "worth it when: the core product has ≥50 active users providing a measurable engagement baseline." **Covers R13, R14, R16.**

## Scope Boundaries

**In scope:**
- SKILL.md files for `/impl-spec` and `/product-review`
- New buildability-probe mode in `/doc-review` SKILL.md
- Shared reference docs: `buildability-probe-protocol.md`, `lifecycle-closure-matrix-template.md`
- Dispatch table updates for `/loop`
- Product requirements and behavioral decisions

**Explicitly out of scope:**
- Modifying existing `/spec` (stays as-is)
- Auto-detection of "/spec or /impl-spec?" (operator chooses)
- Baking in the CAMPPS folder structure (generalized schema discovery instead)
- Porting vecu-test-suite (separate effort)
- Any Claude Code-specific patterns
- Python scripts or implementation code (deferred to `/plan`)
- The vecu `/work-loop` combined plan+execute pattern (Infiquetra keeps `/plan` + `/work` split)

## Dependencies / Assumptions

- Context-library repos have a README with a parseable folder contract (table or structured list of folders, files, and completeness criteria). If no folder contract exists, `/impl-spec` asks the operator to describe the structure.
- Antigravity's `define_subagent` and `invoke_subagent` provide conversation-level isolation sufficient for probe freshness (no leakage of parent context into the subagent's conversation).
- The existing `lifecycle_review.py` rubric engine can be extended with new review phases without architectural changes.
- The dispatch table (`loop/references/dispatch-table.md`) is the single authoritative routing map and can accommodate two new entries.

## Sources / Research

- campps-context-library `docs/engineering-journal/narratives/2026-06-11-spec-authoring-method.md` — the campps 6-stage pipeline with empirical data from identity-access (10 probe rounds, ~$1.3K, ~30 boundary-test failures with zero false positives)
- campps-context-library `platform-specs/06-service-implementations/README.md` — the campps folder contract, completeness checklist, and buildability probe protocol
- vecu-claude-plugins `plugins/vecu-saga/skills/spec/SKILL.md` — vecu's WHAT+HOW spec with blueprint translation (inspiration for lifecycle closure matrix, not directly ported)
- vecu-claude-plugins `plugins/vecu-saga/skills/product-review/SKILL.md` — vecu's build-measure-learn gate (inspiration for experiment routing and threshold enforcement)
- [Prior ideation](docs/ideation/2026-06-11-saga-vecu-port-spec-methodology.md) — survivors M1, M2, M3, S1, S2, S4, A2, A3
- [DECISIONS.md](docs/engineering-journal/DECISIONS.md) — formatting contract (2026-06-08), script consolidation, agent promotion, porting decision (2026-06-06)
- Current `/spec` SKILL.md — 177 lines, WHAT-only, 5 phases, stays unchanged
- Current `/doc-review` SKILL.md — rubric engine via `lifecycle_review.py`, extensible with new phase directories
