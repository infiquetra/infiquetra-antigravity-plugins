---
date: 2026-06-05
topic: port-claude-plugins
---

# Port Claude Plugins Migration

## Summary

A reusable Python script (`scripts/port_claude_plugin.py`) will be built to systematically port any Claude Code plugin to Antigravity format. We will use this to port `saga`, `deploy`, and `mission-control` as three distinct plugins.

---

## Problem Frame

Currently, `saga`, `deploy`, and `mission-control` are built as Claude Code plugins and rely heavily on older patterns. Antigravity handles subagents, plugins, and commands differently. Instead of doing a manual translation for each one, an automated translation tool is needed to transform existing prompt text, file structures, and artifact syncing logic to properly operate in Antigravity.

---

## Requirements

**Migration Script Logic**
- R1. Create `plugin.json` at the root of the targeted plugin.
- R2. Consolidate source Python/JS logic into `src/`.
- R3. Setup a hidden `.gemini/` directory to handle state checkpoints.
- R4. Automatically rewrite `~/.claude/` or `.claude/` path references to `~/.gemini/` and `.gemini/`.

**Prompt and Instruction Translation**
- R5. Translate Claude agent invocation lines (`Task agent-name(args)`) to Antigravity invocation (`Use the @agent-name subagent to: args`).
- R6. Append ` subagent` to `@agent-name` mentions inside instruction texts.
- R7. Convert any existing Claude command configurations into `.toml` command definitions (in `commands/*.toml`) containing `description` and `prompt`.

**Artifact Syncing Integration**
- R8. For ported plugins, ensure that document-writing logic is modified to duplicate or symlink output to the active `.gemini/antigravity-cli/brain/<id>/` context directory.

**Cleanup**
- R9. Once porting is validated, `infiquetra-lifecycle`, `sdlc-manager`, and `infiquetra-deploy` legacy tools must be deleted from the repo.

---

## Acceptance Examples

- AE1. **Covers R5.** Given a SKILL.md file with `Task reviewer(review the code)`, when the script processes it, the output should be `Use the @reviewer subagent to: review the code`.
- AE2. **Covers R6.** Given a text containing `Ask @reviewer to confirm`, when processed, it becomes `Ask @reviewer subagent to confirm`.

---

## Success Criteria

- The script can execute successfully over `saga`, `deploy`, and `mission-control` plugins.
- The resulting plugins can be installed in Antigravity CLI, their subagents can be properly invoked, and documents written by them show up in the Antigravity artifact viewer.

---

## Scope Boundaries

- We are porting the existing Claude plugins as-is functionally; we are not redesigning what `saga`, `deploy`, or `mission-control` do, only adapting how they interface with the CLI.

---

## Key Decisions

- Build a generic migration tool instead of a one-off script so other plugins can be ported later.
- Maintain `saga`, `deploy`, and `mission-control` as separate plugins.

---

## Dependencies / Assumptions

- `infiquetra-claude-plugins` contains the source plugins on disk.
