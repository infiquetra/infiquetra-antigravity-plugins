---
name: multi-agent-consensus
description: Execute a plan with automatic multi-reviewer consensus workflow using Antigravity subagents.
argument-hint: "[plan text or file path]"
---

Handle this command as follows based on what's available:

## Case 1: No plan provided

If `$ARGUMENTS` is empty and there is no plan in the current conversation context:

Ask the user:
```
Please describe what you want to build or provide a plan to execute.

Once you share the details, I'll execute the plan using the Multi-Agent Consensus skill, which spawns parallel workers and a team of reviewers to ensure quality.
```

## Case 2: Plan exists

If a plan is present (from `$ARGUMENTS`, a file path, or the current conversation):

Immediately invoke the `multi-agent-consensus` skill. Follow its instructions to spawn worker subagents using `invoke_subagent`, wait for their completion, and then run the Reviewer Consensus Loop with the defined personas.

---

## Quick Reference

The plan to execute (if provided):

$ARGUMENTS
