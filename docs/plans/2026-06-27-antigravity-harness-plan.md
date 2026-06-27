---
title: Antigravity Harness Implementation Plan
type: feat
status: active
date: 2026-06-27
origin: docs/brainstorms/2026-06-27-antigravity-harness-requirements.md
---

# Antigravity Harness Implementation Plan

## Summary

Build the Antigravity harness in one staged pass: make plugin load/config truth mechanically checkable, remove stale Claude-shaped validator authority, route generic work through saga, package the proven Gemini review shape inside `/doc-review`, and add local canary scoring so prompt changes can be tested without live model calls in CI.

## Problem Frame

The requirements doc establishes that weak Antigravity results may come from missing harness rather than model quality alone. Current repo evidence supports that: CI still runs both `scripts/validate_plugins.py` and `marketplace/validator/validate.py`, the marketplace schema still says "Claude Plugin Manifest", and saga has a router command/skill but no root `agents/` router persona.

This plan treats runtime truth as the first dependency. The generic ask compiler, saga router, Gemini review appliance, and canary evaluator only become reliable after the repo can prove what Antigravity plugin surfaces exist and whether stale Claude-era contracts are still steering agents.

---

## Requirements

**Load And Runtime Truth**

- R1. The canonical doctor reports expected plugins from repo-local `plugins/*/plugin.json`.
- R2. The doctor verifies root manifest, skills, commands, agents, and declared tool/config surfaces for every expected plugin.
- R3. Empty or inert agent files produce warnings.
- R4. Runtime-affecting Claude-shaped drift in specs, validators, registry paths, or manifest schemas is flagged.
- R5. Doctor output separates "not installed or not loaded" from model-quality failure.
- R6. Doctor output gives next actions: reload/restart, install/link, repair manifest, repair stale contract, or proceed.

**Generic Task Intake And Routing**

- R7. Generic repair/build requests get compiled before mutation.
- R8. The task envelope includes target, repo state, saga phase, scope boundary, expected proof, risky-operation boundary, and final report expectations.
- R9. Missing target, acceptance signal, or scope boundary causes a question or clarification route, not editing.
- R10. Persistent context stays compact; heavy task templates live in saga references, skills, commands, or agent behavior.
- R11. Saga gains an active router surface.
- R12. The router classifies and delegates; it does not implement non-trivial work.
- R13. The router covers the shipped saga lifecycle commands.
- R14. Ambiguous lifecycle phase triggers decline or a question.

**Review Appliance And Escalation**

- R15. `/doc-review` gets a reusable Gemini review appliance pattern.
- R16. Serious review is read-only, fresh-context, evidence-gated, and adversarial.
- R17. Review findings include priority, claim/gap, file:line evidence, impact, and fix.
- R18. Findings without supporting evidence are invalid.
- R19. Adversarial persona stays scoped to review tasks.
- R20. Second-opinion comparison must invite disagreement, not rubber-stamp prior review.
- R21. A cheap-first escalation ladder is documented.
- R22. Routine tasks stay with grounding, envelope, narrow checks, and evidence gates.
- R23. High-risk plans and changes escalate to high-thinking Gemini review.
- R24. Full multi-agent consensus stays reserved for real parallelism, high blast radius, or unresolved reviewer disagreement.
- R25. Escalation choices are visible in output.

**Canaries And Artifacts**

- R26. A small canary corpus exists for known-bad plans or diffs.
- R27. The first canary starts from the worker-model cache scheduling review in the sibling `infiquetra-claude-plugins` repo.
- R28. Canary scoring tracks missed defects, false positives, citation completeness, and invalid uncited findings.
- R29. Prompt, model, reasoning level, fresh-session flag, and harness version are recorded for each run.
- R30. Prompt/routing changes are not improvements unless canary or real-review evidence preserves or improves quality.
- R31. Decisions and findings that should survive the session become repo-relative durable artifacts.
- R32. Outputs are usable by `/plan`, `/doc-review`, and future operators without chat history.
- R33. Durable outputs avoid absolute paths.
- R34. Implementation file layout and command naming stay in `/plan` and `/work`, not the requirements doc.

