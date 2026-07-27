---
title: Antigravity Host Contract and Capability Doctor Implementation Plan
type: feat
status: active
date: 2026-07-26
origin: docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md
deepened: 2026-07-26
reviewed: 2026-07-26
review_status: ready
review_artifact: docs/reviews/2026-07-26-antigravity-host-contract-capability-doctor-plan-doc-review.md
---

# Antigravity Host Contract and Capability Doctor Implementation Plan

## Summary

Establish one executable, schema-versioned Antigravity host contract in `fleet-core`, extend the existing plugin doctor to evaluate it, and make Saga consume the same receipt semantics without translation. The work separates safe local diagnostics from promotable evidence, proves behavior instead of allowlisting versions, and brings the active Antigravity surfaces needed for issue #20 to a zero-unresolved-violation lint result.

---

## Problem Frame

The repository can currently validate plugin manifests, surface counts, symlink state, and a narrow set of stale phrases, but it cannot establish whether the installed `agy` CLI and Antigravity host can perform the behaviors Saga depends on. Current runtime observations prove that `agy` 1.1.7 exposes model, effort, agent, resume, plan, and sandbox flags and that Antigravity 2.3.1 is installed, but those observations do not prove the corresponding behavior.

The active repository also contains host assumptions copied from Claude and Codex surfaces: 82 `AskUserQuestion` references across 23 Saga instruction files, a direct Claude Workflow invocation, Antigravity-owned `.claude` state paths, a fixed Antigravity brain root, scheduling claims, and isolation guarantees stronger than the current host evidence. A useful doctor must find these conditions without rejecting historical source evidence, and it must fail the affected consumer when a required capability is failed or unknown.

This is the foundation child under parent issue #13. It owns requirements R19-R24 and acceptance examples AE1, AE2, AE4, AE12, and AE13 from the requirements artifact; it does not implement the downstream lifecycle reconciler, deliberation dispatcher, port ledger, artifact promotion transaction, or conformance laboratory.

---

## Requirements

### Capability contract and evaluation

R1. The canonical probe catalog must be the schema-versioned YAML artifact at `plugins/fleet-core/references/antigravity-capability-probes.yaml`, and every entry must declare identity, consumer-scoped requiredness, a safe registered probe method, expected evidence, outcome rules, and fallback policy. Covers origin R20.

R2. The doctor must record the `agy` CLI and Antigravity host versions separately, represent runtime roots by logical role in promotable evidence, and report supported command-flag observations, plugin link/load/validation state, and observable model, effort, agent, resume, plan-mode, and sandbox facts. Covers origin R19.

R3. Probe acceptance must be behavior-based: an unseen version passes when every capability required by the selected consumer profile passes, while a known version fails when any required behavioral probe fails or remains unknown. Version strings and help text may be observations but never an allowlist. Covers origin R20-R22 and AE1.

R4. Probe outcomes must use one closed vocabulary. Required `failed`, `unknown`, or `unavailable` outcomes block the selected consumer; only a capability declared optional before execution may use a proven fallback and evaluate as `degraded`. Covers origin R22 and AE2/AE13.

R5. Every executable probe must be local, bounded, side-effect-safe, and selected from a fixed Python registry. A catalog row may name a registered method but may not supply an executable, shell command, arbitrary path, or unbounded parser. Covers origin R20 and the issue stop conditions.

### Evidence and privacy

R6. Raw command output, absolute runtime roots, and other rich diagnostics may exist only in a separate ignored local diagnostic format under `.gemini/saga/capability-doctor/`; they must never be accepted as promotable capability receipts. Covers origin R24.

R7. The promotable capability receipt (`antigravity.capabilities.v1`) and host-contract lint receipt (`antigravity.host-contract-lint.v1`) must use strict versioned schemas, reject unknown fields and unsafe values, include the applicable catalog or active-surface digest, and omit usernames, hostnames, credentials, absolute home paths, raw excerpts, transcripts, prompt history, command output, and environment data. Capability receipts must also separate requested facts from observed facts. Covers origin R24 and AE12.

### Host-contract lint and remediation

R8. The host-contract linter must scan the active Saga and adjacent-plugin runtime surfaces with stable rule IDs for executable `.claude` paths, Claude-only interaction and Workflow APIs, fixed brain roots, unproven scheduling, and overclaimed isolation. Each finding must identify the path, line, rule, classification, required capability when applicable, and remediation. Covers origin R23 and AE4.

R9. The linter must distinguish active instructions from tests, fixtures, changelogs, historical lifecycle artifacts, quoted lineage, foreign-runtime read-only inputs, and capability-gated behavior. Exceptions must be narrow, adjacent to the affected text, reasoned, and reviewable; broad path or pattern allowlists are forbidden. Covers origin R23.

R10. All unresolved violations in the linter's selected active surface must be remediated or converted to a valid explicit classification before issue #20 can pass. Antigravity-owned state must not write to `.claude`, direct Claude-only interaction or Workflow calls must not remain active, fixed brain roots must come from discovery, and isolation or scheduling claims must match observed evidence. Covers origin R23 and the issue acceptance criteria.

### Integration and validation

R11. `scripts/validate_plugins.py` must remain the single canonical plugin doctor and continue its current package/install checks while also reporting catalog, capability-receipt, privacy, and host-contract-lint results in human and JSON output. The compatibility wrapper must continue to return equivalent output and exit status.

R12. The default repository-validation profile must be deterministic and safe on CI hosts without `agy`; it must run catalog, receipt-schema, sanitization, and host-contract checks and report any safe observations available. Consumer-specific live capability gates must use an explicit profile and return nonzero when that profile has a required failed, unknown, or unavailable capability.

R13. At least one Saga production-facing adapter and integration fixture must load `antigravity_capabilities` through the existing `fleet_commons_shim`, evaluate the unchanged receipt for a named Saga consumer, and preserve the shared state semantics without copying or translating them.

---

## Key Technical Decisions

KTD1. **Keep the catalog declarative and execution closed:** the YAML catalog names immutable probe IDs and revisions, while a Python registry owns fixed `shell=False` argument vectors, timeouts, parsers, and sanitizers. Executable commands in YAML were rejected because they would turn a data file into an unreviewed command-injection boundary.

KTD2. **Use the JSON-compatible subset of YAML for the catalog:** `fleet-core` is an installed, stdlib-only library with no dependency installation step, so `antigravity_capabilities.py` will parse the canonical `.yaml` file with `json.loads` and validate the closed schema. Depending on PyYAML at plugin runtime or maintaining a custom general YAML parser was rejected. Because JSON does not permit comments, the subset and editing rules live in `plugins/fleet-core/README.md` and the host-contract reference rather than an invalid comment header inside the catalog.

KTD3. **Express requiredness by consumer profile:** each catalog capability declares `required_for` consumers and an optional fallback contract rather than one global required boolean. This lets deterministic repository validation run without a live Antigravity host while making `saga.<phase>` and `live-canary` profiles fail closed on the behavior they actually require.

KTD4. **Separate probe state from consumer evaluation:** raw probe results use exactly `passed`, `failed`, `unknown`, or `unavailable`; consumer evaluation uses exactly `passed`, `blocked`, or `degraded` and preserves the raw state in its blocking/degraded lists. `degraded` is legal only after an optional fallback is proven. A required capability can never become `degraded`, preventing a successful optional fallback from hiding a required failure.

KTD5. **Make local diagnostics and promotable receipts different contracts:** ignored local diagnostics may retain bounded raw evidence for troubleshooting, while `antigravity.capabilities.v1` and `antigravity.host-contract-lint.v1` are strict, closed, sanitized evidence envelopes. Field-specific validators normalize each allowed value; no global hostname-like regex runs across capability IDs, versions, or other dotted safe strings. The library returns validated promotable objects but never writes them into tracked repository paths automatically.

KTD6. **Classify active surfaces explicitly:** the linter uses a maintained surface selector plus stable rule definitions and narrow inline annotations for `historical`, `foreign-runtime-input`, or `capability-gated` evidence. Broad ignored directories and keyword-only scans were rejected because references are executable inputs to skills and because the same token can be either a real host dependency or source lineage.

