# Decisions — Infiquetra Claude Plugins

> **ADR-style records of plugin-pattern / convention / tooling choices.** When you commit a chosen path over alternatives — pick A over B, flip a flag, change a threshold, choose a category, adopt a tool — capture rationale + tradeoff + revisit-when condition + commit hash.
>
> The point is to make **revisit conditions explicit** so a future Claude (or human) reading "why did we pick X?" gets the answer cold, including when it would be right to reconsider.
>
> **Append new entries to the top.** Format:
>
> ```markdown
> ## YYYY-MM-DD
>
> ### Short title (commit hash)  {#slug}
>
> **Decision.** What we picked.
> **Rejected alternatives.** What we considered and didn't pick.
> **Rationale.** Why this won.
> **Revisit when.** Condition that would change the calculus.
> **Refs.** Related LEARNINGS / QUEUED / narratives.
> ```
>
> When new evidence invalidates a decision, **update inline AND move the pre-correction version to `ARCHIVE.md` as SUPERSEDED**.

---

## 2026-06-27

### Antigravity harness plan decisions (commit pending) {#antigravity-harness-plan}

**Decision.** Plan the Antigravity harness as one integrated v1: a single canonical doctor in `scripts/validate_plugins.py`, repo-local `plugins/*/plugin.json` inventory, read-only host-isolated install checks, saga generic-ask routing through `/loop` plus a narrow router agent, `/doc-review`-scoped Gemini review appliance, static review canaries, and shared cheap-first escalation policy.

**Rejected alternatives.** Keep independent validator entrypoints; add a new `/fix` command; put adversarial review behavior in global context; run live Gemini canaries in CI; make multi-agent consensus the default for routine tasks.

**Rationale.** Runtime truth is the cheapest foundation: if Antigravity cannot see the expected plugin surfaces, prompt tuning cannot fix the failure. Reusing `/loop` and `/doc-review` avoids new command sprawl, while static canaries keep CI deterministic.

**Revisit when.** Antigravity publishes a stronger plugin/hook contract, live `agy` invocation becomes stable enough for optional non-CI review runs, or the canary corpus grows large enough to justify a richer evaluator.

**Refs.** Plan: `docs/plans/2026-06-27-antigravity-harness-plan.md`. Requirements: `docs/brainstorms/2026-06-27-antigravity-harness-requirements.md`. Review: `docs/reviews/2026-06-27-antigravity-harness-requirements-review.md`.

---

## 2026-06-11

### `/impl-spec` and `/product-review` plan decisions (commit pending)  {#impl-spec-product-review-plan}

**Decision.** Introduce 2 new saga skills and extend 1:

1. `/impl-spec` — a 6-stage implementation spec pipeline (Archetype B: multi-stage loop). SKILL.md
   stays under 250 lines; stage protocols go to `references/impl-spec-stages.md`. Uses Antigravity-
   native `define_subagent`/`invoke_subagent` for parallel authoring waves and probe spawning (the
   subagent orchestration IS the core behavior, unlike `/optimize` which delegates fan-out to
   operator-choice).
2. `/product-review` — an off-chain advisory experiment gate (Archetype A: advisory gate). No Python
   scripts; the skill is simple enough that the agent handles logic inline. Simplified from vecu's
   version: no revival ceremony.
3. `/doc-review` — gains a buildability-probe mode (~70 lines additive). Probe mode is highest-
   precedence in classification (explicit request first). No existing behavior modified.
4. Shared reference docs (`buildability-probe-protocol.md`, `lifecycle-closure-matrix-template.md`)
   live at `plugins/saga/references/` (plugin-level, following `formatting-style.md` precedent).
5. Dispatch table grows from 17 → 19 routable commands. Both new entries are off-chain + advisory.

**Rejected alternatives.**
- *Add implementation spec as a mode of `/spec`.* Rejected: would make `/spec` monolithic (the vecu
  `/work-loop` at 621 lines is the cautionary example). `/spec` stays WHAT-only.
- *Add a `product_review.py` script.* Rejected: `/product-review` is simple enough to work without
  one. Premature script — can be added later if revival logic is needed.
- *Probe mode as a separate skill.* Rejected: the probe is a quality gate, not a lifecycle phase. It
  belongs in `/doc-review` as a composable mode, callable independently or by `/impl-spec`.

**Rationale.** Each new skill follows an established archetype (advisory gate or multi-stage loop) to
maintain pattern consistency. The shared reference docs avoid duplication between `/impl-spec` and
`/doc-review`. No scripts means less maintenance surface; no probe skill means the probe is composable.