---

## Key Technical Decisions

**KTD1. Canonical doctor lives in `scripts/validate_plugins.py`:** CI already calls this path, so replacing its stale Claude markdown validator with an Antigravity doctor gives the shortest useful path. `marketplace/validator/validate.py` must become a thin compatibility wrapper over the canonical doctor rather than remain a second source of truth.

**KTD2. Expected plugin inventory is repo-local, not marketplace-driven:** v1 walks `plugins/*/plugin.json` as the inventory. No new registry or hosted marketplace work is needed to satisfy the requirements.

**KTD3. Doctor is read-only and host-isolated:** it may inspect the repo, an install directory, symlinks, and file contents, but it must not create symlinks, edit manifests, or restart Antigravity. Tests must mock install directories instead of touching `~/.gemini`.

**KTD4. Generic ask compiler is a saga reference consumed by `/loop` and a router agent:** do not add a new `/fix` command in v1. `/loop` already owns lifecycle routing, so the compiler should be a reusable instruction contract for bare asks.

**KTD5. Saga router agent is a router, not a worker:** create a root saga agent whose role is classification and delegation into existing saga commands. It must not duplicate `/loop` implementation logic.

**KTD6. Gemini review appliance extends `/doc-review`:** use a new doc-review reference for the prompt skeleton, fresh-session rule, evidence gate, and second-opinion comparison. Do not put a hostile persona in global context or add a standalone review command unless `/doc-review` cannot host it.

**KTD7. Canaries are local fixtures, not live model calls in CI:** CI should validate canary scoring and output-shape logic with saved fixture outputs. Live `agy`/Gemini runs remain manual or operator-triggered because they depend on model access and current platform behavior.

**KTD8. Escalation policy is shared documentation, not hidden branching:** the cheap-first ladder should be a reference used by routing/review skills and cited in outputs. Operators need to see why a task stayed inline or escalated.

---

## High-Level Technical Design

The harness has three layers.

1. **Truth layer:** `scripts/validate_plugins.py` becomes the canonical Antigravity doctor. It reports plugin inventory, surface presence, inert agents, install state, stale Claude-shaped contracts, and concrete next actions. Legacy marketplace validation delegates to canonical doctor by default and loses independent authority in docs/CI.
2. **Routing layer:** saga receives a root router agent and a generic ask compiler reference. `/loop` remains the lifecycle router; the new agent and compiler help natural-language asks enter `/loop` correctly.
3. **Review layer:** `/doc-review` gains a Gemini review appliance reference and local canary fixtures/evaluator. The appliance is a repeatable review pattern; canaries measure whether prompt/harness changes catch known defects.

---

## Implementation Units

### U1. Canonical Antigravity Doctor

Replace the stale top-level validator with a read-only Antigravity plugin doctor.

**Goal:** `scripts/validate_plugins.py` should validate the actual flat Antigravity plugin layout and report install/load readiness without mutating the user's machine.

**Requirements:** R1, R2, R3, R5, R6, R31, R32, R33.

**Dependencies:** none.

**Files:** `scripts/validate_plugins.py`, `tests/test_antigravity_plugin_doctor.py`.

**Approach:** Walk `plugins/*/plugin.json`, parse each manifest, validate name/version/description basics, count `skills/*/SKILL.md`, `commands/*.md`, `agents/*.md`, and declared tool/config surfaces. Add an install-dir option with a default matching `~/.gemini/config/plugins`, but allow tests and operators to override it. Emit human output by default and JSON output for CI or later tooling.

**Edge cases:** missing `plugins/` directory, invalid JSON, manifest name that does not match directory, plugin with no skills/commands/agents/tools, empty agent files, copied install directories instead of symlinks, symlink pointing at the wrong plugin directory, unreadable install directory.

