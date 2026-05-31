---
name: handoff
description: Route durable Infiquetra lifecycle artifacts into sdlc-manager prepared issue drafts.
---

# Handoff

Use this when the user wants another team, agent team, or later session to pick up work from an
Infiquetra lifecycle artifact.

## Boundary

`infiquetra-lifecycle` owns the handoff moment:

- select the durable source artifact or active pointer;
- infer lifecycle phase and handoff maturity;
- capture why the work is being handed off, blockers, open questions, target team, and target
  repository when known;
- route to `sdlc-manager`.

`sdlc-manager` owns the issue artifact:

- issue body sections;
- prepared draft markdown and JSON sidecar;
- readiness checks;
- labels, project fields, board placement, and GitHub mutation;
- create-after-confirmation mutation plan.

Do not copy SDLC issue templates into this skill.

## Workflow

1. Prefer an explicit source path or URL from the command arguments.
2. If no source is explicit, inspect `.gemini/infiquetra-lifecycle/state.json` and durable docs.
3. Build the envelope:

   ```bash
   python3 plugins/infiquetra-lifecycle/src/handoff_envelope.py \
     --source docs/plans/example.md \
     --target-team Asgard \
     --target-repo infiquetra-claude-plugins
   ```

4. If the helper finds no source, ask for one.
5. If multiple durable artifacts are plausible, ask the user to choose.
6. Native Antigravity Handoff: Do not suggest a slash command. Instead, use `invoke_subagent` to launch the **SDLC Operator** (TypeName: `self`).
7. Pass the envelope's details (source path, maturity, target team) into the subagent's prompt so it can autonomously prepare the issue.
8. Have the user review the prepared issue draft before confirming the final `issue create-prepared` mutation.

## Maturity

- `docs/ideation/` -> `idea-ready`
- `docs/brainstorms/` -> `requirements-ready`
- `docs/plans/` or `docs/reviews/` -> `plan-ready`
- `docs/work-sessions/` or branch refs -> `resume-ready`
- explicit preserve/defer language -> `deferred-context` when the user says execution should wait

## Recipient Guidance

Prepared issues must be self-contained for recipients without `infiquetra-lifecycle`.

When a recipient does have `infiquetra-lifecycle`, the issue may suggest:

- `/plan <issue>` for `idea-ready` or `requirements-ready`;
- `/work <issue>` for `plan-ready` or `resume-ready`.

Do not suggest `/loop` for normal team handoff.
