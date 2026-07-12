---
date: 2026-07-12
topic: ship-ceremony-safety-pack
maturity: requirements
source: docs/ideation/2026-06-11-saga-vecu-port-spec-methodology.md (survivor #1 "Ship Ceremony Safety Pack" — merged from E1+E2+E3+E4)
---

# Ship Ceremony Safety Pack — Requirements

## Summary

Port the ship-ceremony safety pack from `infiquetra-claude-plugins` into the antigravity saga plugin: three new scripts (ceremony hazard detection, merge expectation watcher, ship undo) plus operator-confirmed gate logic wired into `ship_ceremony.py`'s `run()`. All four mechanisms are proven, tested, and platform-independent — the only adaptation is sidecar paths (`.claude/` → `.gemini/`) and restructuring transition runners to return rollback-manifest fields.

## Problem Frame

The antigravity `ship_ceremony.py` (590 lines) runs the ceremony transition sequence — commit, open_pr, request_review, merge, checkout_main, pull, branch_delete — with no look at the world beyond the saga ledger. `merge` executes `gh pr merge --squash` with no expectation baseline, no check-flip detection. `branch_delete` deletes the recorded branch checking only that the name isn't `main` — no stacked-PR topology detection, no merge-landed verification. There is no undo path. There is no operator-confirmed gate before the two `always_operator`-tier transitions (`merge`, `branch_delete`).

The claude side built four modules addressing these gaps (issue #346, commits 0.75.x–0.77.0), all dogfooded against real PRs. The claude side's own LEARNINGS journal records three separate ceremony-safety lessons from live incidents — including PR #562 (the feature's own merge) being refused because a names-only check baseline couldn't distinguish "was passing, regressed" from "was never passing, unchanged." The antigravity ceremony has none of these guards, and the transitions it gates are the most destructive in the lifecycle.

## Key Decisions

**Ship all four modules together as one coordinated port.** The four modules share the same source issue (#346), the same sidecar-path convention, and interlock at the `run()` level — hazard detection and merge-watcher validation run as preflights inside `run()`, ship_undo appends entries inside the transition runners. Porting them separately would require partial `run()` restructuring that doesn't make sense in isolation.

**Adapt fixtures to the antigravity repo's actual CI shape.** The antigravity repo's `ci.yml` has 5 always-run jobs (`Tests (Python 3.12)`, `Validate Plugins`, `Lint`, `Type Check`, `Security Scan`) plus 1 conditionally-skipped job (`Publish Plugin`, gated on `startsWith(github.ref, 'refs/tags/')`). This is the exact CI shape that caused the claude side's dogfooding bug — a conditionally-skipped workflow that is non-passing at both record and merge time must be baseline, not a flip. The ported test fixtures must mirror this real shape, including the `Publish Plugin` conditional skip, so the merge-watcher's `check_flipped` logic is tested against the same class of bug that bit PR #562.

**Restructure transition runners to return `dict[str, Any]`.** The antigravity transition runners all return `None`. The claude side restructured them to return rollback-manifest fields (branch, head_sha, pr_number, merge_sha, pre_merge_main_sha, remote_created). This restructuring is a prerequisite for ship_undo, not a separate concern — `ship_undo.append_entry` consumes these fields.

**Sidecar paths use `.gemini/saga/sagas/`.** The antigravity saga stores state at `.gemini/saga/` (confirmed: `saga.py` line 45, `STATE_DIR = Path(".gemini/saga")`). The merge-expectation sidecar goes to `.gemini/saga/sagas/<saga_id>/merge_expectation.json`; the rollback manifest goes to `.gemini/saga/sagas/<saga_id>/rollback_manifest.json`. Both are git-ignored, machine-local, written directly by their modules (never through `saga.py save`).

**Update `/work` SKILL.md and `pr-continuation-loop.md` with the safety contracts.** The antigravity versions of these files don't reference any ceremony safety contracts. The claude side's versions document the operator-confirmed gate, the merge-watcher expectation, the hazard acknowledgment, and the undo path. The port includes updating these docs to match.

## Actors

A1. **Operator** — the single human maintainer who runs the ceremony. Approves destructive transitions via `--operator-confirmed <transition>`, acknowledges hazards via `--acknowledge-hazard <hazard-id>`, triggers undo via `--undo`.

## Requirements

### Operator-Confirmed Gate

R1. A bare `run` reaching an `always_operator`-tier transition (`merge`, `branch_delete`) must exit non-zero, name the withheld transition, and leave the ceremony ledger unadvanced — no state changes until the operator passes `--operator-confirmed <transition>` naming that exact transition.

R2. A `--operator-confirmed` value that does not match the upcoming transition must be refused, regardless of the upcoming transition's tier — a mispredicted ledger position always surfaces.

R3. Reversible and additive transitions must behave identically to the current ceremony when `--operator-confirmed` is omitted — no new confirmation requirement for non-destructive steps.

### Ceremony Hazard Detection

R4. Before dispatching `branch_delete`, the ceremony must probe for stacked-PR topology — any open PR whose base is the branch about to be deleted — and refuse if found, with a remedy naming the stacked PR(s).

R5. A stacked-PR hazard must be acknowledgeable via `--acknowledge-hazard stacked_pr` (the operator may have already rebased the child PRs and wants to proceed).

R6. Before dispatching `branch_delete` after a `merge` transition, the ceremony must probe that the merge actually landed — the PR's merged state is non-null. A `merge_not_landed` hazard is not acknowledgeable; it resolves only by the merge actually landing.

R7. Hazard detection must not issue any `gh` call for reversible transitions — no added latency on steps that were never at risk.

### Merge Expectation Watcher

R8. At PR-open time (both the `start()` front-loaded path and the `_do_open_pr` transition), the ceremony must record a merge expectation: target head SHA, required-check names with their passing state, and the review decision.

R9. Before dispatching `merge`, the ceremony must validate the live PR state against the recorded expectation and refuse on any named divergence: `head_moved`, `check_flipped` (a recorded-passing check gone non-passing), `check_missing`, `review_regressed`, `pr_not_open`.

R10. A missing merge-expectation sidecar must be a named refusal with a remedy, never a silent pass — the merge does not proceed without a baseline.

R11. The expectation sidecar must record a name→passing map, not just a set of names, so `validate` can distinguish "was passing, regressed" from "was never passing, unchanged." A conditionally-skipped workflow that is non-passing at both record and merge time is baseline, not a flip.

R12. `record --force` is the only re-baseline path. A plain re-record over an existing sidecar must refuse. Divergence never auto-heals.

### Ship Undo

R13. Every successful ceremony transition must append a rollback-manifest entry: transition name, tier, branch, head SHA, PR number, merge SHA, pre-merge main SHA, remote-created flag, undone flag.

R14. `run --undo` must execute the reverse of recorded ceremonies newest-to-oldest: a landed merge is undone with `git revert <merge SHA>` on `main` (a new commit, never a rewrite); a deleted branch is resurrected from its recorded head SHA. If `git revert` produces conflicts (main diverged since the squash merge), the ceremony must abort the revert (`git revert --abort`), leave the manifest entry un-marked-undone, and surface a named `REVERT_CONFLICT` failure with a remedy pointing at manual resolution followed by re-running `--undo`. The repo must never be left in a conflicted state.

R15. Undo of `always_operator`-reversing entries (merge, branch_delete) must require `--operator-confirmed undo`. Undo of reversible-only entries runs on the bare call.

R16. Undo must be resumable: each manifest entry is marked `undone: true` only after its reverse mutation confirms, and the manifest is rewritten to disk after each step. A process killed mid-undo leaves already-reverted entries marked and everything else untouched.

R17. An empty or fully-undone manifest must be a no-op success, not an error.

R18. A recorded SHA that is unreachable (squash-discarded commits GC'd on origin, absent locally) must surface a named `SHA_UNREACHABLE` failure for that entry with a remedy, not fabricate state. The remaining older entries stay untouched.

R19. The reachability probe must be remote-aware: fetch origin before declaring a SHA unreachable, so a merge-landed-but-not-pulled squash SHA is not falsely refused.

### Tests and Documentation

R20. Port the three test files (`test_ceremony_hazards.py`, `test_merge_watcher.py`, `test_ship_undo.py`) and adapt their fixtures to the antigravity repo's CI shape.

R21. The test suite must include at least one fixture exercising a non-passing-but-steady-state check (the class of bug the claude side found through dogfooding), so the merge-watcher's `check_flipped` logic is tested against a real CI shape including skips.

R22. The `/work` SKILL.md and `pr-continuation-loop.md` must document the operator-confirmed gate, the merge-watcher expectation, the hazard acknowledgment, and the undo path — matching the claude side's contract documentation.

### Auto-Merge Hazard

R23. If `gh pr merge` is invoked with `--auto --delete-branch`, GitHub may delete the branch ahead of the ceremony's `branch_delete` step. The ceremony's `branch_delete` runner must detect an already-deleted branch (remote ref absent) and treat it as a no-op success, not a failure — the branch is gone, the desired end state is achieved, the manifest entry records `branch_already_deleted: true`. This must not require `--operator-confirmed` or `--acknowledge-hazard` since no destructive action is being taken by the ceremony itself.

## Acceptance Examples

**AE1.** **Trigger:** Operator runs `ship_ceremony.py run` with the next transition being `merge`. **Expected:** Exit non-zero with message: `transition 'merge' is tier='always_operator' and requires operator confirmation; re-run with --operator-confirmed merge`. Ledger unadvanced. **Covers R1.**

**AE2.** **Trigger:** Operator runs `run --operator-confirmed merge` but the next transition is `branch_delete`. **Expected:** Exit non-zero with message naming the mismatch. Ledger unadvanced. **Covers R2.**

**AE3.** **Trigger:** Operator runs `run` with next transition `branch_delete`, and an open child PR is based on the branch. **Expected:** Refuse with `stacked_pr` hazard, listing the child PR(s) and a remedy. **Covers R4.**

**AE4.** **Trigger:** Same as AE3, but operator passes `--acknowledge-hazard stacked_pr`. **Expected:** Proceed to `branch_delete` (hazard acknowledged). **Covers R5.**

**AE5.** **Trigger:** `merge` transition completed, then `run --undo --operator-confirmed undo`. **Expected:** `git revert <merge SHA>` on `main`, manifest entry marked `undone: true`. **Covers R14, R15.**

**AE6.** **Trigger:** `merge` transition completed, `run --undo` killed mid-revert. Re-run `run --undo`. **Expected:** Resumes from the un-reverted entry; already-reverted entries stay marked. **Covers R16.**

**AE7.** **Trigger:** Merge expectation recorded with check `Tests (Python 3.12)` as passing. At merge time, `Tests (Python 3.12)` is failing. **Expected:** Refuse with `check_flipped: ['Tests (Python 3.12)']`. **Covers R9, R11.**

**AE8.** **Trigger:** Merge expectation recorded with a conditionally-skipped check `Publish Plugin` as non-passing. At merge time, `Publish Plugin` is still non-passing. **Expected:** No `check_flipped` refusal — the check is baseline, not a flip. **Covers R11.**

**AE9.** **Trigger:** `run --undo` and the recorded merge SHA is not in the local object store. **Expected:** `git fetch origin`, re-probe. If found on origin, proceed. If still not found, `SHA_UNREACHABLE` with remedy. **Covers R18, R19.**

## Scope Boundaries

**In scope:**
- Three new scripts: `ceremony_hazards.py` (library-only, imported by `ship_ceremony.py` — no CLI), `merge_watcher.py` (CLI with `record`/`validate`/`watch` subcommands), `ship_undo.py` (CLI with `undo`/`show` subcommands)
- `ship_ceremony.py` restructuring: `run()` gains `operator_confirmed`, `acknowledge_hazard`, `undo` parameters; transition runners return `dict[str, Any]`; preflight wiring; operator-confirmed gate logic (the fourth safety module, not a separate script)
- `start()` and `_do_open_pr()` gain `merge_watcher.record()` and `ship_undo.append_entry()` calls
- Three test files ported and fixture-adapted, placed at `plugins/saga/tests/` (matching existing saga test placement)
- `/work` SKILL.md and `pr-continuation-loop.md` updated with safety contracts
- `_build_parser()` gains `--operator-confirmed`, `--acknowledge-hazard`, `--undo` flags

**Out of scope:**
- External engine dispatch, subagent routing, second-opinion triggers (separate workstream)
- Engine registry, chaperone economics, bridge signatures (not applicable to antigravity's same-process model)
- Redis-channel plugin (antigravity has no Claude Code session to bridge)
- Saga spec changes (ceremony fields unchanged — safety contracts live in SKILL docs, not the spec)
- The `/engines` command (no engine subsystem in antigravity)

## Dependencies / Assumptions

- The antigravity `ship_ceremony.py` is structurally close enough to the claude version at the last sync point (099ec4c) that the diff is additive — the claude side added imports, new error classes, preflight calls, and return-value restructuring, but did not fundamentally change the transition table or saga resolution logic. **Verified:** both share the same TRANSITIONS tuple, CeremonyTier class, resolve_saga logic, and transition runner signatures (modulo the `None` → `dict` return change).

- The antigravity repo's `ci.yml` has 5 always-run jobs plus 1 conditionally-skipped `Publish Plugin` job. The test fixtures must cover the conditionally-skipped class of bug (R21) so the merge-watcher's `check_flipped` logic doesn't falsely block on a non-passing-but-steady-state check.

- The `saga.py save --ceremony-transition --ceremony-tier` CLI contract is unchanged — the safety modules write sidecars directly, not through `saga.py save`.

- The antigravity saga's `run_ledger.py` already exists but does not need new fact types for this port — the rollback manifest and merge-expectation sidecar are separate stores, not run-fact ledger entries.

## Sources / Research

- `infiquetra-claude-plugins` saga CHANGELOG v0.75.17–v0.77.0 — the four safety modules' release history
- `infiquetra-claude-plugins` `plugins/saga/scripts/ship_ceremony.py` (842 lines) — the target state with all four modules wired in
- `infiquetra-claude-plugins` `plugins/saga/scripts/ceremony_hazards.py` (246 lines) — hazard registry + detect()
- `infiquetra-claude-plugins` `plugins/saga/scripts/merge_watcher.py` (553 lines) — record/validate/watch
- `infiquetra-claude-plugins` `plugins/saga/scripts/ship_undo.py` (585 lines) — rollback manifest + undo engine
- `infiquetra-claude-plugins` `tests/test_ceremony_hazards.py`, `tests/test_merge_watcher.py`, `tests/test_ship_undo.py` — test suites to port
- `infiquetra-claude-plugins` `docs/engineering-journal/LEARNINGS.md` — three ceremony-safety lessons from live dogfooding (check-flip baseline, local-reachability blind spot, auto-merge-delete-branch reorder)
- `infiquetra-claude-plugins` `plugins/saga/skills/work/SKILL.md` and `references/pr-continuation-loop.md` — safety contract documentation to mirror
- `infiquetra-antigravity-plugins` `plugins/saga/scripts/ship_ceremony.py` (590 lines) — current state, confirmed absent of all four safety modules
- `infiquetra-antigravity-plugins` `plugins/saga/scripts/saga.py` line 45 — `STATE_DIR = Path(".gemini/saga")` confirms sidecar path convention
- `infiquetra-antigravity-plugins` `.github/workflows/ci.yml` — 5 always-run jobs (Tests, Validate, Lint, Type Check, Security) + 1 conditionally-skipped `Publish Plugin` (`if: startsWith(github.ref, 'refs/tags/')`)
- `infiquetra-antigravity-plugins` `ANTIGRAVITY.md` — plugin layout conventions (flat `plugin.json`, `src/` for scripts, `.gemini/` paths)