**Error / failure paths:** invalid manifest is an error; missing install is a warning unless operator asks for installed-state strictness; stale or empty surfaces are warnings unless they break a declared expectation; unreadable files produce actionable warnings rather than traceback-only failures.

**Integration scenarios:** a clean checkout with seven repo-local plugin manifests passes core validation while warning on known inert surfaces; a mocked install directory shows linked, missing, copied, and wrong-target plugin states distinctly.

**Test scenarios:** `tests/test_antigravity_plugin_doctor.py` creates temp plugin trees and install dirs to assert valid plugin detection, invalid JSON failure, empty-agent warning, wrong symlink target warning, JSON output shape, and no host filesystem reads when an install dir is supplied.

**Verification:** running `uv run python scripts/validate_plugins.py --json --install-dir <tmp>` in tests returns structured plugin status with separate errors, warnings, and next actions.

### U2. Legacy Validator And Platform-Truth Cleanup

Remove or neutralize stale Claude-shaped validation authority.

**Goal:** CI and docs should no longer bless `.claude-plugin` marketplace assumptions as the Antigravity contract.

**Requirements:** R4, R6, R31, R32, R33, R34.

**Dependencies:** U1.

**Files:** `marketplace/validator/validate.py`, `marketplace/validator/schema.json`, `.github/workflows/ci.yml`, `docs/PLUGIN_SPEC.md`, `docs/MARKETPLACE_GUIDE.md`, `README.md`, `tests/test_antigravity_plugin_doctor.py`.

**Approach:** Make `marketplace/validator/validate.py` a thin wrapper that calls `scripts/validate_plugins.py` by default and cannot contradict canonical doctor status. Replace the Claude manifest schema title/required fields with Antigravity flat-manifest expectations, and keep any legacy schema validation out of CI unless it is explicitly compatibility-only. Update docs to describe root `plugin.json`, `skills/`, `commands/`, `agents/`, and local symlink installation accurately.

**Edge cases:** external users may still run `marketplace/validator/validate.py`; CI may rely on both validator commands; docs may need to preserve historical Claude-port notes without presenting them as current Antigravity spec.

**Error / failure paths:** if the compatibility wrapper cannot import the canonical doctor, it should fail with a clear repair message; if a doc mentions `.claude-plugin` as historical context, the doctor should not fail it unless the text is in a current spec/usage section.

**Integration scenarios:** CI's validate job should run the canonical doctor once, and optionally run the legacy wrapper only to prove compatibility.

**Test scenarios:** extend `tests/test_antigravity_plugin_doctor.py` to prove the legacy wrapper returns the same pass/fail status as the canonical doctor for fixture plugins, and that stale current-spec phrases are detected in `docs/PLUGIN_SPEC.md`-style fixture text.

**Verification:** `uv run python scripts/validate_plugins.py` and `uv run python marketplace/validator/validate.py` agree on status for the repo.

### U3. Saga Router Agent And Generic Ask Compiler

Give Antigravity an active lifecycle routing surface for natural-language work.

**Goal:** generic asks should route through a structured intake envelope instead of jumping straight into edits.

**Requirements:** R7, R8, R9, R10, R11, R12, R13, R14, R25.

**Dependencies:** none.

**Files:** `plugins/saga/agents/lifecycle-router.md`, `plugins/saga/skills/loop/references/generic-ask-compiler.md`, `plugins/saga/skills/loop/SKILL.md`, `plugins/saga/commands/loop.md`, `tests/test_antigravity_harness_docs.py`.

**Approach:** Add a root saga agent with crisp triggers and examples for routing, not implementation. Add a generic ask compiler reference that defines the task envelope fields and the stop conditions. Update `/loop` command/skill to load that reference for bare asks and route ambiguous cases to clarification instead of work.

**Edge cases:** user explicitly invokes `/work` with a settled plan, user gives a vague ask with no target, user asks for a code review rather than work, user asks broad product direction, user asks to continue existing saga.

