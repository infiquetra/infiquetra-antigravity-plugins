---
date: 2026-06-27
topic: antigravity-harness
focus: Improve Antigravity results through harness, configuration, agents, prompt guidance, and Gemini review discipline.
scope: broad
repo: infiquetra-antigravity-plugins
maturity: idea-ready
---

# Ideation: Antigravity Harness

## Grounding Context

**Repo:** `infiquetra-antigravity-plugins` targets a cohesive Google Antigravity plugin ecosystem for lifecycle discipline, SDLC automation, deployment, infrastructure operations, and adversarial quality coordination. Strategy says plugins are self-contained bundles of skills, scripts, agents, and configuration loaded from `~/.gemini/config/plugins/`, and specifically calls for Antigravity-native orchestration rather than mechanical Claude ports (`STRATEGY.md:8-44`). The repo currently has many skills and commands, but only four root agent files and no saga root agent; `plugins/unifi/agents/unifi-network-ops.md` is empty by line count.

**Prompt evidence:** `docs/reviews/2026-06-27-antigravity-prompt-systems-review.md:3-22` says better prompts alone are insufficient; strong Gemini reviews required fresh-session isolation, high thinking, forced first-line disagreement, file:line evidence, and strict output shape. The durable Claude-side memory says Gemini is literal, terse, and sycophantic; "be brutally honest" does not work, constraints should go last, and adversarial critique should use a fresh `agy` session (`reference_gemini_prompting_best_practices.md:14-18`, `:40-55`). The ephemeral `agy_prompt.txt:1-26` shows the concrete working pattern.

**External context:** Google Antigravity and Gemini guidance points to the same separation of concerns: `GEMINI.md` for persistent workspace context, custom slash commands for repeat prompts, skills for on-demand procedures, subagents for isolated specialist work, hooks/policies for deterministic lifecycle control, and plan/model steering for complex work. The most relevant sources were Google Antigravity Skills, Gemini CLI custom commands, Gemini CLI project context, Gemini CLI subagents, Gemini system prompt override, Gemini plan mode, and Google Gemini 3 prompting guidance.

**Config risk:** `README.md:64-72` says installed plugins load via symlink into `~/.gemini/config/plugins/`, but `docs/PLUGIN_SPEC.md:1-54`, `marketplace/validator/schema.json:3-6`, and `marketplace/validator/validate.py:46-54` still describe Claude-shaped plugin manifests or marketplace paths. That is not a cosmetic doc issue; stale platform truth can make validation green while Antigravity runtime behavior is wrong.

## Topic Axes

1. **Automatic prompt shaping/default context** — how generic asks become structured Antigravity work.
2. **Adversarial review harness** — how Gemini review gets forced into the known-good critique shape.
3. **Subagent activation/default agents** — when agents should kick in, and how narrow they should be.
4. **Config/install/validator truth** — whether Antigravity actually sees the intended plugins, skills, commands, and agents.
5. **Evaluation/feedback loops** — how to prove harness changes improve outcomes instead of vibes.

## Ranked Survivors

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

## Did not survive (revivable)

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

## Co-ideation log

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
