---
verdict: ship-with-deferred
health_score: 100
tier: Standard
---

# QA Report: feat/claude-plugins-porting-p1-p2

| Field | Value |
|-------|-------|
| Date | 2026-08-14 |
| Target | `feat/claude-plugins-porting-p1-p2` implementing `docs/plans/2026-08-13-claude-plugins-porting-plan.md` |
| Reviewed revision | working tree over `d450d509` (uncommitted) |
| Merge state | pre-merge (no PR; `HEAD == origin/main == d450d509`) |
| Tier | Standard |
| Scope | behavior, security, config, docs |
| Saga | `task-claude-plugins-porting-p1-p2` |
| Criteria freeze | local only — `evidence_ledger.py` missing from this repo |

## Ship Verdict: ship-with-deferred

Standard blocks critical, high, and medium. The only finding is low (docs). Behavior, security, and config passed with no findings.

## Health Score: 100  (baseline n/a, delta n/a)

| Risk class | Score | Result |
|------------|------:|--------|
| behavior | 100 | pass |
| security | 100 | pass |
| config | 100 | pass |
| docs | 97 | pass |

The score is a deterministic gstack-formula port over LLM-assigned severities — a signal, not the gate. The verdict above is the decision.

Weights in scope: behavior 20, security 20, config 5, docs 3. `qa_health_score.py` returned `overall: 100` (docs 97 after one low deduction).

## Top findings

1. LOW [docs] Journal decision `{#models-json-schema-v2-additive}` still names only two Gemini models; `models.json` lists four.

## Summary by severity

| Severity | Count | Blocks at this tier? |
|----------|------:|----------------------|
| critical | 0 | yes |
| high | 0 | yes |
| medium | 0 | yes |
| low | 1 | no |

## Pass/fail by risk class

| Risk class | Result | Note |
|------------|--------|------|
| behavior | pass | Plan-named suites 282 passed; same-session full suite 1769 passed / 1 skipped; `resolve_for_runtime` smoke and `spec_table.py --help` succeed |
| security | pass | Pre-push runs argv lists without `shell=True`; team-scaffold stores token-var names only; Hermes timeout still 45s |
| config | pass | Doctor `--strict-install` status ok; `models.json` schema 2 loads; `cost_weights` covers every model; `tools/gate-manifest.json` valid; home-lab-ops skill count 6 includes `team-scaffold` |
| docs | pass | One non-blocking stale journal sentence |
| infra | N/A | Generator only; no live cluster mutation |
| API | N/A | No public HTTP contract |
| deployment | N/A | No deploy/release wiring |
| data | N/A | No migrations |
| trivial | N/A | Not a formatting-only change |

## Findings

### F1: Journal Gemini catalog is stale

- **Severity:** low (P3)
- **Risk class:** docs
- **Evidence:** `docs/engineering-journal/DECISIONS.md:65` says keep `gemini-3.1-pro` and `gemini-3.5-flash`. `plugins/fleet-core/scripts/fleet_commons/models.json` lists `gemini-3.1-pro`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`. Working-tree plan R1 matches `models.json`.
- **Repro:** Open those two files and compare the model lists.
- **Falsifiable prediction:** omitted — the mismatch is the file text itself.

## Checks run

| Class | Check | Result |
|---|---|---|
| behavior | `uv run pytest` plan-named suites (execution classes, pre-push, spec table, verify panel, wave conflicts, lease re-add, worktrees, Hermes, team-scaffold) | 282 passed |
| behavior | Same-session full `uv run pytest --no-cov` | 1769 passed, 1 skipped, 50.27s |
| behavior | `resolve_for_runtime('review-max','agy')` → `gemini-3.1-pro-high` / `high`; `resolve('judgment')` still Gemini | ok |
| behavior | `python plugins/saga/scripts/spec_table.py --help` exposes `--outcome` | ok |
| security | `pre_push_gate_hook.py:398,432` `subprocess.run` on argv lists, no `shell=True` | ok |
| security | team-scaffold specs carry `vault_discord_bot_token_*` names; `repo_stamp.py` "secrets never belong in the repo" | ok |
| security | `SUBPROCESS_TIMEOUT_SECONDS = 45` at `profile_request.py:26` | ok |
| config | `uv run python scripts/validate_plugins.py --strict-install` | status ok; home-lab-ops skills=6 |
| config | `models.json` + `cost_weights.json` + `tools/gate-manifest.json` parse | ok |
| docs | Journal vs `models.json` catalog | F1 |

Browser MCP: no-op (no UI surface).

`appsec-audit` offered and not run. The new trust boundary is a local pre-push hook over operator shell text, not a live auth/egress service.

Provenance-manifest confidence: no delegated-execution manifests — no additional signal.

## Recommended regression tests

1. After commit, run `git add` on the untracked implementation files and confirm `git diff --stat origin/main` includes `spec_table.py`, `team-scaffold/`, `test_wave_file_conflicts.py`, `test_verify_panel_severity_axis.py`, `test_pre_push_gate.py`, and `tools/gate-manifest.json`.
2. Push-hook dry run: invoke the hook with `git push origin HEAD` in a throwaway clone after the commit, and confirm the four gate-manifest steps start.
3. Outcome table: `python3 plugins/saga/scripts/spec_table.py docs/outcomes/<id>/outcome-spec.json --outcome` on a real outcome artifact.

## Deferred (with repro)

- **F1** — Update `docs/engineering-journal/DECISIONS.md` `{#models-json-schema-v2-additive}` to name `gemini-3.7-flash` and `gemini-3.6-flash`. Repro: compare line 65 to `models.json` `models` keys.

## Residual

The port is still uncommitted. A commit that omits the untracked new files would ship a partial port. That is a process risk, not an acceptance failure of the code that is on disk.
