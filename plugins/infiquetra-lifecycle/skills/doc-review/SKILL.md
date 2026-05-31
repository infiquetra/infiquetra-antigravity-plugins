---
name: doc-review
description: Review Infiquetra plans, requirements, and SDLC documents for implementation readiness.
---

# Doc Review

Use this when a plan, requirements document, strategy document, or formal Infiquetra SDLC
artifact is about to guide implementation.

The core question is:

> Can this document safely drive implementation without the agent inventing missing decisions
> or acting on unverified assumptions?

This is not a copy-editing workflow and it is not a replacement for code review.

## Agent Invocation

To perform a doc review, **do not run it yourself**. Instead, invoke the specialized doc reviewer subagent.

1. Call the `invoke_subagent` tool:
   - **TypeName**: `doc-reviewer` (Note: If the agent isn't defined yet, use `define_subagent` first, pointing it to `references/personas/doc-reviewer.md` and enabling write tools if safe in-place fixes are desired).
   - **Role**: Doc Reviewer
   - **Prompt**: Pass the document path or content to be reviewed.
2. Wait for the subagent's response.
3. If the review needs multiple reviewer lenses, offer to hand off to `team-execution`.

## Target Resolution

1. If the user supplied a path, pass that document.
2. If no path was supplied, look for an obvious active plan or requirements document under
   `docs/plans/` or `docs/brainstorms/`.
3. If the target is still ambiguous, ask for the document path before reviewing.

## Safe In-Place Fixes

The doc-reviewer may suggest safe fixes or perform them if it has write access. Safe fixes include:
- adding missing schema fields already implied elsewhere in the document
- correct origin requirement mappings when the right mapping is evident
- move follow-up work out of canonical schema and into prose or runbook sections

Unsafe changes become findings instead of edits (e.g. inventing acceptance criteria, choosing architecture without evidence).

## Durable Review Artifacts

Write a review artifact under `docs/reviews/` when any trigger is true:

- any `P0` or `P1` finding remains
- any safe fix edits the document
- a formal SDLC delegate ran
- an issue-attached lifecycle flow is active
- more than three findings remain after safe fixes

Every significant review artifact should include the target path, blocked status, finding priorities, and linked issues.

## Loop And Work Integration

`/doc-review` is explicit by default. `/work` should ask whether to run it before executing from
a plan or requirements document. If unresolved `P0` or `P1` findings remain, `/work` blocks unless explicitly overridden.
