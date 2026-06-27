---
date: 2026-06-27
topic: antigravity-harness
maturity: requirements-ready
source: docs/ideation/2026-06-27-antigravity-harness-ideation.md - ranked survivors 1-6
---

# Antigravity Harness Requirements

## Summary

Build a unified Antigravity harness layer that makes generic work reliable before implementation starts: prove plugin load truth, turn vague asks into structured task envelopes, route lifecycle work through saga, run Gemini reviews in the known-good fresh adversarial shape, and measure quality with canaries.

## Problem Frame

Antigravity underperformance is not cleanly attributable to the model. The repo already records stronger Gemini review results when prompts are treated as execution specs: fresh session, high reasoning, first-line disagreement, strict output schema, file:line citations, and constraints last.

The current repo also has a more basic risk: runtime truth is not fully proven. Strategy says Antigravity plugins load from `~/.gemini/config/plugins/`, but stale Claude-shaped plugin specs and validators still exist, and the richest workflow surface, saga, has skills and commands without a root router agent. More prompt prose alone will not fix unloaded plugins, stale guidance, or vague task framing.

## Key Decisions

**D1. Truth before tuning.** The first requirement is a load/config doctor that proves what Antigravity can actually see. If the harness is not loaded, model-quality work is noise.

**D2. Compile asks before execution.** Generic requests should become a small task envelope before edits begin: target, repo state, saga phase, acceptance proof, mutation boundary, and checks.

**D3. Review hostility is isolated.** Adversarial Gemini behavior belongs in a review appliance, not in global workspace context or normal implementation prompts.

**D4. Cheap-first escalation.** Routine work should use local context, narrow checks, and evidence gates. High-thinking Gemini and multi-agent consensus are escalation paths for risky work, not defaults.

**D5. Measure review quality.** Harness changes must be judged against canaries and accepted findings, not subjective "felt better" reports.

## Actors

- A1. **Operator** - starts work with natural language, command invocations, issue references, or existing artifacts.
- A2. **Main Antigravity agent** - executes the task loop and must receive enough structure to avoid inventing scope.
- A3. **Saga router agent** - classifies lifecycle phase and routes to the right saga skill without becoming a general worker.
- A4. **Review appliance** - runs isolated adversarial review with strict evidence requirements.
- A5. **Harness doctor** - reports installed, loaded, stale, missing, or invalid Antigravity surfaces.
- A6. **Planner/reviewer** - consumes this requirements doc and later implementation artifacts without inventing product behavior.

## Requirements

**Load And Runtime Truth**

- R1. The harness must provide a read-only doctor that reports whether expected plugins are present under Antigravity's plugin loading location. The expected plugin inventory comes from repo-local `plugins/*/plugin.json` unless an explicit operator-supplied allowlist overrides it.
- R2. The doctor must verify every expected plugin has the Antigravity-facing surfaces present in its repo directory: root manifest, skills, commands, agents, and any declared tool/config surfaces.
- R3. The doctor must detect empty or inert agent files as warnings because they create the appearance of active routing without behavior.
- R4. The doctor must flag runtime-affecting Claude-shaped drift, including specs, validators, registry paths, or manifest schemas that tell agents to build or validate the wrong platform contract.
- R5. The doctor must distinguish "not installed or not loaded" from "model performed poorly" so later prompt tuning is not blamed for configuration failure.
- R6. The doctor must produce concrete next action guidance: reload/restart session, install/link plugin, repair manifest, repair stale doc/validator, or proceed.

**Generic Task Intake**

- R7. The harness must define a generic ask compiler for vague repair/build requests such as "please fix this issue."
- R8. The compiler must produce a task envelope before mutation: target source, relevant repo state, likely saga phase, scope boundary, expected proof, risky-operation boundary, and final report expectations.
- R9. The compiler must not invent product behavior. If the ask lacks a target, acceptance signal, or scope boundary, it must ask or route to the appropriate saga clarification phase.
- R10. The compiler must support project-level default context for persistent baseline guidance, but heavy task templates must live in commands, skills, or router behavior rather than bloating all context.

**Saga Routing**

