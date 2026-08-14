# Claude Plugins Porting Plan Implementation Code Review

Independent third-pass review of the working-tree port against `docs/plans/2026-08-13-claude-plugins-porting-plan.md`. The plan is fully implemented. No P0 or P1 findings remain.

## Review Result

| Field | Value |
|---|---|
| Target | Working tree on `feat/claude-plugins-porting-p1-p2` vs `origin/main` (`d450d509`) |
| Reviewed revision | working tree (uncommitted) over `d450d509` |
| Linked saga | `task-claude-plugins-porting-p1-p2` (`kind=task`, `id=claude-plugins-porting-p1-p2`) |
| Backend | inline |
| External engine | operator chose none |
| Blocked | no |
| Untracked implementation files | included in this audit (new tests, `spec_table.py`, `team-scaffold/`, `tools/gate-manifest.json`) |
| Evidence ledger | unavailable (`plugins/saga/scripts/evidence_ledger.py` missing) |

## Team

Always-on: correctness, security, testing, maintainability.

Conditional:

- reliability — pre-push gate, verify-panel quorum, Hermes timeout
- agent-native — `team-scaffold` skill and outcome approval table
- adversarial — large uncommitted port surface

Not selected: deploy/migration-verification (this repo does not deploy; `team-scaffold` only emits harness files), previous-comments (no PR).

## Built-vs-Planned Audit

COMPLETION: 10/10 requirements DONE, 8/8 units DONE, 0 PARTIAL, 0 NOT-DONE, 1 CHANGED (R6 native `--outcome` path, already ratified in the working-tree plan), 0 UNVERIFIABLE.

| ID | State | Mode | Evidence |
|---|---|---|---|
| R1 | DONE | DIFF | `models.json` `schema_version` 2; keys `execution_classes`, `scalar_efforts`, `root_orchestration_profiles`; models `gemini-3.1-pro`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`; no `fable` / `lineage_models` |
| R2 | DONE | DIFF | `resolve_for_runtime` / `adapt_runtime_argv` / `RuntimeResolution` in `tier_resolver.py:163,342,394`; collapse `grok`/`muse` `max→xhigh`, `agy` `max`/`xhigh→high` (`_EFFORT_COLLAPSE` at 126) |
| R3 | DONE | DIFF | `wave_file_conflicts` / `assert_no_wave_file_conflicts` at `execution_spec.py:1311,1342`; emit call 2192; `team_emitter.py:228`; table at `spec_table.py:223`; plan skill split rule `SKILL.md:230-232` |
| R4 | DONE | DIFF | `floor = n // 2 + 1` at `execution_spec.py:1625`; required `refuted_deliverable` / `advisory_corrections`; `test_quorum_floor_uses_strict_majority_for_even_n` asserts n=4 → 3 |
| R5 | DONE | DIFF | `shlex` + `punctuation_chars=True` in `pre_push_gate_hook.py:160`; 33 hook tests passed this run |
| R6 | CHANGED → DONE | DIFF | Native `render_outcome` + `--outcome` (`spec_table.py:288,378`); wired at `outcome/SKILL.md:88`; plan step 5 does not author `ExecutionSpec` |
| R7 | DONE | DIFF | `plugins/home-lab-ops/skills/team-scaffold/` with `scripts/tests/` (43 skill-local tests passed this run) |
| R8 | DONE | DIFF | `SUBPROCESS_TIMEOUT_SECONDS = 45` at `profile_request.py:26`; existing timeout and reply-limit tests still present; stale `2026-07-30` campaign absent |
| R9 | DONE | DIFF | Both modules and their tests deleted; `test_no_lease_broker_readd.py` present; host-contract JSON has no `lease_broker`/`orphan_evidence`; ledger `decision.state: superseded` for both candidates, operator Jeff, `2026-08-13T23:59:00Z` |
| R10 | DONE | EXTERNAL-STATE run here | Full suite **1769 passed, 1 skipped** (50.27s). Doctor `--strict-install` **status: ok**. Plan-named subset **282 passed**. |
| U1 | DONE | DIFF | `test_fleet_core_execution_classes.py` covers `review-max`/`work-high` and collapse; `cost_weights.json` has 3.7/3.6-flash rows |
| U2 | DONE | DIFF | Hook + `spec_table.py` + `tools/gate-manifest.json` + outcome SKILL |
| U3 | DONE | DIFF | Shipped as `test_verify_panel_severity_axis.py` (plan names this file) |
| U4 | DONE | DIFF | 15 wave-conflict tests passed; disjoint vs overlapping cases present |
| U5 | DONE | DIFF | Skill tree + golden/validate-spec tests |
| U6 | DONE | DIFF | Non-regression only; committed adapter unchanged |
| U7 | DONE | DIFF | Deletions + re-add guard + `test_output_attestation.py` + ledger supersede |
| U8 | DONE | DIFF | Journal entries under `docs/engineering-journal/` dated 2026-08-13 |

## Scope Check

CLEAN.

Intent: implement the eight units in `docs/plans/2026-08-13-claude-plugins-porting-plan.md`.

Delivered: all eight. Extra files (gate-manifest, `cost_weights` rows, `test_output_attestation.py`, conformance digest updates) are named in the working-tree plan or are mechanical fallout from the ledger/host-contract edit.

## Findings

### P0 / P1 / P2

None.

### P3

| # | File | Issue | Reviewer | Confidence | Route |
|---|---|---|---|---|---|
| 23 | `docs/engineering-journal/DECISIONS.md:65` | The additive-schema decision still says keep only `gemini-3.1-pro` and `gemini-3.5-flash`. The working-tree plan and `models.json` also list `gemini-3.7-flash` and `gemini-3.6-flash`. | maintainability | 100 | advisory |

Prior Round 2 findings #18–#22 were re-checked this pass and stay resolved: `git diff --check d450d509` is clean; wrapper/foreach/continuation helpers exist; outcome CLI error tests are in `test_spec_table.py:237-249`.

## Verification (this run)

- Plan-named suites: 282 passed.
- Full `uv run pytest --no-cov`: 1769 passed, 1 skipped, 50.27s.
- `uv run python scripts/validate_plugins.py --strict-install`: status ok. Fleet-core inert-surface warning is advisory (library-only plugin).

## Residual Risk

The implementation is still uncommitted on `feat/claude-plugins-porting-p1-p2`. `git diff origin/main` does not include the untracked new files; a commit that omitted them would ship a partial port. Wave-conflict detection compares declared paths as exact strings, same as upstream.

## Review Artifact

`docs/code-reviews/2026-08-14-claude-plugins-porting-plan-code-review.md`

Evidence ledger write skipped — `evidence_ledger.py` is not in this repo's saga scripts.