**Error / failure paths:** if no target can be identified, ask one blocking question or route to `/office-hours`, `/spec`, or `/brainstorm`; if multiple phases match, explain the conflict and ask; if a matching saga exists, prefer resume routing over new work.

**Integration scenarios:** `/loop "please fix this issue"` produces or asks for target information; `/loop docs/brainstorms/...requirements.md` routes to `/plan`; `/loop docs/plans/...plan.md` routes to `/doc-review` or `/work` depending gate state.

**Test scenarios:** `tests/test_antigravity_harness_docs.py` asserts the saga router agent exists, is non-empty, declares router boundaries, and that `/loop` references the generic ask compiler. It should also validate that the compiler reference names target, repo state, saga phase, proof, scope boundary, and mutation boundary.

**Verification:** reading `plugins/saga/agents/lifecycle-router.md` cold makes clear that the agent delegates to existing saga commands and does not implement feature work.

### U4. Gemini Review Appliance In `/doc-review`

Package the known-good Gemini adversarial review shape inside the review phase.

**Goal:** `/doc-review` should give operators a reusable fresh-session Gemini second-opinion path without making all work globally adversarial.

**Requirements:** R15, R16, R17, R18, R19, R20, R23, R25.

**Dependencies:** none.

**Files:** `plugins/saga/skills/doc-review/SKILL.md`, `plugins/saga/skills/doc-review/references/gemini-review-appliance.md`, `tests/test_antigravity_harness_docs.py`.

**Approach:** Add a doc-review reference that contains the adversarial role, fresh-session isolation rule, model/reasoning guidance, constraints-last rule, output schema, evidence gate, second-opinion comparison pattern, and invalid-finding handling. Update `/doc-review` to load it when operator asks for Gemini review, second opinion, adversarial review, or high-risk review.

**Edge cases:** review target has no source files to verify, Gemini review is requested in the same session that generated the plan, model access is unavailable, output lacks citations, operator asks for general "brutal honesty."

**Error / failure paths:** if fresh session cannot be guaranteed, mark the review as weakened; if model access is unavailable, provide the prompt artifact and route to normal `/doc-review`; if findings lack file:line evidence, mark them invalid rather than reporting them.

**Integration scenarios:** a normal `/doc-review` remains local and inline; a serious review can produce an `agy` prompt or external-run instructions; a second-opinion comparison asks Gemini to confirm/refute prior findings without praise.

**Test scenarios:** `tests/test_antigravity_harness_docs.py` asserts the reference contains fresh-session, first-line disagreement/verdict, file:line evidence, constraints-last, read-only, and no-global-hostility rules, and that `/doc-review` references the appliance.

**Verification:** a reviewer can copy the appliance skeleton and know exactly what fields a Gemini review must return.

### U5. Review Canary Fixtures And Scorer

Add a local, deterministic way to check review output quality.

**Goal:** prompt and harness changes should be tested against known defects without calling Gemini or `agy` in CI.

**Requirements:** R26, R27, R28, R29, R30, R31, R32, R33.

**Dependencies:** U4.

**Files:** `scripts/review_canary.py`, `tests/test_review_canary.py`, `tests/fixtures/review_canaries/worker_model_cache_scheduling/expected_findings.json`, `tests/fixtures/review_canaries/worker_model_cache_scheduling/sample_review.md`.

**Source artifact:** `infiquetra-claude-plugins: docs/reviews/2026-06-27-worker-model-cache-scheduling-review.md`.

**Approach:** Create a small fixture format with metadata, expected finding classes, and sample review output. The scorer reads saved review output, checks required fields/citations, maps detected findings to expected classes, and reports missed defects, false positives, and invalid uncited findings. Seed the first fixture from the worker-model cache scheduling review's verified finding set, but store only the minimal expected finding summaries needed for scoring.

