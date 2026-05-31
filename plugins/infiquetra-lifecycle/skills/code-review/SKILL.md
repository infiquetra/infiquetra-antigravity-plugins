---
name: code-review
description: Structured Infiquetra code review for diffs, PRs, and pre-shipping gates.
---

# Code Review

Use this for review requests or before PR and shipping gates.

## Agent Invocation

To perform a code review, **do not run it yourself**. Instead, invoke the specialized code reviewer subagent.

1. Call the `invoke_subagent` tool:
   - **TypeName**: `code-reviewer` (Note: If the agent isn't defined yet, use `define_subagent` first, pointing it to `references/personas/code-reviewer.md`).
   - **Role**: Code Reviewer
   - **Prompt**: Pass the code, diff, or PR link to be reviewed.
2. Wait for the subagent's response.
3. If the review needs multiple reviewer lenses or validators, offer to hand off to `team-execution`.
