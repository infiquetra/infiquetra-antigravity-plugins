---
date: 2026-07-12
target: docs/brainstorms/2026-07-12-ship-ceremony-safety-pack-requirements.md
classification: requirements
reviewed_revision: post-brainstorm (151 lines → 151 lines, 3 in-place edits)
maturity: plan-reviewed
---

# Doc Review — Ship Ceremony Safety Pack Requirements

## Gate status

**Advisory only — not mechanically verified.** This was a synchronous single-model review under the R13 capacity-exhaustion fallback. The named gate checks (`tier-compliance`, `panel-independence`, `receipt-presence`) require `scripts/saga_gate.py` reading `kanban.db`/`state.db` receipts; that script does not exist in this environment, no independent panel was dispatched, and no per-dimension receipts were produced. The verdict below is advisory, not gate-verified. An operator override with recorded rationale is required to proceed to `/work` on this advisory verdict.

## Findings

| # | Priority | Finding | Evidence | Status |
|---|---|---|---|---|
| F1 | P1 | R14 lacked revert-conflict handling — `git revert --no-edit` on a squash SHA produces conflicts when main diverged since merge, leaving the repo in a conflicted state and breaking R16 resumability | claude `ship_undo.py:366` runs `git revert --no-edit` with no conflict detection | **Fixed in-place** (R14 now includes `REVERT_CONFLICT` abort + remedy) |
| F2 | P2 | CI shape grounding was wrong — doc claimed "single job, no conditionally-skipped workflows"; actual `ci.yml` has 5 always-run jobs + 1 conditionally-skipped `Publish Plugin` (`if: startsWith(github.ref, 'refs/tags/')`) | `.github/workflows/ci.yml` full read | **Fixed in-place** (Key Decision 2 corrected) |
| F3 | P2 | Scope miscounted "four new scripts" — `ceremony_hazards.py` is library-only (no CLI, no `_build_parser`, imported by `ship_ceremony.py`); operator-confirmed gate is `run()` logic, not a standalone script | claude `ceremony_hazards.py` has no argparse; claude `ship_ceremony.py:500-540` shows gate logic inline in `run()` | **Fixed in-place** (Scope Boundaries: 3 scripts + gate logic) |
| F4 | P2 | Test placement unspecified — existing saga tests live at `plugins/saga/tests/`, not repo-root `tests/` | `plugins/saga/tests/` contains 19 existing test files | **Fixed in-place** (Scope: tests at `plugins/saga/tests/`) |
| F5 | P3 | Summary said "four safety modules" but 3 are scripts + 1 is inline logic — minor framing mismatch | Same as F3 | **Fixed in-place** (Summary reworded) |
| F6 | P2 | The claude LEARNINGS journal records three live-incident lessons; the doc's Problem Frame mentions all three but only two are traced to requirements: check-flip baseline → R11/R21, local-reachability blind spot → R18/R19. The third lesson (auto-merge-delete-branch reorder) is not explicitly handled by any requirement. | claude `docs/engineering-journal/LEARNINGS.md` | **Fixed in-place** (R23 added — `branch_delete` treats already-deleted branch as no-op success) |

## Applied safe fixes

1. **R14** (line 72) — added `REVERT_CONFLICT` abort + remedy language. Sanctioned: R16 resumability already implies clean-revert success; the conflict surface is the implied gap.
2. **Key Decision 2** (line 24) — corrected CI shape from "single job, no conditional skips" to "5 always-run + 1 conditional `Publish Plugin`". Sanctioned: the full `ci.yml` is local evidence.
3. **Scope Boundaries + Summary** (lines 12, 115-120) — corrected "four new scripts" to "three new scripts + operator-confirmed gate logic in `run()`"; added test placement at `plugins/saga/tests/`. Sanctioned: claude source confirms `ceremony_hazards.py` has no CLI.

## Verdict

**CONDITIONAL PASS — advisory, not gate-verified.**

No P0. No unresolved P1. No unresolved findings — all 6 fixed in-place (F1: R14 revert-conflict, F2: CI shape, F3: scope/script count, F4: test placement, F5: summary framing, F6: R23 auto-merge hazard).

The conditional remains because the gate was not mechanically verified: `saga_gate.py` is absent, no independent panel was dispatched, no per-dimension receipts exist. An operator override with recorded rationale is required to proceed to `/work` on this advisory verdict.

## Next steps

A) `/plan` — create a structured implementation plan from this requirements doc (recommended)
B) `/work` — proceed directly to execution with operator override
C) Say it your own way