KTD7. **Extend the current doctor instead of adding another authority:** `scripts/validate_plugins.py` composes package/install validation, catalog validation, receipt evaluation, privacy validation, and host-contract findings. Host observations require explicit `--observe-host` or a supplied promoted receipt, and controlled/model-bearing probes remain fixture/canary-only so the existing Ubuntu CI path stays deterministic.

KTD8. **Consume the receipt directly through fleet-core:** Saga uses `fleet_commons_shim.load("antigravity_capabilities")` and the shared `evaluate_for_consumer` result rather than mapping states into a Saga-specific vocabulary. A thin adapter may handle file I/O and exit status, but it may not rename, collapse, or reinterpret receipt states.

KTD9. **Remediate claims to the proven Antigravity contract:** platform-specific `AskUserQuestion` and `ToolSearch` instructions become a host-native “ask one blocking question and stop” interaction contract; direct Claude Workflow execution is removed from active Antigravity routing; Antigravity state moves to logical `.gemini` roles; scheduler and isolation language becomes requested-versus-observed and fail-closed. Textual renaming without a capability gate was rejected.

KTD10. **Keep repository validation deterministic by default:** the default `repository-validation` profile performs no `agy` subprocess call. `--observe-host` explicitly requests registered passive observations, but help/version/flag observations never satisfy a capability whose catalog method requires behavioral proof. A command that cannot prevent credential refresh, log/cache writes, remote access, or other durable host mutation returns `unavailable` and must be proven through a controlled fixture or accepted canary receipt instead.

KTD11. **Version the active-surface selector and annotation grammar:** `plugins/fleet-core/references/antigravity-host-contract-surfaces.json` is the closed, reviewable selector for active roots and exact adjacent files. Markdown annotations use an immediately preceding `<!-- antigravity-host-contract: {...} -->` comment and Python uses an immediately preceding `# antigravity-host-contract: {...}` comment; the payload is one JSON object with closed `class`, `rule`, `reason`, and `revisit` keys. `capability-gated` also requires `capability`, and `foreign-runtime-input` also requires `"access":"read-only"`. The scanner computes the excerpt digest instead of trusting a hand-authored hash.

KTD12. **Keep one capability issue and one reviewable PR with atomic unit commits:** U1-U8 are one acceptance boundary because the doctor must not activate until the schema, remediation, privacy, and direct consumer agree. Each unit lands as its own scoped commit and passes its focused checkpoint before the next unit begins; the final PR is reviewed by unit and may not contain unrelated cleanup. Splitting contract pieces into independently closed issues was rejected because none delivers the issue's executable host contract alone.

---

## High-Level Technical Design

The probe catalog, probe registry, receipt schema, and consumer evaluator form one fleet-wide contract. The canonical doctor and Saga both load that contract through the existing fleet-core resolution mechanism.

```text
antigravity-capability-probes.yaml
              |
              v
catalog loader + closed probe registry -----> ignored local diagnostics
              |                                      |
              v                                      | explicit sanitize
antigravity.capabilities.v1 <-------------------------+
              |
              +----> evaluate_for_consumer(profile) ----> passed / blocked / degraded
              |
              +----> scripts/validate_plugins.py
              |
              +----> Saga host-capability gate

active surface selector + rule catalog + receipt capabilities
              |
              v
host-contract findings ----> canonical doctor exit status
```

The initial catalog covers four kinds of evidence:

| evidence class | examples | accepted method |
|---|---|---|
| observation | `agy` version, Antigravity bundle version, supported help flags | bounded command or application metadata read; never sufficient when a behavioral probe exists |
| local structural behavior | plugin symlink target, `agy plugin list`, `agy plugin validate` | injected filesystem/runner probe with sanitized facts |
| controlled behavioral behavior | agent execution, conversation resume, sandbox boundary | opt-in fixture probe or accepted canary evidence; otherwise `unknown` or `unavailable` |
| derived consumer evaluation | required/optional disposition and fallback eligibility | pure evaluation of validated catalog plus validated per-probe results |

The initial capability IDs and profiles are stable API vocabulary. Later children may add profiles or capabilities additively, but they must not rename or reinterpret these rows.

| capability ID | accepted evidence | initial consumers |
|---|---|---|
| `host.cli.available` | fixed executable discovery plus bounded version invocation | `saga.runtime-base`, `live-canary`, `conformance-lab` |
| `host.cli.flags-observed` | bounded help/metadata observation listing normalized supported flags; never behavioral proof | observation for every profile |
| `host.application.version-observed` | application metadata when observable; otherwise `unavailable` | observation for every profile, never a sole gate |
| `host.runtime-roots.discovered` | logical-role discovery with no promoted absolute paths | `saga.runtime-base`, `saga.resume`, `live-canary` |
| `plugin.linked` | filesystem link/copy state | `saga.runtime-base`, `live-canary` |
| `plugin.loaded` | parsed `agy plugin list` evidence | `saga.runtime-base`, `live-canary` |
| `plugin.validated` | parsed `agy plugin validate` evidence | `saga.runtime-base`, `live-canary` |
| `control.model.observed` | controlled invocation or accepted canary receipt showing the applied model | `saga.independent-deliberation`, `live-canary` |
| `control.effort.observed` | controlled invocation or accepted canary receipt showing the applied effort | `saga.independent-deliberation`, `live-canary` |
| `execution.agent.independent` | two bounded workers with distinct execution receipts | optional for `saga.independent-deliberation`, fallback below |
| `execution.sequential.isolated` | separate bounded conversations with distinct receipts | fallback for `execution.agent.independent`; required when that fallback is selected |
| `conversation.resume` | controlled continuation retains a nonce and conversation identity | `saga.resume`, `live-canary` |
| `isolation.sandbox.observed` | controlled fixture proves the declared write/read boundary | `saga.isolated-work`, `live-canary` when requested |
| `control.plan-mode.observed` | controlled fixture proves planning mode does not mutate the fixture | `saga.plan`, `live-canary` |

| profile ID | evaluation boundary |
|---|---|
| `repository-validation` | Requires catalog, receipt-schema, privacy, and host-contract checks; live host capabilities are reported but not required |
| `saga.runtime-base` | Requires CLI, logical roots, and plugin link/load/validation behavior |
| `saga.independent-deliberation` | Extends runtime-base; accepts proven agent independence or its declared proven sequential-isolation fallback |
| `saga.resume` | Extends runtime-base and requires controlled conversation-resume behavior |
| `saga.isolated-work` | Extends runtime-base and requires the exact requested isolation boundary |
| `saga.plan` | Extends runtime-base and requires controlled plan-mode behavior when the phase relies on it |
| `conformance-lab` | Requires only the host behaviors named by the selected deterministic scenario |
| `live-canary` | Evaluates the union of capabilities declared by the reference-lifecycle canary, not every catalog row |

The two state layers are deliberately distinct and closed.

| layer | allowed states | meaning |
|---|---|---|
| per-capability probe result | `passed`, `failed`, `unknown`, `unavailable` | What the registered probe or accepted evidence actually established |
| consumer evaluation | `passed`, `blocked`, `degraded` | Whether one named consumer may proceed; blocking and fallback lists retain the underlying probe states |

The linter does not infer host capabilities from source text. A capability-gated annotation names the required catalog capability, and the doctor accepts it only when the relevant receipt proves the gate or the selected consumer profile treats the surface as unavailable and blocked.

---

## Measured Host-Contract Baseline

The initial remediation is bounded by the current active-surface inventory, not by an open-ended rewrite.

| rule class | current active candidates | required issue #20 disposition |
|---|---:|---|
| Claude interaction API | 82 occurrences in 23 Saga instruction/reference files | Port the interaction semantics and remove unresolved tool names |
| Executable `.claude` path | 33 occurrences in 14 plugin files, plus the active port runbook | Move Antigravity writes; classify only proven read-only migration/foreign inputs |
| Claude Workflow surface | 122 occurrences in 27 Saga files, including one direct invocation | Remove active invocation/routing; explicitly quarantine source lineage |
| Fixed brain root | 2 occurrences in `plugins/saga/scripts/discover_sessions.py` | Require discovered or explicitly supplied logical root |
| Unproven scheduling | 3 strong occurrences in 3 Saga files | Rewrite as externally triggered or capability-gated |
| Overclaimed isolation | 40 occurrences in 3 Saga files | Separate requested from observed and halt when required proof is absent |

