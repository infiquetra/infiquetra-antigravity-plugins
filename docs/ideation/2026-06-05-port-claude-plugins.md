# Ideation: Porting Claude Code Plugins to Antigravity

**Date:** 2026-06-05
**Topic:** Porting `saga`, `deploy`, and `mission-control` from `infiquetra-claude-plugins` to `infiquetra-antigravity-plugins`.

## Grounding & Context
- Antigravity enforces a flat layout with `plugin.json` at the plugin root, not hidden in a `.claude-plugin/` directory.
- `src/` should be used for shared scripts and CLI tools, avoiding nesting scripts inside `skills/` (per `DECISIONS.md`).
- Local state checkpoints must be migrated from `.claude/` paths to `.gemini/` paths.
- **Artifact Integration:** Saga actions write documents to `docs/` and other places. When ported, they should continue writing to `docs/` for compatibility, but *must also* make these files available to the Antigravity artifact viewer, turning them into true native Antigravity ports.
- The user wishes to remove the old plugins `infiquetra-lifecycle`, `sdlc-manager`, and `infiquetra-deploy` and replace them with the ported `saga`, `mission-control`, and `deploy`.

## Explored Angles

1. **Compatibility Layer:** Build an Antigravity plugin that natively runs Claude plugins without modifying them. 
   *Critique:* Rejected. This introduces excessive technical debt and prevents the plugins from utilizing Antigravity's native multi-agent tools (like `invoke_subagent`).
2. **Automated Migration Script:** Create a CLI tool `claude-to-antigravity-porter.sh` that takes a Claude plugin path and spits out an Antigravity plugin.
   *Critique:* Accepted. There's a repetitive nature to flattening the layout, moving `scripts/` and `commands/` to `src/`, and regex-replacing `.claude` with `.gemini`. Automating this ensures consistency.
3. **Drop legacy patterns, adopt Native Agents:** For `saga`, completely rewrite the agent loop to leverage Antigravity's native `multi-agent-consensus` and `invoke_subagent` instead of stringing together script-based orchestrators.
   *Critique:* Accepted. Antigravity's agent capabilities are fundamentally different and more powerful. `saga` should orchestrate actual Antigravity agents instead of just running Python loops.
4. **Relax Layout Constraints:** Allow `mission-control` and `deploy` to keep their Claude layout.
   *Critique:* Rejected. The `DECISIONS.md` file explicitly forbids this. We must stick to the root `src/` directory and flat `plugin.json`.

## Selected Directions

### 1. The Migration Pipeline Approach

A migration script or pipeline will be created to port the plugins systematically. This script will:
1. **Structure Generation**:
   - Create the `plugin.json` file in the root.
   - Move python/js logic into `src/`.
   - Setup the `.gemini/` hidden directory for state checkpoints.
2. **Artifact Syncing**:
   - Modify any document-writing mechanisms (like those outputting to `docs/`) to also write or symlink output into the active context directory: `.gemini/antigravity-cli/brain/<id>/`. This ensures compatibility with the Antigravity artifact viewer.
3. **Prompt & Instruction Transformation Rules**:
   - **Subagent Invocation**: Translate `Task agent-name(args)` to `Use the @agent-name subagent to: args`. This ensures Antigravity natively understands subagent delegation in prompts.
   - **Agent Mentions**: Rewrite `@agent-name` to `@agent-name subagent`.
   - **Path Rewriting**: Automatically replace any `~/.claude/` or `.claude/` references with `~/.gemini/` and `.gemini/`.
   - **Commands Translation**: Claude commands should be mapped to `.toml` files (e.g., `commands/name.toml`), containing `description` and `prompt` fields.
4. **Validation**: Check that the resulting layout satisfies Antigravity's constraints.

### 2. Native Multi-Agent `saga`
While `deploy` and `mission-control` are mostly CLI scripts that can be directly mapped, `saga` relies on `team-execution` (which maps to `multi-agent-consensus`).
- Update `saga` to use `invoke_subagent` instead of calling external tools.
- Bind `saga`'s phases directly to Antigravity's slash commands or background tasks.

## Next Steps
We can move to `ce-brainstorm` or straight to an `implementation_plan.md` to define the exact porting steps and build the migration pipeline.
