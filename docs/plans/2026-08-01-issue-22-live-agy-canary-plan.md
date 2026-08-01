---
title: Live AGY Gemini Lifecycle Canary Implementation Plan
type: feat
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/22
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-issue-22-live-agy-canary-plan-doc-review.md
---

# Live AGY Gemini Lifecycle Canary Implementation Plan

## Summary

Add one bounded runner for the reference lifecycle. It first proves the deterministic issue #18
contracts and the exact host behaviors needed by the run. It then drives one headless AGY conversation
through the required Saga commands, resumes that conversation once, and validates sanitized receipts,
promoted artifacts, settlement, handoff, and the absence of attempted remote mutation. The final
quality decision remains Jeff's judgment against the approved Claude and Codex summaries.

The implementation stays in an isolated worktree until merge because the installed Antigravity
plugins are symlinked to the main checkout. No plugin installation, host configuration, deployment,
or broad model matrix belongs to this issue.

## Live Preconditions

- Every hard dependency named by issue #22 is closed; this was verified live on 2026-08-01.
- AGY CLI version 1.1.9 is installed. Its changelog confirms headless slash-command expansion is
  available.
- The live plugin links resolve to the repository's main checkout. Development therefore uses the
  isolated issue worktree and does not change the installed plugin bytes before explicit authority.
- Jeff approved `gemini-3.1-pro` with `high` effort, the `lifecycle-router` agent, and sandbox mode for
  the bounded probes and single live run.

## Requirements

R1. `preflight --fixture reference-lifecycle` runs deterministic conformance and approved-baseline
validation before any model call. Failure stops immediately.

R2. Preflight then performs only the bounded controlled probes required by the `live-canary`
capability profile. It records requested and observed AGY version, Antigravity version, model, effort,
agent, resume, sandbox, runtime-root, and plugin facts separately. Unknown, unavailable, failed, or
mismatched required facts stop before the reference lifecycle begins. Native AGY plan mode is not a
live-canary prerequisite because this lifecycle must promote a durable plan while running in
edit-enabled sandbox mode.

R3. Headless slash-command execution requires AGY CLI version 1.1.9 or newer. The runner rejects
older versions instead of emulating an interactive terminal or sending slash commands as plain
prompts.

R4. The canary creates one fresh local fixture repository under `.conformance-local/`. The fixture
has no Git remote and contains the bound implementation-spec profile, README folder contract, seed,
local outcome contract, and deterministic validators required by the route.

R5. The selected model and effort are explicit run inputs and must match an operator-approved pair.
The first plan recommends `gemini-3.1-pro` and `high`. The runner also requests the installed
`lifecycle-router` agent and sandbox mode and records what AGY actually reports; a requested value is
never promoted as an observation.

R6. `run --fixture reference-lifecycle` uses one fixed AGY argument template with no shell. It drives
one conversation through `/ideate`, `/brainstorm`, `/impl-spec`, `/plan`, `/doc-review`, `/work`,
`/code-review`, `/qa`, `/retro`, and `/handoff`, with `/resume` invoked in a new process against the
same conversation identity before work continues.

R7. Raw stream events, prompts, transcripts, local diagnostics, and machine paths stay under the
ignored `.conformance-local/` root. Only closed, sanitized receipts, digests, validator results,
semantic summaries, and an operator decision may enter `docs/conformance/runs/`.

R8. `verify <run-manifest>` reuses the existing capability, lifecycle-obligation, transition-receipt,
deliberation, promotion, reconciliation, handoff, and conformance validators. It proves every required
phase and strategy, documentation and code review, quality assurance, resume, settlement, promotion,
and handoff claim from bound evidence rather than file presence or narration.

R9. The mutation audit examines AGY structured tool events and the fixture repository state. It fails
on any attempted push, PR, issue, board, merge, deployment, plugin-management, credential, or remote
configuration action. The fixture has no remote, and the runner never uses
`--dangerously-skip-permissions`.

R10. Mechanical success produces a pending sanitized release record covering depth, evidence use,
seed retention, adjudication, and lifecycle completeness against the bound Claude and Codex baseline.
Only Jeff may change that record to approved. A pending or rejected decision remains release-blocking.

R11. Ordinary repository tests and continuous integration remain deterministic and make no AGY or
Gemini calls. Live tests use injected process results and minimized fixtures; the real run is an
explicit operator-authorized release action.

## Key Technical Decisions

KTD1. **Use the headless interface built for this purpose:** require AGY 1.1.9 or newer and parse its
closed `stream-json` events. A pseudo-terminal driver would be timing-sensitive, difficult to audit,
and would hide whether the installed CLI really supports scripted slash commands.

