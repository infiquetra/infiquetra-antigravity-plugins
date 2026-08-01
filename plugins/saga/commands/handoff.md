---
name: handoff
description: Prepare a lifecycle artifact for SDLC issue handoff through mission-control
argument-hint: "[source artifact, target team, or handoff notes]"
---

Route current lifecycle work to `mission-control` issue preparation.

## Instructions

1. Load `saga/skills/handoff/SKILL.md`.
2. Identify the source artifact from arguments, active loop state, or durable repo docs.
3. Build and validate a `saga.handoff-envelope.v1` envelope with
   `scripts/handoff_envelope.py`. The closed packet must name repository-relative artifacts,
   evidence, risks, and external actions that remain unauthorized.
4. If source, maturity, target repo, target team, or issue type is ambiguous, ask a focused
   question before routing.
5. Route to `/issue --prepare --from <source> --maturity <maturity>`.
6. Do not generate an SDLC issue body in `saga`; `mission-control` owns that artifact and
   all GitHub mutation. Producing the envelope does not authorize issue creation, board updates,
   PR creation, merge, or deployment.

Arguments provided to the command:

`$ARGUMENTS`
