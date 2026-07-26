---
date: 2026-06-27
updated: 2026-07-26
topic: antigravity-harness
focus: Improve Saga and adjacent Antigravity plugins through current cross-host parity, lifecycle proof, Gemini delegation receipts, durable artifacts, AGY runtime truth, and transcript-derived conformance.
scope: broad
repo: infiquetra-antigravity-plugins
maturity: idea-ready
run_id: be1e4941
---

# Ideation: Antigravity Harness

## Grounding Context

**Repo:** The current target is canonical `main`/`origin/main` `aaeac80`; only unrelated `.serena/project.yml` state is dirty. The repository remains a Python 3.12/uv monorepo built around plugin-per-domain and Antigravity-native orchestration. The June 27 harness already shipped the plugin doctor, lifecycle router, generic-ask compiler, Gemini review appliance, citation canaries, and escalation policy.

The July 11 whole-repository review was followed by merged remediation in PR #9. Its documented blind spot was deep semantic review of the large Saga prompt/reference corpus, and current inspection found active host leaks such as `.claude/*` delegation paths, `AskUserQuestion`, Claude Workflow APIs, an unproven `schedule` claim, fixed brain-root assumptions, and isolation promises stronger than local AGY help establishes.

Current target checks are strong but not complete: `uv run pytest -q plugins/saga` passed 799 tests with one skip, Ruff passed, and the plugin doctor passed with one intentional/inert `fleet-core` warning. Targeted mypy still reports 13 `no-any-return` errors in eight Saga scripts.

**Context-libraries:** `infiquetra-context-library` establishes that host variants are native adapters rather than mirrors. It calls for capability matrices, intentional-difference records, source snapshots and revisit triggers, real discovery/execution smoke tests, typed interfaces, durable repository journals, and external fitness signals instead of LLM self-reported success (`docs/ideation/2026-05-27-codex-plugin-strategy.md:91-190`, `docs/brainstorms/2026-05-27-codex-plugin-repo-requirements.md:93-172`, `platform-specs/05-technical-specifications/fitness-signal.md:9-36`).

**Named repos:** `infiquetra-claude-plugins` canonical `origin/main` was fetched on July 25 at `b464d090`. This target records `099ec4c`, leaving 161 commits and 248 relevant changed files across the selected surface, including 141 Saga files and 33 team-execution files. Current Claude contracts add durable gates, intent envelopes, level-triggered reconciliation, liveness and lease fences, evidence-derived settlement, typed findings, provider trust, receipts, and a cross-runtime Outcome contract.

`infiquetra-codex-plugins` canonical `origin/main` is `f79f141`. Its active direction is a minimal host-native orchestration kernel: one Git owner, an explicit workflow contract, actual profile/model/effort/permission readback, typed worker results, independent review, native-runtime authority, and durable `docs/*` artifacts with `.codex/saga/` as rebuildable cache. Verified Workflows replaced historical team-execution.

**AGY runtime evidence:** Local evidence covered 21 repository-scoped conversation summaries with 5,831 recorded steps, 465 prompt-history entries, and six relevant brain-artifact sessions from June 6 through July 9. Two sessions required explicit correction about brain artifacts versus durable repository documents, two corrections asked whether required lifecycle or doc-review gates had actually run, and three sessions showed runtime assumptions outpacing live proof. Full assistant/tool-call transcripts were not available, so these counts are conservative.

The transcript evidence also corrects one premise: Antigravity can produce structured multi-frame ideation. Sampled runs contained multiple frames, axes, survivor/cut logic, and revival conditions, while the tracked skill specifies adaptive 1–6 frames, recovery, same-pool user seeds, and opt-in `docs/ideation/` persistence. The practical gap is unreliable execution, persistence, and continuation—not absence of the method.

**Installed CLI:** Local `agy` is 1.1.7 and Antigravity is 2.3.1. Safe help exposes bounded prompt mode, conversation resume, project roots, model and effort selection, plan/accept-edits mode, sandbox, agents, and plugin validate/link/install operations. No documented schedule/background or transcript-export command was found, and three runtime families exist under `.gemini/antigravity-cli`, `.gemini/antigravity`, and `.gemini/antigravity-ide`.