**Edge cases:** review output uses different wording for the same defect, finding has priority but no citation, citation points to non-existent fixture path, sample has extra advisory findings, canary has no expected finding for a new issue.

**Error / failure paths:** malformed fixture fails fast; uncited findings are invalid; unmatched expected defects count as misses; extra non-advisory findings count as false positives unless explicitly allowed.

**Integration scenarios:** CI runs the scorer against the sample fixture; later manual Gemini outputs can be saved and scored locally.

**Test scenarios:** `tests/test_review_canary.py` asserts a good sample passes, missing expected finding fails, uncited finding fails citation completeness, allowed advisory extra does not fail, and false positive is reported.

**Verification:** `uv run python scripts/review_canary.py tests/fixtures/review_canaries/worker_model_cache_scheduling/sample_review.md` prints a pass/fail summary and structured counts.

### U6. Escalation Policy, Journal, And Quality Gates

Wire the harness into docs, CI, and durable decision records.

**Goal:** implementation leaves a coherent operator path and prevents future drift.

**Requirements:** R21, R22, R24, R25, R31, R32, R33, R34.

**Dependencies:** U1, U2, U3, U4, U5.

**Files:** `plugins/saga/references/harness-escalation-policy.md`, `plugins/saga/skills/loop/SKILL.md`, `plugins/saga/skills/doc-review/SKILL.md`, `README.md`, `ANTIGRAVITY.md`, `.github/workflows/ci.yml`, `docs/engineering-journal/DECISIONS.md`, `docs/engineering-journal/QUEUED.md`, `tests/test_antigravity_harness_docs.py`.

**Approach:** Add a shared escalation reference that defines inline, strict reviewer, high-thinking Gemini, and multi-agent consensus triggers. Update loop/doc-review references to cite it where decisions are made. Update README/ANTIGRAVITY with the operator path: run doctor, use `/loop` for generic tasks, use `/doc-review` appliance for serious review, run canaries for prompt changes. Record the KTDs in the engineering journal, clear or update any queued marketplace-consistency item that this work supersedes, and update `docs/engineering-journal/LEARNINGS.md` only if implementation uncovers new empirical behavior.

**Edge cases:** pure docs work mentioning security should not automatically trigger heavy consensus; actual security/data/infra implementation should escalate; unavailable Gemini should degrade to local review plus saved prompt; operator explicitly asks for consensus.

**Error / failure paths:** if escalation policy and operator-choice reference conflict, operator-choice remains canonical for backend selection and the harness policy must link to it; if CI cannot run live Antigravity, CI should still run static doctor/canary tests.

**Integration scenarios:** a future `/work` run can read the plan, doctor output, router behavior, and review appliance docs without chat history. CI validates tests, formatting, doctor, and canary scorer.

**Test scenarios:** `tests/test_antigravity_harness_docs.py` asserts the escalation policy exists, references inline/high-thinking/consensus paths, and is linked from loop/doc-review docs. Existing `tests/test_saga_doc_formatting.py` continues passing.

**Verification:** full local validation for this plan should run `uv run pytest`, `uv run ruff check .`, `uv run mypy plugins/ scripts/ tests/` if mypy config supports scripts, `uv run bandit -r plugins/ scripts/ tests/ -ll`, and both validator entrypoints.

---

## System-Wide Impact

- **CI:** the validate job currently runs both validator entrypoints. U1/U2 must make that deliberate rather than accidentally duplicative.
- **Saga lifecycle:** router behavior changes how bare asks enter lifecycle, but `/loop` remains the owner of routing and existing commands remain phase owners.
- **Docs:** README, plugin spec, marketplace guide, and Antigravity guidance need to stop presenting Claude-era layout as current runtime truth.
- **Review workflow:** `/doc-review` gets an optional Gemini appliance path, while ordinary review behavior stays local and unchanged.
- **Local host safety:** tests must not read or mutate the real `~/.gemini/config/plugins` install directory.

---

## Risks And Mitigations

