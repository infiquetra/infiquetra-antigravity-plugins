# Antigravity Host Contract and Capability Doctor Work Session

## Phase 1 — U1-U3 capability contract and privacy boundary

Built the first dependency cluster for issue #20:

- U1 defines the JSON-compatible capability catalog, strict
  `antigravity.capabilities.v1` receipt, closed raw/evaluation vocabularies,
  consumer-scoped requiredness, and explicit optional fallback evaluation.
- U2 adds the immutable probe registry with fixed argument vectors, bounded
  output and timeouts, injected execution seams, passive observation controls,
  and fixture-only controlled behavior proof.
- U3 separates rich ignored local diagnostics under
  `.gemini/saga/capability-doctor/` from promotable receipts, uses atomic bounded
  writes, maps absolute discoveries to logical root roles, and rejects unsafe
  promoted fields without echoing their values.

Key decisions implemented:

- Installed fleet-core remains standard-library only; the `.yaml` catalog is
  comment-free JSON syntax.
- CLI and host versions are observations, never support allowlists.
- Required non-passing capabilities block even when an optional fallback passes.
- Default probe execution makes zero `agy` subprocess calls.
- Commands, paths, parsers, and timeouts cannot be supplied by catalog data.

Files modified:

- `plugins/fleet-core/references/antigravity-capability-probes.yaml`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_probes.py`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_diagnostics.py`
- `plugins/fleet-core/tests/test_antigravity_capabilities.py`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/`
- `plugins/fleet-core/README.md`
- `plugins/saga/tests/test_state_paths.py`

Checks:

- `uv run pytest plugins/fleet-core/tests/test_antigravity_capabilities.py plugins/saga/tests/test_state_paths.py -q` — 35 passed.
- `uv run pytest plugins/fleet-core/tests -q` — 37 passed.
- `uv run ruff check` on the U1-U3 Python/test files — passed.
- `uv run mypy` on the three new fleet-core modules — passed.
- `git diff --check` — passed.

Commits:

- `3a8b97f` — U1 capability receipt contract.
- `c6f4f8b` — U2 bounded probe registry.

Next step: implement U4’s versioned active-surface selector, contextual
host-contract linter, strict lint receipt, and positive/negative fixtures.

## Phase 2 — U4 host-contract linter and contract scan

U4 adds the closed active-surface selector, six stable host-contract rules,
adjacent JSON annotations, strict excerpt-free lint receipts, selector-abuse
rejection, capability-gated classifications, and historical/foreign controls.
The initial repository scan found 235 unresolved candidates across 45 active
files, providing the remediation inventory for U5-U6.

The approved read-only `scan-contract` assignment reviewed U1-U4 for injection,
secret leakage, unsafe execution, unsafe exemptions, privacy, and fail-open
behavior. Root verification adopted and fixed all three findings:

- P1: passed capability results now require every catalog-declared evidence ID.
- P2: local diagnostics derive the fixed ignored path from an injected
  repository root and reject symlink escapes.
- P2: invalid evidence IDs and runtime-root roles are rejected without echoing
  attacker-supplied values.

Additional checks:

- `uv run pytest plugins/fleet-core/tests/test_host_contract_lint.py -q` — 21 passed.
- `uv run pytest plugins/fleet-core/tests -q` — 58 passed before scan remediation.
- `uv run pytest plugins/fleet-core/tests/test_antigravity_capabilities.py plugins/fleet-core/tests/test_host_contract_lint.py -q` — 57 passed after remediation.
- Ruff and mypy on the changed U4/remediation modules — passed.

Commit:

- `07b6d34` — U4 host-contract linter.

Next step: execute U5-U6 against the machine-generated active finding
inventory, then require the selected surface to reach zero unresolved findings.

## Phase 3 — U5-U6 native interaction and runtime contracts

U5 ports the surviving Claude interaction semantics into Antigravity-native
instructions: ask one blocking question in the current session, stop until the
answer arrives, and use structured interaction only when the capability receipt
proves it. Active orchestration now has two target modes, `inline` and
`multi-agent-consensus`; the source `team-execution` and
`cc-workflows-ultracode` mechanisms both map to native Antigravity consensus
rather than being renamed or executed as Claude workflows.

U6 enforces those semantics in runtime code:

- Saga dispatch requires proven `agy.agent.execution` before selecting
  `multi-agent-consensus`.
- A restrictive consensus request additionally requires proven
  `agy.sandbox.isolation`; unknown, unavailable, or failed evidence halts.
- Legacy Claude backend names remain parseable only so the dispatcher can emit
  an explicit migration error. They cannot reach active execution.
- Antigravity-owned state defaults to `.gemini`; retained `.claude` paths are
  narrowly annotated read-only foreign inputs.
- Session discovery requires a doctor-resolved projects root instead of a fixed
  Antigravity brain path.
- Scheduling and isolation text distinguishes requests from observed proof.

The versioned selector now reports 13 classified findings and zero unresolved
host-contract violations.

Checks:

- Focused U5 instruction tests — 57 passed, one skipped.
- Focused U6 runtime and adjacent-plugin tests — 204 passed, one skipped.
- Host-contract repository scan — zero unresolved findings.
- Ruff on the changed Python and test surfaces — passed.
- Mypy on the changed runtime modules — passed.
- `git diff --check` — passed.

Commits:

- `2f64a28` — U5 native interaction and orchestration instructions.
- `e6225ef` — U6 executable host boundaries and native runtime routing.

Next step: integrate the capability catalog, receipt evaluator, privacy checks,
and zero-unresolved host-contract scan into the canonical plugin doctor (U7).

## Phase 4 — U7 canonical doctor integration

The existing `scripts/validate_plugins.py` doctor now composes four structured
contract sections with its prior manifest, surface, install, warning, and action
output:

- catalog schema, revision, digest, and capability count;
- capability receipt source and unchanged consumer evaluation;
- strict promotable-receipt privacy disposition;
- selector digest, classified findings, unresolved findings, and remediation.

The default `repository-validation` path constructs a deterministic unavailable
receipt without calling an `agy` runner. `--observe-host` is explicit and runs
only registered bounded observation vectors; controlled behavior remains
unavailable without accepted evidence. `--capability-profile` plus
`--capability-receipt` evaluates a named consumer, returns nonzero for required
non-passing capabilities, and reports a valid optional fallback as degraded
without converting it into a failure.

Invalid receipts are not retained in the result and are rejected with generic
schema/privacy errors so unsafe values are not echoed. Unknown consumer profiles
also fail instead of passing through an empty requirement set. The marketplace
wrapper remains output- and exit-equivalent to the canonical command.

Checks:

- Doctor, harness-doc, capability-contract, and host-linter tests — 74 passed.
- Doctor-focused Ruff and mypy — passed.
- Canonical doctor human and JSON modes — passed.
- Marketplace JSON output equals canonical JSON output — passed.
- `git diff --check` — passed.

Commit:

- `5860e80` — U7 canonical doctor integration.

Next step: add Saga's direct shared-receipt consumer and finish release metadata
and conformance documentation (U8).

## Phase 5 — U8 direct Saga consumer and release surface

Saga now ships `host_capability_gate.py`, a narrow adapter that resolves
fleet-core through the existing vendored shim, validates the canonical catalog
and promotable receipt, and returns `evaluate_for_consumer` unchanged. It
formats the shared result and maps `passed` or valid `degraded` to exit 0 and
`blocked` or invalid evidence to exit 1; it does not write Saga state or infer
lifecycle completion.

Integration fixtures prove:

- `saga.work` reports the declared isolated-sequential fallback as degraded
  when independent agent execution is unavailable;
- `saga.resume` blocks when required resume evidence is unknown;
- schema drift and local diagnostic input are rejected without raw-value echo;
- fleet-core resolution failure is explicit and does not fall back to a copied
  schema.

Release metadata now describes and versions every materially changed plugin:
fleet-core `0.9.0`, Saga `1.4.0`, mission-control `2.7.0`, and
multi-agent-consensus `2.3.0`. The operator docs distinguish ignored local
diagnostics from promoted receipts and document the direct Saga consumer. The
engineering journal records the discovered vacuous-pass risk for undeclared
consumer names and the closed-subject rule used by both doctor and adapter.

Checks:

- Affected Saga, fleet-core, mission-control, multi-agent-consensus, doctor,
  and harness suites — 149 passed, one skipped.
- U8 Ruff and mypy — passed.
- Canonical and marketplace doctor JSON output — equivalent.
- Capability diagnostic root ignore check — passed.
- `git diff --check` — passed.

Next step: run the full validation ladder, independent adversarial and privacy
reviews, and the Saga code-review gate before PR release.

## Phase 6 — verified-workflow review remediation

The first privacy and adversarial reviews both requested changes. Their
deduplicated findings exposed fail-open authorization paths rather than cosmetic
issues, so every P1/P2 finding was remediated:

- optional capability alternatives now block unless the primary passes or the
  declared fallback passes in an allowed fallback state;
- controlled probe state is derived from typed requested and observed facts;
  caller-submitted state is rejected;
- Saga outcome routing accepts a bounded canonical receipt instead of boolean
  host or consensus assertions;
- runtime-base profiles require CLI, host, plugin link/load/validation, and
  discovered logical-root evidence;
- plugin links are checked by required plugin identity and exact repository
  target;
- the generic subprocess runner is non-executable because it cannot prove a
  no-write/no-network boundary;
- receipt loading, promotable values, selected lint files, symlinks, UTF-8, and
  file sizes are bounded and fail closed;
- host-contract linting recognizes constructed `.claude` path components,
  rejects write-shaped read-only annotations, and binds capability annotations
  to the rule-specific capability;
- Saga board progression moved to `.gemini`, active office-hours and retro
  instructions use Antigravity-native language, and the packaged legacy
  workflow-emission CLI was removed.

Negative regression coverage now exercises missing and nonpassing fallbacks,
fact mismatches, fabricated states, incomplete/wrong plugin links, unsafe
selector symlinks, annotation abuse, oversized receipts, disabled generic
subprocess observation, receipt-only outcome authorization, Antigravity-owned
ledger state, and the removed workflow emitter.

Checks:

- Focused capability, lint, routing, and Saga tests — 143 passed, one skipped.
- Full pytest — 1139 passed, one skipped.
- Ruff lint and format checks — passed across 165 files.
- Mypy — passed across 164 source files.
- Bandit medium/high scan excluding tests — passed.
- Canonical doctor — passed with zero unresolved host-contract findings.
- `git diff --check` — passed.

Next step: commit the remediation, rerun the exact privacy and adversarial
reviewers against the new SHA, and resolve any remaining findings before the
Saga code-review gate.