The optional external generator lane was unavailable because this repository does not contain the Saga external-action runtime; all six native ideation frames completed.

## Topic Axes

1. **Cross-host capability parity and port governance** — selectively absorb semantic advances without copying source-host mechanics.
2. **Lifecycle orchestration and gate completion** — prove that the intended Saga route actually advances through required gates.
3. **Gemini reasoning and delegation quality** — make frames, roles, model/effort, fanout, and adjudication observable.
4. **Durable artifacts, state, and resume** — keep tracked documents authoritative while runtime artifacts remain rebuildable projections.
5. **Runtime conformance and feedback evidence** — negotiate installed capabilities and turn operational failures into acceptance evidence.

## Ranked Survivors

Survivors 1-6 were consolidated into `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`.

### 1. Antigravity Host-Contract and Capability Doctor

Make installed host truth executable, then validate every Saga promise against it.

Extend the existing doctor with a versioned local capability receipt: AGY/app versions, supported CLI flags, runtime roots, plugin link/load/validation state, agent and model/effort controls, resume behavior, and explicitly unavailable capabilities. Pair it with a semantic linter for prompts, commands, hooks, references, and runbooks so `.claude/*`, `AskUserQuestion`, Claude Workflow APIs, unproven `schedule`, fixed brain roots, or overstated isolation fail or degrade visibly.

The prior broad review explicitly left deep Saga prompt semantics partial, and live inspection found several host-incompatible promises that valid Markdown and green unit tests do not catch. The downside is that help text is not a complete runtime API; some capabilities need manual or controlled live probes, and the receipt schema needs versioning.

| field | value |
|-------|-------|
| basis | `direct:` `plugins/saga/skills/ideate/SKILL.md:34-39`, `plugins/saga/skills/loop/SKILL.md:240-253`, `plugins/saga/hooks/delegation_stop_audit_hook.py:24,61`, local `agy` 1.1.7 help, and `docs/FULL_REPO_CODE_REVIEW.md:437-444` |
| source | combined |
| confidence | 96 |
| complexity | Med |
| axis | Runtime conformance and feedback evidence |
| status | Explored |

### 2. Living Semantic Port Ledger

Replace periodic bulk ports with continuous capability reconciliation.

Give portable Saga capabilities stable IDs and record their source snapshot, semantic contract, adjacent-plugin dependencies, Antigravity-native realization, intentional differences, classification (`direct`, `adapt`, `metadata`, `superseded`, `defer`), acceptance evidence, and revisit trigger. A read-only drift scanner should cluster new Claude changes into reviewable packets, but a maintainer remains responsible for semantic classification.

The recorded sync is 161 commits and 248 relevant files behind current Claude source, while the existing runbook and queue encode stale ranges and mappings. The downside is meaningful upfront curation and ongoing ownership; source diffs can trigger review but cannot safely decide portability on their own.

| field | value |
|-------|-------|
| basis | `direct:` `README.md:25-30`, `docs/engineering-journal/QUEUED.md:82-93`, `.agents/skills/port-claude-plugins/SKILL.md:16-38`, and Claude `099ec4c..b464d090` local source evidence |
| source | combined |
| confidence | 94 |
| complexity | High |
| axis | Cross-host capability parity and port governance |
| status | Explored |

### 3. Proof-Carrying Lifecycle Reconciler

Advance Saga from observed evidence, not from a model’s completion narrative.

Evolve the Generic Ask Compiler and Saga Router into a desired-state reconciler. Each run declares required phases, gates, artifacts, checks, reviewers, and fallbacks; a transition receipt binds inputs and outputs, operator answers, actual execution receipts, checks, review findings, settlement state, and next valid transitions, while `/loop` and `/resume` route to the earliest unsettled obligation.

