# Claude Plugins Porting Plan Implementation Code Review (Round 2)

Round 2 re-review of the same working-tree port: all 17 findings from the blocked Round 1 verdict are resolved, the full suite and doctor pass, the ledger supersede and conformance digest chain verify clean, and no P0/P1 remains. Five new low-severity findings (1 P2, 4 P3) in the fix-round delta are reported for the work-thread, not blocking.

## Review Result

| Field | Value |
|---|---|
| Target | Working-tree port against `docs/plans/2026-08-13-claude-plugins-porting-plan.md` |
| Reviewed revision | working tree over `d450d509` (uncommitted; `HEAD == origin/main`) |
| Prior review | Round 1 (blocked, 17 findings) in this same file; all resolved |
| Linked saga | `task-claude-plugins-porting-p1-p2` |
| Backend | inline |
| Blocked | no — zero P0/P1 |
| Unresolved P0–P3 findings | 5 (1 P2, 4 P3) |
| Suppressed | 1 (below anchor 75) |

## Built-vs-Planned Audit

| Unit | State | Evidence |
|---|---|---|
| U1 | DONE | execution-class coverage complete (work-high/medium, test-medium, monitor-low, scan-low); fleet-core suite 214 passed |
| U2 | DONE | shlex tokenizer + wrapper/redirect/continuation/foreach hardening (29 hook tests); `spec_table.py` native `--outcome` renderer wired into the `outcome` skill (outcome/SKILL.md:88); plan lists gate-manifest + outcome SKILL |
| U3 | DONE | severity axis + `n // 2 + 1` floor with behavioral under-strength and malformed-verdict tests; plan names the shipped test file |
| U4 | DONE | wave-conflict halt + concurrent-writer table section tested (test_spec_table.py:222,230) |
| U5 | DONE | validate-spec problems + CLI entrypoint tests; skill-local suite 43 passed |
| U6 | DONE | committed adapter keeps 45s timeout and 16,384-char limits; 43 tests pass |
| U7 | DONE | deletions, guard at the plugin path with orphan fixture coverage, ledger supersede recorded (49 approved / 3 superseded census; both validate modes pass), host-contract selector closed |
| U8 | DONE | full suite 1762 passed / 1 skipped (intentional); doctor `status: ok`; conformance verify 21 passed |

## Scope Check

CLEAN.

- Intent: implement the eight plan units.
- Delivered: all eight, and every extra file (gate-manifest, output_attestation, cost_weights rows) is now named in the plan's file lists. The plan itself evolved uncommitted (R1/KTD1 Gemini catalog, R6 native-outcome adaptation, U3 test naming) to ratify the implementation — the plan and code must land in the same commit, and the plan's committed version should not be treated as the review target after that point.

## Findings

### P1

None.

### P2

| # | File | Issue | Reviewer | Confidence | Route |
|---|---|---|---|---|---|
| 18 | `plugins/saga/hooks/pre_push_gate_hook.py:479` | `git diff --check d450d509` reports "new blank line at EOF" (exit 2) — in-delta whitespace error that can break strict patch application. | testing/maintainability | 100 | manual |

### P3

| # | File | Issue | Reviewer | Confidence | Route |
|---|---|---|---|---|---|
| 19 | `plugins/saga/hooks/pre_push_gate_hook.py:173-174` | The wrapper skip only fires when the token directly after the wrapper is `git`, so `sudo -u root git push`, `sudo -H git push`, `sudo env -i git push`, and `command env --chdir=/repo git push` all bypass the gate (empirically: `_push_target` → `(False, None)`). | correctness/security | 100 | advisory |
| 20 | `plugins/saga/hooks/pre_push_gate_hook.py:269` | `_nested_foreach_pushes` hard-indexes `invocation[1]`/`[2]`, so `git -C /repo submodule foreach git push` bypasses the gate (empirically verified). | correctness/security | 100 | advisory |
| 21 | `plugins/saga/scripts/spec_table.py:395-397` | Outcome-mode CLI error paths (missing/malformed outcome file, invalid outcome spec) are untested; only spec-mode CLI errors and the outcome happy path are covered. | testing | 75 | advisory |
| 22 | `plugins/saga/hooks/pre_push_gate_hook.py:78` | `_join_continuations` treats 3+ trailing backslashes as literal (diverges from shell semantics); only the single-backslash case is tested. | testing | 75 | advisory |

## Verification

- Full suite: **1762 passed, 1 skipped** (66s).
- Doctor (`validate_plugins.py --strict-install`): `status: ok` (fleet-core inert-surface warning is advisory; its manifest description declares the library-only intent).
- Ledger: `validate` and `validate --require-migrated` both pass; census 49 approved / 3 superseded / 19 blocked / 8 metadata-only / 1 rejected.
- Conformance: `saga_conformance.py verify --fixture reference-lifecycle` → 21 passed; fixture → manifest binding → live-canary digest chain all recomputed and matching.
- team-scaffold skill-local suite: 43 passed.

## Residual Risk

The two P3 gate-bypass shapes (#19, #20) are the same fail-open-on-exotic-composition class as Round 1's #5 — reported, not blocking; the hook's own docstring declares false negatives strictly worse than over-firing, so they are worth a follow-up hardening pass. Findings #18–#22 are handed back to the work-thread as residual cleanup.

## Review Artifact

`docs/code-reviews/2026-08-13-claude-plugins-porting-plan-code-review.md` (Round 2 supersedes the Round 1 blocked verdict recorded in this file; evidence ledger unavailable — `evidence_ledger.py` missing from `plugins/saga/scripts/`).

## Resolution note (post-review)

Findings #18–#22 were fixed in the working tree after this review:

- #18: trailing blank line removed; `git diff --check d450d509` clean.
- #19: `_skip_wrapper_and_env` walks wrapper options (`sudo -u root`, `sudo -H`, `sudo env -i`, `command env --chdir=`, stacked `sudo command`), with per-wrapper value-option tables so `command -p` stays a flag; false-positive cases asserted.
- #20: `_nested_foreach_pushes` locates the subcommand via `_git_subcommand`; `git -C /repo submodule foreach git push` gated.
- #21: outcome-mode CLI error tests added; `_load_outcome` now runs `OutcomeSpec.validate()`, so an invalid outcome spec exits 2 instead of rendering an empty-id table.
- #22: `_join_continuations` counts trailing backslashes (odd = continuation, even = literal); odd/even cases asserted.

Verification after the fixes: full suite 1769 passed / 1 skipped, doctor `status: ok`, `git diff --check` clean, hook suite 33 passed, spec_table suite 23 passed.
