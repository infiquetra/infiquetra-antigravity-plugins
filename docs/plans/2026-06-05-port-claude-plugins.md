---
title: Port Claude Plugins
type: feat
status: active
date: 2026-06-05
origin: docs/brainstorms/2026-06-05-port-claude-plugins-requirements.md
---

# Port Claude Plugins Migration Plan

## Summary

Implement a reusable Python script (`scripts/port_claude_plugin.py`) to automate the translation of legacy Claude Code plugins (`saga`, `deploy`, `mission-control`) into the Antigravity architecture, migrating directory structures, translating subagent syntax, converting commands to `.md`, and setting up artifact viewer duplication. Following successful porting, the legacy implementations (`infiquetra-lifecycle`, `sdlc-manager`, `infiquetra-deploy`) will be removed.

---

## Problem Frame

Currently, `saga`, `deploy`, and `mission-control` use older Claude Code plugin patterns and need translation into Antigravity framework formats. Rather than a manual translation, an automated tool will modify file structures, prompt text, and artifact syncing logic to operate properly in Antigravity.

---

## Requirements

- R1. Create `plugin.json` at the root of the targeted plugin.
- R2. Consolidate source Python/JS logic into `src/`.
- R3. Automatically rewrite `~/.claude/` or `.claude/` path references to `~/.gemini/` and `.gemini/`.
- R4. Translate Claude agent invocation lines (`Task agent-name(args)`) to Antigravity invocation (`Use the @agent-name subagent to: args`).
- R5. Append ` subagent` to `@agent-name` mentions inside instruction texts.
- R6. Convert any existing Claude command configurations into `.md` command definitions containing YAML frontmatter and a markdown body.
- R7. Strip out legacy Claude artifact-syncing logic entirely instead of symlinking to the Antigravity brain directory.
- R8. Delete `infiquetra-lifecycle`, `sdlc-manager`, and `infiquetra-deploy` legacy tools from the repo once porting is validated.
- R9. Promote passive nested personas to an active root-level `agents/` directory for native Antigravity subagent discovery.

---

## Scope Boundaries

- We are porting the existing Claude plugins as-is functionally; we are not redesigning what `saga`, `deploy`, or `mission-control` do.
- Generalization of the porting script for plugins outside these three is explicitly *not* in scope (per manual review resolution constraint).

---

## Context & Research

### Relevant Code and Patterns

- Use `pathlib.Path` heavily to resolve root and target directories dynamically.
- Follow existing Python CLI patterns found in `scripts/validate_plugins.py` including ANSI colors, modular validation, and returning tuples like `(is_success, errors_list)`.
- Use existing `.md` command formats (seen in `sdlc-manager` commands) as a template for generating Antigravity command structures.

### Institutional Learnings

- **Cross-Plugin Path Audits Are Mandatory**: Recursively search to ensure that deep dependencies aren't broken by path changes (`.claude/` to `.gemini/`).
- **Fallback Mocking in Tests**: Test fixtures must mock both `~/.gemini/` and `~/.claude/` to prevent host filesystem leakage.
- **Root `src/` Consolidation**: Do not leave scripts nested within `skills/` folders; move them to `src/`.
- **Root `agents/` Directory Promotion**: Promote passive nested personas to an active root-level `agents/` directory for native Antigravity subagent discovery.

---

## Key Technical Decisions

- **Command Format Adjustment**: Commands will be generated as `.md` files instead of `.toml` because Antigravity uses Markdown command configurations natively (identified during research).
- **Native State vs Custom Checkpoints**: Removed the requirement to setup a hidden `.gemini` directory for state checkpoints (original R3). We will rely on Antigravity's native artifact capabilities instead, resolving the native state conflict.
- **Focused Script Scope**: The migration script will be hardcoded specifically to handle the directories and files relevant for `saga`, `deploy`, and `mission-control` to avoid building unnecessary generic frameworks.

---

## Output Structure

    scripts/
      port_claude_plugin.py
    tests/
      test_port_claude_plugin.py

---

## Implementation Units