Transcript evidence shows that documented gates can exist without being executed, while current Claude/Codex designs use durable gates, idempotency, leases, reconciliation, and typed results. The downside is high implementation and migration cost plus a real risk of over-ceremony, so trivial routes need an explicit lightweight contract rather than a bypass.

| field | value |
|-------|-------|
| basis | `direct:` AGY `history.jsonl:194-197`, `plugins/saga/skills/loop/SKILL.md:45-66,257-301`, Claude durable gate/reconcile contracts, and Codex workflow-contract requirements |
| source | combined |
| confidence | 93 |
| complexity | High |
| axis | Lifecycle orchestration and gate completion |
| status | Explored |

### 4. Receipt-Backed Gemini Deliberation

Define thorough reasoning as an executed topology with observable coverage.

Before ideation, planning, review, or QA fanout, emit a manifest naming axes, strategies, assigned roles, requested model/effort, tools, bounds, expected schema, and recovery policy. Compare that plan with actual dispatch/readback receipts, require independent convergence, recover missing or duplicate coverage, and preserve the result with the durable artifact; cheap-first escalation remains, but it is earned from fixture results rather than assumed.

Antigravity already describes adaptive 1–6 frames and good sampled runs prove Gemini can execute them, so adding more exhortation would miss the failure. The downside is that AGY may not expose authoritative applied-model or subagent readback for every path; unavailable fields must produce an honest degraded receipt rather than invented proof.

| field | value |
|-------|-------|
| basis | `direct:` `plugins/saga/skills/ideate/SKILL.md:128-167,420-549`, sampled AGY `raw-candidates.md`/`survivors.md`, local AGY model/effort/agent help, and transcript evidence of runtime assumptions outrunning proof |
| source | combined |
| confidence | 92 |
| complexity | High |
| axis | Gemini reasoning and delegation quality |
| status | Explored |

### 5. Canonical Artifact Promotion Transaction

Keep Antigravity’s viewer experience while making tracked repository documents authoritative.

Treat brain and host-local Saga paths as disposable staging or projections. When the operator chooses persistence, deeper work, or handoff, a single promotion primitive writes or updates the canonical `docs/*` artifact, records provenance, phase/predecessor state and hashes, leaves a viewer pointer in the active runtime root, and can import existing brain-only artifacts without making that root authoritative.

Two transcript sessions required explicit correction about brain versus `docs/`, and three distinct Antigravity runtime roots are present locally. The downside is conflict and overwrite handling across concurrent sessions; terminal no-save remains valid but must say clearly that the result is neither durable nor handoffable.

| field | value |
|-------|-------|
| basis | `direct:` AGY `history.jsonl:189,194-196`, multiple local `.gemini/antigravity*` roots, user seed U4, and Claude/Codex durable-doc versus cache contracts |
| source | combined |
| confidence | 95 |
| complexity | Med |
| axis | Durable artifacts, state, and resume |
| status | Explored |

### 6. Transcript-Derived Saga Conformance Laboratory

Turn real operator corrections into a compounding lifecycle acceptance system.

Sanitize representative failures and strong runs into semantic scenarios: required gates reached, user seeds retained, frame coverage proven, canonical artifacts created, claims linked to evidence, reviews adjudicated, degraded capabilities surfaced, and resume completed. Replay bounded cases against fresh AGY sessions and add crash-test variants for stale brain state, conflicting docs, unavailable tools, Claude-only APIs, and mismatched receipts, tracking results by plugin, CLI, and model version.

The existing canaries prove output shape, but 21 conversation summaries and six relevant sessions expose end-to-end failures that unit tests do not exercise. The downside is incomplete transcript availability, privacy/sanitization work, model nondeterminism, and runtime cost; deterministic harness checks and statistical model signals must stay separate.

| field | value |
|-------|-------|
| basis | `direct:` 21 AGY conversation summaries/5,831 steps, 465 `history.jsonl` entries, six relevant brain sessions, `scripts/review_canary.py`, and context-library external-fitness guidance |
| source | combined |
| confidence | 90 |
| complexity | High |
| axis | Runtime conformance and feedback evidence |
| status | Explored |

