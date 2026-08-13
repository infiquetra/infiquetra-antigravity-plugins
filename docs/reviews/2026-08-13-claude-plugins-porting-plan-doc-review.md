# Claude-to-Antigravity Plugins Porting Plan Documentation Review

Third review round: the previous "no findings remain" verdict was wrong against Antigravity `origin/main`. The plan is now rebound to current remotes, the Gemini registry is protected, and the already-landed Hermes work is a non-regression unit.

## Review Result

The plan can drive implementation after the in-place fixes in this round.

| Field | Value |
|---|---|
| Target | `docs/plans/2026-08-13-claude-plugins-porting-plan.md` |
| Reviewed revision | working tree (plan is untracked) |
| Classification | plan (`docs/plans/`, Implementation Units, KTDs, origin) |
| Rubric phase | none — engine only has idea/issue/spec phases |
| External engine | operator chose none |
| Linked issue | none |
| Blocked | no |
| Override | none |
| Review artifact | `docs/reviews/2026-08-13-claude-plugins-porting-plan-doc-review.md` |

## Applied Fixes

Every finding below was edited into the plan from local repository or upstream evidence. No product decisions were invented.

| ID | P | Status | Fix | Evidence |
|---|---|---|---|---|
| D1 | P0 | fixed | U1 tests now use `review-max` / `review-high` / `work-high` | Claude `origin/main` `models.json` `execution_classes` keys |
| D2 | P0 | fixed | R1/KTD1 keep Gemini `models`/`efforts`; portable v2 keys only | AG `models.json` is `gemini-3.1-pro` / `gemini-3.5-flash`; Claude live models are `fable`/`opus`/`sonnet`/`haiku` |
| D3 | P0 | fixed | U6 is a non-regression against committed `origin/main`; untracked tree forbidden | AG `origin/main` `SUBPROCESS_TIMEOUT_SECONDS = 45`; WT untracked copy uses `timeout=10` |
| D4 | P1 | fixed | Origin pin is Claude `origin/main` `ff236284`, not `541b36b9` | `541b36b9` is `feat(orchestrate): U5` and is not an ancestor of Claude `origin/main` |
| D5 | P1 | fixed | U3 depends on U4 (shared `execution_spec.py`, upstream order) | `b3c13006` precedes `f0ca9a47` |
| D6 | P1 | fixed | 45s is the adapter bound; 30s is the producer network bound | `83a1f5a` and `test_adapter_timeout_does_not_preempt_the_producer_transport` |
| D7 | P1 | fixed | U8 and Verification both use `--strict-install` | `scripts/validate_plugins.py` defines that flag |
| D8 | P1 | fixed | Every unit now maps explicit R-IDs | Plan-sections per-unit `Requirements` field |
| D9 | P1 | fixed | U7 updates the saga-reliability ledger | Ledger `decision.state: approved-survivor` for both lease candidates |
| D10 | P1 | fixed | U5 tests stay in `skills/team-scaffold/scripts/tests/` | That directory exists upstream; `plugins/home-lab-ops/tests/` is absent on AG `origin/main` |
| D11 | P2 | fixed | Units gained Approach, Patterns, Verification | Plan-sections required fields |
| D12 | P2 | fixed | Blank lines between `**label:**` fields | `saga/references/formatting-style.md` rule 7 |
| D13 | P2 | fixed | Dropped the absolute `source_repo` path | Plan-sections: repo-relative paths only |
| D14 | P2 | fixed | R2 names `grok`/`muse` `max→xhigh` as well as `agy` | Claude `tier_resolver.py` `_EFFORT_COLLAPSE` |
| D15 | P2 | fixed | Hermes campaign path is `docs/ports/2026-08-01-hermes-profile-evolution/` | Committed on AG `origin/main` |
| D16 | P3 | fixed | Frontmatter `review_status` reflects this round | This artifact |
| D17 | P3 | fixed | Requirement IDs use `R1.` not bold labels | Plan-sections R-ID spec |

## Remaining Findings

| ID | P | Status | Title |
|---|---|---|---|
| — | — | — | No P0, P1, P2, or P3 findings remain |

## Rubric Review

The rubric engine at the installed saga plugin accepts only `idea`, `issue`, and `spec`. This artifact is a plan, so no formal rubric run applies. The readiness-skeptic pass stands in for it.

## Readiness Summary

The document can drive `/work` without inventing the load-bearing choices.

An implementer who follows it literally will start from Antigravity `origin/main`, keep Gemini models, sequence U2 → U4 → U3, treat Hermes as already landed, and record the lease-broker ledger supersede in U7.

## Residual Risk

Claude or Antigravity `origin/main` may move before implementation; re-pin the Sources table and the Implementation Baseline if that happens.

The working tree that hosted this review is still twelve commits behind Antigravity `origin/main` and still contains the untracked Hermes copy. That is workspace state, not a remaining plan defect. Implementation must not use that copy.