These counts are a point-in-time seed inventory, not hard-coded acceptance totals. U4 regenerates the machine inventory from the versioned selector; U5 owns instruction/reference findings, U6 owns executable/runtime findings, and U7 may not integrate the gate until their combined unresolved count is zero.

---

## Active-Surface Contract

The selector is explicit enough that implementation does not have to invent which files can affect Antigravity runtime behavior.

| selector class | paths | treatment |
|---|---|---|
| Saga active Markdown | `plugins/saga/commands/**/*.md`, `plugins/saga/skills/**/*.md`, `plugins/saga/agents/**/*.md`, `plugins/saga/references/**/*.md` | Scan as active unless an adjacent valid annotation classifies the exact match |
| Saga executable runtime | `plugins/saga/hooks/**/*.py`, `plugins/saga/scripts/**/*.py` | Scan as active; executable `.claude` writes, fixed roots, and unsupported proof claims are unresolved |
| Adjacent executable runtime | `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py`, `plugins/fleet-core/scripts/fleet_commons/delegation_state.py`, `plugins/mission-control/scripts/sdlc_manager.py` | Scan as active because issue #20 remediates their Antigravity state contracts |
| Adjacent instruction surface | `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/validator-evidence-state.md` | Scan as active because it directs where Antigravity validation evidence is written |
| Active port runbook | `.agents/skills/port-claude-plugins/SKILL.md` | Scan as active because it can direct future migrations |
| Comparison corpus | tests, fixtures, changelogs, `docs/` lifecycle artifacts, and explicitly quoted source lineage | Never silently ignore matched text; classify it as non-active evidence and keep it out of the unresolved count |

`antigravity-host-contract-surfaces.json` stores the schema version, active globs, exact adjacent paths, comparison roots, and its own digest inputs. Unknown keys, missing paths that were declared exact, traversal, absolute paths, broad `**` exclusions, and selectors outside the repository fail validation.

Annotations apply only to the immediately following matched statement and use the KTD11 grammar. A reason and revisit condition are mandatory; file-wide, directory-wide, wildcard, stale-rule, stale-capability, or missing-access annotations fail closed.

---

## Requirement and Acceptance Traceability

Every issue-owned origin requirement and acceptance example has one implementation and proof path.

| origin | plan requirements | implementation units | acceptance proof |
|---|---|---|---|
| R19 | R2 | U1, U2, U6, U7 | Catalog and doctor tests separately report CLI/host versions, normalized flag observations, logical roots, plugin state, controls, resume, plan mode, and isolation facts |
| R20 | R1, R3-R5 | U1, U2 | Closed-catalog tests reject arbitrary execution and accept only registered bounded probes with typed evidence |
| R21 / AE1 | R3 | U1, U2, U7 | `test_unseen_version_with_required_behavior_passes` and `test_known_version_with_required_behavior_failure_blocks` |
| R22 / AE2 / AE13 | R3-R4, R12-R13 | U1, U2, U7, U8 | Required unknown/failed cases block; optional declared sequential fallback is the only path to `degraded`; Saga preserves the shared lists |
| R23 / AE4 | R8-R10 | U4, U5, U6, U7 | Each named active violation has a positive fixture, historical control, abuse case, and zero-unresolved repository scan |
| R24 / AE12 | R6-R7 | U3, U4, U7, U8 | Capability and lint receipt fixtures reject machine identifiers, unsafe fields, raw excerpts, and transcript/prompt content without echoing rejected values |

The live GitHub issue acceptance criteria map to these exact review surfaces.

| issue acceptance criterion | decisive evidence |
|---|---|
| Behavior, not version identity, governs acceptance | `plugins/fleet-core/tests/test_antigravity_capabilities.py` unseen/known version scenarios |
| Every named host-language violation is detected without rejecting history | `plugins/fleet-core/tests/test_host_contract_lint.py` named-rule, historical, active-quote, and exemption-abuse scenarios |
| Required and optional capability semantics remain distinct | Fleet-core evaluator tests plus the Saga direct-consumer fallback and required-uncertainty fixtures |
| Canonical doctor reports and blocks correctly | `tests/test_antigravity_plugin_doctor.py` human/JSON parity and exit-status scenarios |
| Promoted evidence is safe | Capability and lint unsafe-fixture matrices plus non-echo assertions |
| Local diagnostics stay ignored and host-local | `plugins/saga/tests/test_state_paths.py` and `git check-ignore .gemini/saga/capability-doctor/example.json` |
| One Saga consumer uses the shared schema unchanged | `plugins/saga/tests/test_saga_plugin.py` direct-consumption and schema-drift scenarios |

---

## Implementation Units

### U1. Define the capability catalog and closed receipt model

Create the durable schema, parser, state vocabulary, and consumer evaluator that every later unit uses.

**Goal:** Establish one stdlib-only fleet-core programmatic interface for catalog validation, receipt validation, and required-versus-optional evaluation.

**Requirements:** R1-R4, R7; origin R19-R22, AE1, AE2, AE13.

**Dependencies:** None.

**Files:**

- `plugins/fleet-core/references/antigravity-capability-probes.yaml`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py`
- `plugins/fleet-core/tests/test_antigravity_capabilities.py`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/catalog-valid.yaml`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/catalog-invalid-*.yaml`
- `plugins/fleet-core/README.md`

**Approach:** Define strict allowed-key sets for the catalog, capability rows, fallback rows, receipt root, observations, per-capability results, and evaluation summary. Include `catalog_schema`, `receipt_schema`, immutable probe revision, catalog digest, separate `agy_cli_version` and `antigravity_host_version`, normalized `supported_flags`, logical runtime-root roles, requested/observed facts, and stable blocking/degraded ID lists. Implement `load_catalog`, `validate_catalog`, `validate_receipt`, and `evaluate_for_consumer` as pure functions.

**Patterns to follow:** Mirror the explicit schema version and human-readable validation errors in `plugins/fleet-core/scripts/fleet_commons/bridge_receipt.py`, but use the closed allowed-key pattern from `plugins/saga/scripts/provenance_manifest.py`. Preserve the stdlib-only constraint in `plugins/fleet-core/README.md`.

**Test scenarios:**

1. Happy path — input a valid JSON-compatible YAML catalog and receipt for an unseen CLI/host version with normalized supported-flag observations; load and evaluate it for a consumer whose required probes passed; expect a valid non-blocking evaluation without any version allowlist.
2. Required failure — input a known version with one required probe `failed`; evaluate the same consumer; expect its ID in `blocking_capabilities` and a failed result.
3. Required uncertainty — input required `unknown` and `unavailable` results; expect both to block and neither to become `degraded`.
4. Optional fallback — input an optional unavailable capability with its declared fallback proven; expect `degraded`, the fallback ID recorded, and no blocking result.
5. Invalid contract — input unknown schemas, duplicate IDs, unknown probe revisions, unknown states, missing requiredness, malformed fallback rows, and extra root/nested keys; expect named validation errors and no evaluation.
6. Digest drift — alter one catalog byte after a receipt was produced; validate the receipt against the new catalog; expect a catalog-digest mismatch.

**Verification:** The catalog is parseable with only the Python standard library, all invalid shapes fail closed with actionable errors, and AE1/AE13 are directly represented in unit tests.

### U2. Implement safe discovery and behavioral probe execution

Turn catalog method IDs into bounded local observations without allowing the catalog or caller to choose arbitrary commands.

**Goal:** Produce deterministic probe results for version, root, plugin, CLI-control, agent, resume, and sandbox capabilities through injected and side-effect-safe execution seams.

**Requirements:** R2-R5; origin R19-R22, AE1, AE2.

**Dependencies:** U1.

**Files:**

- `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_probes.py`
- `plugins/fleet-core/tests/test_antigravity_capabilities.py`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/probe-*.json`

**Approach:** Add a closed `probe_id -> ProbeDefinition` registry with fixed argument vectors, timeout, parser, sanitizer, evidence-field allowlist, and an execution class of `passive` or `controlled`. Use injectable runners, clocks, environment/root resolvers, and application metadata readers. The default repository profile executes no subprocess. Explicit `--observe-host` may inspect `agy --version`, `agy --help`, Antigravity application metadata, and plugin symlinks; `agy plugin list` and `agy plugin validate` run only when the runner can prove that auth refresh, log/cache writes, remote access, and other durable host mutation are disabled or redirected to injected temporary state. Otherwise those observations are `unavailable`. Agent, resume, plan-mode, and sandbox behavior runs only against an explicit fixture or consumes accepted canary evidence. Missing executables, auth, permissions, timeouts, malformed output, or absent fixture evidence become named `unknown`/`unavailable` results rather than inferred success.