**Revisit when.** `/product-review` needs revival logic (pulling near-miss ideas from `/ideate`), or
`/impl-spec` needs a crash-recovery checkpoint mechanism beyond the scratch-file approach.

**Refs.** Plan: `docs/plans/2026-06-11-impl-spec-product-review-plan.md`. Requirements:
`docs/brainstorms/2026-06-11-impl-spec-and-product-review-requirements.md`.

---

## 2026-06-09

### Track renamed Hermes plugin repo in Mission Control (commit `eb1c9bd`)  {#mission-control-hermes-plugin-repo-rename}

**Decision.** Update the vendored Mission Control repository mapping to use
`infiquetra-hermes-plugins`, and repair the adjacent syntax corruptions that prevented the mapping
test from collecting.

**Rejected alternatives.**
- *Rely on GitHub redirects.* Rejected: project mapping data is not a clone URL and must match the
  canonical repository name used for board routing.
- *Skip the test because the repo already had syntax corruption.* Rejected: the changed mapping is a
  routing contract, so the local test needed to import before this branch was PR-ready.

**Rationale.** Antigravity carries the same Mission Control board-routing surface as the Claude and
Codex plugin repos. Keeping its vendored repo list current prevents future issue preparation or board
adds from targeting the retired repository identity.

**Revisit when.** Mission Control discovers repositories live instead of using vendored canonical
sets, or Antigravity stops carrying Mission Control as an active plugin.

**Refs.** `plugins/mission-control/config/project-mappings.json`;
`plugins/mission-control/tests/test_project_mappings_resolution.py`.

---

## 2026-06-08

### Adopt shared formatting contract for saga documents (commit pending)  {#adopt-shared-formatting-contract}

**Decision.** Adopt a single, shared formatting contract (`plugins/saga/references/formatting-style.md`) across all saga doc-generating plugins, enforcing clean markdown syntax (such as short paragraphs, lead-with-a-summary, comparative data as tables, and blank-line-separated labels to avoid fatal bold-label collapse).

**Rejected alternatives.**
- *Keep formatting guidelines embedded locally within each individual skill or script.* Rejected: This led to divergent styling rules, drift, and formatting inconsistencies between the different phases of the lifecycle.
- *Rely on raw regex patterns for validation.* Rejected: Generating strict markdown is better validated by structural markdown syntax tests rather than complex and brittle regular expressions.

**Rationale.** A central formatting reference ensures consistency across all generated artifacts (such as plans, specs, strategy files, and reviews). Adding a structural test ensures that these rules are automatically validated and that the formatting contract does not drift.

**Revisit when.** The markdown viewer tools in our runtime environment change, or we adopt a rich web interface that renders structured data instead of markdown files.

