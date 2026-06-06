---
title: Port Todoist Plugin to Antigravity
type: refactor
status: active
date: 2026-06-06
origin: docs/ideation/2026-06-06-port-todoist-plugin.md
---

# Port Todoist Plugin to Antigravity

## Summary
Port the legacy `todoist-manager` plugin from `infiquetra-claude-plugins` to `infiquetra-antigravity-plugins`. This plan migrates the core python logic into a centralized `src/` directory, drops the monolithic markdown persona for native MCP schemas, eliminates local `.claude/` state for an ephemeral architecture, and enforces portability via an executable ledger.

## Problem Frame
The legacy Todoist plugin relies on outdated Claude-specific state synchronization, disjointed skills, and a heavy markdown orchestrator persona. Porting it directly would leak legacy concepts into Antigravity. We need to refactor it to natively align with Antigravity's flat architecture, native tooling, and zero-state execution models while preserving the core Todoist capabilities.

## Requirements
- **R1.** Migrate `todoist_client.py` to `src/` and wrap it as a reusable CLI utility.
- **R2.** Expose Todoist operations via native MCP schemas in `plugin.json`.
- **R3.** Consolidate legacy skills (`todoist-manage`, `plan-task`, `task-review`) into one unified skill instruction.
- **R4.** Ensure Todoist authentication is managed via standard MCP environment variables (`.env` or MCP client config).
- **R5.** Remove all local state syncing (`.claude/` checkpoints); state must be purely ephemeral and read from Todoist API.
- **R6.** Implement an executable `PORTABILITY.md` test to block Claude-oriented terminology drift.

## Key Technical Decisions
- **KTD1: Native Manifest-Driven MCP Schemas over Monolithic Personas:** Rationale: Defining tools in `plugin.json` leverages native parameter validation and avoids the orchestration overhead and token usage of a dedicated subagent persona.
- **KTD2: Lift Output Contract to Reusable SDK:** Rationale: Enforcing strict JSON success/error boundaries at the core utility level compounds execution stability for future plugins.
- **KTD3: Ephemeral Brain, Stateful Todoist:** Rationale: Duplicating a remote, highly-available stateful system (Todoist) locally creates brittle sync scripts. The Antigravity plugin will be stateless and read-through.
- **KTD4: Executable Portability Ledgers:** Rationale: Human audits fail. A `pytest` hook enforcing absence of terms like `<boltArtifact>` structurally guarantees Requirement R8.
- **KTD5: Skill Consolidation:** Rationale: Antigravity's expanded context window can safely absorb the unified capabilities without disjointed file-hopping.
- **KTD6: Standard MCP Environment Injection:** Rationale: Relying on native MCP environment configuration replaces the legacy hardcoded env parsing without introducing mismatched deployment dependencies like vault-helper.

## Implementation Units

### U1. Scaffolding & Executable Portability Ledger
- **Description:** Initialize the plugin directory `plugins/todoist/`, create `PORTABILITY.md`, and implement `tests/test_todoist_portability.py` to assert that no files in `plugins/todoist/` contain forbidden terms (e.g., `Claude`, `Anthropic`, `.claude`). Set up `uv` workspace.
- **Failure modes:** Test misses binary files or fails on valid Antigravity paths.
- **Test scenarios:** `tests/test_todoist_portability.py` should fail when a dummy file with "Claude" is added, and pass when clean.

### U2. Centralize and Refactor Python Core
- **Description:** Move `todoist_client.py` to `plugins/todoist/src/core/todoist_client.py`. Strip out any legacy environment parsing for `TODOIST_TOKEN` and any checkpointing code. Refactor it to accept the token as a CLI argument or `sys.stdin` and ensure its output adheres strictly to the generic success/error JSON contract.
- **Failure modes:** JSON output is malformed; network timeout to Todoist; missing token argument.
- **Test scenarios:** `tests/test_todoist_client.py` to mock Todoist API and verify JSON output structure for both success and error states.

### U3. Native MCP Schemas & Environment Injection (Host Adapter)
- **Description:** Create `plugins/todoist/plugin.json`. Define the MCP tool schemas that wrap `todoist_client.py`. Configure the tools to pass the token via standard MCP environment blocks, deprecating the legacy `agents/todoist-manager.md`.
- **Failure modes:** Schema mismatch with Python argparser; MCP environment variable not set.
- **Test scenarios:** `tests/test_todoist_mcp_schemas.py` to validate `plugin.json` structure and execute a dry-run tool call verifying argument passing.

### U4. Consolidate Skills and References
- **Description:** Merge `plan-task/SKILL.md`, `task-review/SKILL.md`, and `todoist-manage/SKILL.md` into `plugins/todoist/skills/todoist-operations/SKILL.md`. Copy the 5 reference markdown files to `plugins/todoist/skills/todoist-operations/references/` and update internal links.
- **Failure modes:** Broken internal markdown links; overly long skill prompt exceeding optimal token limits.
- **Test scenarios:** Manual validation: load the skill and verify the agent understands the full lifecycle. Test expectation: none -- [documentation/markdown synthesis only].

## Scope Boundaries
- **Deferred to Follow-Up Work:** Adding net-new Todoist API features (like comments or attachments) not present in the legacy plugin.
- **Out of Scope:** Maintaining backward compatibility with legacy `.claude/` state files.