**Patterns to follow:** Use injected runner seams like `plugins/saga/scripts/merge_watcher.py`; use fixed registry rows and bounded input handling like `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py`; never copy its raw absolute-path diagnostics into the promoted receipt.

**Test scenarios:**

1. Happy path — inject successful fixed outputs for CLI version, host version, plugin list/validation, and a controlled behavioral fixture; execute registered probes; expect sanitized `passed` results with separate version observations.
2. Unseen version — inject new version strings with passing required behavior; expect consumer acceptance.
3. Known broken version — inject a familiar version plus a failed behavioral fixture; expect the behavior to block regardless of version.
4. Agent uncertainty — expose an agent flag/list but omit proof of independent execution; expect the agent-execution capability to remain `unknown` and the sequential fallback to be evaluated separately.
5. Runner failures — inject missing executable, nonzero status, timeout, permission denial, malformed JSON, oversized output, and a runner that cannot suppress durable host writes; expect bounded named outcomes with no exception text or raw output in the receipt.
6. Registry safety — request an unknown probe ID or attempt to supply argv/path/shell fields through catalog data; expect validation failure before any runner call.
7. No side effects — run every deterministic probe against a temporary fixture and inspect filesystem/network runner calls; expect no repository mutation, remote call, credential refresh, model invocation, plugin enable/disable, or durable host-state write.

**Verification:** Every catalog method resolves to one immutable registered implementation, subprocess probes use list argv with `shell=False` and timeouts, and no deterministic test requires a live Gemini call.

### U3. Separate local diagnostics from promotable evidence

Make privacy enforcement structural rather than dependent on callers remembering to redact.

**Goal:** Preserve useful local debugging facts while making it impossible to validate or promote machine-identifying evidence.

**Requirements:** R6-R7; origin R24, AE12.

**Dependencies:** U1, U2.

**Files:**