**Refs.**
- LEARNINGS [saga formatting parser constraints](#saga-formatting-parser-constraints)
- [formatting-style.md](../../plugins/saga/references/formatting-style.md)
- [test_saga_doc_formatting.py](../../tests/test_saga_doc_formatting.py)

---

## 2026-05-31

### Promote agent and SRE personas to root-level `agents/` directories (commit `41c9a94`)  {#promote-agents-root-layout}

**Decision.** Promote all passive nested personas (e.g. `skills/.../references/personas/`) to active root-level `agents/` directories at each plugin root, adhering strictly to the official layout standard defined in `ANTIGRAVITY.md`.

**Rejected alternatives.**
- *Keep nested markdown personas under `references/personas/`.* Rejected: This violates the official Antigravity plugin layout structure and hides SRE/agent configs, making them passive instead of active subagent definitions.
- *Define agents as raw system prompts inside `plugin.json`.* Rejected: Keeping system prompts inside structured markdown files under `agents/` is infinitely more readable, easier to maintain, and supports clean version control.

**Rationale.** Promoted personas in the root `agents/` directory are automatically discovered and can be natively invoked using the `invoke_subagent` tool. This simplifies subagent definition and orchestration while maintaining repository layout consistency.

**Revisit when.** The Antigravity SDK changes its agent discovery rules or introduces a centralized agents directory at the repository root.

**Refs.** ANTIGRAVITY.md [Plugin Types](ANTIGRAVITY.md#L41-L83).

---

### Consolidate executable scripts in a root-level `src/` directory (commit `41c9a94`)  {#consolidate-scripts-src}

**Decision.** Consolidate all executable python scripts under a root-level `src/` directory within each plugin's folder (such as relocating `unifi` scripts from `skills/unifi-network/scripts/` to `src/`).

**Rejected alternatives.**
- *Leave scripts nested within skill subfolders (e.g., `skills/.../scripts/`).* Rejected: This makes importing shared helper classes and utilities across different skills in the same plugin difficult and results in duplicate code/helpers. It also breaks repository layout consistency.

**Rationale.** Grouping python files under a unified root-level `src/` directory provides a consistent codebase architecture across all CLI-based plugins, simplifies import paths for tests and commands, and mirrors the architecture of other modernized plugins like `sdlc-manager` and `infiquetra-lifecycle`.

**Revisit when.** A plugin requires isolation of python runtimes or dependencies on a per-skill basis.

---

## 2026-05-08

### Adopt uv as canonical dependency sync (commit pending)  {#uv-canonical-sync}

**Decision.** Use uv as the canonical repository dependency sync tool. Track `uv.lock`, install CI dependencies with `uv sync --locked --extra dev`, and run local and CI checks through `uv run`.

**Rejected alternatives.**
- *Keep using pip in CI.* Rejected: it contradicts the desired repository standard and leaves installs unreproducible.
- *Use `uv pip install` without a lockfile.* Rejected: it is still an ad hoc install path and does not satisfy the existing revisit condition for tracking `uv.lock`.
- *Move all dev dependencies to `[dependency-groups]` now.* Rejected: the existing `dev` extra maps directly from the prior `pip install -e ".[dev]"` workflow, so moving dependency ownership would add churn without improving the conversion.

**Rationale.** The repository already has `pyproject.toml` metadata and had a documented revisit condition to track `uv.lock` once uv became canonical. A checked lockfile plus `uv sync --locked --extra dev` makes CI and local development use the same dependency graph.

**Revisit when.** uv stops being the repository development standard, or the project intentionally changes from extras-based dev dependencies to uv dependency groups.

**Refs.** Supersedes the `uv.lock` portion of [gitignore `.claude/` + no `uv.lock`](#gitignore-claude-and-no-uv-lock); archived pre-correction version in [ARCHIVE](ARCHIVE.md#superseded-no-uv-lock-decision).

---

## 2026-05-01

### Gitignore `.claude/`; `uv.lock` decision superseded (commit `4da5705`)  {#gitignore-claude-and-no-uv-lock}

**Decision.** Add `.claude/` to `.gitignore`. The prior decision not to track `uv.lock` is superseded by [Adopt uv as canonical dependency sync](#uv-canonical-sync).

**Rejected alternatives.**
- *Track `.claude/settings.local.json`.* Rejected: file holds per-user permission grants for the Claude Code session. Sharing one user's allowed-tool list would either leak local preferences or get blindly overwritten by the next user. The file is named `.local.json` for a reason.
- *Track `.claude/context/sdlc-plan-state.json`.* Rejected: mid-session orchestration state from `sdlc-manager`. Stale immediately after the session ends; would create misleading commits if pushed.

**Rationale.** `.claude/` content is per-user / per-session by design (settings.local + context state). The earlier `uv.lock` rationale was correct when the repo used ad hoc pip/uv installs, but no longer applies now that uv is the canonical lock-and-install path.

**Revisit when.** Claude Code introduces a *shared* settings file under `.claude/` that's intended to be checked in. At that point, narrow the gitignore from `.claude/` to specifically `.claude/settings.local.json` and `.claude/context/`.

**Refs.**
- DECISIONS [uv canonical sync](#uv-canonical-sync) — supersedes the lockfile portion of this decision.
- LEARNINGS [marketplace registry drift](LEARNINGS.md#marketplace-drift) — same PR (#112).
- ARCHIVE [PR #112](ARCHIVE.md#pr-112-marketplace-fix) — shipped record.
- ARCHIVE [superseded no-uv-lock decision](ARCHIVE.md#superseded-no-uv-lock-decision) — pre-correction record.

---

## Porting Claude Plugins: Hardcoded Script & Native State
**Date:** 2026-06-06
**Commit:** 8fb23bf

**Decision.** To port `saga`, `deploy`, and `mission-control` from Claude to Antigravity, we wrote a single-purpose script (`scripts/port_claude_plugin.py`) instead of a generic CLI framework. Additionally, we completely stripped out the legacy `.claude/` checkpoint syncing logic.

**Rationale.**
1. **Hardcoded > Generic:** We only needed to port three specific, known plugins. Building a generic framework to handle any arbitrary legacy plugin would have been over-engineering, increasing scope without adding value.
2. **Native State Management:** Antigravity natively manages state in its `brain/` directory (via `implementation_plan.md`, `task.md`, `walkthrough.md`). The legacy plugins manually wrote state checkpoints to `.claude/saga/`. Syncing these into Antigravity would have meant fighting the native architecture. We deleted scripts like `scaffold_checkpoint.py` instead.

**Revisit when.** If we find that subagents lose context too quickly without checkpoints, we may need to implement a native Antigravity state checkpointing mechanism.
