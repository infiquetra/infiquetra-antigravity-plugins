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
