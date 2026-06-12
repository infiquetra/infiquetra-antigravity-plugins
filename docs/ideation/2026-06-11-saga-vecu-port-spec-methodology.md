# Ideation: Saga Plugin Enhancement — Vecu Port Analysis + Spec Authoring Methodology

**Date:** 2026-06-11
**Run ID:** `235c6929`
**Topic:** Enhancing the Infiquetra saga plugin by selectively porting vecu-claude-plugins capabilities and embedding the campps spec authoring methodology, adapted for Antigravity.
**Prior art:** [2026-06-05-port-claude-plugins.md](file:///Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/docs/ideation/2026-06-05-port-claude-plugins.md) — broader porting ideation; this run is more focused.

## Topic Axes

1. **Skill porting** — Which vecu-saga skills to port, adapt, or skip for Infiquetra
2. **Spec authoring methodology** — Embedding the campps research→author→verify→review→probe pipeline
3. **Non-saga plugin absorption** — Which vecu non-saga plugins to port or absorb as patterns
4. **Antigravity adaptation** — Claude Code → Antigravity tool/convention translation
5. **Lifecycle gap closure** — New lifecycle phases vecu has that Infiquetra doesn't

## Grounding Summary

### Repo context

The Infiquetra saga plugin already has 17 skills: brainstorm, code-review, doc-review, founder-review, handoff, ideate, investigate, loop, office-hours, optimize, plan, qa, resume, retro, spec, strategy, work. The plugin was ported from Claude Code (commit `8fb23bf`, 2026-06-06) with native Antigravity state management. Key constraints:
- Flat `plugin.json` at plugin root, `src/` for shared scripts (per DECISIONS.md)
- `.gemini/` paths, not `.claude/`
- Antigravity tools: `invoke_subagent`, `define_subagent`, `ask_question` (not `AskUserQuestion`, `EnterPlanMode`, `Agent`, `ToolSearch`)
- Artifacts write to the Antigravity brain directory, not just `docs/`

### Vecu-saga context

14-command lifecycle across 6 phases. Notable differences from Infiquetra:
- Has `/product-review` (build-measure-learn gate between ideate and brainstorm) — Infiquetra doesn't
- Has `/work-loop` (combined plan+execute+PR, 621 lines) — Infiquetra splits into `/plan` + `/work`
- Vecu `/spec` is WHAT+HOW with a blueprint translation pipeline — Infiquetra `/spec` is WHAT-only
- Vecu `/doc-review` has a buildability-probe mode — Infiquetra doesn't
- Vecu `/qa` has a deterministic health scorer (`qa_health_score.py`) — Infiquetra doesn't

### Campps spec authoring methodology

A 6-stage pipeline proven on the identity-access service spec (10 probe rounds, ~10.7M tokens):
1. **Research** — grounding brief with open questions + recommended resolutions
2. **Author** — parallel folder authoring in dependency waves with class-closure disciplines (lifecycle closure matrix, cross-record interaction rules, contract↔prose synchronization)
3. **Assemble** — README as last-written root contract
4. **Mechanical verification** — scripted checklist, OpenAPI validation, Mermaid rendering, link resolution, sync sweeps
5. **Review** — dual-lens (security + architecture), P0/P1 fixes before probe
6. **Probe loop** — fresh-agent buildability probe with boundary test, bounded at 3 rounds

The key insight: the buildability probe ("if two reasonable implementers could answer differently and the difference is visible in API behavior, data shape, or UX, it is a spec defect") caught ~30 boundary-test failures with zero false positives. Class-closure disciplines moved to authoring time cut convergence from 10 rounds to an expected 1-3.

### Current `/spec` gaps vs. campps methodology

| Feature | Status | Gap |
|---|---|---|
| Research stage | ❌ | No structured upfront research phase |
| Parallel authoring waves | ❌ | Single-agent serial interview |
| Class-closure disciplines | ❌ | No lifecycle closure matrices |
| Mechanical verification | 🟡 | Optional rubric pass, no automated structural validation |
| Dual-lens review | 🟡 | Two options offered but both optional, not opposing lenses |
| Buildability probe loop | ❌ | No fresh-agent probe or boundary test |

---

## Candidate Ideas

### Axis 1: Skill Porting

#### S1 — Port `/product-review` as a new saga skill
**What:** Add a `/product-review` skill to the Infiquetra saga lifecycle, sitting between `/ideate` and `/brainstorm`. Per surviving idea: name the riskiest assumption, design a minimum experiment, set a measurable threshold, run a premise check, then route (experiment → `/plan`, full-build → `/brainstorm`).
**Basis:** `direct:` vecu-saga `/product-review` SKILL.md — four-step de-risking protocol with revival from near-misses and threshold enforcement.
**Why it matters:** Infiquetra goes directly from `/ideate` → `/brainstorm` with no de-risking step. Ideas that sound good in ideation can carry hidden assumptions that blow up in planning. This gate catches them cheaply. The vecu version's revival mechanism (pulling back close non-survivors from ideation) and threshold enforcement (no routing without a concrete pass/fail metric) are battle-tested.
**Sanitization:** Replace `vecu-sdlc` references with Infiquetra context-library paths. Replace `/plan-task` routing with `/plan` or `/work`. Remove "dealers" domain language. Adapt `product_review.py` script for `src/` layout. Replace `AskUserQuestion` with Antigravity `ask_question`.

#### S2 — Absorb the buildability-probe mode into `/doc-review`
**What:** Add a "buildability probe" mode to the existing `/doc-review` skill. When reviewing multi-document spec sets, spawn a fresh subagent (clean context, no authoring history) that receives only the spec + shared standards and must produce: (1) an implementation breakdown, (2) an exhaustive assumptions-and-questions list per category, (3) per-question boundary-test classification.
**Basis:** `direct:` campps 06-service-implementations README (Definition of Done), spec-authoring-method narrative (§1.2-1.4), vecu `/doc-review` buildability-probe mode.
**Why it matters:** This is the single highest-leverage quality mechanism in the campps methodology. Zero false positives across ~30 findings. The key: a fresh agent, forced enumeration, and the boundary test ("two reasonable implementers could answer differently and the difference is visible in API/data/UX"). Self-review by the authoring agent is structurally worthless — the author's assumptions are invisible to the author. Antigravity's `invoke_subagent` is purpose-built for spawning fresh-context agents.

#### S3 — Port vecu's deterministic QA health scorer into `/qa`
**What:** Add a deterministic 0-100 health score to the existing `/qa` skill, computed from severity-weighted finding counts. Track baseline-from-prior-report for delta reporting across QA runs.
**Basis:** `direct:` vecu `/qa`'s `qa_health_score.py` — arithmetic over LLM-assigned severity, baseline tracking via saga ticks.
**Why it matters:** The current Infiquetra `/qa` produces ship/ship-with-deferred/no-ship verdicts, but the underlying score is a judgment call. A deterministic scorer makes QA verdicts reproducible and trending visible. The delta-from-baseline pattern catches regressions that absolute scores miss.
**Sanitization:** Remove `vecu-test-suite`, `vecu-deploy`, `vecu-e2e-toolkit` evidence source references. Port `qa_health_score.py` to `src/`. Replace VECU-specific risk classes with generic ones.

#### S4 — Port the lifecycle closure matrix concept into `/spec`
**What:** When the target is a stateful service, require the spec to include a lifecycle closure matrix: every entity class × origination / mutation / revocation / reads / events / audit / retention. A blank or contradictory cell is flagged as a defect.
**Basis:** `direct:` campps spec-authoring-method (§2, Stage 2, discipline 1), vecu `/spec` lifecycle closure matrix.
**Why it matters:** This is the class-closure discipline that cut probe convergence from 10 rounds to 1-3. It forces the spec author to systematically close every lifecycle path for every entity rather than addressing them ad hoc. Without it, a 40-document spec has an exponential consistency space that random probes sample but never exhaust.

#### S5 — Skip vecu's combined `/work-loop` — keep Infiquetra's split
**What:** Do NOT port vecu's 621-line combined plan+execute+PR skill. Keep Infiquetra's existing `/plan` + `/work` split.
**Basis:** `direct:` Infiquetra saga README (plan and work are separate skills with clear handoff), DECISIONS.md (2026-06-06 porting decision preserved the split).
**Why it matters:** The split is a deliberate architectural choice. `/plan` owns the interrogation of HOW, producing a durable plan artifact. `/work` owns execution. The vecu combined version is harder to maintain (621 lines), harder to enter from different points, and the Phase −1 `EnterPlanMode` concept is Claude Code-specific with no Antigravity equivalent. The Infiquetra split is cleaner for Antigravity's agent model.

#### S6 — Skip vecu's deploy-strategy detection (Phase 1.5)
**What:** Do NOT port vecu's Phase 1.5 release-intent deploy-strategy detection into saga.
**Basis:** `direct:` Infiquetra `deploy` plugin already handles deployment as a separate concern.
**Why it matters:** Infiquetra separates deploy into its own plugin (`deploy-state` skill with tag-promotion). Baking deploy-strategy detection into the saga work phase couples concerns that are currently clean. The vecu version exists because vecu has Pattern A (sandbox/pre-prod/prod) complexity that Infiquetra doesn't.

---

### Axis 2: Spec Authoring Methodology

#### M1 — Embed the campps 6-stage pipeline as the "implementation spec" mode of `/spec`
**What:** Add a second mode to `/spec`: alongside the existing WHAT-interrogation mode, add an "implementation spec" mode that runs the full campps pipeline: Research → Author (parallel subagent waves) → Assemble → Verify → Review → Probe. This mode activates when the target is a service implementation or any multi-document spec set, not a simple feature spec.
**Basis:** `direct:` campps spec-authoring-method narrative (§2, the full pipeline), 06-service-implementations README (folder contract, completeness checklist, definition of done).
**Why it matters:** The current `/spec` is excellent for single-feature specs (WHAT interrogation). But service-level implementation specs need a fundamentally different approach: parallel authoring across multiple folders, cross-document consistency enforcement, mechanical verification, and the buildability probe. The campps methodology is battle-tested with empirical data (identity-access: 10 rounds → convergence, with clear evidence that class-closure at authoring time is the fix). This would make Infiquetra the only Antigravity plugin ecosystem with a proven service-spec pipeline.
**Key adaptation for Antigravity:** Use `invoke_subagent` for parallel folder authoring waves (Wave 1: architecture, api, models, specifications in parallel; Wave 2: workflows, scenarios, integrations, operations in parallel reading Wave 1 output). Use `define_subagent` to create the fresh-context probe agent. Use Antigravity's scratch directory for intermediate checkpoints.

#### M2 — Extract the research-brief stage as a reusable pre-spec phase
**What:** Make the campps research stage (grounding brief with open questions and recommended resolutions) a standalone phase that fires before both spec modes (simple and implementation). The brief settles forks cheaply before they become expensive probe findings.
**Basis:** `direct:` campps spec-authoring-method (§2, Stage 1): "Every question resolved at brief time costs one decision. The same question discovered by a probe in round 6 costs a full probe round (~500K tokens)."
**Why it matters:** The campps narrative explicitly identifies this as the highest-leverage artifact in the pipeline. The current `/spec` Phase 3 reads code but doesn't produce a structured research brief. Front-loading discovery (settled decisions with sources, entity inventories, cross-spec obligations, divergences, open questions with cost-of-deciding-wrong) prevents the expensive tail of probe-fix-probe cycles.

#### M3 — Implement the boundary test as a reusable skill primitive
**What:** Extract the campps boundary test ("if two reasonable implementers could answer differently and the difference is visible in API behavior, data shape, or user experience, it is a spec defect") as a reusable validation primitive that `/spec`, `/doc-review`, and `/qa` can invoke.
**Basis:** `direct:` campps 06-service-implementations README (Definition of Done, probe protocol), spec-authoring-method narrative (§1.2, §1.3).
**Why it matters:** The boundary test is the sharpest quality criterion in the campps methodology. It's currently described only in prose. Codifying it as a reusable primitive — with the per-question classification protocol, the forced enumeration, and the PASS/FAIL verdict — means any saga skill that needs to judge "is this spec complete enough?" can invoke the same standard. It also makes the criterion discoverable and citable in engineering journal entries.

#### M4 — Add the operator playbook as an interactive mode for the implementation spec pipeline
**What:** Implement the campps operator playbook (§4) as the default interactive mode: Research (operator decides open questions) → Author (agents write, operator skims closure matrix) → Verify (scripted) → Review (operator triages P0/P1) → Probe (new session, operator answers boundary-test failures) → Remediate.
**Basis:** `direct:` campps spec-authoring-method (§4, the operator playbook).
**Why it matters:** The autonomous pipeline is powerful but expensive (identity-access: ~$1.3-1.4K). The operator playbook converts "review 40 documents" into "answer five concrete questions," which takes an hour and is the part of this only the human can do best. For judgment-heavy specs (payments, UI), operator-in-the-loop settles forks definitively; agents re-litigate at the margins. Antigravity's `ask_question` tool is well-suited for the structured question presentation.

---

### Axis 3: Non-Saga Plugin Absorption

#### P1 — Port `vecu-test-suite` as a saga-adjacent tool
**What:** Port the parallel test runner (pytest + ruff + mypy + bandit in `concurrent.futures`) as a tool under `plugins/saga/src/` or as a standalone tool. Consolidates HTML reports, enforces configurable coverage thresholds.
**Basis:** `direct:` vecu-test-suite README — parallel execution of 4 quality tools, coverage enforcement, JSON output.
**Why it matters:** Maps directly to Infiquetra's coding standards (ruff 100-char, mypy, bandit, pytest 80% floor). Running them in parallel saves wall-clock time. The consolidated report is consumable by `/qa` and `/code-review`. This is table-stakes tooling that every repo benefits from.
**Sanitization:** Minimal — remove VECU project structure references, adapt for Infiquetra pyproject.toml conventions.

#### P2 — Port `vecu-working-sessions` as a new saga skill
**What:** Add a `/working-session` skill that transforms meeting transcripts (VTT/TXT/SRT) into structured documentation: decisions (TD-NNN), open questions (OQ-NNN), action items (AI-NNN), spec impacts. Multi-agent review (documentarian + quality reviewer + devil's advocate, ≥9.0/10 consensus, max 3 cycles).
**Basis:** `direct:` vecu-working-sessions README — 13-section canonical template, cross-document ID consistency, multi-agent review pipeline.
**Why it matters:** Meeting transcripts are a common input to the Infiquetra lifecycle. Decisions made in meetings need to be captured with the same rigor as decisions made in code review. The cross-document ID system (TD-NNN, OQ-NNN, AI-NNN) makes decisions traceable. The multi-agent review pipeline ensures quality.
**Sanitization:** Remove VECU team references. Remove Microsoft 365 MCP connector references. Adapt for Antigravity subagent patterns.

#### P3 — Port `vecu-team-execution` patterns into `multi-agent-consensus`
**What:** Absorb vecu-team-execution's keyword-driven reviewer selection, triage escape hatch for trivial changes, and structured validator pipeline into the existing Infiquetra `multi-agent-consensus` plugin.
**Basis:** `direct:` vecu-team-execution README — Phase A→B auto-handoff, keyword-driven optional reviewers, 3-base + 7-optional reviewer architecture, ≥9.0/10 consensus threshold, `bypassPermissions` for workers.
**Why it matters:** The current `multi-agent-consensus` plugin is functional but less mature than vecu-team-execution's. The keyword-driven reviewer selection (security keywords trigger security reviewer, API keywords trigger API reviewer) reduces noise on simple changes. The triage escape hatch prevents heavyweight review of trivial fixes.
**Sanitization:** Remove VECU ADR reviewer, VECU-specific validator scripts (wizcli/Wiz), tmux integration (Antigravity has its own UI). Keep the keyword-driven selection, triage, and consensus patterns.

#### P4 — Skip `todoist-manager` for now
**What:** Do NOT port todoist-manager into the Infiquetra ecosystem yet.
**Basis:** While it has zero enterprise dependencies and is well-documented, it's a personal productivity tool that uses the claude.ai MCP connector — a Claude-specific integration path.
**Why it matters:** The MCP connector dependency is the blocker. Antigravity doesn't have the same claude.ai Todoist connector. A proper port would need a Todoist API key-based integration, which is a different effort entirely. The concept is sound but the implementation path diverges too much.

---

### Axis 4: Antigravity Adaptation

#### A1 — Codify the Claude→Antigravity tool translation table as a reference doc
**What:** Create a `references/claude-to-antigravity-mapping.md` in the saga plugin that maps every Claude Code tool/concept to its Antigravity equivalent. This becomes the canonical reference for all porting work.
**Basis:** Cross-cutting from all vecu skills — `EnterPlanMode` → (no equivalent, use plan artifact + confirmation gate), `AskUserQuestion` → `ask_question`, `Agent`/`Skill` → `invoke_subagent`/`define_subagent`, `ToolSearch` → (not needed, tools are registered), etc.
**Why it matters:** Every skill being ported hits the same translation questions. A canonical mapping document prevents inconsistency and speeds future ports. It also documents what has NO equivalent (like `EnterPlanMode`) so we design around it rather than silently dropping the capability.

#### A2 — Use `define_subagent` for probe freshness instead of "new session"
**What:** The campps probe protocol requires a "fresh agent, every round" — no contamination from authoring context. In Claude Code, this means a literal new session. In Antigravity, use `define_subagent` to create a purpose-built probe agent with a clean system prompt and invoke it via `invoke_subagent`. The subagent's conversation context is inherently fresh.
**Basis:** `direct:` campps spec-authoring-method (§1.3, "Non-negotiable: the probe agent must not have seen the authoring context"), Antigravity `define_subagent`/`invoke_subagent` tools.
**Why it matters:** This is the cleanest Antigravity-native implementation of the probe freshness requirement. `define_subagent` creates a new agent type; `invoke_subagent` creates a new conversation with no prior context. The probe's system prompt can include the protocol rules (forced enumeration, boundary test, hard verdict) as first-class instructions rather than hoping the agent follows a long prompt.

#### A3 — Replace script orchestration with subagent fanout for parallel authoring
**What:** Where vecu uses Python scripts to orchestrate sequential operations, and the campps methodology uses "agents in dependency waves," implement parallel authoring waves as parallel `invoke_subagent` calls. Wave 1 agents (architecture, api, models, specifications) run simultaneously; when all complete, Wave 2 agents (workflows, scenarios, integrations, operations) launch reading Wave 1 output from disk.
**Basis:** `direct:` campps spec-authoring-method (§2, Stage 2), Antigravity `invoke_subagent` parallel dispatch.
**Why it matters:** Antigravity's multi-agent tools are purpose-built for this pattern. Unlike Claude Code's script-based approach, `invoke_subagent` with multiple entries runs genuinely parallel agents with independent conversation contexts. This is the native Antigravity advantage — the platform was designed for multi-agent workflows.

---

### Axis 5: Lifecycle Gap Closure

#### L1 — Close the think→plan gap with `/product-review`
**What:** Same as S1 — the gap is: Infiquetra has no de-risking step between `/ideate` (divergent generation) and `/brainstorm` (convergent requirements). `/product-review` fills it.
**Basis:** Same as S1.

#### L2 — Close the spec→build gap with the buildability probe
**What:** Same as S2 — the gap is: Infiquetra has no formal "is this spec actually buildable?" gate. Specs go to `/plan` and `/work` without proof they contain enough information to build from.
**Basis:** Same as S2.

#### L3 — Close the implementation-spec gap with the full campps pipeline
**What:** Same as M1 — the gap is: Infiquetra's `/spec` handles feature specs well but has no mode for service-level implementation specs (multi-document, cross-folder, multi-agent authoring).
**Basis:** Same as M1.

---

## Critique & Convergence

### Rejection Criteria Applied

Every candidate was evaluated against:
1. **Grounded in evidence?** Does it solve a documented problem or fill a verified gap?
2. **Implementable in Antigravity?** Can it use native Antigravity tools, or does it require Claude Code-specific features?
3. **Worth the token cost?** Does the expected value justify the implementation + ongoing maintenance cost?
4. **Non-redundant?** Does it add capability Infiquetra doesn't already have?

### Survivors (Recommended for brainstorm/planning)

| ID | Idea | Axis | Recommendation |
|---|---|---|---|
| **S1** | Port `/product-review` | Skill porting | **BRAINSTORM** — genuinely novel lifecycle phase, no Infiquetra equivalent |
| **S2** | Buildability probe in `/doc-review` | Skill porting | **BRAINSTORM** — highest-leverage quality mechanism, proven zero false positives |
| **S4** | Lifecycle closure matrix in `/spec` | Skill porting | **BRAINSTORM** — proven to cut probe convergence from 10 rounds to 1-3 |
| **M1** | Implementation spec pipeline in `/spec` | Methodology | **BRAINSTORM** — the flagship capability, unique in the Antigravity ecosystem |
| **M2** | Research-brief pre-spec phase | Methodology | **BRAINSTORM** — highest-leverage artifact per campps evidence |
| **M3** | Boundary test as reusable primitive | Methodology | **BRAINSTORM** — enables consistent quality criterion across skills |
| **A2** | `define_subagent` for probe freshness | Adaptation | **PLAN DIRECTLY** — implementation is straightforward, mechanism is clear |
| **A3** | Subagent fanout for parallel authoring | Adaptation | **PLAN DIRECTLY** — Antigravity-native pattern, well-understood |
| **P1** | Port test-suite as saga tool | Non-saga | **PLAN DIRECTLY** — minimal sanitization, clear value |

### Rejected (with reasons and revival conditions)

| ID | Idea | Reason | Revive when |
|---|---|---|---|
| **S3** | QA health scorer | Low priority relative to the spec methodology work. The current `/qa` verdicts work. A deterministic scorer adds precision but not new capability. | QA verdicts are inconsistent across runs, or trending is needed for reporting |
| **S5** | Skip combined work-loop | DECISION, not an idea — recorded as a "keep the existing split" confirmation | Never (architectural choice) |
| **S6** | Skip deploy-strategy detection | DECISION — deploy is a separate plugin concern | Infiquetra adopts multi-env deploy complexity |
| **M4** | Operator playbook as interactive mode | Deferred — adds complexity to M1 before M1 is proven in Infiquetra. Build M1 autonomous-first, then add operator-in-the-loop as a second phase. | M1 is implemented and the autonomous pipeline cost is measured |
| **P2** | Port working-sessions | Good concept but lower priority than the spec methodology work. No current Infiquetra use case for meeting transcript processing. | Infiquetra teams regularly record and need to reference meeting decisions |
| **P3** | team-execution → multi-agent-consensus | Good patterns but the multi-agent-consensus plugin was already ported. Absorbing vecu patterns is enhancement, not gap closure. | multi-agent-consensus review quality is insufficient |
| **P4** | Skip todoist-manager | MCP connector dependency makes it impractical for Antigravity | Antigravity gains native Todoist MCP or API integration |
| **A1** | Claude→Antigravity mapping doc | Useful but incremental — the mapping is already understood from the June 5 ideation and the porting work. A formal doc would be reference material, not a capability. | A third contributor starts porting and needs the reference |

### Implementation Order (recommended)

The survivors cluster into two natural workstreams:

**Workstream 1 — Spec methodology (the flagship):**
1. M2 (research-brief) — prerequisite for everything else, smallest standalone piece
2. S4 (lifecycle closure matrix) — extends `/spec` with the class-closure discipline
3. M3 (boundary test primitive) — extract the reusable quality criterion
4. S2 (buildability probe in `/doc-review`) — uses M3, needs A2
5. A2 (`define_subagent` for probe freshness) — technical enabler for S2
6. M1 (full implementation spec pipeline in `/spec`) — the capstone, uses everything above
7. A3 (subagent fanout for parallel authoring) — technical enabler for M1

**Workstream 2 — Lifecycle enhancement:**
1. S1 (port `/product-review`) — independent, can run in parallel with Workstream 1
2. P1 (port test-suite) — independent, can run in parallel

---

## Next Steps

> [!IMPORTANT]
> The spec methodology workstream (M1/M2/M3/S2/S4/A2/A3) is the high-value core of this ideation. It would make Infiquetra's saga plugin the only Antigravity plugin ecosystem with a proven, multi-agent service-spec pipeline backed by empirical evidence from the campps identity-access experience.

Route recommendations:
- **Workstream 1 survivors** → `/brainstorm` to deep-dive the implementation spec pipeline as a cohesive design (M1+M2+M3+S2+S4+A2+A3 as one topic)
- **S1 (`/product-review`)** → `/brainstorm` separately (independent lifecycle addition)
- **P1 (test-suite)** → `/plan` directly (well-understood port, no design questions)
