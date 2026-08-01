---
title: Live Antigravity Receipt Commands Repair Plan
type: fix
status: active
date: 2026-08-01
origin: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/33
reviewed: 2026-08-01
review_status: ready
review_artifact: docs/reviews/2026-08-01-issue-33-live-receipt-commands-plan-doc-review.md
---

# Live Antigravity Receipt Commands Repair Plan

## Summary

Turn the existing deliberation, transition-receipt, and artifact-promotion Python libraries into
small command-line tools that an Antigravity phase can run while its working directory remains the
target repository. Replace the affected skills' bare helper names with complete installed-plugin
commands. Bind the reference lifecycle fixture to an explicit obligation contract so a later,
separately approved live canary can exercise the real receipt path.

## Observed defect

The final issue #22 canary completed every phase and wrote every expected lifecycle document, but it
produced no deliberation, transition, or promotion receipts. The worker searched for
`artifact_promotion.py` but never invoked it. Repository inspection confirms three connected causes:

1. The skill text names the receipt modules but does not provide complete commands.
2. The three modules expose Python APIs only; invoking them with `--help` does not expose a usable
   command contract.
3. The reference fixture does not contain the lifecycle-obligation contract and identifiers required
   to build a transition receipt.

The schemas, evaluators, persistence functions, conflict handling, and canary detection behaved as
designed. This repair therefore leaves those contracts unchanged.

## Requirements

R1. Each receipt module must expose one narrow `argparse` command that consumes explicit JSON or file
inputs, calls the existing validated Python API, writes only inside the supplied repository root, and
returns non-zero with a sanitized error when validation fails.

R2. Deliberation evaluation must accept a manifest, result list, convergence decision, and escalation
decision. A complete receipt is persisted write-once under
`docs/outcomes/<outcome-id>/deliberation-receipts/`; incomplete receipts remain valid evidence of a
blocked attempt but cannot become transition evidence.

R3. Transition construction must accept one obligation contract plus a closed evidence-input JSON
object using the existing eight receipt categories. Repository evidence keeps the existing path and
digest verification. A complete deliberation receipt may be bound only through the existing
`deliberation_evidence()` adapter.

R4. Artifact promotion must accept a staged file and the existing transaction inputs. It must call
`promote_artifact()` without changing target-family validation, sanitization, idempotency, conflict
preservation, or evidence requirements.

R5. Skill instructions must resolve helpers with the installed Saga plugin root while leaving the
target repository as the current working directory. Use `AGY_PLUGIN_ROOT` when supplied and the
ordinary Antigravity install location `$HOME/.gemini/config/plugins/saga` as the fallback. The
multi-agent-consensus plugin resolves as an installed sibling. Missing helpers fail before receipt
work starts.

R6. The reference lifecycle configuration must bind a committed obligation contract by path and
SHA-256 digest. Fixture preparation copies that contract into the no-remote workspace, and each phase
instruction names the contract, outcome, transition, and obligation identities it must use.

R7. Command and fixture tests must prove success, malformed-input rejection, path containment,
write-once behavior, conflict behavior, and mechanical receipt discovery without calling AGY or any
remote service.

## Key technical decisions

KTD1. **Add command entry points to the existing modules.** A new workflow engine or receipt wrapper
would duplicate contract logic and enlarge the surface. Each CLI remains a thin parser around the
already-tested function.

KTD2. **Use explicit files instead of prose-derived evidence.** The deliberation command receives
four JSON files. The transition command receives one closed evidence JSON file. The promotion command
receives one staged artifact file. The tools never infer proof from a model's narrative.

KTD3. **Keep plugin discovery in skill shell snippets.** No machine-specific absolute path is
committed. The worker checks the resolved helper before use. This fixes the target-repository versus
installed-plugin boundary without changing Antigravity itself.

KTD4. **Seed a canary-specific obligation contract.** The contract declares one required obligation
per artifact-producing reference phase. Each phase transition binds its staged artifact, and phases
with declared independent deliberation additionally bind a completed deliberation receipt. The
promotion transaction then makes the staged artifact canonical. No canary verifier fabricates
evidence.

KTD5. **Do not rerun or install during this defect.** Deterministic tests can prove the command
surface and fixture contract. Installed-plugin mutation and a replacement live run remain explicit
operator boundaries after review.

## Implementation units

### U1. Add thin command-line interfaces

Add `main()` functions and focused persistence helpers to:

- `plugins/multi-agent-consensus/scripts/deliberation.py`
- `plugins/saga/scripts/transition_receipts.py`
- `plugins/saga/scripts/artifact_promotion.py`

The commands print a small JSON result containing schema, state, and repository-relative receipt
path. They never print input documents or secret-shaped content on failure.

### U2. Make skill instructions executable

Update only the receipt-producing sections in the reference lifecycle skills. Add one shared locator
snippet and complete command examples for the receipt type each phase needs. Preserve every current
phase strategy and authority rule.

### U3. Bind the controlled reference fixture

Add the obligation contract beside `live-canary.json`, bind its digest in the configuration, copy it
into the fixture repository, and append its logical identifiers to each phase instruction. Extend
the canary config validator so a missing or changed contract fails preflight.

### U4. Prove the integrated local path

Add subprocess tests that run the three commands against a temporary no-remote repository and then
use the canary's receipt collector and verifier-facing bindings. Extend existing contract tests for
skill command completeness and fixture binding.

## Verification

```bash
uv run pytest plugins/saga/tests/test_live_receipt_commands.py plugins/saga/tests/test_live_canary_contract.py -q
uv run pytest plugins/multi-agent-consensus/tests/test_deliberation.py plugins/saga/tests/test_transition_receipts.py plugins/saga/tests/test_artifact_promotion.py -q
uv run ruff check plugins/multi-agent-consensus/scripts/deliberation.py plugins/saga/scripts/transition_receipts.py plugins/saga/scripts/artifact_promotion.py plugins/saga/tests
uv run mypy plugins/multi-agent-consensus/scripts/deliberation.py plugins/saga/scripts/transition_receipts.py plugins/saga/scripts/artifact_promotion.py
python3 scripts/validate_plugins.py
```

After one code review and one documentation review have no actionable P0 through P3 findings, run the
whole repository suite because the skill text and three shared lifecycle modules affect the release
route. Do not install plugins or invoke AGY in this plan.

## Boundaries

- No schema weakening, fabricated evidence, new dependency, Antigravity application patch, remote
  mutation, deployment, or installed-plugin change.
- No cleanup of unrelated relative script references.
- One remediation pass and one targeted recheck per review. A broader receipt architecture change
  requires operator approval.