## Did Not Survive (Revivable)

Explicit rejection remains the quality mechanism. Stable `R1`–`R8` identities are preserved from the prior run; new cuts begin at `R9`.

| id | title | summary | reason | status |
|----|-------|---------|--------|--------|
| R1 | Global hostile system prompt | Make Antigravity always adversarial. | Existing evidence shows global hostility degrades normal execution; no new evidence addressed that rejection. | rejected |
| R2 | Blind SessionStart hook copy | Copy Claude startup injection into Antigravity. | Current host leakage demonstrates why copied hooks are unsafe; capabilities need the host doctor and native adapter. | rejected |
| R3 | Always Gemini Pro High | Route every task to the strongest model. | Receipt-backed, evidence-earned escalation dominates an always-high policy on cost and task fitness. | rejected |
| R4 | Broad default do-everything agent | One agent owns routing and execution. | It collapses ownership and adjudication boundaries; the reconciler remains a router/coordinator, not a universal doer. | rejected |
| R5 | Whole-repo context dump | Give every run the entire repository corpus. | Conflicts with scoped grounding and creates context/latency cost without execution proof. | rejected |
| R6 | Full system prompt override first | Replace Antigravity’s system prompt. | Still too risky and unnecessary; the host-contract doctor and native adapters address specific defects. | rejected |
| R7 | Consensus for every task | Always fan out reviewers. | Receipt-backed adaptive delegation preserves targeted fanout and cheap paths. | rejected |
| R8 | More docs only | Improve prose and trust the model to comply. | Transcript evidence confirms that written gates already exist; enforcement and receipts are the missing mechanism. | rejected |
| R9 | Host-neutral Saga intermediate representation | Compile every host from a shared IR. | Risks becoming the cross-platform runtime abstraction the repo strategy rejects; the semantic ledger captures parity without generating every host. | rejected |
| R10 | One-writer 100-agent constitution | Design immediately for 100 workers. | Useful principles are absorbed into receipt-backed delegation, but the extreme standalone system is too expensive for the evidenced scale. | rejected |
| R11 | Repeat the generic whole-repo review | Re-run the July inventory review. | Duplicates a recent remediated review; the focused host-contract audit targets its documented semantic blind spot. | rejected |
| R12 | Bulk-port the full current Claude delta | Port all 161 commits with the existing runbook. | Too large and unsafe relative to selective value; static mappings are already stale. | rejected |
| R13 | Mandatory persistence for every ideation exit | Remove terminal no-save behavior. | Violates the explicit opt-in contract; promotion should be reliable when selected, not compulsory for disposable exploration. | rejected |
| R14 | Governed AGY advisory lane now | Add external AGY execution immediately. | Current external-action runtime is absent and CLI isolation/receipt guarantees are insufficient; first establish host truth and adjudication. | rejected |
| R15 | Saga type-health cleanup as the main initiative | Fix 13 mypy findings. | Actionable maintenance, but below the broad run’s ambition floor and not the mechanism behind lifecycle incompleteness; plan separately. | rejected |
| R16 | Clean-room buildability/reviewer triage as a standalone project | Expand the existing review appliance. | Useful but narrower than the evidenced cross-lifecycle problem and partly covered by current fresh-session review behavior. | rejected |
| R17 | Automated revival trigger queue | Reopen rejected ideas automatically. | Weakly connected to the observed completion failures and adds automation before the core ledger exists. | rejected |
| R18 | Generic QA health delta | Add one aggregate QA score. | No current evidence shows score variance is the root issue; transition and scenario evidence are stronger than a single number. | rejected |
| R19 | Separate lifecycle status card project | Show planned, dispatched, returned, adjudicated, and persisted states. | This is a presentation of the reconciler and deliberation receipts, not an independent capability. | rejected |
| R20 | Separate AGY diagnostic command project | Print CLI and plugin facts. | Valuable operator UI, but it is one consumer of the host capability doctor. | rejected |
| R21 | Separate root registry project | Centralize scratch and artifact paths. | Necessary implementation detail of the host doctor and artifact promotion transaction, not a standalone strategic idea. | rejected |
| R22 | Separate brain importer project | Copy old brain artifacts into docs. | Useful migration subfeature of artifact promotion, but too narrow alone. | rejected |
| R23 | Blind external generator lane | Add another generator for novelty. | The action runtime is unavailable and external provenance/adjudication prerequisites are not met. | rejected |
| R24 | Antigravity-Native Saga Kernel mega-project | Build host negotiation, reconciliation, and artifact authority together. | Strong components, but one mega-project hides sequencing and failure isolation; retained as three survivors. | rejected |
| R25 | Continuous parity and fitness mega-loop | Combine drift, lint, and transcript replay in one unit. | Better as a staged roadmap across the port ledger, host doctor, and conformance lab. | rejected |
| R26 | Proof-carrying deliberation mega-pipeline | Fuse reasoning and lifecycle settlement. | Runtime dispatch and lifecycle authority need a clear boundary even though their receipts interoperate. | rejected |
| R27 | Runtime truth card | Build the operator dashboard first. | Presentation should follow the host and execution receipt schemas, not define them. | rejected |
| R28 | Lifecycle traveler as a separate system | Add a manufacturing-style run record. | The useful mechanism is covered by canonical artifact promotion plus lifecycle transition receipts. | rejected |