- `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py`
- `plugins/fleet-core/scripts/fleet_commons/antigravity_diagnostics.py`
- `plugins/fleet-core/tests/test_antigravity_capabilities.py`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/promoted-safe.json`
- `plugins/fleet-core/tests/fixtures/antigravity-capabilities/promoted-unsafe-*.json`
- `plugins/saga/tests/test_state_paths.py`

**Approach:** Define a separate local diagnostic writer rooted at `.gemini/saga/capability-doctor/` and accept its root through an injected repository state path. Bound file size and use atomic writes. Implement a shared explicit sanitizer that maps absolute discoveries to logical root roles or path digests and drops raw stdout/stderr, argv, environment, transcript, prompt, excerpt, raw path, and exception fields before either promotable receipt is constructed. Validate keys and values with field-specific allowlists and path/secret checks so safe dotted capability IDs and version strings are not mistaken for hostnames. The lint receipt stores only path SHA-256, line, rule, classification, capability, bounded reason/remediation codes, excerpt SHA-256, and the active-surface manifest digest.

**Patterns to follow:** Use the ignored state-root assertions in `plugins/saga/tests/test_state_paths.py`, atomic write behavior from `plugins/saga/scripts/manifest_store.py`, and path-traversal rejection from its tests.

**Test scenarios:**

1. Happy path — write a bounded local diagnostic containing absolute fixture roots, sanitize it, and build a receipt; expect only logical root roles and path digests in the receipt.
2. Unsafe promoted path — validate receipts containing `/Users/`, `/home/`, Windows home paths, or parent traversal; expect rejection with the exact field path.
3. Secret material — validate token, authorization header, credential-like environment, URL query secret, hostname, and raw transcript/prompt fixtures; expect rejection and no echoed secret in the error.
4. Unknown field — add `stdout`, `stderr`, `argv`, `cwd`, `environment`, or `transcript_path`; expect closed-schema rejection.
5. Dotted safe values — validate capability IDs, schema IDs, versions, and repository-relative dotted filenames; expect no false hostname rejection.
6. State isolation — run the diagnostic writer with a temporary root; expect files only under the injected ignored local path and no files under repository `docs/`, Saga manifests, or the test checkout.
7. Write failure — inject permission denial or interrupted atomic replacement; expect the probe result to remain usable as `unknown`/`unavailable`, no partial promotable receipt, and no half-written file.

**Verification:** All unsafe promoted fixtures fail deterministically, safe fixtures contain no machine identifiers, and local diagnostics are never accepted by `validate_receipt`.

### U4. Build the active-surface host-contract linter

Create a semantic-enough static gate that finds real host dependencies without treating the repository's historical record as executable.

**Goal:** Detect every issue #20 violation class with stable, reviewable findings and a narrow exemption mechanism.

**Requirements:** R8-R9; origin R23, AE4.

**Dependencies:** U1.

**Files:**

- `plugins/fleet-core/scripts/fleet_commons/host_contract_lint.py`
- `plugins/fleet-core/references/antigravity-host-contract-surfaces.json`
- `plugins/fleet-core/tests/test_host_contract_lint.py`
- `plugins/fleet-core/tests/fixtures/host-contract/active-*.md`
- `plugins/fleet-core/tests/fixtures/host-contract/historical-*.md`
- `plugins/fleet-core/tests/fixtures/host-contract/executable-*.py`
- `plugins/fleet-core/references/host-contract-lint.md`

**Approach:** Load and validate the closed active-surface selector defined above, then implement contextual rules for executable `.claude` paths, `AskUserQuestion`/`ToolSearch`, Workflow call syntax and active execution instructions, fixed brain roots, scheduling assertion verbs, and isolation assertion verbs. Parse line context and only the immediately preceding KTD11 annotation; emit `active`, `historical`, `foreign-runtime-input`, or `capability-gated` classifications with rule ID, path SHA-256, line, excerpt SHA-256, capability ID, bounded reason/remediation codes, and active-surface manifest digest. Unannotated matches in active surfaces are unresolved errors. Validate the resulting `antigravity.host-contract-lint.v1` object with the U3 sanitizer before it can be printed, persisted, or consumed.

**Patterns to follow:** Return structured findings and human-readable errors rather than booleans, as in `bridge_receipt.validate_receipt`; keep the scanner pure over injected paths and text. Follow the repository formatting contract for the rule reference.

**Test scenarios:**

1. Named rules — input one active fixture for each of the six required classes; scan; expect the exact stable rule ID and an unresolved result.
2. Historical evidence — place the same strings inside an explicitly marked source quotation/lineage block; expect `historical`, no unresolved result, and preserved classification output.
3. Active quote trap — place an executable instruction in a Markdown quote without a lineage annotation; expect it to remain active rather than be broadly suppressed.
4. Foreign runtime — annotate a read-only Claude/Codex input path with a reason and revisit condition; expect `foreign-runtime-input`; use the same annotation on a write path; expect rejection.
5. Capability gate — annotate an isolation claim with a catalog capability; evaluate with passed, unknown, and missing receipts; expect permitted, blocked, and invalid-gate results respectively.
6. False-positive controls — scan product names, `hermes-claude-code-router`, generic schedules, networking isolation prose, tests, changelogs, and historical plans; expect no active violation.
7. Exemption abuse — use missing reasons/revisit conditions, unknown rules/capabilities, non-adjacent annotations, file-wide wildcard annotations, or foreign-runtime annotations without `access=read-only`; expect the exemption to fail closed.
8. Selector abuse — use an absolute/traversing path, broad exclusion glob, missing exact adjacent file, unknown selector key, or out-of-repository root; expect selector validation to fail before scanning.
9. Promotable output — serialize a safe lint receipt and unsafe variants with raw excerpts, absolute paths, or machine identifiers; expect only the safe receipt to validate.

**Verification:** The fixture suite detects every issue-named active violation class, preserves historical/foreign classifications, and contains no broad ignored path or pattern list.

### U5. Port active Saga interaction and workflow language

Replace active Claude interaction and execution instructions with an Antigravity-native, capability-aware contract.

**Goal:** Remove unresolved `AskUserQuestion`, `ToolSearch`, direct Workflow invocation, and unproven scheduled-execution instructions from the selected Saga prompt, command, skill, and reference surfaces.

**Requirements:** R8-R10; origin R23, AE4.

**Dependencies:** U1, U4.

**Files:**

- `plugins/saga/skills/brainstorm/SKILL.md`
- `plugins/saga/skills/code-review/SKILL.md`
- `plugins/saga/skills/founder-review/SKILL.md`
- `plugins/saga/skills/founder-review/references/review-modes.md`
- `plugins/saga/skills/ideate/SKILL.md`
- `plugins/saga/skills/ideate/references/convergence-and-partnership.md`
- `plugins/saga/skills/investigate/SKILL.md`
- `plugins/saga/skills/loop/SKILL.md`
- `plugins/saga/skills/loop/references/drive-and-resume.md`
- `plugins/saga/skills/office-hours/SKILL.md`
- `plugins/saga/skills/optimize/SKILL.md`
- `plugins/saga/skills/outcome/SKILL.md`
- `plugins/saga/skills/plan/SKILL.md`
- `plugins/saga/skills/promote/SKILL.md`
- `plugins/saga/skills/qa/SKILL.md`
- `plugins/saga/skills/resume/SKILL.md`
- `plugins/saga/skills/retro/SKILL.md`
- `plugins/saga/skills/retro/references/retro-passes.md`
- `plugins/saga/skills/retro/references/self-edit-safety.md`
- `plugins/saga/skills/spec/SKILL.md`
- `plugins/saga/skills/strategy/SKILL.md`
- `plugins/saga/skills/work/SKILL.md`
- `plugins/saga/skills/work/references/execution-strategy.md`
- `plugins/saga/references/operator-choice.md`
- `plugins/saga/references/saga-spec.md`
- `plugins/saga/tests/test_saga_plugin.py`
- `plugins/saga/tests/test_saga_doc_formatting.py`

**Approach:** Replace the 82 platform-specific question-tool references with one shared Antigravity interaction rule: ask one blocking question through the current session, recommend an option when useful, and stop until the operator answers; a structured interaction surface may be used only when the capability receipt proves it. Remove direct `Workflow({ ... })` instructions and active routing to the Claude Workflow backend; preserve any source-lineage discussion only through explicit historical annotations. Rewrite cron/scheduling narration as externally repeated invocation unless a future receipt proves a scheduler. Update mechanism-floor tests to assert the semantic interaction behavior, not a Claude tool token.

**Patterns to follow:** Preserve each skill's existing one-question-per-turn and channel-inline behavior, but express it in Antigravity language. Use the current installed Saga operator-choice dimensions as semantic guidance while retaining Antigravity-native backend names and proven capabilities.

**Test scenarios:**

1. Interaction migration — scan all 23 listed instruction files; expect zero unresolved interaction-tool findings while each skill still requires one blocking question per turn and an explicit wait.
2. Workflow migration — scan `/work`, execution-strategy, operator-choice, and saga-spec; expect no active direct Workflow API call and no route that claims the backend ran without receipt proof.
3. Scheduling migration — scan `/outcome` and saga-spec; expect externally triggered repetition language or a named capability gate, not an asserted host scheduler.
4. Historical lineage — retain a quoted source comparison with an explicit reason; expect it classified historical and not executable.
5. Semantic regression — run existing Saga mechanism-floor and formatting tests; expect lifecycle questions, routing choices, and output structure to remain intact despite token replacement.

**Verification:** The host-contract linter reports no unresolved prompt/command/skill/reference interaction, Workflow, or scheduling findings in the selected active Saga surface, and Saga tests no longer require Claude-only tool names.

### U6. Repair executable roots and proof claims

Bring Antigravity-owned Python, hooks, and agent contracts into the same logical-root and observed-capability model.

**Goal:** Eliminate executable `.claude` writes, fixed brain-root defaults, and unconditional isolation guarantees while preserving explicit foreign-runtime read compatibility.

**Requirements:** R2, R6, R8-R10; origin R19, R23-R24.

**Dependencies:** U1-U4.

**Files:**

- `plugins/fleet-core/scripts/fleet_commons/delegation_state.py`
- `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py`
- `plugins/mission-control/scripts/sdlc_manager.py`
- `plugins/mission-control/tests/test_user_defaults.py`
- `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/validator-evidence-state.md`
- `plugins/multi-agent-consensus/tests/test_multi_agent_consensus_plugin.py`
- `plugins/saga/commands/retro.md`
- `plugins/saga/hooks/delegation_stop_audit_hook.py`
- `plugins/saga/hooks/delegation_tripwire_hook.py`
- `plugins/saga/scripts/board_progression.py`
- `plugins/saga/scripts/discover_sessions.py`
- `plugins/saga/scripts/execution_spec.py`
- `plugins/saga/scripts/lifecycle_state.py`
- `plugins/saga/scripts/outcome.py`
- `plugins/saga/scripts/outcome_dispatcher.py`
- `plugins/saga/scripts/outcome_spec.py`
- `plugins/saga/scripts/saga.py`
- `plugins/saga/agents/readonly-verifier.md`
- `plugins/saga/references/command_dry_runs.md`
- `plugins/saga/references/escape_hatches.md`
- `plugins/fleet-core/tests/test_fleet_commons.py`
- `plugins/saga/tests/test_state_paths.py`
- `plugins/saga/tests/test_outcome_dispatcher.py`
- `plugins/saga/tests/test_saga_saga.py`

**Approach:** Move Antigravity-owned delegation, audit, board, and retro state to injected logical `.gemini` roles. Keep a `.claude` path only when it is a read-only foreign-engine or one-time migration input, and annotate/test that boundary. Require `discover_sessions.py` to receive a root resolved by the doctor or explicit CLI argument rather than synthesizing a home path. Change isolation and sandbox structures to distinguish requested controls from observed enforcement; unknown required isolation halts. Quarantine legacy Claude Workflow generation from active Antigravity dispatch and preserve it only as explicitly classified source lineage until a separately proven host-native backend replaces it.

**Patterns to follow:** Preserve the canonical `.gemini/saga` state convention in `plugins/saga/tests/test_state_paths.py`, fleet-core injected-path tests, and the existing halt-not-degrade behavior in `plugins/saga/scripts/outcome_dispatcher.py`.

**Test scenarios:**

1. Antigravity state — invoke delegation, audit, board, retro, and session discovery with temporary logical roots; expect writes only under injected `.gemini` roots and no `.claude` write.
2. Foreign read compatibility — provide a declared Claude/Codex input root; expect bounded read-only discovery and an explicit `foreign-runtime-input` lint classification.
3. Brain discovery — omit the discovered brain role; expect an actionable unavailable result and no fallback to `Path.home()`.
4. Isolation proof — request disposable-worktree or read-only enforcement with passed, unknown, and failed capability results; expect dispatch, visible halt, and visible halt respectively.
5. Workflow quarantine — attempt to choose the legacy Claude Workflow route from active Antigravity orchestration; expect rejection before script emission or tool invocation.
6. Migration compatibility — provide legacy state plus a current target; expect one-way import/read behavior without new writes to the legacy path.
7. Full executable scan — lint all selected scripts, hooks, agents, and runbooks; expect zero unresolved root, Workflow, fixed-brain, schedule, or isolation findings.

**Verification:** No Antigravity-owned executable writes `.claude`, no home-derived brain default remains, required isolation uncertainty halts, and explicit foreign-runtime inputs remain bounded and reviewable.

### U7. Integrate the contract into the canonical plugin doctor

Compose package truth, capability truth, privacy, and host-language findings behind the existing command and output model.

**Goal:** Make `scripts/validate_plugins.py` report the complete host-contract result and return nonzero for the selected profile's required failures without making CI depend on a live model.

**Requirements:** R3-R5, R7-R12; origin R19-R24.

**Dependencies:** U1-U6.

**Files:**

- `scripts/validate_plugins.py`
- `tests/test_antigravity_plugin_doctor.py`
- `marketplace/validator/validate.py`
- `.github/workflows/ci.yml`
- `ANTIGRAVITY.md`
- `docs/PLUGIN_SPEC.md`

**Approach:** Extend `DoctorResult` with structured catalog, capability, receipt-privacy, and host-contract sections while preserving existing plugin entries, warnings, errors, next actions, and wrapper equivalence. Add `--capability-profile PROFILE`, `--capability-receipt PATH`, and `--observe-host`; runner, catalog, receipt, and local-state roots remain injectable Python seams for tests. Default to `repository-validation` with host observation disabled. `--observe-host` enables only the KTD10 passive registry and never starts a Gemini prompt, refreshes credentials, accesses a remote system, or mutates plugin/host state. Convert required failures for the selected profile and unresolved active lint findings into errors; optional unavailable capabilities remain visible and become degraded only through their declared fallback. Preserve exit `0` for passed or eligible degraded evaluation, exit `1` for validation/blocking failures, and argparse exit `2` for invalid invocation.

**Patterns to follow:** Retain `run_doctor` dependency injection, `--json`, human output, and error-driven exit semantics from `scripts/validate_plugins.py`. Preserve compatibility-wrapper equality from `tests/test_antigravity_plugin_doctor.py`.

**Test scenarios:**

1. Repository CI — run with no `agy` executable and the repository-validation profile; expect deterministic catalog/lint/privacy checks, unavailable runtime observations, and success when no repository-required check fails.
2. Observation opt-in — run the same default with an injected runner and no `--observe-host`; expect zero runner calls, then add `--observe-host`; expect only registered passive calls and unavailable results for commands that cannot prove no durable writes.
3. Required runtime failure — inject a receipt with a failed or unknown capability required by `live-canary`; run that profile; expect nonzero exit and the exact blocking capability in human/JSON output.
4. Optional degradation — inject an unavailable optional capability with a proven fallback; expect zero exit when no required failure exists plus explicit degraded/fallback output.
5. Lint failure — add an active violating fixture to the selected surface; expect nonzero exit and path/rule/line remediation in both output formats.
6. Privacy failure — inject an otherwise valid promoted receipt containing a home path or credential-shaped value; expect nonzero exit without echoing the unsafe value.
7. Backward behavior — validate existing manifest, empty agent, symlink, strict-install, stale-spec, and wrapper cases; expect unchanged results.
8. Live safety — intercept runner calls from the default command; expect no model prompt, credential refresh, plugin install/enable/disable, remote mutation, or unsanctioned write.

**Verification:** `python3 scripts/validate_plugins.py` reports capability-receipt and host-contract checks, CI remains deterministic, the wrapper is equivalent, and required profile failures return 1.

### U8. Add the direct Saga consumer and complete conformance documentation

Prove that a real adjacent plugin uses the same receipt and state semantics before downstream reliability children depend on it.

**Goal:** Provide a production-facing Saga gate for a named consumer and document the reusable contract, without turning the receipt into Saga lifecycle authority.

**Requirements:** R4, R7, R13; origin R22-R24, AE2, AE13.

**Dependencies:** U1, U3, U7.

**Files:**

- `plugins/saga/scripts/host_capability_gate.py`
- `plugins/saga/tests/fixtures/host-capabilities/*.json`
- `plugins/saga/tests/test_saga_plugin.py`
- `plugins/saga/tests/test_state_paths.py`
- `plugins/fleet-core/README.md`
- `plugins/fleet-core/plugin.json`
- `plugins/fleet-core/CHANGELOG.md`
- `plugins/mission-control/plugin.json`
- `plugins/mission-control/CHANGELOG.md`
- `plugins/multi-agent-consensus/plugin.json`
- `plugins/multi-agent-consensus/CHANGELOG.md`
- `plugins/saga/plugin.json`
- `plugins/saga/CHANGELOG.md`
- `ANTIGRAVITY.md`
- `docs/PLUGIN_SPEC.md`
- `docs/engineering-journal/LEARNINGS.md`

**Approach:** Add a narrow Saga adapter with `--consumer PROFILE`, `--receipt PATH`, and optional `--json`. It resolves fleet-core through the vendored shim, validates the receipt and catalog, invokes `evaluate_for_consumer`, and returns the shared result with exit `0` for `passed` or eligible `degraded`, exit `1` for blocked/invalid evidence, and argparse exit `2` for invalid invocation. It may resolve a receipt path and format output, but it must not rename states, copy schema fields, write tracked evidence, or mark a Saga phase complete. Add fixtures for one phase requiring independent agent execution with isolated sequential fallback, and for required unknown behavior that blocks. Document profile selection, local diagnostic location, promoted receipt restrictions, and how later reliability children consume the gate. Bump only the materially changed plugin manifests, update their changelogs, and prove every manifest version and package description matches the shipped runtime surface.

Use the next non-conflicting minor versions from the implementation branch's rebased `origin/main`; the reviewed baseline is:

| plugin | reviewed version | planned version |
|---|---:|---:|
| fleet-core | `0.8.1` | `0.9.0` |
| saga | `1.3.0` | `1.4.0` |
| mission-control | `2.6.3` | `2.7.0` |
| multi-agent-consensus | `2.2.0` | `2.3.0` |

If `origin/main` advances one of these versions before U8, rebase first and select the next minor version rather than overwriting or decrementing the newer release.

**Patterns to follow:** Use `plugins/saga/scripts/fleet_commons_shim.py` without modification and mirror the no-translation consumer pattern used for fleet-core tier primitives. Record empirical implementation findings in the engineering journal only after tests establish them.

**Test scenarios:**

1. Direct consumption — load a valid receipt through the Saga adapter for a named phase; expect byte-for-byte state vocabulary and blocking/degraded lists from fleet-core.
2. Sequential fallback — mark agent execution unavailable and isolated sequential execution passed/optional fallback; expect `degraded` only when the phase contract declares that fallback optional and sufficient.
3. Required uncertainty — mark a required phase capability unknown; expect nonzero exit and no Saga state mutation.
4. Schema drift — provide an unknown receipt schema or catalog digest; expect rejection before consumer evaluation.
5. Privacy boundary — provide a local diagnostic file where a promoted receipt is required; expect rejection and no raw data in output.
6. Resolution failure — make fleet-core unavailable; expect a clear installation/remediation error and no fallback schema copy.

**Verification:** A Saga integration fixture consumes the fleet-core receipt without state translation, required uncertainty blocks, optional fallback remains explicit, and the full targeted validation command set passes.

---

## Workflow Structure

Implementation uses a root-owned Verified Workflow because the change crosses shared contracts, privacy enforcement, active prompts, executable runtime state, and the canonical validator. The root remains the sole writer, Git owner, integrator, and completion authority; delegated profiles perform bounded scanning and fresh-root review only.

The canonical execution contract is the `## Workflow Contract` immediately below. This reviewed contract is plan revision `2`; any material graph, role, profile, model, effort, context, write, completion, check, fallback, external-action, or authority change requires explicit operator approval.

---

## Workflow Contract

### Assignments

| id | depends | parent | role | profile | model | effort | context | writes | completion | fallback |
|---|---|---|---|---|---|---|---|---|---|---|
| root-contract | none | root | root implementer | root | gpt-5.6-sol | high | root | unit:U1,unit:U2,unit:U3 | U1-U3 complete with typed contract tests passing and no out-of-scope paths | none |
| root-linter | root-contract | root | root implementer | root | gpt-5.6-sol | high | root | unit:U4 | U4 complete with every named rule and classification fixture passing | none |
| scan-contract | root-linter | root | security-scanner | scan_low | gpt-5.6-terra | low | none | none | assignment-result.v1 identifies injection, secret, unsafe-execution, and unsafe-exemption findings | none |
| root-instructions | root-linter,scan-contract | root | root implementer | root | gpt-5.6-sol | high | root | unit:U5 | U5 complete with zero unresolved instruction, Workflow, and scheduling findings | none |
| root-runtime | root-instructions | root | root implementer | root | gpt-5.6-sol | high | root | unit:U6 | U6 complete with zero unresolved executable-root or proof-claim findings | none |
| root-integration | root-runtime | root | root implementer | root | gpt-5.6-sol | high | root | unit:U7 | U7 complete with canonical human and JSON doctor behavior proven | none |
| root-consumer | root-integration | root | root implementer | root | gpt-5.6-sol | high | root | unit:U8 | U8 complete with direct Saga receipt consumption and validation ladder passing | none |
| review-adversarial | root-consumer | fresh-root:review-adversarial | devils-advocate-reviewer | review_high | gpt-5.6-sol | high | none | none | reviewer-result.v1 adjudicates correctness, scope, failure handling, and regression risk | none |
| review-privacy | root-consumer | fresh-root:review-privacy | privacy-reviewer | review_high | gpt-5.6-sol | high | none | none | reviewer-result.v1 adjudicates local versus promoted evidence and privacy rejection coverage | none |
| root-remediation | review-adversarial,review-privacy | root | root implementer | root | gpt-5.6-sol | high | root | unit:review-remediation | every P0-P3 finding is fixed or evidence-reclassified and all affected focused plus full checks pass | none |
| root-release | root-remediation | root | root orchestrator | root | gpt-5.6-sol | high | root | unit:delivery | scoped atomic commits and PR CI pass, merge completes, and origin/main readback contains the merge | none |

`unit:U1` through `unit:U8` resolve to the exact production, test, fixture, and directly affected documentation paths in each unit's **Files** field. `unit:review-remediation` is restricted to those same declared paths and the durable review/code-review artifacts. `unit:delivery` is restricted to plugin version/changelog metadata, work-session evidence, and root-owned Git/PR/merge operations; it excludes `.serena/project.yml` and every unrelated pre-existing path.

### Blocking Checks

| id | owner | after | command-or-proof | blocking | failure |
|---|---|---|---|---|---|
| check-contract | root | root-contract | U1-U3 focused pytest results plus catalog and receipt schema validation | yes | Return to the failing contract unit; no remediation may weaken closed states or privacy boundaries |
| check-host-lint | root | root-runtime | Host-contract linter machine output reports zero unresolved findings across the selected active surface | yes | Return to U4-U6; exemptions require a reasoned classification and matching fixture |
| check-validation | root | root-consumer | Validation Plan commands pass and canonical doctor human and JSON exit semantics agree | yes | Return to the owning unit with a fresh attempt; do not waive required failures |
| check-review-assurance | root | root-remediation | Fresh-root reviewer-result.v1 objects validate and every P0-P3 finding is fixed or explicitly reclassified with evidence | yes | Reopen the owning unit and rerun both affected checks and independent review |
| check-workspace-audit | root | root-release | Root pre/post audit proves only plan-declared paths changed and Git metadata remained root-owned | yes | Block integration, classify foreign edits, and restore or carry forward only attributable work |
| check-delivery | root | root-release | Targeted and full validation pass on the final diff; PR checks succeed; GitHub merge SHA equals origin/main ancestry; issue #20 remains open for QA/closure | yes | Do not claim merge completion; repair the failing check or merge/readback drift and rerun delivery proof |

### External Actions

External actions: []

No external model/provider action is part of this workflow. Root-owned GitHub PR and merge operations are delivery actions authorized by the selected `merge` destination, not advisory provider actions; they occur only in `root-release` after review and validation. The Saga plan-stage external-action helper is absent in this repository, and ungoverned provider substitution is forbidden.

---

## Sequencing and Checkpoints

The work should land in dependency order so later units never invent their own states or probe semantics.

1. **[SEQ] Contract foundation:** U1, then U2, then U3.
2. **[SEQ] Static policy:** U4 after the capability IDs and evaluation semantics are stable.
3. **[SEQ] Active remediation:** U5 and U6 are conceptually independent after U4, but the selected Verified Workflow executes them sequentially under the sole root writer so workspace attribution remains unambiguous.
4. **[SEQ] Canonical integration:** U7 after both remediation units reach zero unresolved findings.
5. **[SEQ] First consumer and closure:** U8 after the canonical doctor output and exit contract are stable.
6. **[SEQ] Assurance and delivery:** run both fresh-root reviews, remediate every actionable finding, rerun the complete validation ladder, then open, verify, and merge the scoped PR with origin/main readback.

At each unit boundary, commit only that unit's production paths, tests, and directly affected documentation. Do not include the existing unrelated `.serena/project.yml` change.

---

## Reviewability and Delivery Boundary

Issue #20 remains one capability and one PR, but review is segmented into eight atomic commits and blocking checkpoints.

Each commit corresponds to exactly one U-ID, includes that unit's tests and directly affected documentation, and is independently inspectable. U7 does not activate the doctor gate until U1-U6 agree, and U8 closes the shared-consumer proof and release metadata. If any unit cannot pass its focused checkpoint without borrowing unreviewed work from a later unit, stop and amend the plan rather than creating a mixed-purpose commit.

The single-PR exception is deliberate: merging the catalog without an active consumer produces unused policy, merging prompt/runtime remediation without the selector and gate permits immediate drift, and merging the doctor without the complete remediation would make CI fail. Unit commits, the zero-unresolved checkpoint, two fresh-root reviews, and the final workspace audit bound review risk without adding coordination-only sub-issues.

---

## System-Wide Impact

**Shared contract:** `fleet-core` becomes the authority for Antigravity capability identities, receipt states, and consumer evaluation. Later issues #16, #15, #19, #23, and #22 must reference this interface rather than define local capability booleans.

**Runtime state:** Rich probe diagnostics are volatile `.gemini` state. Promotable receipts are evidence artifacts, not lifecycle state and not permission to mutate a repository, GitHub, installed plugins, or the host.

**Failure propagation:** A malformed catalog or receipt fails before probing. A required failed/unknown/unavailable capability blocks only consumers that declare it required. An optional unavailable capability remains visible and can degrade only through a predeclared, proven fallback.

**Compatibility:** Existing package/install validation and the marketplace wrapper remain stable. Legacy `.claude` inputs may be read only through explicit migration or foreign-runtime classifications; Antigravity-owned writes move to logical `.gemini` roles.

**Privacy:** The promotable schema is closed and value-sanitized. Downstream consumers receive only logical roles, path digests, bounded facts, and stable reason codes, never a raw command, raw path, or transcript record.

---

## Prerequisite and Unlock Map

The work has no hard upstream implementation dependency, but its evidence and downstream consumers are explicit.

| relationship | item | current state | execution rule |
|---|---|---|---|
| Authoritative input | Issue #20 plus R19-R24 and AE1/AE2/AE4/AE12/AE13 | Requirements-ready and planned | Any scope change must amend the issue/requirements mapping before code |
| Repository prerequisite | Existing canonical `scripts/validate_plugins.py`, fleet-commons shim, and ignored `.gemini/` root | Present and locally verified | Preserve wrapper and shim compatibility; do not create a second doctor |
| Optional live evidence | Local `agy`/Antigravity runtime | May be absent, unauthenticated, or unable to prove non-mutation | Deterministic work continues; explicit live observations remain unavailable until safely proven |
| Downstream unlock | #16 lifecycle reconciler | Open child | Consume the shared receipt/evaluator after issue #20 merges |
| Downstream unlock | #15 semantic port ledger | Open child | Use host-contract findings and capability IDs rather than local booleans |
| Downstream unlock | #19 Gemini deliberation | Open child | Use agent/sequential-isolation capability and fallback semantics |
| Downstream unlock | #23 artifact promotion | Open child | Reuse logical roots and promoted-evidence privacy rules |
| Downstream unlock | #22 conformance lab/canary | Open child | Select explicit profiles and preserve exact capability/lint receipts |

No cloud account, secret, vendor approval, sibling-repository mutation, installed-plugin change, or paid model call is a prerequisite for deterministic implementation and CI.

---

## Risks and Dependencies

| risk or dependency | impact | mitigation |
|---|---|---|
| Linter false positives classify lineage as active | The gate becomes noisy and developers add unsafe suppressions | Use explicit active roots, contextual rules, adjacent reasoned annotations, excerpt hashes, and paired active/historical fixtures |
| Linter false negatives miss renamed host dependencies | Unsupported behavior remains executable despite a green check | Use semantic rule fixtures for assertion verbs and API syntax, scan linked references and executable scripts, and preserve zero-unresolved inventory tests |
| Probe execution mutates host or remote state | A diagnostic damages user state or spends model/API resources | Fixed registry, injected runner, list argv, timeouts, no shell, deterministic default profile, and explicit opt-in for controlled behavior |
| A nominally read-only `agy` command refreshes credentials or writes logs/cache | Explicit observation still mutates durable host state | Require proof that durable writes and remote access are disabled or redirected to injected temporary state; otherwise emit `unavailable` and use controlled evidence |
| Local AGY auth or sandbox restrictions make observations noisy | Host facts are mistaken for failures or the command crashes | Convert missing auth/permissions/write access into named unknown/unavailable results and keep raw errors local |
| Promoted evidence leaks private machine data | Receipts cannot be safely committed or shared | Closed schema, field/value sanitizer, unsafe fixtures, size bounds, and separate local-diagnostic type |
| Consumer profiles drift | Different plugins interpret the same host state differently | Store `required_for` and fallback policy in the canonical catalog and require direct evaluator use through fleet-core |
| U5/U6 expand into a general Saga rewrite | Foundation work stalls and overlaps later children | Limit changes to unresolved issue #20 rules and the minimum semantic preservation tests; defer lifecycle settlement and deliberation orchestration |
| JSON-compatible YAML surprises maintainers | Catalog edits use unsupported YAML features | Document the subset in fleet-core README/reference docs, keep the catalog itself comment-free JSON syntax, and validate with a clear error that names the stdlib runtime constraint |
| Active-surface selector drifts or hides violations | A new executable surface bypasses the gate or a broad exclusion suppresses evidence | Version and validate the selector, reject broad exclusions, require exact adjacent paths to exist, and bind every lint receipt to its selector digest |
| Current repository Saga engine uses older backend vocabulary than the installed planning skill | The plan's execution metadata and target runtime can diverge | Use the installed current Saga engine for planning ticks; treat target-source backend cleanup as U5/U6 implementation work |

---

## Alternatives Considered

| alternative | decision |
|---|---|
| Hard-code supported `agy` and Antigravity versions | Rejected because it fails AE1 and cannot detect a broken known version |
| Put shell command templates in the YAML catalog | Rejected because it creates an injection and side-effect boundary |
| Use PyYAML in fleet-core | Rejected because installed fleet-core is explicitly stdlib-only and marketplace installation provides no dependency environment |
| Treat every capability as globally required | Rejected because repository CI, a Saga phase, and a live canary have different legitimate requirements |
| Store raw and promoted evidence in one schema | Rejected because a flag or caller mistake could commit private diagnostics |
| Ignore `docs/`, `references/`, or all `.claude` tokens | Rejected because active skills consume references and executable foreign paths require semantic classification |
| Add a second host-doctor CLI under fleet-core | Rejected because the repository already established `scripts/validate_plugins.py` as canonical |
| Translate receipt states in Saga | Rejected because it recreates the consumer-drift failure the shared contract is meant to prevent |

---

## Scope Boundaries

### In Scope

- Issue #20 and origin requirements R19-R24 with AE1, AE2, AE4, AE12, and AE13.
- The canonical probe catalog, safe registry, versioned receipt, consumer evaluation, local diagnostics, and promoted-evidence sanitization.
- Active-surface linting for Saga, fleet-core, mission-control, multi-agent-consensus where applicable, and the active port runbook.
- Remediation required for a truthful zero-unresolved issue #20 lint gate.
- Extension of the existing validator and one direct Saga consumer fixture.

### Deferred to Follow-Up Work

- Full proof-carrying lifecycle settlement and `/outcome` reconciliation (#16).
- Complete semantic port inventory and survivor migration (#15).
- Receipt-backed Gemini deliberation execution (#19).
- Canonical artifact promotion (#23).
- Transcript-derived conformance laboratory and live release canary (#22).
- Broader live qualification matrices across models, versions, hosts, and lifecycle routes.

### Non-Goals

- Choosing port survivors, modifying sibling source repositories, or implementing rejected source deltas.
- Raw transcript collection or committing private histories.
- Automatically installing/enabling plugins, changing credentials, invoking paid model work in deterministic CI, or mutating remote systems.
- Claiming scheduler, concurrency, isolation, sandbox, model, effort, or agent behavior that a catalog probe cannot establish.
- Rewriting historical lifecycle artifacts merely because they quote Claude or Codex source behavior.

---

## Success Metrics

- Every catalog and receipt fixture validates or fails for a named deterministic reason.
- Supported command flags are recorded as normalized observations without being treated as behavioral proof.
- Unseen-version success and known-version behavioral failure pass the issue's required tests.
- Every named active violation class has positive and historical/false-positive fixtures.
- The selected active surface has zero unresolved host-contract findings.
- Unsafe promoted capability and lint fixtures containing home paths, credentials, hostnames, transcripts, excerpts, or raw diagnostic fields are rejected without echoing unsafe values.
- `python3 scripts/validate_plugins.py` reports capability and lint sections and returns nonzero for repository-required failures.
- Default repository validation invokes no `agy` subprocess; explicit observation never performs a model call, credential refresh, remote mutation, or durable host-state write.
- A Saga integration fixture consumes the same fleet-core evaluation without translating states.
- Every materially changed plugin manifest and changelog describes the shipped runtime surface, and the compatibility wrapper remains output/exit equivalent.

---

## Validation Plan

Run checks from narrow contract tests to repository-wide gates so failures stay attributable.

1. Contract and linter:
   - `uv run pytest plugins/fleet-core/tests/test_antigravity_capabilities.py -q`
   - `uv run pytest plugins/fleet-core/tests/test_host_contract_lint.py -q`
2. Fleet and Saga integration:
   - `uv run pytest plugins/fleet-core/tests -q`
   - `uv run pytest plugins/saga/tests/test_saga_plugin.py plugins/saga/tests/test_saga_doc_formatting.py plugins/saga/tests/test_state_paths.py -q`
   - `uv run pytest plugins/mission-control/tests/test_user_defaults.py plugins/multi-agent-consensus/tests/test_multi_agent_consensus_plugin.py -q`
   - Run the focused outcome/dispatch tests named in U6 when isolation or backend behavior changes.
3. Canonical command behavior:
   - `python3 scripts/validate_plugins.py`
   - Assert through `tests/test_antigravity_plugin_doctor.py` that the default command makes zero host-runner calls and that `--observe-host` invokes only passive registered probes.
   - Run the same command with injected failing required, unknown required, and optional-fallback receipts; assert exit status and human/JSON equivalence.
   - `python3 marketplace/validator/validate.py`
4. Static quality:
   - `uv run ruff check plugins/fleet-core plugins/saga plugins/mission-control plugins/multi-agent-consensus scripts/validate_plugins.py tests/test_antigravity_plugin_doctor.py`
   - `uv run mypy plugins/fleet-core plugins/saga plugins/mission-control plugins/multi-agent-consensus scripts/validate_plugins.py tests/test_antigravity_plugin_doctor.py`
   - `uv run bandit -r plugins/fleet-core plugins/saga plugins/mission-control plugins/multi-agent-consensus scripts/validate_plugins.py -x '*/tests/*'`
5. Final regression:
   - `git diff --check`
   - `uv run pytest -q`
   - `python3 scripts/validate_plugins.py --json` and verify that no promoted receipt field contains raw diagnostic data.
   - `git check-ignore .gemini/saga/capability-doctor/example.json`

No deterministic validation step may initiate a Gemini prompt, mutate installed plugin state, access a remote system, or write outside injected temporary/ignored local roots.

---

## Sources / Research

- `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`
- `docs/ideation/2026-06-27-antigravity-harness-ideation.md`
- `docs/engineering-journal/DECISIONS.md`
- `docs/engineering-journal/LEARNINGS.md`
- `STRATEGY.md`
- `scripts/validate_plugins.py`
- `tests/test_antigravity_plugin_doctor.py`
- `plugins/fleet-core/README.md`
- `plugins/fleet-core/scripts/fleet_commons/bridge_receipt.py`
- `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py`
- `plugins/fleet-core/scripts/fleet_commons_shim.py`
- `plugins/saga/scripts/provenance_manifest.py`
- `plugins/saga/scripts/discover_sessions.py`
- `plugins/saga/scripts/execution_spec.py`
- `plugins/saga/tests/test_state_paths.py`
- GitHub issue `infiquetra/infiquetra-antigravity-plugins#20`
- Local read-only observations on 2026-07-26: `agy` CLI 1.1.7, Antigravity app 2.3.1, available CLI flags, imported plugin list, and plugin validation output. These observations seed probes but do not establish permanent support.
