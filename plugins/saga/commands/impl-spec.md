---
name: impl-spec
description: Build and prove a profile-backed multi-document implementation specification
argument-hint: "<profile.json> [autonomous|interactive]"
---

Load `saga/skills/impl-spec/SKILL.md` and run the six-stage implementation-specification pipeline.
Treat `$ARGUMENTS` as a repository-relative profile plus an optional interaction mode.

The profile and its README folder contract are mandatory. Stop as unavailable rather than inventing
a folder layout. `/impl-spec` is off-chain: it writes no Saga tick and performs no commit, push, PR,
issue, board, merge, or deployment mutation. The completed set must pass the buildability probe and
be promoted through the canonical artifact transaction before routing its manifest to `/plan`.

`$ARGUMENTS`