The cuts primarily duplicated stronger combinations, proposed premature cross-host abstraction, repeated remediated review work, or promoted presentation and narrow implementation details into standalone strategic projects. Every topic axis retains at least one survivor.

## Co-Ideation Log

| source | entered | idea / seed | outcome |
|--------|---------|-------------|---------|
| user-seed | Phase 0 | Port recent Claude-plugin updates using the existing runbook. | Survived as #2 after reframing from bulk copy to semantic capability reconciliation; the literal bulk-port version was cut as R12. |
| user-seed | Phase 0 | Improve workflow orchestration using lessons from Claude and Codex. | Survived as #3 and #4 with native authority and runtime-receipt boundaries. |
| user-seed | Phase 0 | Gemini work is less thorough and may lack multi-strategy ideation. | Partly refuted: tracked and sampled AGY ideation is multi-frame. The enforcement problem survived as #3, #4, and #6. |
| user-seed | Phase 0 | Stop relying on AGY artifact directories; persist under repository docs. | Survived as #5. Mandatory persistence for disposable terminal sessions was cut as R13. |
| user-seed | Phase 0 | Use newer AGY CLI capabilities. | Survived as #1, #4, and #6, bounded to locally proven capabilities; unproven scheduling and isolation claims were rejected. |
| user-seed | Phase 0 | Consider a decent code review. | Survived as the focused semantic audit/linter in #1; a generic rerun was cut as R11 and tactical mypy cleanup as the main initiative was cut as R15. |
| prior survivor | Resume | Load-Proof Antigravity Truth Gate. | Strengthened into #1; status remains `Unexplored`. |
| prior survivor | Resume | Generic Ask Compiler. | Strengthened into #3; status remains `Unexplored`. |
| prior survivor | Resume | Fresh-Session Gemini Review Appliance. | Extended into #6; status remains `Unexplored`. |
| prior survivor | Resume | Saga Router Agent. | Strengthened into #3; status remains `Unexplored`. |
| prior survivor | Resume | Citation-Gated Review Canaries. | Extended into #6; status remains `Unexplored`. |
| prior survivor | Resume | Cheap-First Reasoning Escalator. | Incorporated into #4 as evidence-earned escalation; status remains `Unexplored`. |
| frame-agent | Phase 2 | Desired-state lifecycle reconciliation and proof-carrying transitions. | Combined into #3. |
| frame-agent | Phase 2 | Capability handshake and executable host promises. | Combined into #1. |
| frame-agent | Phase 2 | Transcript-to-regression flywheel and crash-test laboratory. | Combined into #6. |
| combined | Phase 2 | Canonical docs plus transient viewer pointer and content hash. | Survived as #5. |

