---
title: Doc Review - Port Claude July Updates Plan
type: review
date: 2026-07-08
target: docs/plans/2026-07-08-port-claude-july-updates-plan.md
revision: working tree
status: unblocked-after-fixes
plan_ref: 2026-07-08-port-claude-july-updates-plan
---

# Review: Port Claude July Updates Plan

## Applied Fixes

Verdict: the plan was rewritten into an executable, evidence-grounded handoff.

- Added explicit source repo, source range `3987510..099ec4c`, and target baseline `99df140`.
- Restored mandatory port classifications for direct ports, Antigravity adaptations, metadata-only changes, and blocked/deferred surfaces.
- Defined `plugins/fleet-core` as the Antigravity utility-plugin target for shared fleet primitives.
- Replaced the vague `EFFORT_RIDER` claim with a concrete Gemini `thinking_level` adapter and `xhigh` handling rule.
- Reworked verifier hardening around Antigravity-owned response validation instead of assuming native StructuredOutput enforcement.
- Replaced stale top-level `marketplace.json` work with root `plugin.json`, `scripts/validate_plugins.py`, and install-surface validation.
- Added missing source-delta surfaces, including completeness/empty-delivery gates, provenance/manifest/spore/status files, hook gating, and deferred bridge surfaces.
- Replaced impossible full-repo Bandit pass expectations with scoped checks and a known-baseline note.

## Readiness Summary

Verdict: unblocked for implementation after the fixes in this review.

The reviewed plan can now drive `/work` without requiring the implementer to invent the source range, the missing `fleet-core` target, the model-effort mapping, verifier enforcement semantics, release validation surface, or deferred Claude-only surfaces. Implementation must still regenerate the source inventory at start and re-review if the source range has moved.

## Remaining Findings

Verdict: no P0 or P1 findings remain after the applied fixes.

| Priority | Finding | Status |
| --- | --- | --- |
| P1 | Source range and target baseline were not reproducible. | Resolved by adding `3987510..099ec4c` and `99df140`. |
| P1 | Required direct/adapt/metadata/deferred classification was missing. | Resolved by adding the delta inventory and classification table. |
| P1 | `fleet-core` target did not exist in Antigravity. | Resolved by choosing an Antigravity utility plugin target. |
| P1 | Gemini effort mapping was underspecified and overstated. | Resolved by defining `thinking_level` translation and `xhigh` clamp semantics. |
| P1 | Verifier hardening assumed StructuredOutput support without proof. | Resolved by requiring Antigravity-owned verdict validation. |
| P1 | Verification gates were not executable as written. | Resolved by replacing impossible gates with scoped and baseline-aware gates. |
| P2 | Release surface work targeted stale marketplace behavior. | Resolved by using root `plugin.json` and `scripts/validate_plugins.py`. |
| P2 | Source-delta surfaces were missing from the plan. | Resolved by adding manifest/provenance/spore/status/hook/completeness and deferred bridge handling. |

## Review Artifact Path

Verdict: this file is the durable review artifact.

`docs/reviews/2026-07-08-port-claude-july-updates-plan-review.md`

## Residual Risk

Verdict: remaining risk is execution-time verification, not plan ambiguity.

Gemini model behavior and Antigravity subagent enforcement are runtime surfaces, so the implementation must prove actual payloads and verifier isolation with tests or recorded evidence. The target worktree also has unrelated dirty state and untracked implementation-looking files; implementation should avoid committing those unless a later unit explicitly claims them.
