---
title: Ship Ceremony Safety Pack — Implementation Plan
type: feat
status: active
date: 2026-07-12
origin: docs/brainstorms/2026-07-12-ship-ceremony-safety-pack-requirements.md
maturity: plan
---

# Ship Ceremony Safety Pack — Implementation Plan

## Summary

Port three safety scripts (ceremony_hazards.py, merge_watcher.py, ship_undo.py) plus operator-confirmed gate logic into the antigravity saga plugin's ship_ceremony.py. Adapt sidecar paths from `.claude/` to `.gemini/`, restructure transition runners to return `dict[str, Any]`, strip the teardown/resource-manifest wiring that doesn't exist in antigravity, port and adapt three test suites, and update the /work skill docs.

## Problem Frame

The antigravity `ship_ceremony.py` (590 lines) runs the ceremony transition sequence with no preflight safety checks, no merge-expectation baseline, no undo path, and no operator-confirmed gate before destructive transitions. The claude side built and dogfooded all four mechanisms (issue #346). The requirements doc (23 R-IDs, 9 acceptance examples) is reviewed and all findings resolved. This plan turns those requirements into executable units.

## Requirements

Carried forward from the requirements doc. R-IDs are stable and not renumbered here.

**Operator-Confirmed Gate:** R1, R2, R3

**Ceremony Hazard Detection:** R4, R5, R6, R7

**Merge Expectation Watcher:** R8, R9, R10, R11, R12

**Ship Undo:** R13, R14, R15, R16, R17, R18, R19

**Tests and Documentation:** R20, R21, R22

**Auto-Merge Hazard:** R23

## Key Technical Decisions

**KTD1 — Strip teardown wiring from ported transition runners.** The claude `ship_ceremony.py` weaves `ship_teardown.register()`/`_close_if_registered()` calls through `_do_commit`, `_do_open_pr`, `_do_merge`, `_do_branch_delete`, and `start()`. Those modules (`ship_teardown.py` 954 lines, `ship_receipt.py` 291 lines) are issue #347, not #346, and are out of scope per the requirements doc. The ported transition runners must strip all `_register_branch`, `_register_pr`, and `_close_if_registered` calls. The rollback-manifest fields these runners return (branch, head_sha, pr_number, merge_sha, pre_merge_main_sha, remote_created) are independent of teardown and stay. Rejected alternative: port teardown too — rejected because it doubles the scope and the requirements explicitly excluded it.

**KTD2 — Import safety modules via `sys.path.insert(0, str(SCRIPT_DIR))`, not relative imports.** The antigravity scripts directory uses sibling-file imports (`importlib.util.spec_from_file_location` in tests, `sys.path.insert` in modules). The claude side imports the safety modules with `sys.path.insert(0, str(SCRIPT_DIR))` followed by `import ceremony_hazards` / `import merge_watcher` / `import ship_undo` with `# noqa: E402`. This pattern already exists in the claude version and matches the antigravity test-loading convention. Rejected alternative: restructure as a package — rejected because the existing scripts are standalone files, not a package, and restructuring is out of scope.

**KTD3 — `ceremony_hazards.py` has no `STATE_DIR` — no path adaptation needed.** Unlike `merge_watcher.py` and `ship_undo.py`, which both hardcode `STATE_DIR = Path(".claude/saga")`, `ceremony_hazards.py` is a pure probe layer with no sidecar storage. It receives `repo_root` and `saga_id` from the caller. The only path adaptation is in `merge_watcher.py` and `ship_undo.py`.

**KTD4 — Port `merge_watcher.py` and `ship_undo.py` with `.gemini/saga` state paths.** Both modules hardcode `STATE_DIR = Path(".claude/saga")` at module level. The antigravity adaptation changes these to `Path(".gemini/saga")` to match `saga.py:45`. The antigravity `test_state_paths.py` already tests `SAGA.STATE_DIR == Path(".gemini/saga")` — the ported modules should pass a similar path assertion. Rejected alternative: import `STATE_DIR` from `saga.py` — rejected because the claude modules explicitly document "Depends on: nothing" (no import of saga.py) to keep the import graph one-directional; matching that discipline avoids a circular import risk.

**KTD5 — Port the `run()` function's safety wiring from claude, not the teardown transition.** The claude `run()` function has safety preflights (operator-confirmed gate, hazard detection, merge-watcher validate) wired before transition dispatch. This wiring is self-contained in `run()` and doesn't depend on teardown. The `teardown` transition and the `_teardown_ceremony_summary`/`_teardown_attempt_closes` functions are stripped. The `TRANSITIONS` tuple stays at 7 entries (no `teardown`).

**KTD6 — `R23 (already-deleted branch)` is a new adaptation, not a claude port.** The claude `_do_branch_delete` doesn't handle an already-deleted branch because the claude side's hazard detection (R4/R6) prevents the scenario. But `gh pr merge --auto --delete-branch` can race ahead. The antigravity port adds a `git ls-remote --exit-code --heads origin <branch>` check before the delete; if the remote ref is absent, the runner records `branch_already_deleted: true` and returns success without attempting deletion.

## Implementation Units

### U1. Port ceremony_hazards.py (library-only, no CLI)

**Goal:** Create the hazard-detection probe module that `run()` consults before `branch_delete` and `merge` transitions.

**Requirements:** R4, R5, R6, R7

**Dependencies:** none (first unit)

**Files:**
- Create: `plugins/saga/scripts/ceremony_hazards.py`
- Test: `plugins/saga/tests/test_ceremony_hazards.py`

**Approach:** Port the claude `ceremony_hazards.py` (246 lines) verbatim with zero path adaptation (KTD3 — no sidecar storage). The module is a pure probe layer: `detect()` takes a saga, upcoming transition, repo_root, and runner; returns a list of `HazardFinding` dataclass instances. Two hazard types: `stacked_pr` (acknowledgeable) and `merge_not_landed` (non-acknowledgeable). Reversible transitions return `[]` without any `gh` call (R7). Probe failures raise `HazardProbeError` — never silently return empty (fail-loud contract).

**Patterns to follow:** `plugins/saga/scripts/ship_ceremony.py:29-32` (house testability pattern — runner callable, defaulted at call time).

**Test scenarios:**
- **Happy path — clean topology:** `branch_delete` with no stacked PRs and merge landed → `detect()` returns `[]`.
- **Edge case — stacked PR:** `branch_delete` with an open child PR based on the branch → returns `stacked_pr` hazard with child PR info.
- **Edge case — merge not landed:** `branch_delete` after `merge` where PR state is not `MERGED` → returns `merge_not_landed` hazard.
- **Error path — probe failure:** `gh` returns non-zero → raises `HazardProbeError`, never returns `[]`.
- **Behavioral — reversible skip:** `commit` transition → `detect()` returns `[]` without issuing any `gh` call.
- **Behavioral — ordering:** multiple hazards returned in registry order, not probe-completion order.
- **Behavioral — acknowledgeable vs non-acknowledgeable:** `stacked_pr` is acknowledgeable, `merge_not_landed` is not.

**Verification:** `uv run python -m pytest plugins/saga/tests/test_ceremony_hazards.py -v` passes with all oracles from the claude test suite.

---

### U2. Port merge_watcher.py (CLI with record/validate/watch)

**Goal:** Create the merge-expectation watcher that records a baseline at PR-open time and validates it before merge.

**Requirements:** R8, R9, R10, R11, R12

**Dependencies:** U1 (shared test patterns, no code dependency)

**Files:**
- Create: `plugins/saga/scripts/merge_watcher.py`
- Test: `plugins/saga/tests/test_merge_watcher.py`

**Approach:** Port the claude `merge_watcher.py` (553 lines) with one adaptation: change `STATE_DIR = Path(".claude/saga")` to `Path(".gemini/saga")` (KTD4). The module provides three subcommands: `record` (writes `merge_expectation.json` sidecar with head SHA, check name→passing map, review decision), `validate` (point-in-time comparison against live PR state, refuses on named divergence), `watch` (polls N ticks, catches mid-poll flips). `record --force` is the only re-baseline path (R12); a plain re-record over an existing sidecar refuses (KTD7). A missing sidecar is a named refusal, never a silent pass (R10). The name→passing map (not just names) distinguishes "was passing, regressed" from "was never passing, unchanged" (R11).

**Patterns to follow:** `plugins/saga/scripts/ship_ceremony.py:29-32` (runner testability). `plugins/saga/tests/test_state_paths.py` (importlib loading convention).

**Test scenarios:**
- **Happy path — record:** Sidecar written with SHA/checks/review before any poll (R8).
- **Edge case — re-record refuses:** Plain `record` over existing sidecar → refuses; `--force` re-baselines (R12).
- **Edge case — missing sidecar:** `validate` with no sidecar → named refusal with remedy, not a silent pass (R10).
- **Error path — head moved:** Live head SHA differs from baseline → `head_moved` divergence.
- **Error path — check flipped:** A recorded-passing check is now non-passing → `check_flipped` divergence (R9, R11).
- **Error path — check missing:** A recorded check is absent from live state → `check_missing` divergence.
- **Error path — review regressed:** Review decision worsened → `review_regressed` divergence.
- **Error path — PR not open:** PR state is closed/merged → `pr_not_open` divergence.
- **Behavioral — conditionally-skipped steady state:** A check non-passing at both record and merge time → no `check_flipped` refusal (R11, AE8).
- **Behavioral — watch mid-poll flip:** Pass → fail → pass sequence → still raises `check_flipped` despite final green tick.
- **Integration — CI fixture shape:** Fixtures must use the antigravity repo's actual job names: `Tests (Python 3.12)`, `Validate Plugins`, `Lint`, `Type Check`, `Security Scan` (always-run), `Publish Plugin` (conditionally-skipped, `if: startsWith(github.ref, 'refs/tags/')`) — R21.

**Verification:** `uv run python -m pytest plugins/saga/tests/test_merge_watcher.py -v` passes. Sidecar path assertion: `merge_watcher.STATE_DIR == Path(".gemini/saga")`.

---

### U3. Port ship_undo.py (CLI with undo/show)

**Goal:** Create the rollback-manifest and undo engine that reverses recorded ceremonies.

**Requirements:** R13, R14, R15, R16, R17, R18, R19, R23

**Dependencies:** U1 (shared test patterns, no code dependency)

**Files:**
- Create: `plugins/saga/scripts/ship_undo.py`
- Test: `plugins/saga/tests/test_ship_undo.py`

**Approach:** Port the claude `ship_undo.py` (585 lines) with one adaptation: change `STATE_DIR = Path(".claude/saga")` to `Path(".gemini/saga")` (KTD4). The module provides `append_entry` (called by `ship_ceremony.py`'s transition runners), `undo` (executes reverse newest-to-oldest), and `show` (reads manifest). Undo of `merge` runs `git revert --no-edit <merge_sha>` on main; undo of `branch_delete` resurrects from recorded head SHA. R14 conflict handling: if `git revert` produces conflicts, abort the revert (`git revert --abort`), leave the entry un-marked-undone, surface `REVERT_CONFLICT` failure. R18/R19: unreachable SHA surfaces `SHA_UNREACHABLE` after a `git fetch origin` re-probe. R23: `branch_delete` runner (in U4) records `branch_already_deleted: true` when the remote ref is absent; undo of such an entry is a no-op success (the branch was already gone).

**Patterns to follow:** `plugins/saga/scripts/ship_ceremony.py:29-32` (runner testability). Claude `ship_undo.py` docstring (KTD4 forward-only, KTD5 gating, resumability contract).

**Test scenarios:**
- **Happy path — full completion:** Reverting a fully completed ceremony produces a revert commit on `main` and resurrects the deleted branch (R14).
- **Edge case — reversible-only:** A ceremony killed after PR-open (no merge/branch_delete) undoes on a bare call, no `--operator-confirmed` (R15).
- **Edge case — gated:** Undo plan with `merge`/`branch_delete` entries refuses without `--operator-confirmed undo` (R15).
- **Edge case — empty/fully-undone:** Absent or fully-undone manifest → no-op success, not an error (R17).
- **Error path — revert conflict:** `git revert` produces conflicts → abort revert, surface `REVERT_CONFLICT`, entry stays un-marked-undone, repo not left conflicted (R14).
- **Error path — SHA unreachable:** Recorded SHA not in local store → `git fetch origin`, re-probe; if still absent → `SHA_UNREACHABLE` with remedy (R18, R19).
- **Error path — mid-undo kill:** Process killed mid-revert → already-reverted entries marked `undone: true`, remaining entries untouched (R16).
- **Behavioral — resumable:** Re-run `--undo` after a kill → resumes from the un-reverted entry (R16).
- **Behavioral — scope:** Gating looks only at not-yet-undone entries; an already-undone `always_operator` entry doesn't force confirmation on a later call.
- **Behavioral — already-deleted branch:** Manifest entry with `branch_already_deleted: true` → undo is a no-op success (R23).

**Verification:** `uv run python -m pytest plugins/saga/tests/test_ship_undo.py -v` passes. Sidecar path assertion: `ship_undo.STATE_DIR == Path(".gemini/saga")`.

---

### U4. Wire safety pack into ship_ceremony.py

**Goal:** Restructure `ship_ceremony.py`'s `run()`, `start()`, transition runners, and `_build_parser()` to integrate all four safety mechanisms.

**Requirements:** R1, R2, R3, R8, R9, R13, R23

**Dependencies:** U1, U2, U3 (all three modules must exist before wiring)

**Files:**
- Modify: `plugins/saga/scripts/ship_ceremony.py`
- Modify: `plugins/saga/tests/test_ship_ceremony.py` (existing — update calls for new signatures)
- Test: `plugins/saga/tests/test_ship_ceremony_safety.py` (new integration test)

**Approach:**

1. **Imports (KTD2):** Add `sys.path.insert(0, str(SCRIPT_DIR))` after the existing imports, then `import ceremony_hazards`, `import merge_watcher`, `import ship_undo` with `# noqa: E402`. Do not import `ship_receipt` or `ship_teardown` (KTD1 — stripped).

2. **Error classes:** Add `OperatorConfirmationError`, `HazardRefusedError`, `MergePreflightError` alongside the existing `ShipCeremonyError` subclasses.

3. **Transition runners return `dict[str, Any]` (KTD1):** Change every runner from `-> None` to `-> dict[str, Any]`. Port the return values from the claude version:
   - `_do_commit` → `{"branch", "head_sha", "remote_created"}` (uses new `_remote_branch_exists` + `_push_and_record_commit_fields` helpers)
   - `_do_open_pr` → `{"pr_number", "branch"}`
   - `_do_request_review` → `{"pr_number", "branch"}`
   - `_do_merge` → `{"pr_number", "branch", "pre_merge_main_sha", "merge_sha"}`
   - `_do_checkout_main` → `{"branch"}`
   - `_do_pull` → `{"branch"}`
   - `_do_branch_delete` → `{"branch", "head_sha"}` + R23 already-deleted check
   - Strip all `_register_branch`, `_register_pr`, `_close_if_registered` calls (KTD1).

4. **`run()` safety wiring (KTD5):** Add `operator_confirmed`, `acknowledge_hazard`, `undo` parameters to `run()`. Sequence in `run()`:
   - Resolve saga
   - If `undo`: fork to `ship_undo.undo()` immediately, before the mismatch check (mirrors claude KTD6)
   - Compute `upcoming = next_transition()`
   - If upcoming is `None`: return "already shipped"
   - **Operator-confirmed gate (R1/R2/R3):** If `TRANSITION_TIERS[upcoming] == ALWAYS_OPERATOR` and `operator_confirmed != upcoming`: raise `OperatorConfirmationError` before dispatch and before `saga.py save`. If `operator_confirmed` is set but doesn't match `upcoming`: raise regardless of tier.
   - **Hazard detection (R4-R7):** `ceremony_hazards.detect(saga, upcoming, repo_root, runner)` — refuse on any unacknowledged finding. A finding is acknowledged if its `hazard_id` is in `acknowledge_hazard` and `acknowledgeable` is true.
   - **Merge-watcher validate (R8-R12):** If `upcoming == "merge"`: call `merge_watcher.validate(saga_id, repo_root)` — refuse on missing sidecar or named divergence.
   - Dispatch runner: `fields = _RUNNERS[upcoming](saga, repo_root=repo_root, runner=runner)`
   - `ship_undo.append_entry(repo_root, saga_id, transition=upcoming, tier=..., **fields)` (R13)
   - `saga.py save --ceremony-transition upcoming --ceremony-tier` (existing)
   - Return status line including operator-confirmed note

5. **`start()` safety wiring:** Add `merge_watcher.record(saga_id, pr_number, repo_root, runner)` after the draft PR is opened (R8 front-loaded path). Add `ship_undo.append_entry` after the push (R13).

6. **`_do_branch_delete` R23 (KTD6):** Before `git branch -d` and `git push origin --delete`, check `git ls-remote --exit-code --heads origin <branch>`. If returncode != 0 (remote ref absent), skip deletion, record `{"branch": branch, "head_sha": head_sha, "branch_already_deleted": True}`, return. If returncode == 0, proceed with local + remote delete as today, return `{"branch": branch, "head_sha": head_sha}`.

7. **`_build_parser()`:** Add to `p_run`: `--operator-confirmed` (default None), `--acknowledge-hazard` (nargs="*", default None), `--undo` (action="store_true"). Add the `--acknowledge-hazard` choices from `ceremony_hazards.HAZARD_REGISTRY`.

8. **`main()`:** Pass new args through to `run()`.

**Patterns to follow:** Claude `ship_ceremony.py:500-540` (run() safety wiring). `plugins/saga/scripts/ship_ceremony.py:538-563` (existing _build_parser pattern).

**Test scenarios:**
- **Happy path — reversible transition:** `run` with next transition `commit` → proceeds without operator confirmation (R3).
- **Edge case — always_operator gate:** `run` with next transition `merge`, no `--operator-confirmed` → `OperatorConfirmationError`, ledger unadvanced (R1, AE1).
- **Edge case — mismatched confirmation:** `run --operator-confirmed merge` but next is `branch_delete` → refused (R2, AE2).
- **Edge case — hazard refusal:** `run` with next `branch_delete`, stacked PR detected → `HazardRefusedError` (R4, AE3).
- **Edge case — hazard acknowledged:** Same as above with `--acknowledge-hazard stacked_pr` → proceeds (R5, AE4).
- **Edge case — merge watcher refusal:** `run` with next `merge`, `check_flipped` detected → `MergePreflightError` (R9, AE7).
- **Edge case — already-deleted branch:** `run` with next `branch_delete`, remote ref absent → no-op success, manifest records `branch_already_deleted: true` (R23).
- **Integration — undo fork:** `run --undo --operator-confirmed undo` → forks to `ship_undo.undo()` before forward-transition logic (R14, R15, AE5).
- **Integration — start records expectation:** `start()` → `merge_watcher.record()` called after draft PR opened (R8).
- **Error path — missing sidecar:** `run` with next `merge`, no merge_expectation sidecar → named refusal with remedy (R10).

**Verification:** `uv run python -m pytest plugins/saga/tests/test_ship_ceremony_safety.py -v` passes. `uv run python -m pytest plugins/saga/tests/ -v` (full saga test suite) passes with no regressions. `uv run python -m ruff check plugins/saga/scripts/ship_ceremony.py` passes. `uv run python -m mypy plugins/saga/scripts/ship_ceremony.py --ignore-missing-imports` passes.

---

### U5. Port and adapt test suites + update /work docs

**Goal:** Port the three claude test files with adapted fixtures, and update the /work SKILL.md and pr-continuation-loop.md with safety contract documentation.

**Requirements:** R20, R21, R22

**Dependencies:** U1, U2, U3, U4 (all modules and wiring must exist)

**Files:**
- Create: `plugins/saga/tests/test_ceremony_hazards.py` (port + adapt)
- Create: `plugins/saga/tests/test_merge_watcher.py` (port + adapt)
- Create: `plugins/saga/tests/test_ship_undo.py` (port + adapt)
- Modify: `plugins/saga/skills/work/SKILL.md`
- Modify: `plugins/saga/skills/work/references/pr-continuation-loop.md`

**Approach:**

*Tests (R20, R21):* Port each claude test file and adapt:
- Change test loading paths from `plugins/saga/scripts/` to match antigravity's directory layout (same path — no change needed, both repos use `plugins/saga/scripts/`).
- Change all `STATE_DIR` / `SAGAS_DIR` references from `.claude/saga` to `.gemini/saga` in fixtures and assertions.
- Adapt `test_merge_watcher.py` fixtures to use the antigravity repo's actual CI job names: `Tests (Python 3.12)`, `Validate Plugins`, `Lint`, `Type Check`, `Security Scan` (always-run), `Publish Plugin` (conditionally-skipped). Include a fixture exercising a non-passing-but-steady-state check (R21) — specifically a `Publish Plugin` check that is non-passing at both record and merge time, asserting no `check_flipped` refusal.
- Each test file uses `importlib.util.spec_from_file_location` to load the module under test — the same loading pattern as the existing `plugins/saga/tests/test_ship_ceremony.py:42-53` (`_load_ship_ceremony`), not just `test_state_paths.py`.

*Docs (R22):* Update the antigravity `/work` SKILL.md and `pr-continuation-loop.md` to mirror the claude side's safety contract documentation:
- Document `run --operator-confirmed merge` and `run --operator-confirmed branch_delete`.
- Document the merge-watcher expectation (recorded at PR-open, validated before merge).
- Document hazard acknowledgment (`--acknowledge-hazard stacked_pr`).
- Document the undo path (`run --undo`, `--operator-confirmed undo`).
- Document the already-deleted branch behavior (R23).

**Patterns to follow:** `plugins/saga/tests/test_state_paths.py` (importlib loading, path assertions). Claude `plugins/saga/skills/work/SKILL.md` and `references/pr-continuation-loop.md` (safety contract docs to mirror).

**Test scenarios:**
- **Integration — full test suite:** `uv run python -m pytest plugins/saga/tests/ -v` — all tests pass including the three new test files and existing tests with no regressions.
- **Behavioral — CI fixture shape:** `test_merge_watcher.py` includes a `Publish Plugin` conditionally-skipped fixture (R21).
- **Behavioral — path assertions:** All three test files assert sidecar paths use `.gemini/saga`, not `.claude/saga`.

**Verification:** `uv run python -m pytest plugins/saga/tests/ -v --cov=plugins/saga/scripts --cov-report=term-missing` passes with no regressions. `uv run python -m ruff check plugins/saga/tests/` passes. `uv run python -m mypy plugins/saga/tests/ --ignore-missing-imports` passes. Manual review: `/work` SKILL.md and `pr-continuation-loop.md` contain the safety contract sections.

---

## Scope Boundaries

**In scope:**
- Three new scripts + operator-confirmed gate logic in `ship_ceremony.py`
- Transition runner restructuring (`None` → `dict[str, Any]`)
- Sidecar path adaptation (`.claude/` → `.gemini/`)
- Three test files ported and fixture-adapted
- `/work` SKILL.md and `pr-continuation-loop.md` updated
- R23 already-deleted branch handling (new, not a claude port)

**Deferred to follow-up work:**
- `ship_teardown.py` and `ship_receipt.py` (issue #347, 1245 lines + tests) — resource manifest and receipt system
- `teardown` transition (depends on ship_teardown/ship_receipt)
- External engine dispatch, second-opinion, engine registry (separate workstream)

**Out of scope (non-goals):**
- Redis-channel plugin (antigravity has no Claude Code session to bridge)
- Saga spec changes (ceremony fields unchanged)
- The `/engines` command (no engine subsystem)
- Engine dispatch, chaperone economics, bridge signatures

## Risks & Dependencies

**Risk: transition runner restructuring breaks existing ceremony tests.** The existing `plugins/saga/tests/test_ship_ceremony.py` (654 lines) directly calls `SC.run()`, `SC.start()`, `SC._do_branch_delete()`, and `SC._do_request_review()`. Changing runner return types from `None` to `dict[str, Any]` changes the `_RUNNERS` type signature, and adding `operator_confirmed`/`acknowledge_hazard`/`undo` parameters to `run()` changes its call signature. The full-ceremony test loop at line 241 calls `SC.run()` for every transition including `merge` and `branch_delete` — after U4, these calls must pass `operator_confirmed="merge"` and `operator_confirmed="branch_delete"` respectively. *Mitigation:* U4 must update `test_ship_ceremony.py` to pass the new parameters where the existing tests drive `always_operator`-tier transitions, and update any assertions that depend on runner return values. This test file is added to U4's Files list.

**Risk: sidecar path mismatch breaks tests on machines with cached `.claude/saga` state.** *Mitigation:* `.gitignore` already ignores both `.claude/` and `.gemini/` (confirmed: `.gitignore:55-61`). No cached state will conflict.

**Dependency: `gh` CLI must be available and authenticated.** The hazard detection and merge-watcher modules shell out to `gh pr view` and `gh pr list`. *Mitigation:* same dependency as the existing ceremony — no new requirement.

**Dependency: the antigravity `ship_ceremony.py` must be structurally close to the claude version at the last sync point.** *Verified:* both share the same `TRANSITIONS` tuple (7 entries), `CeremonyTier` class, `resolve_saga` logic, and runner signatures. The claude side added 8th transition `teardown` which we strip (KTD1/KTD5).

## Sources / Research

- `infiquetra-claude-plugins` `plugins/saga/scripts/ship_ceremony.py` (842 lines) — target state with safety wiring + teardown (teardown stripped per KTD1)
- `infiquetra-claude-plugins` `plugins/saga/scripts/ceremony_hazards.py` (246 lines) — no path adaptation needed (KTD3)
- `infiquetra-claude-plugins` `plugins/saga/scripts/merge_watcher.py` (553 lines) — `STATE_DIR` adaptation (KTD4)
- `infiquetra-claude-plugins` `plugins/saga/scripts/ship_undo.py` (585 lines) — `STATE_DIR` adaptation (KTD4)
- `infiquetra-claude-plugins` `tests/test_ceremony_hazards.py` (242 lines), `tests/test_merge_watcher.py` (593 lines), `tests/test_ship_undo.py` (988 lines) — test suites to port
- `infiquetra-claude-plugins` `plugins/saga/scripts/ship_teardown.py` (954 lines), `ship_receipt.py` (291 lines) — NOT ported (issue #347, out of scope)
- `infiquetra-antigravity-plugins` `plugins/saga/scripts/ship_ceremony.py` (590 lines) — current state, 7 transitions, no safety wiring
- `infiquetra-antigravity-plugins` `plugins/saga/scripts/saga.py:45` — `STATE_DIR = Path(".gemini/saga")`
- `infiquetra-antigravity-plugins` `plugins/saga/tests/test_state_paths.py` — importlib loading convention, path assertion pattern
- `infiquetra-antigravity-plugins` `.github/workflows/ci.yml` — 5 always-run + 1 conditionally-skipped job
- `infiquetra-antigravity-plugins` `.gitignore:55-61` — `.claude/` and `.gemini/` both ignored
- `docs/brainstorms/2026-07-12-ship-ceremony-safety-pack-requirements.md` — 23 R-IDs, 9 AEs, reviewed and all findings resolved
- `docs/reviews/2026-07-12-ship-ceremony-safety-pack-doc-review.md` — advisory conditional pass, all 6 findings fixed in-place