## Prior Run Grounding Context (2026-06-27)

**Repo:** `infiquetra-antigravity-plugins` targets a cohesive Google Antigravity plugin ecosystem for lifecycle discipline, SDLC automation, deployment, infrastructure operations, and adversarial quality coordination. Strategy says plugins are self-contained bundles of skills, scripts, agents, and configuration loaded from `~/.gemini/config/plugins/`, and specifically calls for Antigravity-native orchestration rather than mechanical Claude ports (`STRATEGY.md:8-44`). The repo currently has many skills and commands, but only four root agent files and no saga root agent; `plugins/unifi/agents/unifi-network-ops.md` is empty by line count.

**Prompt evidence:** `docs/reviews/2026-06-27-antigravity-prompt-systems-review.md:3-22` says better prompts alone are insufficient; strong Gemini reviews required fresh-session isolation, high thinking, forced first-line disagreement, file:line evidence, and strict output shape. The durable Claude-side memory says Gemini is literal, terse, and sycophantic; "be brutally honest" does not work, constraints should go last, and adversarial critique should use a fresh `agy` session (`reference_gemini_prompting_best_practices.md:14-18`, `:40-55`). The ephemeral `agy_prompt.txt:1-26` shows the concrete working pattern.

**External context:** Google Antigravity and Gemini guidance points to the same separation of concerns: `GEMINI.md` for persistent workspace context, custom slash commands for repeat prompts, skills for on-demand procedures, subagents for isolated specialist work, hooks/policies for deterministic lifecycle control, and plan/model steering for complex work. The most relevant sources were Google Antigravity Skills, Gemini CLI custom commands, Gemini CLI project context, Gemini CLI subagents, Gemini system prompt override, Gemini plan mode, and Google Gemini 3 prompting guidance.

**Config risk:** `README.md:64-72` says installed plugins load via symlink into `~/.gemini/config/plugins/`, but `docs/PLUGIN_SPEC.md:1-54`, `marketplace/validator/schema.json:3-6`, and `marketplace/validator/validate.py:46-54` still describe Claude-shaped plugin manifests or marketplace paths. That is not a cosmetic doc issue; stale platform truth can make validation green while Antigravity runtime behavior is wrong.

## Prior Run Topic Axes (2026-06-27)

1. **Automatic prompt shaping/default context** — how generic asks become structured Antigravity work.
2. **Adversarial review harness** — how Gemini review gets forced into the known-good critique shape.
3. **Subagent activation/default agents** — when agents should kick in, and how narrow they should be.
4. **Config/install/validator truth** — whether Antigravity actually sees the intended plugins, skills, commands, and agents.
5. **Evaluation/feedback loops** — how to prove harness changes improve outcomes instead of vibes.

## Prior Run Ranked Survivors (2026-06-27)

### 1. Load-Proof Antigravity Truth Gate

Build a validator/doctor that proves a fresh Antigravity session can see the expected plugin surfaces.

This should check installed symlinks under `~/.gemini/config/plugins/`, root `plugin.json`, `skills/`, `commands/`, `agents/`, empty agent files, stale Claude-only docs that affect runtime guidance, and whether a restart/reload is required. Keep it read-only first; this is a truth check, not an installer rewrite.

The rationale is blunt: if Antigravity is not loading the right surfaces, no prompt template fixes the problem. The downside is that it starts with repo hygiene instead of the shinier prompt system, but that is the smaller bet and it protects everything else.

| field | value |
|-------|-------|
| basis | `direct:` `README.md:64-72`, `STRATEGY.md:35-44`, `docs/PLUGIN_SPEC.md:1-54`, `marketplace/validator/schema.json:3-6`, `marketplace/validator/validate.py:46-54` |
| confidence | 92 |
| complexity | Med |
| axis | Config/install/validator truth |
| status | Unexplored |

