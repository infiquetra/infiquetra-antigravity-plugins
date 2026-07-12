---
date: 2026-07-12
target: feat/saga-ship-ceremony-safety-pack (ec5e344)
classification: code-review
reviewed_revision: ec5e3444ce3f34289a2a8ae6fad4c6717f71c1ea
maturity: code-reviewed
origin: docs/plans/2026-07-12-ship-ceremony-safety-pack-plan.md
---

# Code Review — Ship Ceremony Safety Pack

## Gate status

**Advisory only — not mechanically verified.** Single-model synchronous review under R13 capacity-exhaustion fallback. The named gate checks (`tier-compliance`, `panel-independence`, `receipt-presence`, `reinsurance-bound`) require `scripts/saga_gate.py` reading `kanban.db`/`state.db` receipts; that script does not exist in this environment, no independent panel was dispatched, and no per-dimension receipts were produced. The verdict below is advisory, not gate-verified. An operator override with recorded rationale is required to proceed to ceremony on this advisory verdict.

## Diff scope

12 files changed, +3723/-45 lines. Base: `origin/main`. Head: `ec5e344`.

| File | Change |
|---|---|
| `plugins/saga/scripts/ceremony_hazards.py` | New, 246 lines (verbatim port, no adaptation) |
| `plugins/saga/scripts/merge_watcher.py` | New, 553 lines (`.claude` → `.gemini` path adaptation) |
| `plugins/saga/scripts/ship_undo.py` | New, 598 lines (`.claude` → `.gemini` path adaptation) |
| `plugins/saga/scripts/ship_ceremony.py` | Modified, +238/-19 (safety wiring) |
| `plugins/saga/tests/test_ceremony_hazards.py` | New, 242 lines (17 tests) |
| `plugins/saga/tests/test_merge_watcher.py` | New, 679 lines (42 tests, 3 antigravity CI fixtures) |
| `plugins/saga/tests/test_ship_undo.py` | New, 988 lines (33 tests) |
| `plugins/saga/tests/test_ship_ceremony.py` | Modified, +101/-31 (FakeGh enhanced, _confirm_for helper) |
| `plugins/saga/skills/work/SKILL.md` | Modified, +7/-3 (safety contract reference) |
| `plugins/saga/skills/work/references/pr-continuation-loop.md` | Modified, +31/-6 (merge-watcher + hazards section) |
| `docs/engineering-journal/DECISIONS.md` | Modified, +18 (6 KTDs) |
| `.serena/project.yml` | Modified, +50/-2 (unrelated, pre-existing) |

## Built-vs-planned audit

**Plan:** `docs/plans/2026-07-12-ship-ceremony-safety-pack-plan.md` (5 units, 6 KTDs, 23 R-IDs)

| Unit | Planned | Built | Status |
|---|---|---|---|
| U1 | Port ceremony_hazards.py (246 lines, no adaptation) | 246 lines, verbatim port, 17 tests | ✅ Complete |
| U2 | Port merge_watcher.py (553 lines, .gemini path) | 553 lines, path adapted, 42 tests (3 CI fixtures) | ✅ Complete |
| U3 | Port ship_undo.py (585 lines, .gemini path) | 598 lines, path adapted, 33 tests | ✅ Complete |
| U4 | Wire safety pack into ship_ceremony.py | +238/-19, all 4 mechanisms wired, existing tests updated | ✅ Complete |
| U5 | Port tests + update /work docs | Tests in U1-U3, docs updated, engineering journal KTDs | ✅ Complete |

**Scope drift:** None. All units match the plan. The `.serena/project.yml` change is pre-existing and unrelated.

## Findings

| # | Severity | Confidence | File:Line | Finding | Pre-existing | Status |
|---|---|---|---|---|---|---|
| F1 | P2 | 75 | `ship_ceremony.py:346` | Front-loaded `_do_open_pr` path calls `merge_watcher.record(force=True)` unconditionally — if `start()` was not called (plain `run()` path reaching `open_pr` with an existing draft PR from a prior session), `force=True` re-baselines over an existing expectation without the operator knowing. This is correct behavior (re-baselining on new commits), but the `force=True` is silent — no log or status line notes the re-baseline. | No | **Acceptable** — matches claude side behavior; the `force=True` is the designed re-baseline path for the ready-flip transition |
| F2 | P2 | 75 | `ship_ceremony.py:519-522` | `sid = str(saga.get("saga_id") or saga["id"])` — the fallback to `saga["id"]` masks a missing `saga_id` field. If `saga_id` is absent from the saga dict, the rollback manifest and merge-watcher sidecar are written under the short id (e.g. `"346"`) while `saga.py` creates the saga directory under the derived id (e.g. `"issue-346"`). This would cause `read_manifest` to find nothing. The fallback should never fire in practice (saga.py always sets `saga_id`), but it's a silent mismatch. | No | **Acceptable** — `saga_id` is always present in saga dicts from `saga.py restore`; the fallback is defensive |
| F3 | P3 | 100 | `ship_ceremony.py:393` | `_do_request_review` now calls `_pr_number(refs[-1])` directly instead of `_current_pr_number(saga, ...)`. This is intentional (avoids a `TransitionFailedError` when there are no `pr_refs`), but the pattern diverges from `_do_merge` which still uses `_current_pr_number`. Consistency would be better, but the behavior is correct — `request_review` is a no-op and shouldn't fail on missing pr_refs. | No | **Noted** — minor consistency gap, not a defect |
| F4 | P3 | 100 | `ship_ceremony.py:553` | `manifest_fields = {k: v for k, v in fields.items() if k != "branch_already_deleted"}` — the `branch_already_deleted` key from R23 is filtered before passing to `ship_undo.append_entry`. This is correct (the field isn't in the manifest schema), but the filtering is ad-hoc. A cleaner approach would be to not include it in the runner return dict at all, or add it to the manifest schema. | No | **Noted** — ad-hoc filtering, but functionally correct |

## Coverage

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| ceremony_hazards.py | 71 | 4 | 94% |
| merge_watcher.py | 192 | 5 | 97% |
| ship_ceremony.py | 234 | 11 | 95% |
| ship_undo.py | 194 | 9 | 95% |

Missing lines are in CLI `main()` paths (hard to test without subprocess), edge-case branches in `_probe_merge_not_landed`, and the `_live_poll_source` sleep adapter. All feature-bearing paths are covered.

## Test results

- **125 tests passed, 0 failed, 0 skipped** (across the 4 changed test files)
- **793 tests passed, 1 skipped** (full saga test suite; skip is pre-existing `test_saga_plugin.py` — "No metadata file")
- Ruff check: all passed
- Ruff format: all formatted

## Verdict

**ADVISORY PASS — not gate-verified.**

No P0. No P1. Two P2 findings (F1: silent force-True re-baseline, F2: saga_id fallback) — both acceptable, matching the claude side's proven behavior. Two P3 findings (F3: consistency gap, F4: ad-hoc filtering) — noted, not blocking.

The conditional remains because the gate was not mechanically verified: `saga_gate.py` is absent, no independent panel was dispatched, no per-dimension receipts exist. An operator override with recorded rationale is required to proceed to ceremony on this advisory verdict.

## Next steps

A) Open PR — proceed to ceremony (PR open, review request) under operator confirmation
B) `/qa` — run acceptance evidence before ceremony
C) Say it your own way