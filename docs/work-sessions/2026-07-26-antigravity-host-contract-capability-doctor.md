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