### 2. Generic Ask Compiler

Turn vague requests like "please fix this issue" into a small structured task envelope before edits begin.

The lazy version is a project-level command or front-door saga preamble: identify target issue/path, inspect repo state, choose saga phase, state acceptance proof, state mutation boundaries, run narrow checks, and report changed files/checks. Use `GEMINI.md` for baseline behavior and a command/workflow for the heavy template; do not stuff all of it into every skill.

This directly addresses the user-facing problem without assuming a mysterious default agent. The downside is that it will not catch users who bypass the command unless paired later with workspace context or a router agent.

| field | value |
|-------|-------|
| basis | `direct:` `STRATEGY.md:10-13` names lost context, skipped gates, inconsistent artifacts, and poor coordination as target problems; Gemini CLI docs support `GEMINI.md` context and project custom commands for reusable prompts. |
| confidence | 88 |
| complexity | Low |
| axis | Automatic prompt shaping/default context |
| status | Unexplored |

### 3. Fresh-Session Gemini Review Appliance

Package the proven Gemini review pattern into a repeatable command/harness rather than a copied prompt note.

For serious plan/doc/code review, the appliance should run read-only, prefer Gemini Pro/High or the strongest available planning/review model, start from fresh context, require first-line disagreement, require `[P0|P1|P2|P3] | claim/gap | evidence | fix`, and reject uncited findings. It should be review-only; do not make normal implementation globally adversarial.

This is the highest-confidence answer to "how do others get good Gemini results": they do not ask for honesty, they constrain the execution shape. The downside is that Antigravity may not expose a perfect "fresh run from command" primitive, so the first implementation may be a documented `agy -p` launcher or slash command plus manual fresh-session rule.

| field | value |
|-------|-------|
| basis | `direct:` `docs/reviews/2026-06-27-antigravity-prompt-systems-review.md:3-22`, `:107-114`; `reference_gemini_prompting_best_practices.md:40-55`; `agy_prompt.txt:1-26` |
| confidence | 90 |
| complexity | Low |
| axis | Adversarial review harness |
| status | Unexplored |

### 4. Saga Router Agent

Add a narrow saga root agent that routes lifecycle work; do not build a broad default doer.

The agent's job should be classification and delegation: decide whether a natural-language ask belongs in `/office-hours`, `/ideate`, `/brainstorm`, `/spec`, `/plan`, `/work`, `/doc-review`, `/code-review`, `/qa`, `/resume`, or `/retro`. It should not implement features itself except for tiny routing-safe actions.

This matches Antigravity's agent model without turning the global prompt into a confused personality. The downside is activation quality: the description and examples must be precise, or the agent becomes another passive file.

| field | value |
|-------|-------|
| basis | `direct:` `STRATEGY.md:85-96` makes saga the active lifecycle track; repo scan found root agents for deploy, home-lab-ops, mission-control, and unifi, but no `plugins/saga/agents/`; Antigravity/Gemini docs describe subagents as specialist agents with their own prompt and context. |
| confidence | 82 |
| complexity | Low |
| axis | Subagent activation/default agents |
| status | Unexplored |

### 5. Citation-Gated Review Canaries

Create a tiny replay corpus of known-bad plans/diffs and a validator for review output shape.

Each canary should have seeded defects, expected finding classes, and allowed false-positive notes. The validator can start dumb: every finding must include priority, claim, impact, file:line evidence, and concrete fix; uncited claims fail. Track missed defects and false positives by prompt/model/harness.

This changes "Gemini felt better" into regression evidence. The downside is maintenance, so start with only the June 27 worker-model cache scheduling review and one or two future misses.

| field | value |
|-------|-------|
| basis | `direct:` `docs/reviews/2026-06-27-antigravity-prompt-systems-review.md:12` says Codex and Gemini caught non-overlapping P1 findings; `infiquetra-claude-plugins/docs/reviews/2026-06-27-worker-model-cache-scheduling-review.md:8-27` records the verified finding set. |
| confidence | 84 |
| complexity | Med |
| axis | Evaluation/feedback loops |
| status | Unexplored |

