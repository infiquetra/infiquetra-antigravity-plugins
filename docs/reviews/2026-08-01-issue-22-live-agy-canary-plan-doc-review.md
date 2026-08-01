# Live AGY Gemini Lifecycle Canary Plan Documentation Review

The issue #22 plan defines one controlled release canary over the completed deterministic contracts
and keeps live model use, host mutation, raw evidence, and operator judgment behind explicit gates.

## Review Result

| Field | Value |
|---|---|
| Target | `docs/plans/2026-08-01-issue-22-live-agy-canary-plan.md` |
| Reviewed revision | isolated worktree based on `6e4e36f` |
| Linked issue | `infiquetra-antigravity-plugins#22` |
| Blocked | no |
| Override | none |

## Applied Findings

| Priority | Status | Finding | Applied fix |
|---|---|---|---|
| P1 | fixed | Editing the main checkout would immediately alter the installed plugins because Antigravity loads repository symlinks. | The plan requires an isolated worktree and leaves the installed checkout on `main` until separate authority. |
| P1 | fixed | Installed AGY 1.1.8 does not provide the headless slash-command expansion needed by the scripted route. | R3 and KTD1 require version 1.1.9 or newer and reject a fragile pseudo-terminal workaround. |
| P1 | fixed | Treating flags or requested values as proof would let model, effort, routing agent, execution worker, sandbox, or resume capabilities pass without observation. | R2 and R5 require separate requested and observed facts. Lifecycle-router proves routing; the unnamed default worker executes phases and remains observed as `unknown`. Native plan mode is not required because the canary promotes a plan in edit-enabled sandbox mode. |
| P1 | fixed | Requiring a fully passing live-canary receipt before any controlled probe creates a circular prerequisite. | KTD3 makes preflight deterministic-first, then runs bounded controlled probes, then gates the full lifecycle on the completed receipt. |
| P1 | fixed | A no-remote fixture proves that mutation cannot succeed but does not prove the model never attempted it. | R9 and KTD4 also audit structured tool-call intent and fail on every forbidden action attempt. |
| P1 | fixed | Mechanical completeness could be mistaken for substantive quality. | R10 and KTD6 keep the five-dimension decision pending until Jeff approves the sanitized comparison. |
| P2 | fixed | The issue's recommended model and effort are not themselves authority to spend live model capacity. | R5 and the operator gates require Jeff to select the pair before any live call. |
| P2 | fixed | A general transcript pipeline would expand privacy and maintenance scope beyond one release canary. | R7, KTD2, and the boundaries keep raw events ignored and commit only closed sanitized evidence. |
| P2 | fixed | A new verifier could conflict with the capability, obligation, receipt, promotion, deliberation, reconciliation, and handoff contracts. | R8 and KTD5 compose those existing validators and limit new logic to orchestration, event parsing, audit, and release binding. |

## Formal Issue Rubrics

| Rubric | Result | Evidence |
|---|---|---|
| Acceptance criteria clarity | ready | Every issue criterion maps to a unit and a decisive test or run command. |
| Devil's advocate | ready | Version mismatch, false observation, remote intent, raw evidence, shallow output, and stale bindings fail closed. |
| Specification fidelity | ready | R49-R54, F6, AE10-AE11, and AE14-AE15 are represented without a model matrix or remote lifecycle mutation. |
| Context completeness | ready | All nine issue dependencies are live-verified closed, issue #18's approved baseline is on main, and AGY 1.1.9 is installed. |
| Issue sizing | ready | One runner, one reference fixture, one verifier extension, one release record, and focused docs form the final release gate. |
| Prerequisite mapping | ready | AGY 1.1.9 supplies headless slash expansion, and Jeff approved the live model configuration. |

## Remaining Findings

No documentation P0, P1, P2, or P3 findings remain. Jeff approved the required host version and live
model configuration, so implementation is ready.

## Residual Risk

A live model can still produce a mechanically valid but weak result. The planned verifier will keep
that outcome pending or rejected, and Jeff's post-run comparison remains the final release-quality
gate.
