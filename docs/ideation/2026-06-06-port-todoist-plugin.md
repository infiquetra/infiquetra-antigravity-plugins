# Ideation: Porting Todoist Plugin to Antigravity

**Date:** 2026-06-06
**Topic:** Port the legacy `todoist-manager` plugin from `infiquetra-claude-plugins` to `infiquetra-antigravity-plugins` in the Antigravity way.

## Grounding Context
- **Constraints:** Must use flat layout, `plugin.json` manifest, native `brain/` state, `uv` dependencies, root-level subagents, unified `src/`. Must include `PORTABILITY.md` ledger. Strictly prohibit Claude terminology.
- **Legacy Shape:** Heavy markdown persona (`agents/todoist-manager.md`), nested scripts with strict JSON contracts, legacy `.claude/` state checkpointing. Three fragmented skills.

## Final Survivors

### 1. Native Manifest-Driven MCP Schemas over Monolithic Personas
- **Axis:** Host Adapter Rewrite
- **Idea:** Instead of relying on a heavy `todoist-manager.md` persona to delegate workflows, define native MCP tool schemas for the Python operations in `plugin.json`. This allows the host adapter to wire capabilities directly into the orchestrator context with native parameter validation, eliminating the subagent middleman.

### 2. Lift the Output Contract into a Reusable CLI SDK
- **Axis:** Portable Core Migration
- **Idea:** Extract the strict JSON success/error contract from the legacy script into a shared `plugins/todoist/src/core/` utility. This enforces Antigravity-friendly JSON shapes for any Python tool invocation, giving future ports robust parsing guardrails for free.

### 3. Ephemeral Brain, Stateful Todoist (Zero-State Local)
- **Axis:** State & Path Modernization
- **Idea:** Strip out legacy `.claude/` checkpoint syncing completely and treat the Todoist API as the absolute real-time source of truth. Bypassing local state synchronization removes brittle reconciliation scripts and drift errors.

### 4. Executable Portability Ledgers (Drift Prevention as Code)
- **Axis:** Portability Governance
- **Idea:** Reframe `PORTABILITY.md` from a static document to an executable test manifest. Introduce a `pytest` hook or pre-commit rule that reads the ledger and statically analyzes the ported codebase, explicitly failing CI if legacy terms (like `<boltArtifact>`) are detected.

### 5. Skill Consolidation via High-Context LLMs
- **Axis:** Portable Core Migration
- **Idea:** Collapse the three legacy skills (`todoist-manage`, `plan-task`, `task-review`) into a single unified `todoist-operations` skill or unified MCP server. Antigravity's expanded context window can handle the consolidated operations without disjointed file-hopping.

### 6. Ephemeral Token Injection via Vault-Helper
- **Axis:** State & Path Modernization
- **Idea:** Invert the auth flow: remove static `TODOIST_TOKEN` parsing from the Python script. The Host Adapter will use Antigravity's `vault-helper` to dynamically inject the token via STDIN or an ephemeral environment only at execution time.

## Next Steps
This ideation is complete. To proceed with implementation planning, run:
`/plan docs/ideation/2026-06-06-port-todoist-plugin.md`
