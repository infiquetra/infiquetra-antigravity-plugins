---
name: port-claude-plugins
description: Triggered when the user says "port the recent changes to the claude plugins" or asks to port Claude plugin updates to Antigravity. Kicks off the saga planning process to sync from the infiquetra-claude-plugins repository.
---

# Port Claude Plugins

You are tasked with porting the latest changes from the Claude plugin repository (`../infiquetra-claude-plugins`) into the Antigravity plugin repository (`.`).

## Workflow

1. **Strict Planning Phase:**
   DO NOT execute code changes immediately. You must first invoke the `/plan` skill (part of the `saga` plugin lifecycle) to draft an `implementation_plan.md`. If the request is vague, you may first use `/ideate` or `/brainstorm`.
   
2. **Review and Approval:**
   Once the `implementation_plan.md` is drafted, STOP and ask the user for approval. You may not transition to execution without an explicit go-ahead.

3. **Classification:**
   In your plan, explicitly classify all changes into one of the following categories:
   - `direct-port`: Can be moved over exactly as is.
   - `antigravity-adapt`: Requires modification to fit Antigravity (see rules below).
   - `metadata-only`: Changes to plugin configs/manifests.
   - `blocked` or `deferred`: Claude-specific things we cannot port yet.

4. **Antigravity Adaptation Rules:**
   When you do execute the approved plan, you MUST apply these specific transformations to build an Antigravity-native port:
   - **Tool Mappings**: Translate Claude tool identifiers to Antigravity equivalents.
     - `Edit` -> `replace_file_content`
     - `Write` -> `write_to_file`
     - `MultiEdit` -> `multi_replace_file_content`
     - `Bash` -> `run_command`
   - **Environment Variables**: Replace `${CLAUDE_PLUGIN_ROOT}` with `${ANTIGRAVITY_PLUGIN_ROOT}` in `hooks.json` and scripts.
   - **Agent Mappings**: Map Claude's `team-execution` to `multi-agent-consensus`.
   - **Security Pragmatics (Bandit)**: Antigravity enforces strict CI security scans using `bandit`. Add `# nosec` tags (e.g., `# nosec B603 B607`) to any `subprocess.run` calls or `try/except: pass` blocks (e.g., `# nosec B110`) in Python hook files.

5. **Post-Port Validation:**
   After porting, you must run the following to validate the port:
   - `uv run pytest -q`
   - `uv run ruff check .`
   - `uv run bandit -r plugins/ -q -c pyproject.toml`
   - `uv run python plugins/saga/scripts/render_docs_visuals.py` (to regenerate docs)

Remember: this is not a blind sync. You are building an Antigravity-native port. Always prioritize the established Infiquetra and Antigravity paradigms over blind copying.
