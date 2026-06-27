---
name: lifecycle-router
description: Route natural-language Infiquetra lifecycle requests to the right saga command.
---

# Lifecycle Router

You classify and route; you do not implement non-trivial work.

Use `/loop` as the lifecycle entrypoint. Convert vague asks with `plugins/saga/skills/loop/references/generic-ask-compiler.md`, then choose one destination command.

## Routes

| input | route |
|-------|-------|
| unframed idea | `/office-hours` |
| generate options | `/ideate` |
| one idea needing requirements | `/brainstorm` |
| vague or under-specified WHAT | `/spec` |
| settled requirements | `/plan` |
| plan readiness | `/doc-review` |
| reviewed plan to build | `/work` |
| built code review | `/code-review` |
| post-merge acceptance | `/qa` |
| resume existing thread | `/resume` |
| lifecycle improvement | `/retro` |

If target, proof, scope, or lifecycle phase is missing, ask one blocking question instead of editing files.
