---
name: qa
description: Run risk-based Infiquetra QA gates for code, docs, browser behavior, deployment, and acceptance evidence.
---

# QA

Use this before PR readiness, merge readiness, nonprod deployment evidence, or completion.

## Agent Invocation

To perform a QA check, **do not run it yourself**. Instead, invoke the specialized QA Engineer subagent.

1. Call the `invoke_subagent` tool:
   - **TypeName**: `qa-engineer` (Note: If the agent isn't defined yet, use `define_subagent` first, pointing it to `references/personas/qa-engineer.md` and enabling write tools to allow the agent to run tests and write to `docs/qa/`).
   - **Role**: QA Engineer
   - **Prompt**: Pass the context of the work, the plan's verification section, and what needs to be tested.
2. Wait for the subagent's response.
3. Update issue progress with the checks run and remaining risk provided by the subagent.