- R11. Saga must gain an active router surface that classifies natural-language lifecycle work and routes to existing saga skills.
- R12. The router must be narrow: it chooses between lifecycle skills and explains routing, but it does not implement non-trivial work itself.
- R13. The router must cover at least: `/office-hours`, `/ideate`, `/brainstorm`, `/spec`, `/plan`, `/work`, `/doc-review`, `/code-review`, `/qa`, `/resume`, and `/retro`.
- R14. The router must decline or ask when lifecycle phase is ambiguous enough that automatic routing would hide a product decision.

**Gemini Review Appliance**

- R15. The harness must package the proven Gemini review pattern as a reusable review appliance.
- R16. Serious plan/doc/code review through the appliance must be read-only, fresh-context, evidence-gated, and explicitly adversarial.
- R17. Review output must use a strict findings schema with priority, claim or gap, file:line evidence, impact, and proposed fix.
- R18. The appliance must reject or mark invalid any finding that lacks evidence supporting the claim.
- R19. The appliance must keep adversarial persona scoped to review tasks only; it must not make global implementation behavior hostile.
- R20. The appliance must support second-opinion comparison without flattering or rubber-stamping the first reviewer.

**Escalation Policy**

- R21. The harness must define a cheap-first escalation ladder for task handling.
- R22. Routine tasks default to repo grounding, task envelope, narrow checks, and citation/evidence gates.
- R23. High-risk plans, security/data/infra changes, broad cross-file changes, or prior failed attempts escalate to high-thinking Gemini review.
- R24. Full multi-agent consensus is reserved for work with real parallelism, high blast radius, or reviewer disagreement that one strict reviewer cannot resolve.
- R25. Escalation decisions must be visible in the output so the operator can tell why a task stayed cheap or moved to a heavier path.

**Canaries And Feedback**

- R26. The harness must include a small canary corpus of known-bad plans or diffs with expected finding classes.
- R27. The first canaries should come from prior verified review episodes where Gemini and Codex caught non-overlapping issues, starting with the worker-model cache scheduling review recorded in the sibling `infiquetra-claude-plugins` repo.
- R28. The canary evaluator must track at least missed defects, false positives, citation completeness, and invalid uncited findings.
- R29. Prompt, model, reasoning level, fresh-session flag, and harness version must be recorded for each canary/review run.
- R30. Changes to review prompts or routing rules should not be considered improvements unless canary or real-review evidence improves or preserves quality.

**Artifacts And Handoff**

- R31. The harness must produce durable, repo-relative artifacts when decisions or findings should survive the session.
- R32. Generated artifacts must be usable by `/plan`, `/doc-review`, and future operators without requiring chat history.
- R33. The requirements, review, and canary outputs must avoid absolute local paths except transient operator-facing links.
- R34. The harness must leave implementation design, file layout, schemas, and command naming to `/plan` unless those details are themselves the requirement under discussion.

## Key Flows

- F1. **Harness preflight.** **Trigger:** Operator wants to use or debug Antigravity in this repo. **Steps:** run doctor, report installed surfaces, warn stale or empty surfaces, identify restart/reload needs, and separate configuration failure from model behavior. **Covers R1-R6.**
- F2. **Generic fix intake.** **Trigger:** Operator says "please fix this issue" or equivalent. **Steps:** compiler identifies target, reads enough repo state, chooses saga route or asks one blocking question, creates task envelope, then proceeds to the selected lifecycle skill. **Covers R7-R14.**
- F3. **Serious adversarial review.** **Trigger:** Operator asks for plan/doc/code review or a lifecycle gate requires review. **Steps:** appliance starts fresh read-only review, applies strict schema, requires first-line disagreement or verdict, rejects uncited findings, and returns evidence-backed findings only. **Covers R15-R20.**
- F4. **Escalation decision.** **Trigger:** Task has security/data/infra blast radius, broad diff, prior failure, or review disagreement. **Steps:** harness explains escalation, chooses strict reviewer, high-thinking Gemini, or multi-agent consensus, then records why. **Covers R21-R25.**
- F5. **Review quality replay.** **Trigger:** prompt/harness changes or periodic quality check. **Steps:** run canaries, compare expected defects to findings, record misses/false positives/citation gaps, and decide whether prompt/harness change improves quality. **Covers R26-R30.**

## Acceptance Examples