KTD2. **One script, three commands:** `preflight` proves deterministic and controlled prerequisites;
`run` creates and drives one local fixture; `verify` validates an existing sanitized run manifest.
There is no general transcript collector, replay engine, minimizer, scheduler, or model matrix.

KTD3. **Separate probe traffic from the lifecycle:** preflight runs deterministic checks first, then
small controlled AGY probes. It emits a current passing capability receipt. The full reference
lifecycle starts only after the shared `live-canary` consumer accepts that receipt.

KTD4. **Audit structured intent, then remove reachability:** structured tool events are checked for
forbidden action attempts, and the fresh fixture has no Git remote. This covers both attempted and
successful mutation without installing global wrappers or modifying user policy files.

KTD5. **Reuse contract owners:** the runner coordinates existing validators and records their receipt
identities. It does not reimplement lifecycle settlement, promotion, deliberation, capability state,
or handoff semantics.

KTD6. **Human quality remains human:** verification can prove evidence structure and completeness but
cannot decide whether Gemini's reasoning is deep enough. Jeff receives the five sanitized comparison
summaries and records the only release-quality decision.

KTD7. **Keep installation out of implementation:** code and deterministic tests run in the isolated
worktree. Updating AGY or causing the linked main checkout to expose merged plugin bytes requires the
separate authority called out below.

## Acceptance Traceability

| Issue acceptance criterion | Implementation | Proof |
|---|---|---|
| Preflight blocks on deterministic, capability, profile, and baseline failures | U1-U2 | injected failures plus actual deterministic commands |
| One fresh live route and one resume | U3 | bound conversation and phase receipts |
| Mechanical verification covers every obligation and artifact | U1-U3 | negative fixtures and real run verification |
| Requested and observed host facts remain separate | U1-U2 | shared capability receipt validation |
| No unauthorized remote mutation | U1-U3 | event audit, no-remote fixture, forbidden-action tests |
| Five-dimension quality review | U4 | pending record plus Jeff's canonical decision reference |
| Shallow mechanical success remains blocked | U1-U4 | pending/rejected decision tests |

## Implementation Units

### U1. Closed canary and release-record contracts

Add the live-canary manifest, structured-event parser, mutation audit, release-review record, and
failure fixtures. Add contract tests for missing profile/README, capability failure, missing phase or
strategy, failed resume, invalid handoff, baseline drift, unsafe evidence, shallow pending quality,
and attempted remote mutation.

### U2. Deterministic and controlled preflight

Extend `scripts/saga_conformance.py` only where the canary needs a reusable validated binding. Add
`scripts/run_agy_saga_canary.py preflight` with deterministic-first ordering, the AGY 1.1.9 floor,
fixed controlled probe arguments, the shared `live-canary` capability evaluation, and ignored local
evidence output.

### U3. One live lifecycle and mechanical verification

Build a fresh no-remote fixture, run the exact command route through one conversation, exercise
`/resume`, preserve structured events locally, sanitize the result, and verify every contract before
producing a pending release record. Stop on the first failed phase or forbidden action.

### U4. Operator quality decision and package closeout

Document the run contract and five-dimension rubric. Present the sanitized Gemini summaries to Jeff.
After his decision, bind the canonical issue-comment reference to the unchanged release record. Bump
Saga once, run one code review and one documentation review, then complete normal CI, PR, merge,
issue, board, and branch cleanup.

## Verification

```bash
python3 scripts/run_agy_saga_canary.py preflight --fixture reference-lifecycle
python3 scripts/run_agy_saga_canary.py run --fixture reference-lifecycle
python3 scripts/run_agy_saga_canary.py verify <run-manifest>
python3 scripts/saga_conformance.py verify --fixture reference-lifecycle
uv run pytest plugins/saga/tests/test_live_canary_contract.py plugins/saga/tests/test_conformance_scenarios.py -q
uv run ruff check .
uv run ruff format --check .
uv run mypy .
python3 scripts/validate_plugins.py
```

Then run the whole repository suite and GitHub checks before merge.

## Operator Gates

1. Completed: AGY 1.1.9 is installed and provides headless slash-command expansion.
2. Completed: Jeff approved `gemini-3.1-pro` with `high` effort, `lifecycle-router`, and sandbox mode.
3. After the run, approve or reject the sanitized five-dimension Gemini comparison. Mechanical
   success cannot substitute for this decision.

## Boundaries

- No pseudo-terminal automation, broad version/model matrix, transcript replay, or general evaluator.
- No raw transcript, prompt, history, brain state, machine path, credential, or host identity in Git.
- No push, PR, issue, board, merge, deployment, plugin-management, credential, or remote mutation by
  the canary.
- No AGY update, plugin installation, host configuration, or live model call before the named gate.
- One implementation pass, one code review, and one documentation review. Further work requires a
  failed acceptance criterion or a new operator-approved scope.