| risk | mitigation |
|------|------------|
| Doctor becomes a second installer | Keep it read-only; install/uninstall remains `tools/install-plugin.sh`. |
| Legacy validator wrapper hides real failures | Add tests proving wrapper and canonical doctor agree. |
| Router agent duplicates `/loop` | Agent prompt must route to `/loop`/saga commands and forbid non-trivial implementation. |
| Gemini appliance becomes global hostility | Keep appliance reference loaded only by `/doc-review`; no global prompt changes. |
| Canary scorer overfits one review | Start with one fixture but keep fixture schema generic and allow future canaries. |
| CI tries to call live Gemini/Antigravity | CI uses static fixtures and local scripts only. |

---

## Alternatives Considered

| alternative | decision |
|-------------|----------|
| Add a new `/fix` command for generic asks | Rejected for v1. `/loop` already owns lifecycle routing; adding `/fix` duplicates entrypoints. |
| Keep both validators independent | Rejected. Two validators already drifted; v1 needs one canonical source. |
| Run live Gemini canaries in CI | Rejected. Model access and current platform behavior are unstable external dependencies. |
| Put adversarial review guidance in global context | Rejected. The source review explicitly warned this degrades normal execution. |
| Implement canaries before review appliance | Rejected. The scorer needs the expected output contract from the appliance. |

---

## Success Metrics

- `uv run python scripts/validate_plugins.py` reports seven repo-local plugins and distinguishes errors from warnings.
- `uv run python marketplace/validator/validate.py` is a thin compatibility wrapper over canonical doctor status.
- Tests cover doctor success, invalid manifest, empty agent, install-state warning, canary pass, canary miss, uncited finding, router doc presence, and Gemini appliance doc presence.
- README and spec docs no longer describe `.claude-plugin` as the current Antigravity plugin layout.
- `/doc-review` has a reusable Gemini appliance reference with strict evidence output.
- `/loop` and the saga router agent have a shared generic ask compiler reference.

---

## Scope Boundaries

**In scope**

- Antigravity plugin doctor/validator.
- Legacy validation/docs drift cleanup.
- Saga router agent and generic ask compiler reference.
- `/doc-review` Gemini appliance reference.
- Static canary fixture/scorer.
- CI/test/doc/journal integration.

**Deferred Follow-Up Work**

- Live `agy` execution wrapper for the Gemini appliance.
- More canary fixtures beyond the first worker-model cache scheduling seed.
- Hosted marketplace or remote plugin distribution.
- Runtime proof inside an actual fresh Antigravity GUI/CLI session.

**Out of scope**

- Full system prompt replacement.
- Global hostile default personality.
- Blind Claude `SessionStart` hook port.
- Multi-agent consensus for every task.
- Implementation of feature work outside the harness.

---

## Sources / Research

- `docs/brainstorms/2026-06-27-antigravity-harness-requirements.md`
- `docs/reviews/2026-06-27-antigravity-harness-requirements-review.md`
- `docs/ideation/2026-06-27-antigravity-harness-ideation.md`
- `README.md:64-72`
- `STRATEGY.md:35-44`
- `docs/PLUGIN_SPEC.md:1-54`
- `marketplace/validator/schema.json:3-6`
- `marketplace/validator/validate.py:46-54`
- `scripts/validate_plugins.py:1-7`
- `.github/workflows/ci.yml`
- `docs/engineering-journal/DECISIONS.md:112-122`
- `docs/engineering-journal/LEARNINGS.md:50-64`
- `plugins/saga/commands/loop.md:7-27`
- `infiquetra-claude-plugins: docs/reviews/2026-06-27-worker-model-cache-scheduling-review.md`
- `plugins/saga/skills/loop/SKILL.md:8-12`
- `plugins/saga/skills/loop/references/dispatch-table.md:42-57`
- `plugins/saga/skills/code-review/references/findings-schema.md:14-28`
- `plugins/saga/skills/code-review/references/validator.md:8-24`