- AE1. **Stale Claude contract caught.** Given a validator or spec still requires `.claude-plugin` layout for an Antigravity plugin, the doctor reports runtime-affecting Claude drift and explains whether to repair docs, schema, or validator before prompt tuning. **Covers R4, R5, R6.**
- AE2. **Empty agent caught.** Given an agent file exists but has no usable content, the doctor warns that the agent surface is inert and should not be counted as active routing. **Covers R2, R3.**
- AE3. **Vague fix compiled.** Given "please fix this issue" with no issue number, path, or failure signal, the compiler does not start editing. It asks for the target or routes to the saga clarification phase. **Covers R7, R8, R9.**
- AE4. **Review claim rejected.** Given a Gemini review finding that says "plan is missing rollback handling" but cites no file:line evidence, the appliance marks it invalid or asks for evidence rather than surfacing it as a finding. **Covers R17, R18.**
- AE5. **Cheap path preserved.** Given a one-file docs typo fix, the harness uses local grounding and narrow checks, not high-thinking Gemini or multi-agent consensus. **Covers R21, R22, R25.**
- AE6. **Risk path escalated.** Given a plan touching deployment, identity, data contracts, or security boundaries, the harness escalates to the review appliance or consensus path and records why. **Covers R23, R24, R25.**
- AE7. **Canary prevents regression.** Given a prompt change makes reviews sound stronger but misses a previously known P1 defect, the canary evaluator blocks calling the change an improvement. **Covers R26-R30.**

## Success Criteria

- A fresh operator can run one harness check and know whether Antigravity is actually seeing the expected repo plugin surfaces.
- A generic fix request is converted into a structured task envelope or a single blocking question before any edit.
- Serious reviews consistently include evidence-backed findings and reject uncited claims.
- Saga lifecycle routing works from natural-language requests without requiring the operator to remember every command.
- Prompt/harness changes can be evaluated against at least one canary with known expected findings.

## Scope Boundaries

**In scope**

- Requirements for a read-only Antigravity load/config doctor.
- Requirements for generic task intake and saga routing.
- Requirements for a fresh-context Gemini review appliance.
- Requirements for cheap-first escalation and canary measurement.
- Runtime-affecting stale Claude contract detection.

**Out of scope**

- Full system prompt replacement as the first move.
- Global hostile or adversarial default personality.
- Blind port of Claude `SessionStart` hooks.
- Whole-repo context dumping as a default.
- Multi-agent consensus for every task.
- Implementation file layout, command names, schemas, and code structure.
- Hosted marketplace or plugin distribution service.

## Dependencies / Assumptions

- Antigravity continues to support plugin surfaces conceptually equivalent to skills, commands, agents, and configuration loaded at session start.
- Exact reload/restart mechanics may need live verification during `/plan` or implementation.
- The repo can keep ignored scratch artifacts for lifecycle work, but durable requirements/review/canary outputs belong under tracked `docs/`.
- The first canary corpus can be small; one verified prior review is enough to start.
- Some external Gemini CLI mechanisms may not map one-to-one to Antigravity. `/plan` must verify the current Antigravity contract before choosing the implementation lever.

## Outstanding Questions

**Deferred planning**

- Which exact Antigravity surface should host the generic ask compiler: project command, saga command, router agent, workspace context, or a combination?
- Which current docs and validators are runtime-affecting enough to fail the truth gate versus merely historical references?
- What is the smallest live command that proves Antigravity has loaded a plugin's commands, skills, and agents in a fresh session?
- What should the first canary fixture include beyond the worker-model cache scheduling review?

There are no resolve-before-planning questions.

## Sources / Research

- `docs/ideation/2026-06-27-antigravity-harness-ideation.md`
- `docs/reviews/2026-06-27-antigravity-prompt-systems-review.md`
- `README.md`
- `STRATEGY.md`
- `ANTIGRAVITY.md`
- `docs/PLUGIN_SPEC.md`
- `marketplace/validator/validate.py`
- `marketplace/validator/schema.json`
- `docs/ideation/2026-06-21-stale-main-sessionstart-antigravity-port.md`
- `docs/ideation/2026-06-21-stale-main-sessionstart-claude-pass.md`
- `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/consensus-protocol.md`
- `infiquetra-claude-plugins: docs/reviews/2026-06-27-worker-model-cache-scheduling-review.md`