### 6. Cheap-First Reasoning Escalator

Define task classes that decide when to use simple grounding, one strict reviewer, high-thinking Gemini, or full multi-agent consensus.

Routine edits should get local repo context, narrow checks, and the citation/output gate. High-risk plans, security/data/infra work, or large cross-file changes escalate to high-thinking Gemini review. Full multi-agent consensus remains for plans with real parallel work or high blast radius.

This avoids the trap of treating Gemini Pro High as a universal fix. The downside is policy design: thresholds need to be boring and explicit, or the model will rationalize whichever path it wanted.

| field | value |
|-------|-------|
| basis | `direct:` `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/consensus-protocol.md:61-88` already documents rate-limit and context-cost mitigations; Gemini prompting guidance recommends high reasoning where needed but also task-specific model/thinking choices. |
| confidence | 80 |
| complexity | Low |
| axis | Automatic prompt shaping/default context |
| status | Unexplored |

## Prior Run Cuts (2026-06-27)

Explicit rejection is the quality mechanism. Cut ideas stay revivable if new Antigravity platform evidence changes the basis.

| id | title | summary | reason | status |
|----|-------|---------|--------|--------|
| R1 | Global hostile system prompt | Make Antigravity always adversarial | Rejected because local review guidance explicitly warns adversarial personas degrade normal execution (`docs/reviews/2026-06-27-antigravity-prompt-systems-review.md:111`). | rejected |
| R2 | Blind SessionStart hook copy | Port Claude hooks directly into Antigravity | Rejected because prior ideation found no proven Antigravity `SessionStart` equivalent and rejected direct `hooks.json` copying (`docs/ideation/2026-06-21-stale-main-sessionstart-antigravity-port.md:14-22`, `:78-82`). | rejected |
| R3 | Always Gemini Pro High | Route every task to high-thinking Gemini | Too expensive and not task-correct; keep high reasoning for review/planning gates and risky work. | rejected |
| R4 | Broad default do-everything agent | One default agent owns routing and execution | Too vague; likely repeats the global-persona problem. Surviving version is a narrow saga router agent. | rejected |
| R5 | Whole-repo context dump | Use giant packed repo context for generic tasks | Conflicts with progressive-disclosure guidance; likely worsens context rot and latency for routine work. | rejected |
| R6 | Full system prompt override first | Replace Gemini/Antigravity system prompt with custom prompt | Too risky as first move; Gemini docs describe system prompt override as a full replacement, so built-in safety/workflow instructions can be lost unless reimplemented. | rejected |
| R7 | Multi-agent consensus for every task | Spawn reviewer swarms by default | Too costly and slow; consensus protocol itself contains rate-limit mitigation, which implies fan-out should be reserved. | rejected |
| R8 | More docs only | Write better prompt docs and trust agents to read them | Already happened. The missing piece is load proof, commands, agents, gates, and replay evidence. | rejected |

## Prior Run Co-Ideation Log (2026-06-27)

Records partnership provenance: user seeds entered the same pool and faced the same critique as generated candidates.

| source | entered | idea / seed | outcome |
|--------|---------|-------------|---------|
| user-seed | Phase 0 | Antigravity may need more harness, configuration, and LLM guidance. | survived as #1, #2, #3, #6 |
| user-seed | Phase 0 | Generic asks like "please fix this issue" should maybe become a better prompt automatically. | survived as #2 |
| user-seed | Phase 0 | Maybe Antigravity wants agents that automatically kick in or a default agent. | survived as #4, narrowed to router-only |
| user-seed | Phase 0 | Find out how others get good results with Gemini models. | survived as #3, #5, #6 |
| frame-agent | Phase 2 | Global hostile system prompt | cut -> R1 |
| frame-agent | Phase 2 | Direct hook copy / hidden startup auto-injection | cut -> R2 |
| frame-agent | Phase 2 | Always-high Gemini everywhere | cut -> R3 |