### U1. Implement the Porting Script Core Framework

**Goal:** Create `scripts/port_claude_plugin.py` with standard CLI scaffolding, Pathlib usage, and the main execution flow to iterate through the 3 targeted plugins.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Create: `scripts/port_claude_plugin.py`
- Test: `tests/test_port_claude_plugin.py`

**Approach:**
- Start with `#!/usr/bin/env python3`.
- Iterate through a hardcoded list of the three targeted plugins (saga, deploy, mission-control) and write outputs to `plugins/<name>` in the current repository.
- Ensure the base plugin creates a `plugin.json` and moves loose python scripts to `src/`.
- Ensure tests mock `~/.gemini/` and `~/.claude/` paths to prevent host filesystem leakage.

**Patterns to follow:**
- `scripts/validate_plugins.py` (ANSI colors, return tuples)

**Test scenarios:**
- Happy path: Script executes and successfully creates `plugin.json` for all three hardcoded target plugins.

### U2. Implement Path Rewriting and Syntax Translation

**Goal:** Add functions to the script to translate `.claude/` paths and subagent invocations inside `.md` and `.py` files.

**Requirements:** R3, R4, R5

**Dependencies:** U1

**Files:**
- Modify: `scripts/port_claude_plugin.py`
- Modify: `tests/test_port_claude_plugin.py`

**Approach:**
- Use regex to safely locate `Task agent-name(...)` and `@agent-name` and replace them.
- Deeply audit path translations (e.g., using `re.sub` for `.claude` paths) to ensure fallback mechanisms aren't broken.

**Patterns to follow:**
- Cross-Plugin Path Audits learning.

**Test scenarios:**
- Happy path: A file containing `Task reviewer(review the code)` is converted to `Use the @reviewer subagent to: review the code`.
- Happy path: A text containing `Ask @reviewer to confirm` is converted to `Ask @reviewer subagent to confirm`.

### U3. Implement Command Format Conversion

**Goal:** Translate legacy command configs into Antigravity `.md` format.

**Requirements:** R6

**Dependencies:** U1

**Files:**
- Modify: `scripts/port_claude_plugin.py`
- Modify: `tests/test_port_claude_plugin.py`

**Approach:**
- Read old command properties and construct a `.md` file containing YAML frontmatter (`name`, `description`) and a markdown body for the prompt.

**Patterns to follow:**
- `plugins/sdlc-manager/commands/*.md`

**Test scenarios:**
- Happy path: Old config is outputted as a valid `.md` command file with YAML frontmatter.

### U4. Implement Artifact Syncing and Agent Promotion

**Goal:** Remove legacy artifact duplication logic and promote personas to `agents/`.

**Requirements:** R7

**Dependencies:** U1

**Files:**
- Modify: `scripts/port_claude_plugin.py`
- Modify: `tests/test_port_claude_plugin.py`

**Approach:**
- Strip out any document write outputs or syncing logic meant for legacy artifacts.
- Move any `references/personas/*.md` files into a root `agents/` directory.

**Patterns to follow:**
- Root `agents/` Directory Promotion learning.

**Test scenarios:**
- Happy path: Personas are successfully detected and moved from references to the agents directory.

### U5. Execute Porting and Cleanup

**Goal:** Run the script to port the 3 plugins and remove the old legacy Antigravity plugins.

**Requirements:** R8

**Dependencies:** U1, U2, U3, U4

**Files:**
- Remove: `plugins/infiquetra-lifecycle/`
- Remove: `plugins/sdlc-manager/`
- Remove: `plugins/infiquetra-deploy/`

**Approach:**
- Run the script from the repository root to port `saga`, `deploy`, and `mission-control` into `plugins/<name>`.
- Verify behavior.
- Delete the old implementation plugins from the repository.

**Test scenarios:**
- Test expectation: none -- this is an execution/cleanup step, not a code implementation step.

---

## Open Questions

- **Deferred to Implementation**: Missing backward compatibility for renamed plugins (`saga`, `mission-control`). We need to consider if CI scripts, CLI configs, or docs will break without a shim.
