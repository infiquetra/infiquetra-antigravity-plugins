---
title: Migrate Every Approved Port Survivor Natively
type: feat
status: approval-ready
revision: 2
date: 2026-07-30
origin: docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md
linked_issue: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/15
ledger: docs/ports/2026-07-30-saga-reliability/ledger.yaml
---

# Migrate Every Approved Port Survivor Natively

## Summary

Migrate the exact 51 `approved-survivor` stable IDs from the fully decided Saga reliability
semantic port ledger into the existing Antigravity plugin portfolio. Preserve each useful outcome,
but implement it with Antigravity terminology, Gemini controls, repository-canonical artifacts,
current host-capability evidence, and deterministic target-side tests.

This is not 51 file-copy jobs. The ledger says 41 survivors are already partial and 10 are absent.
Several partial survivors need only a documented native adaptation and stronger target evidence;
the absent survivors need new target behavior. Source paths are provenance, never target design.

The target remains the existing `fleet-core`, `mission-control`, `multi-agent-consensus`, and
`saga` plugins. Source `team-execution` behavior maps to `multi-agent-consensus`. No new plugin,
sibling-repository write, installed-plugin change, host mutation, issue or board mutation,
deployment, or opportunistic non-survivor work is authorized.

## Grounded Inputs and Gate

The canonical ledger is fully decided and currently validates. Its exact decision counts are:

| decision state | count | implementation scope |
|---|---:|---|
| `approved-survivor` | 51 | in scope |
| `blocked` | 19 | not in scope |
| `metadata-only` | 8 | not in scope |
| `rejected` | 1 | not in scope |
| `superseded` | 1 | not in scope |
| total | 80 | complete candidate universe |

The 51 approved rows have 41 `partial` and 10 `absent` Antigravity states. Their decided v1 rows
currently have empty `required_host_capabilities` lists, but that historical classification is not
implementation proof. The current sanitized receipt reports `agy.agent.execution` and
`agy.sequential.isolation` as `unavailable`. The plan therefore observes the host again before any
implementation assignment and again before migration recording, then applies the five-row
capability audit in KTD8. The receipt is bound by catalog digest
`8c65e3bc2a97878804645443541624c255ee89a716f89e5b098b54f1bcf62ae4` and receipt
SHA-256 digest
`ddebb99594afce219ca44a818097a5a163f2e2bd8c1cc62a65e194101e2726b0`.

The implementation gate is set equality, not a count alone:

```text
plan traceability IDs
  == ledger IDs where decision.state == approved-survivor
count(plan IDs) == count(unique(plan IDs)) == 51
plan IDs intersect ledger non-survivor IDs == empty set
```

`plugins/saga/tests/test_port_ledger.py` will encode this equality against the real campaign ledger.
Any missing, duplicate, extra, newly pending, or newly blocked ID stops implementation. The ledger
remains the decision authority; this plan does not edit its decisions.

GitHub issue #16 is the satisfied prerequisite that supplied this fully decided ledger. GitHub
issue #20 supplies the host-capability catalog and sanitized receipt evaluated per survivor.
GitHub issue #22 remains downstream and cannot begin release qualification until this issue
delivers all 51 migration receipts.

## Requirements

R1. Implement only the 51 stable IDs in the traceability table. A count match without exact ID-set
equality fails.

R2. Preserve each ledger `semantic_contract` as the useful outcome. Source file names, package
layouts, prompt text, and source tests are evidence inputs, not acceptance criteria.

R3. Put each behavior in the Antigravity product boundary named in the table. In particular,
source `team-execution` maps to `multi-agent-consensus`; a target `team-execution` plugin or path is
forbidden.

R4. Use Antigravity and Gemini terminology. Model and effort choices must resolve through
`fleet-core`'s current Gemini registry and effort seam. Do not embed source-host model names,
Claude workflow APIs, `AskUserQuestion`, executable `.claude` paths, fixed brain roots, or
unproven scheduling, sandbox, isolation, agent, model, or effort claims.

R5. Independent execution may be claimed only when the current safe host observation reports
`agy.agent.execution=passed`. An isolated sequential fallback may be claimed only when
`agy.sequential.isolation=passed`. Where the semantic contract only consumes typed evidence,
deterministic non-agent validation is allowed but must not be described as independent execution.
Where independence is semantically required, a non-passing capability makes that migration row
`blocked`; prose, fixtures, role play, or a weaker fallback cannot replace the capability.

R6. Repository documents under the established `docs/` and `plugins/saga/docs/` contracts are
authoritative. Antigravity brain or host-local state may stage or project work, but cannot be the
only durable artifact or migration evidence.

R7. Define `antigravity.semantic-port-ledger.v2`. Version 1 remains valid exactly as it is and may
not carry migration fields. A deterministic v1-to-v2 upgrade preserves every campaign field,
snapshot, edit packet, candidate, ranking, rationale, revisit trigger, decision, and packet
ordering; it changes only the root schema and adds the closed `migration` object to the exact 51
approved rows from the closed migration-plan mapping. Migration-bearing data labeled v1 and every
unknown schema version fail before mutation. Non-survivors cannot carry implementation targets or
migration evidence.

R8. Migration states are `planned`, `migrated`, and `blocked`. The operator's semantic
`decision.state` remains `approved-survivor`; migration state records delivery without erasing the
decision history. A row can become `migrated` only through the atomic migration-recording command
after all named target tests and blocking checks pass. The same atomic transition changes
`antigravity_state` from `partial` or `absent` to `present` or
`intentional-divergence`; a migrated row may not remain partial or absent.

R9. A newly required capability in `failed`, `unknown`, or `unavailable` state changes that
survivor's Antigravity state to `blocked-by-host`, proposed disposition to `blocked`, and migration
state to `blocked`. It retains the approved semantic decision and a concrete revisit trigger. No
automatic fallback or migration receipt is allowed.

R10. Each migrated row must bind every ledger-owned edit packet automatically, name exact
Antigravity target files plus its exact positive and negative Pytest node IDs, record intentional
Claude/Codex differences, and bind the one closed content-addressed migration-evidence manifest.
That manifest contains the normalized full result content needed for validation; `record-migrations`
must not infer a result, verdict, check, finding, changed path, or test status from an opaque digest.
Text similarity, source-test parity, or a copied source path is not evidence.

R11. `scripts/validate_plugins.py`,
`plugins/fleet-core/references/antigravity-host-contract-surfaces.json`,
`plugins/fleet-core/scripts/fleet_commons/host_contract_lint.py`, and
`plugins/fleet-core/tests/test_host_contract_lint.py` are the single host-lint policy and
implementation. The canonical selector must include every changed active Saga, Fleet Core,
Mission Control, and Multi-Agent Consensus runtime path from the closed migration-plan mapping.
The test asserts selector equality with that mapping and rejects a narrowed selector. No second
lint implementation is allowed.

R12. Release-drift refresh is fail-closed. Before implementation and again after recheck,
immediately before migration recording, repeat
issue #16's local read-only discovery against matching Claude and Codex `HEAD` and
`origin/main`, and Antigravity `origin/main` with feature `HEAD` recorded separately. Any changed
snapshot, packet identity, selected surface, semantic input, or required host receipt returns
affected decisions to `pending` under the ledger contract and stops this issue for renewed operator
review. The final refresh emits a typed assignment result and source/host binding that the evidence
manifest includes. Changed result bytes, changed evidence-manifest bytes, or any operator-gate reset
makes `record-migrations` fail with the ledger bytes unchanged. Only byte-identical evidence
preserves the current approval.

R13. Preserve sibling repositories, installed plugins, user configuration, and host state.
`.serena/project.yml` is operator-owned and excluded from every write set, check, commit, and PR.

R14. Complete origin requirements R15-R17, flow F1's post-approval half, and acceptance example
AE4 without pulling in issue #22 release qualification or any issue #16 decision change.

## Key Technical Decisions

KTD1. **Version the ledger without replacing decision authority.**
`antigravity.semantic-port-ledger.v1` remains a valid, closed, decision-only schema.
`antigravity.semantic-port-ledger.v2` is the only schema that may carry migration evidence.
`decision.state` continues to answer what Jeff approved. The new closed `migration` object answers
whether Antigravity implementation and evidence are complete. The campaign ledger remains the one
canonical authority; `migration-plan.v1.yaml` and `migration-evidence.v1.json` are closed,
digest-bound inputs, never competing decision stores.

KTD2. **Upgrade and record atomically.** Add `upgrade-v2`, `record-migrations`, and
`validate --require-migrated` to `scripts/port_ledger.py`.

- `upgrade-v2 LEDGER migration-plan.v1.yaml` accepts only a valid v1 ledger and the closed exact
  51-ID plan. It deep-copies the parsed v1 data, verifies that re-serializing every preserved
  decision and packet subtree is byte-for-byte canonical-equivalent, changes only `schema`, and
  adds `planned` migration objects. Repeating the command on the same inputs is byte-identical.
- A valid v1 ledger remains accepted by ordinary `validate` and `report`. A v1 document carrying
  `migration`, a v2 document missing the migration rules, and any unknown version fail.
- `record-migrations` accepts the v2 ledger, the exact 51-ID plan, and
  `migration-evidence.v1.json`. It validates the full typed evidence content and recomputes every
  digest. It rejects partial or extra IDs, non-survivors, failed or skipped required tests, stale
  host or source bindings, missing target files, missing test node IDs, unsafe paths, invalid final
  Antigravity state, and any `blocked` row. Either all eligible rows transition or the original
  ledger bytes remain unchanged.

KTD3. **Keep target design small.** Reuse existing Antigravity modules and tests for partial
survivors. Add a new module only for an absent semantic boundary or when combining it with an
existing module would mix product ownership. Shared evidence and compatibility primitives live in
`fleet-core`; GitHub and project behavior lives in `mission-control`; reviewer behavior lives in
`multi-agent-consensus`; lifecycle behavior and canonical Saga docs live in `saga`.

KTD4. **Make canonical docs a maintained model.** `codex-portability-contracts` becomes a curated
Antigravity portability page and model entry under `plugins/saga/docs/`, not a copy of Codex's
`docs/portability` tree. The Saga docs model must call Antigravity the source of truth and use
current target backend names.

KTD5. **Treat deterministic evidence as behavior proof.** Every survivor has one named positive
semantic test and at least one meaningful negative path in its owning unit. Negative coverage
includes malformed evidence, missing ownership, host mismatch, unsupported mutation, stale
receipt, source-host vocabulary, and incomplete pagination or settlement as applicable.

KTD6. **Do not infer host support during implementation.** The current approved set requires no
host capabilities. If implementation discovers that a useful outcome truly needs a capability,
the ledger must name it and the current receipt must pass it. An unavailable requirement blocks
the row instead of authorizing a synthetic Python, prompt, or sequential fallback.

KTD7. **Preserve the previously approved autonomy boundary.** One directly blocking,
implementation-caused defect inside the declared write-set union may receive one bounded
remediation and one targeted recheck. A failed recheck, second defect, new dependency, new schema
version beyond the approved v2 edge, new plugin, broader product boundary, changed survivor set,
new outcome edge, credential
need, installation, deployment, destructive action, or sibling write returns to Jeff.

KTD8. **Audit the five independence-sensitive rows against the current host.** Before execution,
run the safe passive observation:

```bash
python3 scripts/validate_plugins.py \
  --capability-profile repository-validation \
  --observe-host \
  --json
```

This command may perform only the registered passive observations. It may not prompt a model,
refresh credentials, access a remote system, install or enable a plugin, or persist host state.
The resulting sanitized receipt is evaluated as follows:

| stable ID | independence interpretation | exact capability gate or deterministic proof |
|---|---|---|
| `application-security-audit` | The approved semantic contract requires bounded findings and validation evidence, not a claim that Antigravity spawned an independent reviewer. | Deterministically validate the closed request, findings, checks, and reviewer identity fields. If the workflow is asked to originate an independent reviewer, require `agy.agent.execution=passed`; otherwise state that independence was not performed. |
| `saga-code-review` | The migrated command compares a plan and implementation and validates typed findings. It does not itself create independent execution. | Deterministically compare committed inputs and validate an imported `reviewer-result.v1`. Any mode that originates an independent review requires `agy.agent.execution=passed`. |
| `saga-ideation` | Distinct perspectives may be explicit operator-supplied inputs; distinct does not mean independently executed. | Validate separately identified seed, alternative, disagreement, and convergence records. Do not call them independent. An independent multi-agent mode requires `agy.agent.execution=passed`; a sequential-isolation fallback also requires `agy.sequential.isolation=passed`. |
| `saga-lifecycle-settlement` | Independence is semantically required for a receipt that satisfies an obligation marked `independence: required`. | Settlement may deterministically consume an already independent, identity-bound receipt. If Saga must originate that receipt, require `agy.agent.execution=passed`; a non-passing state blocks only that origin mode and can never be replaced by a self-issued fixture or narration. |
| `saga-quality-assurance` | “Without self-certification” requires different producer and validator identities, not necessarily host-created agents. | Validate distinct typed producer/tester identities and exact executed test nodes. A mode that asks Antigravity to originate the tester requires `agy.agent.execution=passed`; otherwise consume an externally supplied typed tester result without claiming host independence. |

The current receipt has both named capabilities `unavailable`. Therefore no implementation or test
may claim host-created independence or sequential isolation. A future passing safe observation may
unlock those modes without changing the deterministic consumer behavior.

### Closed migration object

Every approved row receives this exact closed shape after the deterministic v1-to-v2 upgrade.
Field names and state rules are part of the v2 contract, not implementation choices:

```yaml
migration:
  state: planned
  target_paths:
    - plugins/saga/example.py
  test_node_ids:
    - plugins/saga/tests/test_example.py::test_example_semantic_outcome
  negative_test_node_ids:
    - plugins/saga/tests/test_example.py::test_example_semantic_outcome_rejects_negative_cases
  intentional_differences:
    - Uses the Antigravity target contract instead of the source runtime API.
  packet_set_sha256: 0000000000000000000000000000000000000000000000000000000000000000
  host_receipt_sha256: ddebb99594afce219ca44a818097a5a163f2e2bd8c1cc62a65e194101e2726b0
  evidence_manifest_sha256: null
  blocking_capabilities: []
  validated_at: null
```

`packet_set_sha256` is calculated from the candidate's `edit_packet_ids` as follows: validate each
ID as a Unicode string, sort by Unicode code-point order, encode each ID as UTF-8, join the encoded
IDs with one byte `0x0a`, and append one final `0x0a` only when the list is nonempty. The empty set
hashes the zero-length byte string. Inputs containing a carriage return, line feed, invalid Unicode,
or duplicate ID fail. Fixed vectors are:

| packet IDs | exact bytes | SHA-256 |
|---|---|---|
| `[]` | zero bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `["packet-a"]` | UTF-8 `packet-a` plus terminal `0x0a` | `280974ba2126ccefddb24654e6dfaa24657498b97586fc8c6a4bf72fd89d184b` |
| `["packet-b", "packet-a"]` | UTF-8 `packet-a`, `0x0a`, UTF-8 `packet-b`, terminal `0x0a` | `8e87fbe7e0b6ed4766ec752f3b932df2e0bf78b6026c44d5090bd8aa9d1996d9` |

`target_paths`, `test_node_ids`, `negative_test_node_ids`, and
`intentional_differences` are nonempty for every state. A `planned` row has no evidence-manifest
digest,
blocking capabilities, or validation time. A `migrated` row has one or more validated typed-result
entries in its bound evidence manifest, no blocking capability, and an ISO-8601 validation time. A
`blocked` row has one or more
required capability IDs, no evidence-manifest digest, and no validation time. Non-survivors must not
have a `migration` key.

`migration-plan.v1.yaml` is a strict mapping keyed by the exact approved ID set. Each value supplies
the final `antigravity_state` (`present` or `intentional-divergence`), exact target paths, exact
positive and negative Pytest node IDs, and intentional differences. Packet and host digests are
recomputed from the ledger, not trusted from the mapping. The command verifies every target and
test path exists beneath the allowed repository roots before one atomic replacement.

### Closed migration evidence manifest

`docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json` has schema
`antigravity.semantic-port-migration-evidence.v1`. It is canonical JSON: UTF-8, sorted keys,
compact separators, no byte-order mark, and exactly one terminal line feed. Its SHA-256 is over
those exact bytes. Unknown fields fail. The root contains:

- `schema`, `campaign_id`, `ledger_schema`, and the exact 51 `candidate_ids`;
- `source_binding` with the three snapshot commits, selected-surface digest, packet-content digest,
  decision digest, operator-gate state, and final no-write Git refresh assignment ID;
- `host_binding` with capability receipt schema, catalog digest, receipt digest, and sorted
  capability ID/state pairs;
- `results`, keyed by assignment ID. Each value contains `result_schema`,
  `assignment_id`, `attempt_id`, `agent_path`, `role_id`, `profile_id`, `terminal_status`,
  `summary`, `changed_paths`, `no_change`, `checks`, `findings`, and `residual_risks`. A
  `reviewer-result.v1` entry additionally contains `dimensions`, `exclusions`, `denominator`,
  `overall`, `verdict`, and `hard_stop`;
- `candidate_evidence`, keyed by the exact 51 IDs, with target paths, positive and negative node
  IDs, owning result IDs, and the exact collected Pytest outcomes; and
- `manifest_sha256`, calculated over the same canonical object with that field omitted.

Only `assignment-result.v1` and `reviewer-result.v1` are accepted. Required assignments must be
`completed`; required checks and every mapped node must be `pass`; required reviewer results must
have verdict `accept`, `hard_stop=false`, and no unresolved actionable finding. `changed_paths`
must equal the declared literal write set for each writer. Result content is validated before its
digest is trusted. The manifest and the final source/host refresh result are assembled by separate
declared-write assignments; the root only validates and releases gates.

## Exact Survivor Traceability

Every row's stable ID is an exact reference to
`ledger.candidates[id].semantic_contract`. The second column is a non-authoritative plain-language
summary. `plugins/saga/tests/test_port_ledger.py` must resolve all 51 references and assert the
implementation mapping stores the ledger string byte-for-byte; it must fail if a summary is used as
the contract or if a target difference changes the contract. Target adaptations remain in the
separate “native adaptation and intentional difference” column.

Every table row also writes that survivor's closed `migration` object in
`docs/ports/2026-07-30-saga-reliability/ledger.yaml`; the ledger path is not repeated in every
file cell. “None” under host capabilities means the approved ledger's current sanitized receipt
names no candidate-level required capability; KTD8 still gates modes that originate independent
execution. The exact positive and negative Pytest node IDs are in the closed mapping immediately
after this table and are both stored in the v2 migration object.

| stable ID | semantic outcome | Antigravity boundary | adjacent dependencies | current state / host capabilities | exact implementation files | native adaptation and intentional difference | deterministic test and acceptance evidence |
|---|---|---|---|---|---|---|---|
| `application-security-audit` | Bounded application-security review emits explicit findings and validation evidence. | `multi-agent-consensus` skill | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/multi-agent-consensus/skills/appsec-audit/SKILL.md`; `plugins/multi-agent-consensus/tests/test_appsec_audit.py` | Keep reviewer workflow native; do not recreate source `team-execution` or claim unproven worker isolation. | `test_appsec_audit_preserves_bounded_findings_and_validation`; negative rejects self-certified or evidence-free completion; receipt binds both owned packets. |
| `bridge-receipt-contract` | Bridge results preserve requested and observed facts in a portable receipt. | `fleet-core` shared receipt | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/fleet-core/scripts/fleet_commons/bridge_receipt.py`; `plugins/fleet-core/tests/test_bridge_receipt.py` | Keep requested facts distinct from observable facts; unknown stays unknown. | `test_bridge_receipt_distinguishes_requested_observed_and_unknown`; negative rejects malformed or self-attested evidence; receipt binds all five packets. |
| `codex-portability-contracts` | Runtime-specific Saga behavior remains visible through provenance, target mappings, and cutover classifications. | canonical Saga documentation | ledger: none; implementation: all owning boundaries | absent / none | `plugins/saga/docs/portability.md`; `plugins/saga/docs/README.md`; `plugins/saga/docs/model/saga-docs-model.yaml`; `plugins/saga/tests/test_saga_docs_coverage.py` | Curate one Antigravity page; do not copy Codex's portability tree or treat Codex paths as target truth. | `test_portability_page_maps_every_runtime_specific_contract_to_antigravity`; negative rejects source paths presented as executable target paths; receipt binds all 45 packets. |
| `concurrency-lease-policy` | Bounded concurrency, durable leases, and liveness prevent duplicate or abandoned ownership. | `fleet-core` shared coordination | ledger: none; implementation: `shared-runtime-resolution`, `delegation-audit-state` | absent / none | `plugins/fleet-core/scripts/fleet_commons/concurrency_policy.py`; `plugins/fleet-core/scripts/fleet_commons/lease_broker.py`; `plugins/fleet-core/scripts/fleet_commons/liveness_engine.py`; `plugins/fleet-core/tests/test_concurrency_policy.py`; `plugins/fleet-core/tests/test_lease_broker.py` | Implement deterministic local lease semantics only; do not claim host scheduling or isolation. | `test_bounded_leases_prevent_duplicate_and_abandoned_ownership`; negatives cover expiry, duplicate claim, unknown owner, and clock boundary; receipt binds all ten packets. |
| `cross-runtime-acceptance-tools` | Bounded Saga canaries produce reviewable compatibility evidence. | `fleet-core` conformance utility | ledger: none; implementation: `bridge-receipt-contract`, `saga-manifest-provenance-ledgers` | absent / none | `plugins/fleet-core/scripts/fleet_commons/saga_acceptance.py`; `plugins/fleet-core/references/saga-acceptance-contract.json`; `plugins/fleet-core/tests/test_saga_acceptance.py` | Compare semantic receipts, not source files, transcript text, or live host calls. | `test_saga_acceptance_compares_bounded_semantic_receipts`; negative rejects missing, stale, or differently bound receipts; receipt binds all eight packets. |
| `delegation-audit-state` | Delegated work records ownership and completion so missing or duplicate evidence is detectable. | `fleet-core` shared audit state | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/fleet-core/scripts/fleet_commons/delegation_audit.py`; `plugins/fleet-core/scripts/fleet_commons/delegation_state.py`; `plugins/fleet-core/tests/test_delegation_audit_state.py` | Extend current target state rather than adding the source audit-store layout. | `test_delegation_audit_detects_missing_duplicate_and_wrong_owner_evidence`; negative covers replay and unknown worker; receipt binds all eight packets. |
| `mission-board-census-pagination` | Board reads traverse every page and reconcile a complete census before reporting or mutation. | `mission-control` project reads | ledger: none; implementation: `mission-control-runtime` | absent / none | `plugins/mission-control/scripts/sdlc_manager.py`; `plugins/mission-control/tests/test_sdlc_manager.py` | First close the existing `sdlc_manager.py` pagination seam. Add repeated-cursor, missing-cursor, and partial-census tests there. Do not add `board_census.py`, `check_pagination.py`, or a second client/source helper unless distinct product ownership is proved and Jeff approves the expanded path set. | `test_board_census_requires_every_page_before_complete`; negatives cover repeated cursor, missing cursor, and partial census; receipt binds all ten packets. |
| `mission-board-operations` | Operators inspect, add, move, and archive cards through explicit workflow gates. | `mission-control` board command and skill | ledger: none; implementation: `mission-control-runtime`, `mission-board-census-pagination` | partial / none | `plugins/mission-control/commands/board.md`; `plugins/mission-control/skills/board/SKILL.md`; `plugins/mission-control/skills/board/references/graphql-queries.md`; `plugins/mission-control/skills/board/references/kanban-workflow.md`; `plugins/mission-control/tests/test_board_add_multi_project.py`; `plugins/mission-control/tests/test_board_move_exit.py`; `plugins/mission-control/tests/test_graphql_issue_resolution.py` | Preserve preparation and confirmation before mutation; tests use injected responses only. | `test_board_move_requires_resolved_item_field_and_status`; negative rejects ambiguous item, missing exit rule, and partial census; receipt binds all 19 packets. |
| `mission-control-runtime` | Typed GitHub and project operations normalize repository inputs and fail explicitly. | `mission-control` runtime | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/mission-control/scripts/sdlc_manager.py`; `plugins/mission-control/tests/test_sdlc_manager.py` | Consolidate target behavior in the existing runtime; do not add a second API client. | `test_runtime_normalizes_repository_inputs_and_typed_failures`; negative covers malformed repository, response, and mutation denial; receipt binds all four packets. |
| `mission-executor-profile-policy` | Issue profiles accept only supported model and tier policy before dispatch. | `mission-control` profile lint | ledger: none; implementation: `mission-control-runtime`, `shared-runtime-resolution` | partial / none | `plugins/mission-control/scripts/executor_profile_lint.py`; `plugins/mission-control/tests/test_executor_profile_lint.py` | Resolve Gemini models and efforts from `fleet-core`; no source-host model literals. | `test_executor_profile_accepts_only_current_gemini_registry`; negative rejects unknown model, effort, and source-host literal; receipt binds all four packets. |
| `mission-flow-metrics` | Project history yields throughput, cycle time, work age, and per-state flow. | `mission-control` metrics skill | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/commands/metrics.md`; `plugins/mission-control/skills/metrics/SKILL.md`; `plugins/mission-control/skills/metrics/references/metrics-targets.md`; `plugins/mission-control/tests/test_metrics_contract.py` | Keep metrics descriptive; do not turn them into automatic routing authority. | `test_metrics_contract_covers_throughput_cycle_age_and_state_time`; negative rejects incomplete history presented as complete; receipt binds all eight packets. |
| `mission-issue-contract` | Prepared issues conform to the shared taxonomy, generated data, and template parity. | `mission-control` issue contract | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/config/sdlc-schema.json`; `plugins/mission-control/config/generated/check_issue_contract_parity.py`; `plugins/mission-control/config/generated/issue_contract_data.py`; `plugins/mission-control/config/generated/issue_contract_data.py.sha256`; `plugins/mission-control/config/generated/issue_contract_shim.py`; `plugins/mission-control/config/generated/issue_contract_shim.py.sha256`; `plugins/mission-control/scripts/sync_template_docs.py`; `plugins/mission-control/tests/test_issue_contract_parity.py`; `plugins/mission-control/tests/test_issue_source_artifacts.py`; `plugins/mission-control/tests/test_prompt_alignment.py`; `plugins/mission-control/tests/test_template_sync.py` | Regenerate target contract data from its schema; do not copy generated source bytes as proof. | `test_generated_issue_contract_matches_schema_and_templates`; negative rejects digest and template drift; receipt binds all owned packets. |
| `mission-issue-preparation` | Issue preparation, review, approval, and remote mutation remain separate and preserve source evidence. | `mission-control` issue command and skill | ledger: none; implementation: `mission-control-runtime`, `mission-issue-contract` | partial / none | `plugins/mission-control/commands/issue.md`; `plugins/mission-control/commands/triage.md`; `plugins/mission-control/scripts/sdlc_manager.py`; `plugins/mission-control/skills/issues/SKILL.md`; `plugins/mission-control/skills/issues/references/issue-types.md`; `plugins/mission-control/skills/issues/references/templates-reference.md`; `plugins/mission-control/tests/test_issue_create_prepared.py`; `plugins/mission-control/tests/test_issue_prepare.py`; `plugins/mission-control/tests/test_issue_prepare_compile_approve.py`; `plugins/mission-control/tests/test_typed_exceptions.py` | Preserve the explicit mutation gate; no issue mutation occurs in acceptance tests. | `test_issue_preparation_requires_review_and_approval_before_mutation`; negative rejects missing source artifact and unauthorized write; receipt binds all owned packets. |
| `mission-label-operations` | Label audits and changes use the declared taxonomy and explicit mutation boundary. | `mission-control` labels skill | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/skills/labels/SKILL.md`; `plugins/mission-control/skills/labels/references/labels-reference.md`; `plugins/mission-control/tests/test_label_contract.py` | Keep audit read-only until separately authorized. | `test_label_skill_preserves_taxonomy_and_mutation_gate`; negative rejects unknown labels and implicit writes; receipt binds all owned packets. |
| `mission-milestone-operations` | Objective milestones can be created, linked, and assessed with progress and risk evidence. | `mission-control` milestones skill | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/skills/milestones/SKILL.md`; `plugins/mission-control/skills/milestones/references/objective-workflow.md`; `plugins/mission-control/tests/test_milestone_contract.py` | Separate planning/read evidence from remote creation. | `test_milestone_skill_requires_objective_progress_and_risk_evidence`; negative rejects unapproved creation; receipt binds all owned packets. |
| `mission-project-flow` | Project fields, sub-issues, assignments, and repository mappings resolve before mutation. | `mission-control` flow skill | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/config/project-mappings.json`; `plugins/mission-control/skills/flow/SKILL.md`; `plugins/mission-control/tests/test_flow_subcommands.py`; `plugins/mission-control/tests/test_project_mappings_resolution.py` | Preserve current target project names and explicit resolution; no source mapping assumptions. | `test_flow_resolves_project_field_issue_and_repository_before_mutation`; negative rejects ambiguous mapping and missing option; receipt binds all owned packets. |
| `mission-rollout-operations` | Organization rollout status and gaps remain inspectable; mutation occurs only through rollout workflow. | `mission-control` rollout skill | ledger: none; implementation: `mission-control-runtime` | partial / none | `plugins/mission-control/skills/rollout/SKILL.md`; `plugins/mission-control/skills/rollout/references/work-hierarchy.md`; `plugins/mission-control/tests/test_rollout_contract.py` | Keep census/status read-only and mutation separately authorized. | `test_rollout_skill_separates_status_gap_analysis_and_mutation`; negative rejects implicit deployment or issue changes; receipt binds all owned packets. |
| `orphan-evidence-attestation` | Worker output is accepted only when ownership, shape, and attestation bind it to the run. | `fleet-core` evidence primitive | ledger: none; implementation: `delegation-audit-state`, `saga-manifest-provenance-ledgers` | absent / none | `plugins/fleet-core/scripts/fleet_commons/orphan_evidence.py`; `plugins/fleet-core/scripts/fleet_commons/output_attestation.py`; `plugins/fleet-core/tests/fixtures/orphan-evidence/valid.json`; `plugins/fleet-core/tests/fixtures/orphan-evidence/duplicate-schema.json`; `plugins/fleet-core/tests/test_orphan_evidence.py` | Use Antigravity run and worker identities; no model narration can attest itself. | `test_orphan_evidence_requires_owner_shape_and_run_attestation`; negatives cover duplicate schema, wrong owner, replay, and missing output; receipt binds all nine packets. |
| `repository-quality-guards` | Repository checks reject fake fixtures, ownership gaps, misleading journals, and weak test shapes. | repository validator backed by `fleet-core` tests | ledger: none; implementation: `shared-runtime-resolution` | absent / none | `scripts/validate_plugins.py`; `plugins/fleet-core/tests/test_repository_quality_guards.py` | Add focused Antigravity validation rules to the canonical validator; do not port six standalone source scripts. | `test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps`; negative fixtures prove each failure class; receipt binds all owned packets. |
| `saga-artifact-promotion` | Staged lifecycle artifacts become authoritative only through a validated repository promotion transaction. | `saga` promote command and skill | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/commands/promote.md`; `plugins/saga/scripts/promote_scan.py`; `plugins/saga/skills/promote/SKILL.md`; `plugins/saga/skills/promote/references/promotion-contract.md`; `plugins/saga/tests/test_promote_scan.py` | Repository documents are canonical; brain state is staging only. | `test_promotion_requires_canonical_target_provenance_and_no_conflict`; negatives cover overwrite conflict, brain-only completion, and partial promotion; receipt binds all owned packets. |
| `saga-code-review` | Code review compares implementation with the plan and records typed evidence-backed findings. | `saga` code-review command and skill | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-operator-safety` | partial / none | `plugins/saga/commands/code-review.md`; `plugins/saga/skills/code-review/SKILL.md`; `plugins/saga/skills/code-review/references/built-vs-planned.md`; `plugins/saga/skills/code-review/references/findings-schema.md`; `plugins/saga/skills/code-review/references/lens-catalog.md`; `plugins/saga/skills/code-review/references/validator.md`; `plugins/saga/tests/test_code_review_contract.py` | Use Antigravity reviewers and typed receipts; do not self-certify or assume source workflow APIs. | `test_code_review_requires_plan_comparison_typed_findings_and_disposition`; negative rejects missing evidence, malformed finding, and self-review completion; receipt binds all owned packets. |
| `saga-cross-runtime-reconciliation` | Runtime projections reconcile without overriding canonical repository truth. | `saga` reconciliation scripts and reference | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-lifecycle-settlement` | absent / none | `plugins/saga/references/outcome-cross-runtime.md`; `plugins/saga/scripts/override_rate_reader.py`; `plugins/saga/scripts/reconcile.py`; `plugins/saga/scripts/reconcile_controller.py`; `plugins/saga/tests/test_cross_runtime_reconciliation.py` | Reconcile receipts and repository facts, not source-host state directories. | `test_reconciliation_keeps_repository_truth_authoritative`; negatives cover conflict, stale projection, and attempted overwrite; receipt binds all owned packets. |
| `saga-deploy-strategy` | Deployment intent is handed to the owning deploy workflow without unauthorized release. | `saga` deploy-intent detector | ledger: none; implementation: `saga-operator-safety` | partial / none | `plugins/saga/scripts/detect_deploy_strategy.py`; `plugins/saga/tests/test_detect_deploy_strategy.py` | Detect and hand off only; no deployment, tag, or credential action. | `test_deploy_strategy_detects_intent_without_executing_release`; negative rejects ambiguous or unauthorized action; receipt binds all owned packets. |
| `saga-executive-review` | Founder and chief-executive review challenge value and strategy without approving delivery. | `saga` executive-review commands and skill | ledger: none; implementation: `saga-operator-safety` | partial / none | `plugins/saga/commands/ceo-review.md`; `plugins/saga/commands/founder-review.md`; `plugins/saga/skills/founder-review/SKILL.md`; `plugins/saga/skills/founder-review/references/ceo-cognition.md`; `plugins/saga/skills/founder-review/references/review-modes.md`; `plugins/saga/tests/test_executive_review_contract.py` | Keep `/ceo-review` as the documented alias and avoid source-only agent metadata. | `test_executive_review_challenges_value_without_delivery_approval`; negative rejects silent approval and lifecycle mutation; receipt binds all owned packets. |
| `saga-external-action-boundary` | External mutation requires typed intent, workspace boundary, adapter result, and separate authority receipt. | `saga` external-action contract | ledger: none; implementation: `saga-operator-safety`, `saga-manifest-provenance-ledgers` | absent / none | `plugins/saga/scripts/external_action_adapters.py`; `plugins/saga/scripts/external_action_contract.py`; `plugins/saga/scripts/external_action_egress.py`; `plugins/saga/scripts/external_action_workspace.py`; `plugins/saga/tests/test_external_action_adapters.py` | Implement a fail-closed local contract only; this issue authorizes no external action. | `test_external_action_requires_intent_workspace_adapter_and_authority`; negatives cover missing receipt, boundary escape, replay, and adapter failure; receipt binds all five packets. |
| `saga-fleet-doctor` | Saga consumes the host contract and blocks unsupported behavior before dispatch. | `saga` doctor command, skill, and gate | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/saga/commands/fleet-doctor.md`; `plugins/saga/references/fleet-doctor-sources.md`; `plugins/saga/scripts/fleet_doctor.py`; `plugins/saga/scripts/host_capability_gate.py`; `plugins/saga/skills/fleet-doctor/SKILL.md`; `plugins/saga/tests/test_fleet_doctor.py` | Consume only sanitized capability states and digests; do not probe or mutate the live host here. | `test_fleet_doctor_blocks_required_unknown_failed_and_unavailable`; negative proves optional fallback cannot satisfy required capability; receipt binds all owned packets. |
| `saga-handoff` | Completed work emits a validated envelope naming artifacts, evidence, risks, and still-unauthorized actions. | `saga` handoff command and skill | ledger: none; implementation: `saga-external-action-boundary`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/commands/handoff.md`; `plugins/saga/references/handoff_failure_matrix.md`; `plugins/saga/scripts/handoff_envelope.py`; `plugins/saga/skills/handoff/SKILL.md`; `plugins/saga/tests/test_handoff_envelope.py` | Stop at a local validated packet; do not create issues, boards, PRs, merges, or deployments. | `test_handoff_names_artifacts_evidence_risks_and_external_authority`; negative rejects missing evidence and implied mutation; receipt binds all owned packets. |
| `saga-ideation` | Ideation preserves perspectives, alternatives, convergence evidence, and a durable artifact. | `saga` ideate command and skill | ledger: none; implementation: `saga-operator-safety`, `saga-artifact-promotion` | partial / none | `plugins/saga/commands/ideate.md`; `plugins/saga/skills/ideate/SKILL.md`; `plugins/saga/skills/ideate/references/convergence-and-partnership.md`; `plugins/saga/skills/ideate/references/ideation-artifact.md`; `plugins/saga/tests/test_ideate_contract.py` | Express Gemini deliberation requirements without claiming unavailable independent execution. | `test_ideation_preserves_seeds_alternatives_disagreement_and_artifact`; negative rejects one-response role play as independent execution evidence; receipt binds all owned packets. |
| `saga-investigation` | Investigation separates facts, hypotheses, experiments, root cause, and unresolved uncertainty. | `saga` investigate command and skill | ledger: none; implementation: `saga-artifact-promotion` | partial / none | `plugins/saga/commands/investigate.md`; `plugins/saga/skills/investigate/SKILL.md`; `plugins/saga/skills/investigate/references/debug-report.md`; `plugins/saga/skills/investigate/references/methodology.md`; `plugins/saga/skills/investigate/references/pattern-taxonomy.md`; `plugins/saga/tests/test_investigate_contract.py` | Preserve evidence categories and durable report; no source-specific tool names. | `test_investigation_separates_observation_hypothesis_experiment_and_uncertainty`; negative rejects asserted root cause without experiment; receipt binds all owned packets. |
| `saga-lifecycle-settlement` | Lifecycle advancement derives from declared obligations and independent receipts. | `saga` lifecycle core | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-operator-safety` | partial / none | `plugins/saga/references/lifecycle-obligation-contract.md`; `plugins/saga/references/lifecycle-obligation-schema.json`; `plugins/saga/references/saga-spec.md`; `plugins/saga/references/transition-receipt-schema.json`; `plugins/saga/scripts/lifecycle_obligations.py`; `plugins/saga/scripts/lifecycle_state.py`; `plugins/saga/scripts/saga.py`; `plugins/saga/scripts/transition_receipts.py`; `plugins/saga/tests/test_lifecycle_obligations.py`; `plugins/saga/tests/test_saga_saga.py`; `plugins/saga/tests/test_transition_receipts.py` | Extend current obligation/receipt design; narration and GitHub state cannot replace canonical evidence. | `test_lifecycle_advances_only_when_required_obligations_have_independent_receipts`; negatives cover missing, degraded, conflicting, and self-certified evidence; receipt binds all owned packets. |
| `saga-loop-routing` | Loop chooses the earliest unsettled required obligation without skipping or repeating work. | `saga` loop command, router, and skill | ledger: none; implementation: `saga-lifecycle-settlement`, `saga-session-context-and-spores` | partial / none | `plugins/saga/agents/lifecycle-router.md`; `plugins/saga/commands/loop.md`; `plugins/saga/skills/loop/SKILL.md`; `plugins/saga/skills/loop/references/dispatch-table.md`; `plugins/saga/skills/loop/references/drive-and-resume.md`; `plugins/saga/skills/loop/references/generic-ask-compiler.md`; `plugins/saga/tests/test_loop_routing.py` | Route from canonical settlement; no source backend or unproven scheduler. | `test_loop_routes_to_earliest_unsettled_required_obligation_idempotently`; negative rejects skipped and duplicated obligations; receipt binds all owned packets. |
| `saga-manifest-provenance-ledgers` | Run manifests bind inputs, outputs, digests, and ownership for reconstruction. | `saga` evidence storage | ledger: none; implementation: `shared-runtime-resolution` | partial / none | `plugins/saga/scripts/manifest_reader.py`; `plugins/saga/scripts/manifest_store.py`; `plugins/saga/scripts/provenance_manifest.py`; `plugins/saga/scripts/run_ledger.py`; `plugins/saga/tests/test_manifest_consumer_matrix.py`; `plugins/saga/tests/test_manifest_reader.py`; `plugins/saga/tests/test_manifest_store.py`; `plugins/saga/tests/test_run_ledger.py` | Preserve target schemas and add only fields required for approved evidence; no source manifest copy. | `test_manifest_round_trip_binds_input_output_digest_and_owner`; negatives cover tampering, orphan evidence, and duplicate identity; receipt binds all owned packets. |
| `saga-office-hours` | Office hours diagnoses the decision frame and advises without lifecycle completion. | `saga` office-hours command and skill | ledger: none; implementation: `saga-operator-safety` | partial / none | `plugins/saga/commands/office-hours.md`; `plugins/saga/skills/office-hours/SKILL.md`; `plugins/saga/skills/office-hours/references/frame-diagnostic.md`; `plugins/saga/tests/test_office_hours_contract.py` | Keep the surface advisory and artifact-optional. | `test_office_hours_returns_frame_and_route_without_completion_claim`; negative rejects implementation or lifecycle mutation; receipt binds all owned packets. |
| `saga-operator-safety` | Shared controls preserve operator choice, escalation boundaries, escape hatches, and formatting. | `saga` shared references | ledger: none; implementation: none | partial / none | `plugins/saga/references/command_dry_runs.md`; `plugins/saga/references/escape_hatches.md`; `plugins/saga/references/formatting-style.md`; `plugins/saga/references/harness-escalation-policy.md`; `plugins/saga/references/operator-choice.md`; `plugins/saga/scripts/journal_triggers.py`; `plugins/saga/tests/test_operator_safety_contract.py` | Use Antigravity prompts and repository artifacts; no Claude interaction API. | `test_operator_safety_preserves_choice_escalation_escape_and_formatting`; negative rejects implicit approval and source-host interaction primitives; receipt binds all owned packets. |
| `saga-optimization` | Optimization defines a measurable experiment, baseline, change, and stop condition. | `saga` optimize command and skill | ledger: none; implementation: `saga-artifact-promotion` | partial / none | `plugins/saga/commands/optimize.md`; `plugins/saga/skills/optimize/SKILL.md`; `plugins/saga/skills/optimize/references/experiment-loop.md`; `plugins/saga/skills/optimize/references/metric-taxonomy.md`; `plugins/saga/tests/test_optimize_contract.py` | Keep measurement separate from automatic deployment or completion. | `test_optimization_requires_baseline_change_measurement_and_stop_condition`; negative rejects unmeasured improvement claim; receipt binds all owned packets. |
| `saga-outcome-board-integration` | Outcome state reconciles issue and project facts idempotently while remote changes remain separately authorized. | `saga` outcome-board adapter | ledger: none; implementation: `mission-control-runtime`, `saga-external-action-boundary` | partial / none | `plugins/saga/scripts/board_progression.py`; `plugins/saga/scripts/issue_progress.py`; `plugins/saga/scripts/outcome_board_sync.py`; `plugins/saga/scripts/outcome_github.py`; `plugins/saga/scripts/parse_issue.py`; `plugins/saga/tests/test_outcome_board_sync.py` | Keep remote facts as inputs and mutation behind authority; tests are fixture-only. | `test_outcome_board_reconciliation_is_idempotent_and_authority_bounded`; negatives cover stale event, duplicate comment, and unauthorized update; receipt binds all owned packets. |
| `saga-outcome-economics-liveness` | Outcome reports cost, progress, and liveness without equating activity or spend with completion. | `saga` outcome telemetry | ledger: none; implementation: `saga-lifecycle-settlement` | partial / none | `plugins/saga/scripts/outcome_costs.py`; `plugins/saga/scripts/outcome_liveness.py`; `plugins/saga/tests/test_outcome_liveness.py`; `plugins/saga/tests/test_outcome_economics.py` | Metrics are evidence, not settlement authority. | `test_outcome_telemetry_never_converts_activity_or_spend_to_completion`; negative covers active-but-stalled and expensive-but-unsettled work; receipt binds all owned packets. |
| `saga-outcome-merge-worktrees` | Worktrees and merge queues preserve ownership and settle only from verified integration evidence. | `saga` local integration state | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/scripts/merge_watcher.py`; `plugins/saga/scripts/outcome_merge.py`; `plugins/saga/scripts/outcome_worktrees.py`; `plugins/saga/tests/test_merge_watcher.py`; `plugins/saga/tests/test_outcome_merge_queue.py`; `plugins/saga/tests/test_outcome_worktrees.py` | Model local state and verified receipts; do not execute Git outside the Git role. | `test_outcome_merge_settles_only_from_verified_integration_receipt`; negatives cover wrong branch owner, stale queue, and narration-only merge; receipt binds all owned packets. |
| `saga-outcome-orchestration` | Outcome graphs decompose objectives, dispatch owned leaves, reconcile evidence, and refuse unsupported completion. | `saga` outcome core | ledger: none; implementation: `saga-lifecycle-settlement`, `saga-loop-routing`, `saga-manifest-provenance-ledgers` | partial / none | `plugins/saga/commands/outcome.md`; `plugins/saga/scripts/outcome.py`; `plugins/saga/scripts/outcome_decompose.py`; `plugins/saga/scripts/outcome_dispatcher.py`; `plugins/saga/scripts/outcome_edges.py`; `plugins/saga/scripts/outcome_gate_transport.py`; `plugins/saga/scripts/outcome_orchestrator.py`; `plugins/saga/scripts/outcome_projection.py`; `plugins/saga/scripts/outcome_reconcile.py`; `plugins/saga/scripts/outcome_report.py`; `plugins/saga/scripts/outcome_spec.py`; `plugins/saga/scripts/outcome_store.py`; `plugins/saga/skills/outcome/SKILL.md`; `plugins/saga/tests/test_outcome_completion.py`; `plugins/saga/tests/test_outcome_dispatcher.py`; `plugins/saga/tests/test_outcome_integration.py`; `plugins/saga/tests/test_outcome_reconcile.py`; `plugins/saga/tests/test_outcome_spec.py`; `plugins/saga/tests/test_outcome_store.py` | Preserve the committed outcome spec and receipt hierarchy; no new outcome edge is invented by this migration. | `test_outcome_refuses_completion_without_owned_leaf_and_settlement_evidence`; negatives cover orphan leaf, unsupported completion, and conflicting receipts; receipt binds all owned packets. |
| `saga-planning` | Planning turns approved requirements into a decision-complete, testable implementation plan. | `saga` plan command and skill | ledger: none; implementation: `saga-operator-safety`, `saga-artifact-promotion` | partial / none | `plugins/saga/commands/plan.md`; `plugins/saga/skills/plan/SKILL.md`; `plugins/saga/skills/plan/references/interrogation.md`; `plugins/saga/skills/plan/references/plan-sections.md`; `plugins/saga/tests/test_plan_contract.py` | Keep decisions, write sets, dependencies, tests, and authority explicit; use target roles and Gemini tiers. | `test_plan_contract_requires_decisions_files_dependencies_tests_and_authority`; negative rejects vague scope and source-host execution design; receipt binds all owned packets. |
| `saga-plugin-readiness` | Saga proves dependent plugin and workflow contracts exist before routing work. | `saga` dependency resolver | ledger: none; implementation: `shared-runtime-resolution`, `saga-fleet-doctor` | absent / none | `plugins/saga/scripts/plugin_dependency_resolver.py`; `plugins/saga/tests/test_plugin_dependency_resolver.py` | Resolve actual Antigravity plugin contracts; map source team execution to `multi-agent-consensus` and do not require a target `verified-workflows` plugin. | `test_plugin_readiness_resolves_target_plugins_and_consensus_mapping`; negative rejects missing plugin, source package name, and unsupported workflow; receipt binds all owned packets. |
| `saga-provider-pulse` | Provider telemetry reports quality and drift without automatic routing authority. | `saga` pulse command and skill | ledger: none; implementation: `saga-manifest-provenance-ledgers` | absent / none | `plugins/saga/commands/pulse.md`; `plugins/saga/scripts/capability_elo.py`; `plugins/saga/scripts/provider_control_chart.py`; `plugins/saga/scripts/pulse.py`; `plugins/saga/scripts/second_opinion.py`; `plugins/saga/skills/pulse/SKILL.md`; `plugins/saga/skills/pulse/references/manual-verification.md`; `plugins/saga/tests/test_provider_pulse.py` | Operate on supplied sanitized receipts only; no live provider calls and no model auto-selection. | `test_provider_pulse_reports_quality_drift_without_routing_authority`; negatives cover sparse data, stale receipt, and attempted auto-route; receipt binds all owned packets. |
| `saga-quality-assurance` | Quality assurance chooses risk-based scenarios, executes acceptance checks, and records failures without self-certification. | `saga` quality-assurance command and skill | ledger: none; implementation: `saga-code-review`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/commands/qa.md`; `plugins/saga/scripts/qa_health_score.py`; `plugins/saga/skills/qa/SKILL.md`; `plugins/saga/skills/qa/references/qa-report.md`; `plugins/saga/skills/qa/references/risk-taxonomy.md`; `plugins/saga/tests/test_qa_contract.py` | Use deterministic checks and independent evidence; response length is not quality. | `test_qa_requires_risk_scenarios_checks_failure_disposition_and_independence`; negative rejects self-certified pass and missing failure record; receipt binds all owned packets. |
| `saga-requirements-brainstorm` | Brainstorming turns an approved idea into testable requirements, assumptions, actors, and examples. | `saga` brainstorm command and skill | ledger: none; implementation: `saga-operator-safety`, `saga-artifact-promotion` | partial / none | `plugins/saga/commands/brainstorm.md`; `plugins/saga/skills/brainstorm/SKILL.md`; `plugins/saga/skills/brainstorm/references/requirements-sections.md`; `plugins/saga/tests/test_brainstorm_contract.py` | Preserve requirements depth and operator questions using ordinary interaction, not Claude APIs. | `test_brainstorm_requires_requirements_assumptions_actors_and_acceptance_examples`; negative rejects premature implementation plan; receipt binds all owned packets. |
| `saga-retrospective` | Retrospective records evidence-backed learning after delivery without changing lifecycle state. | `saga` retro command and skill | ledger: none; implementation: `saga-lifecycle-settlement` | partial / none | `plugins/saga/commands/retro.md`; `plugins/saga/skills/retro/SKILL.md`; `plugins/saga/skills/retro/references/retro-passes.md`; `plugins/saga/skills/retro/references/retro-report.md`; `plugins/saga/skills/retro/references/self-edit-safety.md`; `plugins/saga/tests/test_retro_contract.py` | Keep retro off-chain and Saga-read-only. | `test_retro_records_evidence_backed_learning_without_state_mutation`; negative rejects retro as settlement or self-edit authority; receipt binds all owned packets. |
| `saga-session-context-and-spores` | Interrupted work preserves bounded context, reconstructs in-flight state, and renders truthful status. | `saga` session and spore scripts | ledger: none; implementation: `saga-manifest-provenance-ledgers`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/scripts/discover_sessions.py`; `plugins/saga/scripts/extract_session_skeleton.py`; `plugins/saga/scripts/find_inflight_work.py`; `plugins/saga/scripts/load_saga_context.py`; `plugins/saga/scripts/saga_spore.py`; `plugins/saga/scripts/scaffold_checkpoint.py`; `plugins/saga/scripts/status_card.py`; `plugins/saga/tests/test_saga_spore.py`; `plugins/saga/tests/test_spore_seam_roundtrip.py`; `plugins/saga/tests/test_state_paths.py` | Resolve repository and Antigravity-local paths through current target conventions; no fixed brain root. | `test_session_reconstruction_uses_bounded_canonical_evidence_and_truthful_status`; negatives cover stale local projection, missing artifact, and fixed source root; receipt binds all owned packets. |
| `saga-ship-ceremony` | Shipping uses resumable transitions, hazard checks, reversible receipts, and explicit confirmation. | `saga` ship scripts | ledger: none; implementation: `saga-external-action-boundary`, `saga-lifecycle-settlement` | partial / none | `plugins/saga/scripts/ceremony_hazards.py`; `plugins/saga/scripts/reversibility_certificate.py`; `plugins/saga/scripts/ship_ceremony.py`; `plugins/saga/scripts/ship_undo.py`; `plugins/saga/tests/test_ceremony_hazards.py`; `plugins/saga/tests/test_ship_ceremony.py`; `plugins/saga/tests/test_ship_undo.py` | Preserve local state and receipts; actual GitHub, merge, or deploy actions stay separately authorized. | `test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation`; negatives cover missing confirmation, irreversible step, and replay; receipt binds all owned packets. |
| `saga-specification` | Specification defines outcome and acceptance without prematurely choosing implementation. | `saga` spec command and skill | ledger: none; implementation: `saga-operator-safety`, `saga-artifact-promotion` | partial / none | `plugins/saga/commands/spec.md`; `plugins/saga/skills/spec/SKILL.md`; `plugins/saga/skills/spec/references/interrogation.md`; `plugins/saga/skills/spec/references/spec-template.md`; `plugins/saga/tests/test_spec_contract.py` | Keep specification off-chain and focused on what, not source implementation layout. | `test_spec_defines_outcome_scope_failures_and_acceptance_without_how`; negative rejects implementation prescription and lifecycle tick; receipt binds all owned packets. |
| `saga-strategy` | Strategy records direction, alternatives, constraints, and revisit conditions before planning. | `saga` strategy command and skill | ledger: none; implementation: `saga-operator-safety`, `saga-artifact-promotion` | partial / none | `plugins/saga/commands/strategy.md`; `plugins/saga/skills/strategy/SKILL.md`; `plugins/saga/skills/strategy/references/interview.md`; `plugins/saga/skills/strategy/references/strategy-template.md`; `plugins/saga/tests/test_strategy_contract.py` | Preserve operator decision and rejected alternatives; no delivery approval. | `test_strategy_records_choice_alternatives_constraints_and_revisit_trigger`; negative rejects unexplained choice and implicit work start; receipt binds all owned packets. |
| `saga-work-execution` | Work follows approved units, preserves unrelated changes, runs checks, and stops at authority gates. | `saga` work command and skill | ledger: none; implementation: `saga-plugin-readiness`, `saga-code-review`, `saga-operator-safety` | partial / none | `plugins/saga/commands/work.md`; `plugins/saga/skills/work/SKILL.md`; `plugins/saga/skills/work/references/execution-strategy.md`; `plugins/saga/skills/work/references/pr-continuation-loop.md`; `plugins/saga/skills/work/references/test-and-gates.md`; `plugins/saga/tests/test_work_contract.py` | Use Antigravity-native assignments and Gemini tiers; no source mechanical executor or automatic lifecycle continuation. | `test_work_obeys_units_write_sets_checks_and_authority_gates`; negatives cover unrelated edit, missing test, and unauthorized PR or merge; receipt binds all owned packets. |
| `shared-runtime-resolution` | Plugins resolve shared fleet behavior without machine-specific import assumptions. | `fleet-core` plus consumer shims | ledger: none; implementation: none | partial / none | `plugins/fleet-core/scripts/fleet_commons/plugin_resolution.py`; `plugins/fleet-core/scripts/fleet_commons/workflow_compat.py`; `plugins/fleet-core/scripts/fleet_commons_shim.py`; `plugins/mission-control/scripts/fleet_commons_shim.py`; `plugins/saga/scripts/fleet_commons_shim.py`; `plugins/fleet-core/tests/test_fleet_commons.py`; `plugins/fleet-core/tests/test_fleet_commons_resolution.py`; `plugins/fleet-core/tests/test_workflow_compat.py` | Resolve logical plugin roots and target workflow vocabulary; no absolute home paths or source package assumptions. | `test_shared_runtime_resolution_is_logical_portable_and_target_bound`; negatives cover machine path, source plugin name, incompatible schema, and shim drift; receipt binds all 18 packets. |

### Exact positive and negative Pytest mapping

The closed migration-plan mapping contains these exact node IDs. Collection must return exactly
these 102 nodes: one positive and one negative for each of the exact 51 stable IDs. A shared
implementation helper is allowed, but every parametrized case must collect under the exact node
shown here. `plugins/saga/tests/test_port_ledger.py` mechanically proves ID equality, nonempty
positive and negative lists, node uniqueness within each row, filesystem containment, successful
`pytest --collect-only` resolution, and passed final outcomes.

| stable ID | exact positive Pytest node ID | exact negative Pytest node ID |
|---|---|---|
| `application-security-audit` | `plugins/multi-agent-consensus/tests/test_appsec_audit.py::test_appsec_audit_preserves_bounded_findings_and_validation` | `plugins/multi-agent-consensus/tests/test_appsec_audit.py::test_appsec_audit_preserves_bounded_findings_and_validation_rejects_negative_cases` |
| `bridge-receipt-contract` | `plugins/fleet-core/tests/test_bridge_receipt.py::test_bridge_receipt_distinguishes_requested_observed_and_unknown` | `plugins/fleet-core/tests/test_bridge_receipt.py::test_bridge_receipt_distinguishes_requested_observed_and_unknown_rejects_negative_cases` |
| `codex-portability-contracts` | `plugins/saga/tests/test_saga_docs_coverage.py::test_portability_page_maps_every_runtime_specific_contract_to_antigravity` | `plugins/saga/tests/test_saga_docs_coverage.py::test_portability_page_maps_every_runtime_specific_contract_to_antigravity_rejects_negative_cases` |
| `concurrency-lease-policy` | `plugins/fleet-core/tests/test_concurrency_policy.py::test_bounded_leases_prevent_duplicate_and_abandoned_ownership` | `plugins/fleet-core/tests/test_concurrency_policy.py::test_bounded_leases_prevent_duplicate_and_abandoned_ownership_rejects_negative_cases` |
| `cross-runtime-acceptance-tools` | `plugins/fleet-core/tests/test_saga_acceptance.py::test_saga_acceptance_compares_bounded_semantic_receipts` | `plugins/fleet-core/tests/test_saga_acceptance.py::test_saga_acceptance_compares_bounded_semantic_receipts_rejects_negative_cases` |
| `delegation-audit-state` | `plugins/fleet-core/tests/test_delegation_audit_state.py::test_delegation_audit_detects_missing_duplicate_and_wrong_owner_evidence` | `plugins/fleet-core/tests/test_delegation_audit_state.py::test_delegation_audit_detects_missing_duplicate_and_wrong_owner_evidence_rejects_negative_cases` |
| `mission-board-census-pagination` | `plugins/mission-control/tests/test_sdlc_manager.py::test_board_census_requires_every_page_before_complete` | `plugins/mission-control/tests/test_sdlc_manager.py::test_board_census_requires_every_page_before_complete_rejects_negative_cases` |
| `mission-board-operations` | `plugins/mission-control/tests/test_board_move_exit.py::test_board_move_requires_resolved_item_field_and_status` | `plugins/mission-control/tests/test_board_move_exit.py::test_board_move_requires_resolved_item_field_and_status_rejects_negative_cases` |
| `mission-control-runtime` | `plugins/mission-control/tests/test_sdlc_manager.py::test_runtime_normalizes_repository_inputs_and_typed_failures` | `plugins/mission-control/tests/test_sdlc_manager.py::test_runtime_normalizes_repository_inputs_and_typed_failures_rejects_negative_cases` |
| `mission-executor-profile-policy` | `plugins/mission-control/tests/test_executor_profile_lint.py::test_executor_profile_accepts_only_current_gemini_registry` | `plugins/mission-control/tests/test_executor_profile_lint.py::test_executor_profile_accepts_only_current_gemini_registry_rejects_negative_cases` |
| `mission-flow-metrics` | `plugins/mission-control/tests/test_metrics_contract.py::test_metrics_contract_covers_throughput_cycle_age_and_state_time` | `plugins/mission-control/tests/test_metrics_contract.py::test_metrics_contract_covers_throughput_cycle_age_and_state_time_rejects_negative_cases` |
| `mission-issue-contract` | `plugins/mission-control/tests/test_issue_contract_parity.py::test_generated_issue_contract_matches_schema_and_templates` | `plugins/mission-control/tests/test_issue_contract_parity.py::test_generated_issue_contract_matches_schema_and_templates_rejects_negative_cases` |
| `mission-issue-preparation` | `plugins/mission-control/tests/test_issue_prepare_compile_approve.py::test_issue_preparation_requires_review_and_approval_before_mutation` | `plugins/mission-control/tests/test_issue_prepare_compile_approve.py::test_issue_preparation_requires_review_and_approval_before_mutation_rejects_negative_cases` |
| `mission-label-operations` | `plugins/mission-control/tests/test_label_contract.py::test_label_skill_preserves_taxonomy_and_mutation_gate` | `plugins/mission-control/tests/test_label_contract.py::test_label_skill_preserves_taxonomy_and_mutation_gate_rejects_negative_cases` |
| `mission-milestone-operations` | `plugins/mission-control/tests/test_milestone_contract.py::test_milestone_skill_requires_objective_progress_and_risk_evidence` | `plugins/mission-control/tests/test_milestone_contract.py::test_milestone_skill_requires_objective_progress_and_risk_evidence_rejects_negative_cases` |
| `mission-project-flow` | `plugins/mission-control/tests/test_project_mappings_resolution.py::test_flow_resolves_project_field_issue_and_repository_before_mutation` | `plugins/mission-control/tests/test_project_mappings_resolution.py::test_flow_resolves_project_field_issue_and_repository_before_mutation_rejects_negative_cases` |
| `mission-rollout-operations` | `plugins/mission-control/tests/test_rollout_contract.py::test_rollout_skill_separates_status_gap_analysis_and_mutation` | `plugins/mission-control/tests/test_rollout_contract.py::test_rollout_skill_separates_status_gap_analysis_and_mutation_rejects_negative_cases` |
| `orphan-evidence-attestation` | `plugins/fleet-core/tests/test_orphan_evidence.py::test_orphan_evidence_requires_owner_shape_and_run_attestation` | `plugins/fleet-core/tests/test_orphan_evidence.py::test_orphan_evidence_requires_owner_shape_and_run_attestation_rejects_negative_cases` |
| `repository-quality-guards` | `plugins/fleet-core/tests/test_repository_quality_guards.py::test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps` | `plugins/fleet-core/tests/test_repository_quality_guards.py::test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps_rejects_negative_cases` |
| `saga-artifact-promotion` | `plugins/saga/tests/test_promote_scan.py::test_promotion_requires_canonical_target_provenance_and_no_conflict` | `plugins/saga/tests/test_promote_scan.py::test_promotion_requires_canonical_target_provenance_and_no_conflict_rejects_negative_cases` |
| `saga-code-review` | `plugins/saga/tests/test_code_review_contract.py::test_code_review_requires_plan_comparison_typed_findings_and_disposition` | `plugins/saga/tests/test_code_review_contract.py::test_code_review_requires_plan_comparison_typed_findings_and_disposition_rejects_negative_cases` |
| `saga-cross-runtime-reconciliation` | `plugins/saga/tests/test_cross_runtime_reconciliation.py::test_reconciliation_keeps_repository_truth_authoritative` | `plugins/saga/tests/test_cross_runtime_reconciliation.py::test_reconciliation_keeps_repository_truth_authoritative_rejects_negative_cases` |
| `saga-deploy-strategy` | `plugins/saga/tests/test_detect_deploy_strategy.py::test_deploy_strategy_detects_intent_without_executing_release` | `plugins/saga/tests/test_detect_deploy_strategy.py::test_deploy_strategy_detects_intent_without_executing_release_rejects_negative_cases` |
| `saga-executive-review` | `plugins/saga/tests/test_executive_review_contract.py::test_executive_review_challenges_value_without_delivery_approval` | `plugins/saga/tests/test_executive_review_contract.py::test_executive_review_challenges_value_without_delivery_approval_rejects_negative_cases` |
| `saga-external-action-boundary` | `plugins/saga/tests/test_external_action_adapters.py::test_external_action_requires_intent_workspace_adapter_and_authority` | `plugins/saga/tests/test_external_action_adapters.py::test_external_action_requires_intent_workspace_adapter_and_authority_rejects_negative_cases` |
| `saga-fleet-doctor` | `plugins/saga/tests/test_fleet_doctor.py::test_fleet_doctor_blocks_required_unknown_failed_and_unavailable` | `plugins/saga/tests/test_fleet_doctor.py::test_fleet_doctor_blocks_required_unknown_failed_and_unavailable_rejects_negative_cases` |
| `saga-handoff` | `plugins/saga/tests/test_handoff_envelope.py::test_handoff_names_artifacts_evidence_risks_and_external_authority` | `plugins/saga/tests/test_handoff_envelope.py::test_handoff_names_artifacts_evidence_risks_and_external_authority_rejects_negative_cases` |
| `saga-ideation` | `plugins/saga/tests/test_ideate_contract.py::test_ideation_preserves_seeds_alternatives_disagreement_and_artifact` | `plugins/saga/tests/test_ideate_contract.py::test_ideation_preserves_seeds_alternatives_disagreement_and_artifact_rejects_negative_cases` |
| `saga-investigation` | `plugins/saga/tests/test_investigate_contract.py::test_investigation_separates_observation_hypothesis_experiment_and_uncertainty` | `plugins/saga/tests/test_investigate_contract.py::test_investigation_separates_observation_hypothesis_experiment_and_uncertainty_rejects_negative_cases` |
| `saga-lifecycle-settlement` | `plugins/saga/tests/test_lifecycle_obligations.py::test_lifecycle_advances_only_when_required_obligations_have_independent_receipts` | `plugins/saga/tests/test_lifecycle_obligations.py::test_lifecycle_advances_only_when_required_obligations_have_independent_receipts_rejects_negative_cases` |
| `saga-loop-routing` | `plugins/saga/tests/test_loop_routing.py::test_loop_routes_to_earliest_unsettled_required_obligation_idempotently` | `plugins/saga/tests/test_loop_routing.py::test_loop_routes_to_earliest_unsettled_required_obligation_idempotently_rejects_negative_cases` |
| `saga-manifest-provenance-ledgers` | `plugins/saga/tests/test_manifest_store.py::test_manifest_round_trip_binds_input_output_digest_and_owner` | `plugins/saga/tests/test_manifest_store.py::test_manifest_round_trip_binds_input_output_digest_and_owner_rejects_negative_cases` |
| `saga-office-hours` | `plugins/saga/tests/test_office_hours_contract.py::test_office_hours_returns_frame_and_route_without_completion_claim` | `plugins/saga/tests/test_office_hours_contract.py::test_office_hours_returns_frame_and_route_without_completion_claim_rejects_negative_cases` |
| `saga-operator-safety` | `plugins/saga/tests/test_operator_safety_contract.py::test_operator_safety_preserves_choice_escalation_escape_and_formatting` | `plugins/saga/tests/test_operator_safety_contract.py::test_operator_safety_preserves_choice_escalation_escape_and_formatting_rejects_negative_cases` |
| `saga-optimization` | `plugins/saga/tests/test_optimize_contract.py::test_optimization_requires_baseline_change_measurement_and_stop_condition` | `plugins/saga/tests/test_optimize_contract.py::test_optimization_requires_baseline_change_measurement_and_stop_condition_rejects_negative_cases` |
| `saga-outcome-board-integration` | `plugins/saga/tests/test_outcome_board_sync.py::test_outcome_board_reconciliation_is_idempotent_and_authority_bounded` | `plugins/saga/tests/test_outcome_board_sync.py::test_outcome_board_reconciliation_is_idempotent_and_authority_bounded_rejects_negative_cases` |
| `saga-outcome-economics-liveness` | `plugins/saga/tests/test_outcome_economics.py::test_outcome_telemetry_never_converts_activity_or_spend_to_completion` | `plugins/saga/tests/test_outcome_economics.py::test_outcome_telemetry_never_converts_activity_or_spend_to_completion_rejects_negative_cases` |
| `saga-outcome-merge-worktrees` | `plugins/saga/tests/test_outcome_merge_queue.py::test_outcome_merge_settles_only_from_verified_integration_receipt` | `plugins/saga/tests/test_outcome_merge_queue.py::test_outcome_merge_settles_only_from_verified_integration_receipt_rejects_negative_cases` |
| `saga-outcome-orchestration` | `plugins/saga/tests/test_outcome_completion.py::test_outcome_refuses_completion_without_owned_leaf_and_settlement_evidence` | `plugins/saga/tests/test_outcome_completion.py::test_outcome_refuses_completion_without_owned_leaf_and_settlement_evidence_rejects_negative_cases` |
| `saga-planning` | `plugins/saga/tests/test_plan_contract.py::test_plan_contract_requires_decisions_files_dependencies_tests_and_authority` | `plugins/saga/tests/test_plan_contract.py::test_plan_contract_requires_decisions_files_dependencies_tests_and_authority_rejects_negative_cases` |
| `saga-plugin-readiness` | `plugins/saga/tests/test_plugin_dependency_resolver.py::test_plugin_readiness_resolves_target_plugins_and_consensus_mapping` | `plugins/saga/tests/test_plugin_dependency_resolver.py::test_plugin_readiness_resolves_target_plugins_and_consensus_mapping_rejects_negative_cases` |
| `saga-provider-pulse` | `plugins/saga/tests/test_provider_pulse.py::test_provider_pulse_reports_quality_drift_without_routing_authority` | `plugins/saga/tests/test_provider_pulse.py::test_provider_pulse_reports_quality_drift_without_routing_authority_rejects_negative_cases` |
| `saga-quality-assurance` | `plugins/saga/tests/test_qa_contract.py::test_qa_requires_risk_scenarios_checks_failure_disposition_and_independence` | `plugins/saga/tests/test_qa_contract.py::test_qa_requires_risk_scenarios_checks_failure_disposition_and_independence_rejects_negative_cases` |
| `saga-requirements-brainstorm` | `plugins/saga/tests/test_brainstorm_contract.py::test_brainstorm_requires_requirements_assumptions_actors_and_acceptance_examples` | `plugins/saga/tests/test_brainstorm_contract.py::test_brainstorm_requires_requirements_assumptions_actors_and_acceptance_examples_rejects_negative_cases` |
| `saga-retrospective` | `plugins/saga/tests/test_retro_contract.py::test_retro_records_evidence_backed_learning_without_state_mutation` | `plugins/saga/tests/test_retro_contract.py::test_retro_records_evidence_backed_learning_without_state_mutation_rejects_negative_cases` |
| `saga-session-context-and-spores` | `plugins/saga/tests/test_spore_seam_roundtrip.py::test_session_reconstruction_uses_bounded_canonical_evidence_and_truthful_status` | `plugins/saga/tests/test_spore_seam_roundtrip.py::test_session_reconstruction_uses_bounded_canonical_evidence_and_truthful_status_rejects_negative_cases` |
| `saga-ship-ceremony` | `plugins/saga/tests/test_ship_ceremony.py::test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation` | `plugins/saga/tests/test_ship_ceremony.py::test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation_rejects_negative_cases` |
| `saga-specification` | `plugins/saga/tests/test_spec_contract.py::test_spec_defines_outcome_scope_failures_and_acceptance_without_how` | `plugins/saga/tests/test_spec_contract.py::test_spec_defines_outcome_scope_failures_and_acceptance_without_how_rejects_negative_cases` |
| `saga-strategy` | `plugins/saga/tests/test_strategy_contract.py::test_strategy_records_choice_alternatives_constraints_and_revisit_trigger` | `plugins/saga/tests/test_strategy_contract.py::test_strategy_records_choice_alternatives_constraints_and_revisit_trigger_rejects_negative_cases` |
| `saga-work-execution` | `plugins/saga/tests/test_work_contract.py::test_work_obeys_units_write_sets_checks_and_authority_gates` | `plugins/saga/tests/test_work_contract.py::test_work_obeys_units_write_sets_checks_and_authority_gates_rejects_negative_cases` |
| `shared-runtime-resolution` | `plugins/fleet-core/tests/test_fleet_commons_resolution.py::test_shared_runtime_resolution_is_logical_portable_and_target_bound` | `plugins/fleet-core/tests/test_fleet_commons_resolution.py::test_shared_runtime_resolution_is_logical_portable_and_target_bound_rejects_negative_cases` |

## Seven Dependency-Ordered Migration Units

The ledger records no candidate-level `adjacent_dependencies` for these approved rows. That means
there is no ledger-authored graph to preserve, not that implementation is independent. The
seven units U0-U6 are retained because the target evidence supports six distinct product/consumer
boundaries plus the schema/evidence gate that every boundary consumes. Collapsing Fleet Core,
Mission Control, Multi-Agent Consensus, Saga substrate, Saga orchestration, or Saga methods would
mix product ownership or break the named dependency order. Splitting by source package or by each
of 51 rows would add unsupported coordination. The ordering is derived from actual Antigravity
consumers and the table above; it does not use source path proximity or file-copy order. U7 below
is closeout, not an eighth migration unit.

### U0. Add the closed migration-evidence gate

**Goal:** Make it impossible to mark a survivor migrated without exact target and evidence
bindings.

**Stable IDs:** all 51 as data only; no semantic implementation.

**Files:**

- `scripts/port_ledger.py`
- `plugins/saga/tests/test_port_ledger.py`
- `plugins/saga/tests/fixtures/port-ledger/complete.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-planned.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-migrated.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-blocked.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-v1-mislabeled.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-unknown-version.yaml`
- `plugins/saga/tests/fixtures/port-ledger/migration-evidence-valid.json`
- `plugins/saga/tests/fixtures/port-ledger/migration-evidence-invalid.json`
- `docs/ports/2026-07-30-saga-reliability/ledger.yaml`
- `docs/ports/2026-07-30-saga-reliability/README.md`
- `docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml`
- `docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json`

**Approach:** Add the deterministic `upgrade-v2`, the closed v2 migration object, exact real-ledger
ID/contract/packet-claim equality tests, `record-migrations`, `validate --require-migrated`,
target-path containment, exact 51-row positive/negative mapping, sanitized source/host binding,
full typed evidence-manifest validation, digest vectors, and atomic replacement. Initialize all 51
approved rows as `planned`; preserve every v1 decision and packet; do not add migration fields to
non-survivors.

**Blocking tests:** exact 51-ID and 102-node equality; deterministic v1-to-v2 preservation; ordinary
v1 acceptance; migration-bearing v1 rejection; unknown-version rejection; duplicate, extra, and
non-survivor rejection; both typed result schemas; failed or missing evidence; stale source or host
receipt; operator-gate reset; changed manifest bytes; blocked capability; unsafe target path; source
`team-execution` target; migration before tests; packet digest vectors; numeric packet-claim
equality; and atomic byte preservation on every failure.

### U1. Establish shared runtime and evidence primitives

**Goal:** Complete the `fleet-core` contracts consumed by every later plugin.

**Stable IDs:** `shared-runtime-resolution`, `bridge-receipt-contract`,
`delegation-audit-state`, `concurrency-lease-policy`, `orphan-evidence-attestation`,
`cross-runtime-acceptance-tools`, and `repository-quality-guards`.

**Dependencies:** U0.

**Files:** The exact literal Fleet Core paths in the compiled Workflow Contract, including
`plugins/fleet-core/references/antigravity-host-contract-surfaces.json`,
`plugins/fleet-core/scripts/fleet_commons/host_contract_lint.py`,
`plugins/fleet-core/tests/test_host_contract_lint.py`, and `scripts/validate_plugins.py`.

**Approach:** Reuse current shims and receipt types, add only missing semantic modules, keep all
state and receipts deterministic, and add active-surface source-host lint coverage. No live host,
GitHub, model, or sibling call is part of these tests.

### U2. Complete Mission Control semantics

**Goal:** Make target GitHub and project operations typed, complete, and authority-bounded.

**Stable IDs:** `mission-control-runtime`, `mission-executor-profile-policy`,
`mission-board-census-pagination`, `mission-board-operations`, `mission-flow-metrics`,
`mission-issue-contract`, `mission-issue-preparation`, `mission-label-operations`,
`mission-milestone-operations`, `mission-project-flow`, and `mission-rollout-operations`.

**Dependencies:** U1.

**Files:** The exact literal Mission Control paths in the compiled Workflow Contract.

**Approach:** Use existing injectable API seams and generated-contract workflow. For
`mission-board-census-pagination`, first extend only `plugins/mission-control/scripts/sdlc_manager.py`
and `plugins/mission-control/tests/test_sdlc_manager.py`; prove repeated-cursor, missing-cursor, and
partial-census failures. Do not add a second client, `board_census.py`, or `check_pagination.py`
unless distinct ownership is proved and Jeff approves a contract amendment. Other positive tests
exercise normalized fixture responses. Negative tests prove target resolution, typed errors, and
the separation between preparation and remote mutation. No live GitHub action is authorized.

### U3. Close the Team Execution mapping in Multi-Agent Consensus

**Goal:** Preserve the approved security-audit outcome in the actual Antigravity reviewer plugin.

**Stable IDs:** `application-security-audit`.

**Dependencies:** U1.

**Files:** The exact literal Multi-Agent Consensus paths in the compiled Workflow Contract.

**Approach:** Adapt the current skill in place. Reference current Gemini and effort policy through
`fleet-core`. Do not create `team-execution`, claim a host capability, or port source worker
plumbing.

### U4. Complete Saga evidence, safety, and settlement substrate

**Goal:** Establish the canonical evidence and authority contracts required by Saga routing and
commands.

**Stable IDs:** `saga-manifest-provenance-ledgers`, `saga-operator-safety`,
`saga-external-action-boundary`, `saga-fleet-doctor`, `saga-artifact-promotion`,
`saga-lifecycle-settlement`, `saga-cross-runtime-reconciliation`, `saga-plugin-readiness`, and
`codex-portability-contracts`.

**Dependencies:** U1-U3.

**Files:** The exact literal Saga substrate paths in the compiled Workflow Contract.

**Approach:** Preserve repository-canonical evidence, current target state schemas, sanitized host
receipt rules, and separate authority for external actions. Update the curated Saga docs model
before rendered pages or visuals. Runtime-specific provenance remains visible but never
executable.

### U5. Complete Saga orchestration and operational controls

**Goal:** Build routing and outcome behavior on the settled evidence substrate.

**Stable IDs:** `saga-loop-routing`, `saga-session-context-and-spores`,
`saga-outcome-orchestration`, `saga-outcome-board-integration`,
`saga-outcome-economics-liveness`, `saga-outcome-merge-worktrees`, `saga-handoff`,
`saga-ship-ceremony`, and `saga-deploy-strategy`.

**Dependencies:** U2 and U4.

**Files:** The exact literal Saga orchestration paths in the compiled Workflow Contract.

**Approach:** Derive state from canonical receipts, keep retry idempotent, and keep GitHub, Git,
merge, and deployment actions behind separate authority. Tests use fixtures and injected
boundaries only.

### U6. Adapt Saga lifecycle methods and close target evidence

**Goal:** Preserve the remaining user-facing method outcomes without needless new runtime code.

**Stable IDs:** `saga-code-review`, `saga-executive-review`, `saga-ideation`,
`saga-investigation`, `saga-office-hours`, `saga-optimization`, `saga-planning`,
`saga-provider-pulse`, `saga-quality-assurance`, `saga-requirements-brainstorm`,
`saga-retrospective`, `saga-specification`, `saga-strategy`, and `saga-work-execution`.

**Dependencies:** U4-U5.

**Files:** The exact literal Saga method paths in the compiled Workflow Contract.

**Approach:** For the 13 partial method rows, begin with semantic gap tests and change prose or
code only where the current Antigravity contract fails. `saga-provider-pulse` is absent and gets
the small receipt-driven target implementation named in the table. Every method uses canonical
docs, target tool names, Gemini policy, and explicit stop conditions.

### Issue #15 plugin version ownership

This issue owns the feature-version changes required to make the four migrated plugin contracts
visible before issue #22 performs release qualification:

| plugin | current version | intended version | exact manifest | exact changelog | exact version test |
|---|---:|---:|---|---|---|
| Saga | `1.5.0` | `1.6.0` | `plugins/saga/plugin.json` | `plugins/saga/CHANGELOG.md` | `plugins/saga/tests/test_saga_plugin.py` |
| Fleet Core | `0.9.0` | `0.10.0` | `plugins/fleet-core/plugin.json` | `plugins/fleet-core/CHANGELOG.md` | `plugins/fleet-core/tests/test_fleet_commons.py` |
| Mission Control | `2.7.0` | `2.8.0` | `plugins/mission-control/plugin.json` | `plugins/mission-control/CHANGELOG.md` | `plugins/mission-control/tests/test_prompt_alignment.py` |
| Multi-Agent Consensus | `2.3.0` | `2.4.0` | `plugins/multi-agent-consensus/plugin.json` | `plugins/multi-agent-consensus/CHANGELOG.md` | `plugins/multi-agent-consensus/tests/test_multi_agent_consensus_plugin.py` |

Each test asserts the exact intended version and parity between the manifest and the newest
changelog heading. `scripts/validate_plugins.py` asserts that every plugin version is valid and
that packaged metadata agrees. This issue does not tag, install, deploy, or qualify a release;
issue #22 consumes these exact versions after the migration ledger is complete.

### U7. Closeout after the seven migration units

**Goal:** Prove all 51 rows as one exact campaign and atomically change their migration states to
`migrated`.

**Dependencies:** U0-U6.

**Files:**

- `docs/ports/2026-07-30-saga-reliability/ledger.yaml`
- `docs/ports/2026-07-30-saga-reliability/README.md`
- `docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json`
- `docs/code-reviews/2026-07-30-migrate-approved-port-survivors-code-review.md`

**Approach:** Run scoped suites first, then independent code review. Fix every actionable P0-P3
finding in the one bounded remediation assignment or reclassify it with concrete evidence. Run
one targeted recheck, then run the no-write Git/source/host refresh immediately before assembling
the evidence manifest. Root validates the manifest content and releases `record-migrations` only
when every named check and review result passes. The command writes all 51 migration records
atomically and
`validate --require-migrated` proves no approved row remains `planned`, `blocked`, `partial`, or
`absent`.

## Deterministic Validation

### Git-bearing node ownership

Only `test-git-bearing-nodes`, using role `git-integration-operator` and profile `work_medium`, may
run these nodes:

- `plugins/saga/tests/test_port_ledger.py::test_release_refresh_uses_controlled_temporary_repositories`
- `plugins/saga/tests/test_port_ledger.py::test_release_refresh_rejects_drift_byte_identically`
- `plugins/saga/tests/test_promote_scan.py::test_promotion_requires_canonical_target_provenance_and_no_conflict`
- `plugins/saga/tests/test_promote_scan.py::test_promotion_requires_canonical_target_provenance_and_no_conflict_rejects_negative_cases`
- `plugins/saga/tests/test_outcome_merge_queue.py::test_outcome_merge_settles_only_from_verified_integration_receipt`
- `plugins/saga/tests/test_outcome_merge_queue.py::test_outcome_merge_settles_only_from_verified_integration_receipt_rejects_negative_cases`
- `plugins/saga/tests/test_ship_ceremony.py::test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation`
- `plugins/saga/tests/test_ship_ceremony.py::test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation_rejects_negative_cases`

They run only against explicitly created temporary repositories, with no remote configured,
network-disabled adapters, deterministic author identity, and cleanup after result capture. All
other roles receive a deselection file containing these exact node IDs and run only Git-free
nodes. Full-suite evidence is the union of the Git integration result and the scenario tester
result; neither role may claim the other's nodes. Final repository delivery is not this assignment
and remains outside this workflow.

Run narrow checks before broad checks:

```bash
python3 scripts/port_ledger.py validate \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

python3 scripts/port_ledger.py report \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

uv run pytest plugins/saga/tests/test_port_ledger.py -q
uv run pytest --collect-only -q \
  $(python3 scripts/port_ledger.py test-nodes \
    docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml)

uv run pytest plugins/fleet-core/tests -q
uv run pytest plugins/mission-control/tests -q
uv run pytest plugins/multi-agent-consensus/tests -q
uv run pytest plugins/saga/tests -q \
  $(python3 scripts/port_ledger.py pytest-args \
    docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml \
    --partition non-git)

uv run python plugins/saga/scripts/render_docs_visuals.py --check

uv run ruff check plugins scripts
uv run mypy plugins scripts
python3 scripts/validate_plugins.py \
  --capability-profile repository-validation \
  --observe-host \
  --json
uv run pytest -q \
  $(python3 scripts/port_ledger.py pytest-args \
    docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml \
    --partition non-git)

python3 scripts/port_ledger.py validate --require-migrated \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml
```

The Git integration operator performs release-drift and cleanliness proof because no other role may
run Git. Before implementation and again after recheck, immediately before migration recording, it
captures local `HEAD`, local `origin/main`, index tree, worktree/untracked paths, and
selected-surface identities for Antigravity, Claude, and Codex. Claude and Codex must have matching
local `HEAD` and
`origin/main`; Antigravity inventory stays bound to `origin/main` while feature `HEAD` is recorded
separately. The before/after sibling states must be byte-identical, and the final Antigravity diff
must equal the workflow write-set union with `.serena/project.yml` excluded.

### Required negative cases

- A 50-ID or 52-ID migration mapping fails without changing ledger bytes.
- A blocked, metadata-only, rejected, or superseded ID in implementation evidence fails.
- One source edit packet owned by no approved row or two rows fails.
- A required capability newly reported as `failed`, `unknown`, or `unavailable` leaves the
  survivor blocked and prevents the all-migrated gate.
- A claimed fallback absent from the probe catalog or current receipt fails.
- A target path under `plugins/team-execution`, `.claude`, a sibling repository, installed-plugin
  root, absolute home path, or `.serena/project.yml` fails.
- Active `AskUserQuestion`, Claude workflow API, source-host model, fixed brain root, or unproven
  scheduling/isolation language fails host-contract validation.
- A copied source file, matching source test name, or text-similarity score without target semantic
  evidence fails.
- A positive or negative node missing from the validated test result, a failed or skipped required
  node, a stale result, a changed evidence-manifest byte, or a target path not present in the
  reviewed changed-path set fails migration recording.
- Canonical Saga docs that disagree with the docs model, use source package ownership, or leave
  generated visuals stale fail.
- Remote mutation without a separate authority receipt fails even when local preparation passes.

## Release-Drift Refresh

The pre-implementation Git assignment repeats issue #16 discovery as a no-write comparison using
the current committed ledger and safe host receipt. It emits `assignment-result.v1` and writes no
repository path. Only after that result passes does `upgrade-v2` initialize migration planning. A
byte-identical refresh preserves all decisions. Any changed
source snapshot, selected surface, packet content identity, semantic contract, packet ownership, or
host receipt invalidates affected decisions to `pending` under the existing ledger rules and
stops before U0.

Repeat the same no-write comparison after the one recheck, immediately before migration recording.
That result and its exact source/host bindings are included in the evidence
manifest. `record-migrations` compares the current bytes with those bindings and fails atomically
on any mismatch, changed evidence, or operator-gate reset. Implementation files on the
Antigravity feature branch are not source candidates because Antigravity comparison remains bound
to local `origin/main`. If release drift appears, do not edit the traceability table in place,
invent a new candidate, or carry old migration evidence forward; return to the operator decision
gate.

## Root-Orchestrated Codex Verified Workflow

Root releases only dependency-ready direct-child assignments, validates their typed results, and
reports gates. Root does not implement, test, review, remediate, or run Git. All overlapping write
sets are dependency-ordered. The first plan reviewer was correctly read-only and returned
`reviewer-result.v1`; it could not durably write the plan-stage review artifact. The current
declared-write remediation assignment
`/root/issue15_remediate_plan` is the authorized transcriber for
`docs/reviews/2026-07-30-migrate-approved-port-survivors-plan-doc-review.md`. That correction is
plan-stage orchestration only and is not repeated in the implementation graph.

The implementation graph uses the active Verified Workflows 3.0.0 registry schema and role
specification version 1. The active registry digest is
`c11c5f062bf33771e46e8ce5c42b0fb15334bd6b1e20f5349f9d1314199afecb`.
Every role/profile pair below is registry-allowed and every reviewer is read-only with
`reviewer-result.v1`; workers, testers, Git operators, transcription assignments, and remediation
return `assignment-result.v1`. Two independent code-review lenses are proportional to a 51-row,
four-plugin migration. One bounded remediation and one recheck are the only automatic repair
cycle.

### Workflow Contract

| id | depends | role | profile | writes | completion | fallback |
|---|---|---|---|---|---|---|
| `refresh-approved-ledger` | `none` | `git-integration-operator` | `work_medium` | `none` | Run the no-write three-repository and safe-host refresh; prove byte-identical decision evidence, exact 51 approved IDs, unchanged siblings, and final `git diff --name-only`; return `assignment-result.v1`; drift stops. | `none` |
| `implement-migration-gate` | `refresh-approved-ledger` | `implementation-worker` | `work_high` | `docs/ports/2026-07-30-saga-reliability/README.md,docs/ports/2026-07-30-saga-reliability/ledger.yaml,docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml,plugins/saga/tests/fixtures/port-ledger/complete.yaml,plugins/saga/tests/fixtures/port-ledger/migration-blocked.yaml,plugins/saga/tests/fixtures/port-ledger/migration-evidence-invalid.json,plugins/saga/tests/fixtures/port-ledger/migration-evidence-valid.json,plugins/saga/tests/fixtures/port-ledger/migration-migrated.yaml,plugins/saga/tests/fixtures/port-ledger/migration-planned.yaml,plugins/saga/tests/fixtures/port-ledger/migration-unknown-version.yaml,plugins/saga/tests/fixtures/port-ledger/migration-v1-mislabeled.yaml,plugins/saga/tests/test_port_ledger.py,scripts/port_ledger.py` | Implement deterministic v1-to-v2 upgrade, the closed plan and evidence schemas, exact ID/contract/packet/node checks, digest vectors, atomic failure, and v1/unknown-version rules; return `assignment-result.v1`. | `none` |
| `implement-fleet-survivors` | `implement-migration-gate` | `implementation-worker` | `work_high` | `plugins/fleet-core/CHANGELOG.md,plugins/fleet-core/plugin.json,plugins/fleet-core/references/antigravity-host-contract-surfaces.json,plugins/fleet-core/references/saga-acceptance-contract.json,plugins/fleet-core/scripts/fleet_commons/bridge_receipt.py,plugins/fleet-core/scripts/fleet_commons/concurrency_policy.py,plugins/fleet-core/scripts/fleet_commons/delegation_audit.py,plugins/fleet-core/scripts/fleet_commons/delegation_state.py,plugins/fleet-core/scripts/fleet_commons/host_contract_lint.py,plugins/fleet-core/scripts/fleet_commons/lease_broker.py,plugins/fleet-core/scripts/fleet_commons/liveness_engine.py,plugins/fleet-core/scripts/fleet_commons/orphan_evidence.py,plugins/fleet-core/scripts/fleet_commons/output_attestation.py,plugins/fleet-core/scripts/fleet_commons/plugin_resolution.py,plugins/fleet-core/scripts/fleet_commons/saga_acceptance.py,plugins/fleet-core/scripts/fleet_commons/workflow_compat.py,plugins/fleet-core/scripts/fleet_commons_shim.py,plugins/fleet-core/tests/fixtures/orphan-evidence/duplicate-schema.json,plugins/fleet-core/tests/fixtures/orphan-evidence/valid.json,plugins/fleet-core/tests/test_bridge_receipt.py,plugins/fleet-core/tests/test_concurrency_policy.py,plugins/fleet-core/tests/test_delegation_audit_state.py,plugins/fleet-core/tests/test_fleet_commons.py,plugins/fleet-core/tests/test_fleet_commons_resolution.py,plugins/fleet-core/tests/test_host_contract_lint.py,plugins/fleet-core/tests/test_lease_broker.py,plugins/fleet-core/tests/test_orphan_evidence.py,plugins/fleet-core/tests/test_repository_quality_guards.py,plugins/fleet-core/tests/test_saga_acceptance.py,plugins/fleet-core/tests/test_workflow_compat.py,plugins/mission-control/scripts/fleet_commons_shim.py,plugins/saga/scripts/fleet_commons_shim.py,scripts/validate_plugins.py` | Implement U1, expand the single canonical host selector to the exact changed runtime paths, enforce all seven Fleet Core rows, and return `assignment-result.v1`. | `none` |
| `implement-mission-survivors` | `implement-fleet-survivors` | `implementation-worker` | `work_high` | `plugins/mission-control/CHANGELOG.md,plugins/mission-control/commands/board.md,plugins/mission-control/commands/issue.md,plugins/mission-control/commands/metrics.md,plugins/mission-control/commands/triage.md,plugins/mission-control/config/generated/check_issue_contract_parity.py,plugins/mission-control/config/generated/issue_contract_data.py,plugins/mission-control/config/generated/issue_contract_data.py.sha256,plugins/mission-control/config/generated/issue_contract_shim.py,plugins/mission-control/config/generated/issue_contract_shim.py.sha256,plugins/mission-control/config/project-mappings.json,plugins/mission-control/config/sdlc-schema.json,plugins/mission-control/plugin.json,plugins/mission-control/scripts/executor_profile_lint.py,plugins/mission-control/scripts/sdlc_manager.py,plugins/mission-control/scripts/sync_template_docs.py,plugins/mission-control/skills/board/SKILL.md,plugins/mission-control/skills/board/references/graphql-queries.md,plugins/mission-control/skills/board/references/kanban-workflow.md,plugins/mission-control/skills/flow/SKILL.md,plugins/mission-control/skills/issues/SKILL.md,plugins/mission-control/skills/issues/references/issue-types.md,plugins/mission-control/skills/issues/references/templates-reference.md,plugins/mission-control/skills/labels/SKILL.md,plugins/mission-control/skills/labels/references/labels-reference.md,plugins/mission-control/skills/metrics/SKILL.md,plugins/mission-control/skills/metrics/references/metrics-targets.md,plugins/mission-control/skills/milestones/SKILL.md,plugins/mission-control/skills/milestones/references/objective-workflow.md,plugins/mission-control/skills/rollout/SKILL.md,plugins/mission-control/skills/rollout/references/work-hierarchy.md,plugins/mission-control/tests/test_board_add_multi_project.py,plugins/mission-control/tests/test_board_move_exit.py,plugins/mission-control/tests/test_executor_profile_lint.py,plugins/mission-control/tests/test_flow_subcommands.py,plugins/mission-control/tests/test_graphql_issue_resolution.py,plugins/mission-control/tests/test_issue_contract_parity.py,plugins/mission-control/tests/test_issue_create_prepared.py,plugins/mission-control/tests/test_issue_prepare.py,plugins/mission-control/tests/test_issue_prepare_compile_approve.py,plugins/mission-control/tests/test_issue_source_artifacts.py,plugins/mission-control/tests/test_label_contract.py,plugins/mission-control/tests/test_metrics_contract.py,plugins/mission-control/tests/test_milestone_contract.py,plugins/mission-control/tests/test_project_mappings_resolution.py,plugins/mission-control/tests/test_prompt_alignment.py,plugins/mission-control/tests/test_rollout_contract.py,plugins/mission-control/tests/test_sdlc_manager.py,plugins/mission-control/tests/test_template_sync.py,plugins/mission-control/tests/test_typed_exceptions.py` | Implement U2 through the existing typed runtime and pagination seam, preserve mutation gates, bump Mission Control to 2.8.0, and return `assignment-result.v1`. | `none` |
| `implement-consensus-survivor` | `implement-fleet-survivors` | `implementation-worker` | `work_high` | `plugins/multi-agent-consensus/CHANGELOG.md,plugins/multi-agent-consensus/plugin.json,plugins/multi-agent-consensus/skills/appsec-audit/SKILL.md,plugins/multi-agent-consensus/tests/test_appsec_audit.py,plugins/multi-agent-consensus/tests/test_multi_agent_consensus_plugin.py` | Implement U3 without a new plugin or false independence claim, bump Multi-Agent Consensus to 2.4.0, and return `assignment-result.v1`. | `none` |
| `implement-saga-substrate` | `implement-consensus-survivor,implement-mission-survivors` | `implementation-worker` | `work_high` | `plugins/saga/commands/fleet-doctor.md,plugins/saga/commands/promote.md,plugins/saga/docs/README.md,plugins/saga/docs/model/saga-docs-model.yaml,plugins/saga/docs/portability.md,plugins/saga/references/command_dry_runs.md,plugins/saga/references/escape_hatches.md,plugins/saga/references/fleet-doctor-sources.md,plugins/saga/references/formatting-style.md,plugins/saga/references/harness-escalation-policy.md,plugins/saga/references/lifecycle-obligation-contract.md,plugins/saga/references/lifecycle-obligation-schema.json,plugins/saga/references/operator-choice.md,plugins/saga/references/outcome-cross-runtime.md,plugins/saga/references/saga-spec.md,plugins/saga/references/transition-receipt-schema.json,plugins/saga/scripts/external_action_adapters.py,plugins/saga/scripts/external_action_contract.py,plugins/saga/scripts/external_action_egress.py,plugins/saga/scripts/external_action_workspace.py,plugins/saga/scripts/fleet_doctor.py,plugins/saga/scripts/host_capability_gate.py,plugins/saga/scripts/journal_triggers.py,plugins/saga/scripts/lifecycle_obligations.py,plugins/saga/scripts/lifecycle_state.py,plugins/saga/scripts/manifest_reader.py,plugins/saga/scripts/manifest_store.py,plugins/saga/scripts/override_rate_reader.py,plugins/saga/scripts/plugin_dependency_resolver.py,plugins/saga/scripts/promote_scan.py,plugins/saga/scripts/provenance_manifest.py,plugins/saga/scripts/reconcile.py,plugins/saga/scripts/reconcile_controller.py,plugins/saga/scripts/run_ledger.py,plugins/saga/scripts/saga.py,plugins/saga/scripts/transition_receipts.py,plugins/saga/skills/fleet-doctor/SKILL.md,plugins/saga/skills/promote/SKILL.md,plugins/saga/skills/promote/references/promotion-contract.md,plugins/saga/tests/test_cross_runtime_reconciliation.py,plugins/saga/tests/test_external_action_adapters.py,plugins/saga/tests/test_fleet_doctor.py,plugins/saga/tests/test_lifecycle_obligations.py,plugins/saga/tests/test_manifest_consumer_matrix.py,plugins/saga/tests/test_manifest_reader.py,plugins/saga/tests/test_manifest_store.py,plugins/saga/tests/test_operator_safety_contract.py,plugins/saga/tests/test_plugin_dependency_resolver.py,plugins/saga/tests/test_promote_scan.py,plugins/saga/tests/test_run_ledger.py,plugins/saga/tests/test_saga_docs_coverage.py,plugins/saga/tests/test_saga_saga.py,plugins/saga/tests/test_transition_receipts.py` | Implement U4 with canonical evidence, host gates, authority boundaries, settlement, and documentation; return `assignment-result.v1`. | `none` |
| `implement-saga-orchestration` | `implement-saga-substrate` | `implementation-worker` | `work_high` | `plugins/saga/agents/lifecycle-router.md,plugins/saga/commands/handoff.md,plugins/saga/commands/loop.md,plugins/saga/commands/outcome.md,plugins/saga/references/handoff_failure_matrix.md,plugins/saga/scripts/board_progression.py,plugins/saga/scripts/ceremony_hazards.py,plugins/saga/scripts/detect_deploy_strategy.py,plugins/saga/scripts/discover_sessions.py,plugins/saga/scripts/extract_session_skeleton.py,plugins/saga/scripts/find_inflight_work.py,plugins/saga/scripts/handoff_envelope.py,plugins/saga/scripts/issue_progress.py,plugins/saga/scripts/load_saga_context.py,plugins/saga/scripts/merge_watcher.py,plugins/saga/scripts/outcome.py,plugins/saga/scripts/outcome_board_sync.py,plugins/saga/scripts/outcome_costs.py,plugins/saga/scripts/outcome_decompose.py,plugins/saga/scripts/outcome_dispatcher.py,plugins/saga/scripts/outcome_edges.py,plugins/saga/scripts/outcome_gate_transport.py,plugins/saga/scripts/outcome_github.py,plugins/saga/scripts/outcome_liveness.py,plugins/saga/scripts/outcome_merge.py,plugins/saga/scripts/outcome_orchestrator.py,plugins/saga/scripts/outcome_projection.py,plugins/saga/scripts/outcome_reconcile.py,plugins/saga/scripts/outcome_report.py,plugins/saga/scripts/outcome_spec.py,plugins/saga/scripts/outcome_store.py,plugins/saga/scripts/outcome_worktrees.py,plugins/saga/scripts/parse_issue.py,plugins/saga/scripts/reversibility_certificate.py,plugins/saga/scripts/saga_spore.py,plugins/saga/scripts/scaffold_checkpoint.py,plugins/saga/scripts/ship_ceremony.py,plugins/saga/scripts/ship_undo.py,plugins/saga/scripts/status_card.py,plugins/saga/skills/handoff/SKILL.md,plugins/saga/skills/loop/SKILL.md,plugins/saga/skills/loop/references/dispatch-table.md,plugins/saga/skills/loop/references/drive-and-resume.md,plugins/saga/skills/loop/references/generic-ask-compiler.md,plugins/saga/skills/outcome/SKILL.md,plugins/saga/tests/test_ceremony_hazards.py,plugins/saga/tests/test_detect_deploy_strategy.py,plugins/saga/tests/test_handoff_envelope.py,plugins/saga/tests/test_loop_routing.py,plugins/saga/tests/test_merge_watcher.py,plugins/saga/tests/test_outcome_board_sync.py,plugins/saga/tests/test_outcome_completion.py,plugins/saga/tests/test_outcome_dispatcher.py,plugins/saga/tests/test_outcome_economics.py,plugins/saga/tests/test_outcome_integration.py,plugins/saga/tests/test_outcome_liveness.py,plugins/saga/tests/test_outcome_merge_queue.py,plugins/saga/tests/test_outcome_reconcile.py,plugins/saga/tests/test_outcome_spec.py,plugins/saga/tests/test_outcome_store.py,plugins/saga/tests/test_outcome_worktrees.py,plugins/saga/tests/test_saga_spore.py,plugins/saga/tests/test_ship_ceremony.py,plugins/saga/tests/test_ship_undo.py,plugins/saga/tests/test_spore_seam_roundtrip.py,plugins/saga/tests/test_state_paths.py` | Implement U5 with fixture-backed routing and no external action; return `assignment-result.v1`. | `none` |
| `implement-saga-methods` | `implement-saga-orchestration` | `implementation-worker` | `work_high` | `plugins/saga/CHANGELOG.md,plugins/saga/commands/brainstorm.md,plugins/saga/commands/ceo-review.md,plugins/saga/commands/code-review.md,plugins/saga/commands/founder-review.md,plugins/saga/commands/ideate.md,plugins/saga/commands/investigate.md,plugins/saga/commands/office-hours.md,plugins/saga/commands/optimize.md,plugins/saga/commands/plan.md,plugins/saga/commands/pulse.md,plugins/saga/commands/qa.md,plugins/saga/commands/retro.md,plugins/saga/commands/spec.md,plugins/saga/commands/strategy.md,plugins/saga/commands/work.md,plugins/saga/plugin.json,plugins/saga/scripts/capability_elo.py,plugins/saga/scripts/provider_control_chart.py,plugins/saga/scripts/pulse.py,plugins/saga/scripts/qa_health_score.py,plugins/saga/scripts/second_opinion.py,plugins/saga/skills/brainstorm/SKILL.md,plugins/saga/skills/brainstorm/references/requirements-sections.md,plugins/saga/skills/code-review/SKILL.md,plugins/saga/skills/code-review/references/built-vs-planned.md,plugins/saga/skills/code-review/references/findings-schema.md,plugins/saga/skills/code-review/references/lens-catalog.md,plugins/saga/skills/code-review/references/validator.md,plugins/saga/skills/founder-review/SKILL.md,plugins/saga/skills/founder-review/references/ceo-cognition.md,plugins/saga/skills/founder-review/references/review-modes.md,plugins/saga/skills/ideate/SKILL.md,plugins/saga/skills/ideate/references/convergence-and-partnership.md,plugins/saga/skills/ideate/references/ideation-artifact.md,plugins/saga/skills/investigate/SKILL.md,plugins/saga/skills/investigate/references/debug-report.md,plugins/saga/skills/investigate/references/methodology.md,plugins/saga/skills/investigate/references/pattern-taxonomy.md,plugins/saga/skills/office-hours/SKILL.md,plugins/saga/skills/office-hours/references/frame-diagnostic.md,plugins/saga/skills/optimize/SKILL.md,plugins/saga/skills/optimize/references/experiment-loop.md,plugins/saga/skills/optimize/references/metric-taxonomy.md,plugins/saga/skills/plan/SKILL.md,plugins/saga/skills/plan/references/interrogation.md,plugins/saga/skills/plan/references/plan-sections.md,plugins/saga/skills/pulse/SKILL.md,plugins/saga/skills/pulse/references/manual-verification.md,plugins/saga/skills/qa/SKILL.md,plugins/saga/skills/qa/references/qa-report.md,plugins/saga/skills/qa/references/risk-taxonomy.md,plugins/saga/skills/retro/SKILL.md,plugins/saga/skills/retro/references/retro-passes.md,plugins/saga/skills/retro/references/retro-report.md,plugins/saga/skills/retro/references/self-edit-safety.md,plugins/saga/skills/spec/SKILL.md,plugins/saga/skills/spec/references/interrogation.md,plugins/saga/skills/spec/references/spec-template.md,plugins/saga/skills/strategy/SKILL.md,plugins/saga/skills/strategy/references/interview.md,plugins/saga/skills/strategy/references/strategy-template.md,plugins/saga/skills/work/SKILL.md,plugins/saga/skills/work/references/execution-strategy.md,plugins/saga/skills/work/references/pr-continuation-loop.md,plugins/saga/skills/work/references/test-and-gates.md,plugins/saga/tests/test_brainstorm_contract.py,plugins/saga/tests/test_code_review_contract.py,plugins/saga/tests/test_executive_review_contract.py,plugins/saga/tests/test_ideate_contract.py,plugins/saga/tests/test_investigate_contract.py,plugins/saga/tests/test_office_hours_contract.py,plugins/saga/tests/test_optimize_contract.py,plugins/saga/tests/test_plan_contract.py,plugins/saga/tests/test_provider_pulse.py,plugins/saga/tests/test_qa_contract.py,plugins/saga/tests/test_retro_contract.py,plugins/saga/tests/test_saga_plugin.py,plugins/saga/tests/test_spec_contract.py,plugins/saga/tests/test_strategy_contract.py,plugins/saga/tests/test_work_contract.py` | Implement U6, enforce the five-row host interpretation, bump Saga to 1.6.0, and return `assignment-result.v1`. | `none` |
| `test-git-bearing-nodes` | `implement-saga-methods` | `git-integration-operator` | `work_medium` | `none` | Run only the declared Git-bearing node IDs in controlled temporary repositories with network-disabled fixtures, then run final `git diff --name-only`; return `assignment-result.v1`. | `none` |
| `test-git-free-migration` | `test-git-bearing-nodes` | `scenario-tester` | `test_medium` | `none` | Run all 102 mapped semantic nodes except the declared Git-bearing nodes, four plugin suites, docs rendering, Ruff, mypy, canonical host lint, plugin validation, and full non-Git checks; return `assignment-result.v1` with exact collected nodes. | `none` |
| `review-migration-correctness` | `test-git-free-migration` | `devils-advocate-reviewer` | `review_high` | `none` | Return read-only `reviewer-result.v1` covering ledger fidelity, semantic loss, wrong boundary, host honesty, state transitions, and non-survivor scope. | `none` |
| `review-migration-evidence` | `test-git-free-migration` | `testing-reviewer` | `review_high` | `none` | Return read-only `reviewer-result.v1` covering all 51 positive and negative mappings, typed evidence content, isolation claims, atomic recording, and failure cases. | `none` |
| `transcribe-code-reviews` | `review-migration-correctness,review-migration-evidence` | `implementation-worker` | `work_medium` | `docs/code-reviews/2026-07-30-migrate-approved-port-survivors-code-review.md` | Transcribe both immutable reviewer results and all P0-P3 dispositions into the durable implementation code-review artifact; return `assignment-result.v1`; do not alter reviewer verdicts. | `none` |
| `remediate-migration-once` | `transcribe-code-reviews` | `remediation-worker` | `work_high` | `docs/code-reviews/2026-07-30-migrate-approved-port-survivors-code-review.md,docs/ports/2026-07-30-saga-reliability/README.md,docs/ports/2026-07-30-saga-reliability/ledger.yaml,docs/ports/2026-07-30-saga-reliability/migration-plan.v1.yaml,plugins/fleet-core/CHANGELOG.md,plugins/fleet-core/plugin.json,plugins/fleet-core/references/antigravity-host-contract-surfaces.json,plugins/fleet-core/references/saga-acceptance-contract.json,plugins/fleet-core/scripts/fleet_commons/bridge_receipt.py,plugins/fleet-core/scripts/fleet_commons/concurrency_policy.py,plugins/fleet-core/scripts/fleet_commons/delegation_audit.py,plugins/fleet-core/scripts/fleet_commons/delegation_state.py,plugins/fleet-core/scripts/fleet_commons/host_contract_lint.py,plugins/fleet-core/scripts/fleet_commons/lease_broker.py,plugins/fleet-core/scripts/fleet_commons/liveness_engine.py,plugins/fleet-core/scripts/fleet_commons/orphan_evidence.py,plugins/fleet-core/scripts/fleet_commons/output_attestation.py,plugins/fleet-core/scripts/fleet_commons/plugin_resolution.py,plugins/fleet-core/scripts/fleet_commons/saga_acceptance.py,plugins/fleet-core/scripts/fleet_commons/workflow_compat.py,plugins/fleet-core/scripts/fleet_commons_shim.py,plugins/fleet-core/tests/fixtures/orphan-evidence/duplicate-schema.json,plugins/fleet-core/tests/fixtures/orphan-evidence/valid.json,plugins/fleet-core/tests/test_bridge_receipt.py,plugins/fleet-core/tests/test_concurrency_policy.py,plugins/fleet-core/tests/test_delegation_audit_state.py,plugins/fleet-core/tests/test_fleet_commons.py,plugins/fleet-core/tests/test_fleet_commons_resolution.py,plugins/fleet-core/tests/test_host_contract_lint.py,plugins/fleet-core/tests/test_lease_broker.py,plugins/fleet-core/tests/test_orphan_evidence.py,plugins/fleet-core/tests/test_repository_quality_guards.py,plugins/fleet-core/tests/test_saga_acceptance.py,plugins/fleet-core/tests/test_workflow_compat.py,plugins/mission-control/CHANGELOG.md,plugins/mission-control/commands/board.md,plugins/mission-control/commands/issue.md,plugins/mission-control/commands/metrics.md,plugins/mission-control/commands/triage.md,plugins/mission-control/config/generated/check_issue_contract_parity.py,plugins/mission-control/config/generated/issue_contract_data.py,plugins/mission-control/config/generated/issue_contract_data.py.sha256,plugins/mission-control/config/generated/issue_contract_shim.py,plugins/mission-control/config/generated/issue_contract_shim.py.sha256,plugins/mission-control/config/project-mappings.json,plugins/mission-control/config/sdlc-schema.json,plugins/mission-control/plugin.json,plugins/mission-control/scripts/executor_profile_lint.py,plugins/mission-control/scripts/fleet_commons_shim.py,plugins/mission-control/scripts/sdlc_manager.py,plugins/mission-control/scripts/sync_template_docs.py,plugins/mission-control/skills/board/SKILL.md,plugins/mission-control/skills/board/references/graphql-queries.md,plugins/mission-control/skills/board/references/kanban-workflow.md,plugins/mission-control/skills/flow/SKILL.md,plugins/mission-control/skills/issues/SKILL.md,plugins/mission-control/skills/issues/references/issue-types.md,plugins/mission-control/skills/issues/references/templates-reference.md,plugins/mission-control/skills/labels/SKILL.md,plugins/mission-control/skills/labels/references/labels-reference.md,plugins/mission-control/skills/metrics/SKILL.md,plugins/mission-control/skills/metrics/references/metrics-targets.md,plugins/mission-control/skills/milestones/SKILL.md,plugins/mission-control/skills/milestones/references/objective-workflow.md,plugins/mission-control/skills/rollout/SKILL.md,plugins/mission-control/skills/rollout/references/work-hierarchy.md,plugins/mission-control/tests/test_board_add_multi_project.py,plugins/mission-control/tests/test_board_move_exit.py,plugins/mission-control/tests/test_executor_profile_lint.py,plugins/mission-control/tests/test_flow_subcommands.py,plugins/mission-control/tests/test_graphql_issue_resolution.py,plugins/mission-control/tests/test_issue_contract_parity.py,plugins/mission-control/tests/test_issue_create_prepared.py,plugins/mission-control/tests/test_issue_prepare.py,plugins/mission-control/tests/test_issue_prepare_compile_approve.py,plugins/mission-control/tests/test_issue_source_artifacts.py,plugins/mission-control/tests/test_label_contract.py,plugins/mission-control/tests/test_metrics_contract.py,plugins/mission-control/tests/test_milestone_contract.py,plugins/mission-control/tests/test_project_mappings_resolution.py,plugins/mission-control/tests/test_prompt_alignment.py,plugins/mission-control/tests/test_rollout_contract.py,plugins/mission-control/tests/test_sdlc_manager.py,plugins/mission-control/tests/test_template_sync.py,plugins/mission-control/tests/test_typed_exceptions.py,plugins/multi-agent-consensus/CHANGELOG.md,plugins/multi-agent-consensus/plugin.json,plugins/multi-agent-consensus/skills/appsec-audit/SKILL.md,plugins/multi-agent-consensus/tests/test_appsec_audit.py,plugins/multi-agent-consensus/tests/test_multi_agent_consensus_plugin.py,plugins/saga/CHANGELOG.md,plugins/saga/agents/lifecycle-router.md,plugins/saga/commands/brainstorm.md,plugins/saga/commands/ceo-review.md,plugins/saga/commands/code-review.md,plugins/saga/commands/fleet-doctor.md,plugins/saga/commands/founder-review.md,plugins/saga/commands/handoff.md,plugins/saga/commands/ideate.md,plugins/saga/commands/investigate.md,plugins/saga/commands/loop.md,plugins/saga/commands/office-hours.md,plugins/saga/commands/optimize.md,plugins/saga/commands/outcome.md,plugins/saga/commands/plan.md,plugins/saga/commands/promote.md,plugins/saga/commands/pulse.md,plugins/saga/commands/qa.md,plugins/saga/commands/retro.md,plugins/saga/commands/spec.md,plugins/saga/commands/strategy.md,plugins/saga/commands/work.md,plugins/saga/docs/README.md,plugins/saga/docs/model/saga-docs-model.yaml,plugins/saga/docs/portability.md,plugins/saga/plugin.json,plugins/saga/references/command_dry_runs.md,plugins/saga/references/escape_hatches.md,plugins/saga/references/fleet-doctor-sources.md,plugins/saga/references/formatting-style.md,plugins/saga/references/handoff_failure_matrix.md,plugins/saga/references/harness-escalation-policy.md,plugins/saga/references/lifecycle-obligation-contract.md,plugins/saga/references/lifecycle-obligation-schema.json,plugins/saga/references/operator-choice.md,plugins/saga/references/outcome-cross-runtime.md,plugins/saga/references/saga-spec.md,plugins/saga/references/transition-receipt-schema.json,plugins/saga/scripts/board_progression.py,plugins/saga/scripts/capability_elo.py,plugins/saga/scripts/ceremony_hazards.py,plugins/saga/scripts/detect_deploy_strategy.py,plugins/saga/scripts/discover_sessions.py,plugins/saga/scripts/external_action_adapters.py,plugins/saga/scripts/external_action_contract.py,plugins/saga/scripts/external_action_egress.py,plugins/saga/scripts/external_action_workspace.py,plugins/saga/scripts/extract_session_skeleton.py,plugins/saga/scripts/find_inflight_work.py,plugins/saga/scripts/fleet_commons_shim.py,plugins/saga/scripts/fleet_doctor.py,plugins/saga/scripts/handoff_envelope.py,plugins/saga/scripts/host_capability_gate.py,plugins/saga/scripts/issue_progress.py,plugins/saga/scripts/journal_triggers.py,plugins/saga/scripts/lifecycle_obligations.py,plugins/saga/scripts/lifecycle_state.py,plugins/saga/scripts/load_saga_context.py,plugins/saga/scripts/manifest_reader.py,plugins/saga/scripts/manifest_store.py,plugins/saga/scripts/merge_watcher.py,plugins/saga/scripts/outcome.py,plugins/saga/scripts/outcome_board_sync.py,plugins/saga/scripts/outcome_costs.py,plugins/saga/scripts/outcome_decompose.py,plugins/saga/scripts/outcome_dispatcher.py,plugins/saga/scripts/outcome_edges.py,plugins/saga/scripts/outcome_gate_transport.py,plugins/saga/scripts/outcome_github.py,plugins/saga/scripts/outcome_liveness.py,plugins/saga/scripts/outcome_merge.py,plugins/saga/scripts/outcome_orchestrator.py,plugins/saga/scripts/outcome_projection.py,plugins/saga/scripts/outcome_reconcile.py,plugins/saga/scripts/outcome_report.py,plugins/saga/scripts/outcome_spec.py,plugins/saga/scripts/outcome_store.py,plugins/saga/scripts/outcome_worktrees.py,plugins/saga/scripts/override_rate_reader.py,plugins/saga/scripts/parse_issue.py,plugins/saga/scripts/plugin_dependency_resolver.py,plugins/saga/scripts/promote_scan.py,plugins/saga/scripts/provenance_manifest.py,plugins/saga/scripts/provider_control_chart.py,plugins/saga/scripts/pulse.py,plugins/saga/scripts/qa_health_score.py,plugins/saga/scripts/reconcile.py,plugins/saga/scripts/reconcile_controller.py,plugins/saga/scripts/reversibility_certificate.py,plugins/saga/scripts/run_ledger.py,plugins/saga/scripts/saga.py,plugins/saga/scripts/saga_spore.py,plugins/saga/scripts/scaffold_checkpoint.py,plugins/saga/scripts/second_opinion.py,plugins/saga/scripts/ship_ceremony.py,plugins/saga/scripts/ship_undo.py,plugins/saga/scripts/status_card.py,plugins/saga/scripts/transition_receipts.py,plugins/saga/skills/brainstorm/SKILL.md,plugins/saga/skills/brainstorm/references/requirements-sections.md,plugins/saga/skills/code-review/SKILL.md,plugins/saga/skills/code-review/references/built-vs-planned.md,plugins/saga/skills/code-review/references/findings-schema.md,plugins/saga/skills/code-review/references/lens-catalog.md,plugins/saga/skills/code-review/references/validator.md,plugins/saga/skills/fleet-doctor/SKILL.md,plugins/saga/skills/founder-review/SKILL.md,plugins/saga/skills/founder-review/references/ceo-cognition.md,plugins/saga/skills/founder-review/references/review-modes.md,plugins/saga/skills/handoff/SKILL.md,plugins/saga/skills/ideate/SKILL.md,plugins/saga/skills/ideate/references/convergence-and-partnership.md,plugins/saga/skills/ideate/references/ideation-artifact.md,plugins/saga/skills/investigate/SKILL.md,plugins/saga/skills/investigate/references/debug-report.md,plugins/saga/skills/investigate/references/methodology.md,plugins/saga/skills/investigate/references/pattern-taxonomy.md,plugins/saga/skills/loop/SKILL.md,plugins/saga/skills/loop/references/dispatch-table.md,plugins/saga/skills/loop/references/drive-and-resume.md,plugins/saga/skills/loop/references/generic-ask-compiler.md,plugins/saga/skills/office-hours/SKILL.md,plugins/saga/skills/office-hours/references/frame-diagnostic.md,plugins/saga/skills/optimize/SKILL.md,plugins/saga/skills/optimize/references/experiment-loop.md,plugins/saga/skills/optimize/references/metric-taxonomy.md,plugins/saga/skills/outcome/SKILL.md,plugins/saga/skills/plan/SKILL.md,plugins/saga/skills/plan/references/interrogation.md,plugins/saga/skills/plan/references/plan-sections.md,plugins/saga/skills/promote/SKILL.md,plugins/saga/skills/promote/references/promotion-contract.md,plugins/saga/skills/pulse/SKILL.md,plugins/saga/skills/pulse/references/manual-verification.md,plugins/saga/skills/qa/SKILL.md,plugins/saga/skills/qa/references/qa-report.md,plugins/saga/skills/qa/references/risk-taxonomy.md,plugins/saga/skills/retro/SKILL.md,plugins/saga/skills/retro/references/retro-passes.md,plugins/saga/skills/retro/references/retro-report.md,plugins/saga/skills/retro/references/self-edit-safety.md,plugins/saga/skills/spec/SKILL.md,plugins/saga/skills/spec/references/interrogation.md,plugins/saga/skills/spec/references/spec-template.md,plugins/saga/skills/strategy/SKILL.md,plugins/saga/skills/strategy/references/interview.md,plugins/saga/skills/strategy/references/strategy-template.md,plugins/saga/skills/work/SKILL.md,plugins/saga/skills/work/references/execution-strategy.md,plugins/saga/skills/work/references/pr-continuation-loop.md,plugins/saga/skills/work/references/test-and-gates.md,plugins/saga/tests/fixtures/port-ledger/complete.yaml,plugins/saga/tests/fixtures/port-ledger/migration-blocked.yaml,plugins/saga/tests/fixtures/port-ledger/migration-evidence-invalid.json,plugins/saga/tests/fixtures/port-ledger/migration-evidence-valid.json,plugins/saga/tests/fixtures/port-ledger/migration-migrated.yaml,plugins/saga/tests/fixtures/port-ledger/migration-planned.yaml,plugins/saga/tests/fixtures/port-ledger/migration-unknown-version.yaml,plugins/saga/tests/fixtures/port-ledger/migration-v1-mislabeled.yaml,plugins/saga/tests/test_brainstorm_contract.py,plugins/saga/tests/test_ceremony_hazards.py,plugins/saga/tests/test_code_review_contract.py,plugins/saga/tests/test_cross_runtime_reconciliation.py,plugins/saga/tests/test_detect_deploy_strategy.py,plugins/saga/tests/test_executive_review_contract.py,plugins/saga/tests/test_external_action_adapters.py,plugins/saga/tests/test_fleet_doctor.py,plugins/saga/tests/test_handoff_envelope.py,plugins/saga/tests/test_ideate_contract.py,plugins/saga/tests/test_investigate_contract.py,plugins/saga/tests/test_lifecycle_obligations.py,plugins/saga/tests/test_loop_routing.py,plugins/saga/tests/test_manifest_consumer_matrix.py,plugins/saga/tests/test_manifest_reader.py,plugins/saga/tests/test_manifest_store.py,plugins/saga/tests/test_merge_watcher.py,plugins/saga/tests/test_office_hours_contract.py,plugins/saga/tests/test_operator_safety_contract.py,plugins/saga/tests/test_optimize_contract.py,plugins/saga/tests/test_outcome_board_sync.py,plugins/saga/tests/test_outcome_completion.py,plugins/saga/tests/test_outcome_dispatcher.py,plugins/saga/tests/test_outcome_economics.py,plugins/saga/tests/test_outcome_integration.py,plugins/saga/tests/test_outcome_liveness.py,plugins/saga/tests/test_outcome_merge_queue.py,plugins/saga/tests/test_outcome_reconcile.py,plugins/saga/tests/test_outcome_spec.py,plugins/saga/tests/test_outcome_store.py,plugins/saga/tests/test_outcome_worktrees.py,plugins/saga/tests/test_plan_contract.py,plugins/saga/tests/test_plugin_dependency_resolver.py,plugins/saga/tests/test_port_ledger.py,plugins/saga/tests/test_promote_scan.py,plugins/saga/tests/test_provider_pulse.py,plugins/saga/tests/test_qa_contract.py,plugins/saga/tests/test_retro_contract.py,plugins/saga/tests/test_run_ledger.py,plugins/saga/tests/test_saga_docs_coverage.py,plugins/saga/tests/test_saga_plugin.py,plugins/saga/tests/test_saga_saga.py,plugins/saga/tests/test_saga_spore.py,plugins/saga/tests/test_ship_ceremony.py,plugins/saga/tests/test_ship_undo.py,plugins/saga/tests/test_spec_contract.py,plugins/saga/tests/test_spore_seam_roundtrip.py,plugins/saga/tests/test_state_paths.py,plugins/saga/tests/test_strategy_contract.py,plugins/saga/tests/test_transition_receipts.py,plugins/saga/tests/test_work_contract.py,scripts/port_ledger.py,scripts/validate_plugins.py` | Fix every implementation-caused actionable P0-P3 finding within this literal union, update the durable code-review artifact, run focused checks, and return `assignment-result.v1`; one attempt only. | `none` |
| `recheck-migration-once` | `remediate-migration-once` | `scenario-tester` | `test_medium` | `none` | Run one targeted recheck over every affected check and all 102 mappings; return `assignment-result.v1`; any failure stops. | `none` |
| `refresh-before-recording` | `recheck-migration-once` | `git-integration-operator` | `work_medium` | `none` | Repeat the no-write source and safe-host refresh immediately before recording, bind exact source and host evidence, prove no operator-gate reset and final `git diff --name-only`, and return `assignment-result.v1`. | `none` |
| `assemble-migration-evidence` | `refresh-before-recording` | `implementation-worker` | `work_medium` | `docs/ports/2026-07-30-saga-reliability/migration-evidence.v1.json` | Write canonical `antigravity.semantic-port-migration-evidence.v1` from only root-validated assignment and reviewer results, exact nodes, changed paths, and source/host bindings; return `assignment-result.v1`. | `none` |
| `record-migrated-survivors` | `assemble-migration-evidence` | `implementation-worker` | `work_medium` | `docs/ports/2026-07-30-saga-reliability/README.md,docs/ports/2026-07-30-saga-reliability/ledger.yaml` | Validate full evidence content and exact bytes, atomically mark exactly 51 v2 migrations, preserve all decisions and packets, reject stale evidence, and return `assignment-result.v1`. | `none` |
| `validate-migrated-campaign` | `record-migrated-survivors` | `scenario-tester` | `test_medium` | `none` | Rerun final ledger, 102-node mapping, four plugin suites, docs, Ruff, mypy, canonical host lint, plugin validation, full non-Git suite, version parity, and exact path/evidence checks; return `assignment-result.v1`. | `none` |

All `writes` cells above are literal repository-relative paths accepted by the active compiler;
there are no directory aliases, globs, prose expansions, or `unit:` tokens. The remediation row is
the exact literal union of all implementation rows plus the durable code-review artifact. The union
excludes `.serena/project.yml`, sibling repositories, installed-plugin roots, credentials, issue or
board state, deployment state, and every path outside this repository.

The active `workflow_dispatch.py` compiler accepts this contract as schema 3 when invoked with the
active registry, role directory, profile catalog, and explicit current runtime-capability snapshot.
The compiled contract has 19 assignments, 11 blocking checks, zero external actions, registry
digest `c11c5f062bf33771e46e8ce5c42b0fb15334bd6b1e20f5349f9d1314199afecb`, and contract
digest `4265afaa7d421a641266b2fae2dd1afbcda13549decddb55fc650a2443a8a3b7`.

### Blocking Checks

| id | owner | after | command-or-proof | blocking | failure |
|---|---|---|---|---|---|
| `approved-ledger-equality` | `refresh-approved-ledger` | `refresh-approved-ledger` | 51 unique trace IDs exactly equal the current approved set; category counts remain 51/19/8/1/1; all semantic contracts and numeric packet claims resolve from the ledger | `yes` | stop for operator reconciliation |
| `release-drift-host-binding` | `refresh-approved-ledger` | `refresh-approved-ledger` | source evidence is byte-identical and the safe current host receipt is sanitized and evaluated under KTD8 | `yes` | affected rows return to pending or blocked; no implementation |
| `migration-schema-gate` | `implement-migration-gate` | `implement-migration-gate` | v1 remains valid; deterministic v2 upgrade, mislabeled-v1, unknown-version, digest-vector, containment, evidence-shape, and atomicity tests pass | `yes` | stop at U0 |
| `git-bearing-tests` | `test-git-bearing-nodes` | `test-git-bearing-nodes` | exact declared Git-bearing nodes pass in controlled temporary repositories and repository bytes remain outside the declared writes | `yes` | block semantic test aggregation |
| `semantic-node-map` | `test-git-free-migration` | `test-git-free-migration` | exact 51 IDs map to 51 positive and 51 negative collected node IDs and all required non-Git nodes pass | `yes` | block reviews and recording |
| `canonical-host-lint` | `test-git-free-migration` | `test-git-free-migration` | the one canonical selector equals all changed active runtime paths and AGHC001-AGHC006 have zero unresolved active findings | `yes` | block |
| `independent-code-review` | `review-migration-correctness` | `review-migration-correctness,review-migration-evidence` | both read-only reviewer-result.v1 results are accept, have no hard stop, and contain no unresolved actionable P0-P3 finding | `yes` | transcribe findings; release the one remediation only if needed |
| `remediation-recheck` | `recheck-migration-once` | `recheck-migration-once` | one bounded remediation and one targeted recheck pass every affected check and all 102 mappings | `yes` | stop for Jeff; no second automatic repair |
| `final-refresh-evidence` | `refresh-before-recording` | `assemble-migration-evidence,refresh-before-recording` | no-write refresh is byte-identical; operator gate remains decided; full typed evidence manifest validates and its digest matches exact canonical bytes | `yes` | preserve ledger bytes and stop |
| `migrated-ledger` | `record-migrated-survivors` | `record-migrated-survivors` | exact 51-ID atomic v2 mapping has final target state, paths, positive and negative tests, differences, evidence digest, and current host binding; non-survivors are unchanged | `yes` | preserve pre-recording ledger bytes and stop |
| `final-validation` | `validate-migrated-campaign` | `validate-migrated-campaign` | deterministic validation, four intended plugin versions, canonical docs, exact paths, and every required result pass | `yes` | stop; do not claim completion |

### External Actions

`External actions: []` is the exact approved value.

No external model/provider call, plugin installation, live Antigravity execution, credential
change, deployment, sibling write, issue mutation, board mutation, or outcome-edge mutation is
authorized. No push, PR creation/update, merge, release, tag, or deployment is part of this
workflow. A later delivery assignment is separate and requires Jeff's explicit authority.

Root may release the one remediation assignment for every implementation-caused actionable P0-P3
finding whose fix is contained in the remediation row's literal write union. It gets one attempt,
then root may release one recheck. The assignment must stop for a path outside the union, a new
dependency, a new interface, a schema beyond approved v2, a product-boundary expansion, a
credential, deployment, destructive action, sibling write, external mutation, or failed recheck.
Any such condition requires a contract amendment from Jeff; it is not reclassified or silently
deferred.

## Scope Boundaries

### In scope

- Exactly 51 approved stable IDs in the traceability table.
- Antigravity-native adaptation or evidence closure in the four existing plugins.
- The closed ledger migration-evidence object and atomic migration command.
- Deterministic positive and negative target tests.
- Canonical Saga documentation updates and generated-asset validation where required.
- Host-contract and plugin validation for changed active surfaces.
- One bounded review remediation and one targeted recheck.
- PR-ready local evidence only; delivery remains a separate operator decision.

### Non-goals

- Any of the 29 non-survivors.
- Changing ledger decisions, rankings, rationales, packet ownership, or stable IDs.
- File-for-file source parity, prompt renaming, source test parity, or text-similarity evidence.
- A new plugin for a source package, including `team-execution`, `verified-workflows`, or `agy`.
- Source-host model names, Claude workflow APIs, `AskUserQuestion`, executable `.claude` paths,
  fixed brain roots, or unproven scheduling, agent, isolation, sandbox, model, or effort behavior.
- A host-neutral runtime, broad provider matrix, live Gemini canary, plugin install, host sync,
  release tag, deployment, issue/board update, or sibling-repository change.
- Issue #22 conformance and release qualification.
- General cleanup unrelated to a named approved survivor.
- `.serena/project.yml`.

## Completion and Handoff

Issue #15 is implementation-complete only when:

1. the final ledger validates with the original 80 decisions and exact category counts;
2. all 51 approved rows have migration state `migrated` and Antigravity state `present` or
   `intentional-divergence`;
3. every migrated row names exact target paths, positive and negative test node IDs, intentional
   differences, current sanitized host binding, and its validated evidence-manifest digest;
4. no non-survivor carries a target path or migration evidence;
5. all four plugin suites, full repository checks, host-contract lint, canonical docs check, and
   plugin validation pass;
6. sibling repositories and installed/plugin host state remain unchanged;
7. the reviewed changed-path set excludes `.serena/project.yml` and is PR-ready, but no delivery
   action has been performed; and
8. issue #22 may consume the migrated ledger, but no release qualification or live canary has been
   claimed by this issue.

## Sources

- GitHub issue #15, `Migrate every approved port survivor natively`
- `docs/ports/2026-07-30-saga-reliability/ledger.yaml`
- `docs/ports/2026-07-30-saga-reliability/README.md`
- `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`
- `docs/reviews/2026-07-26-antigravity-saga-reliability-system-requirements-review.md`
- `docs/plans/2026-07-30-semantic-port-ledger-plan.md`
- `docs/reviews/2026-07-30-semantic-port-ledger-plan-doc-review.md`
- `docs/code-reviews/2026-07-30-semantic-port-ledger-code-review.md`
- `plugins/fleet-core/references/antigravity-capability-probes.yaml`
- `plugins/fleet-core/references/host-contract-lint.md`
- `plugins/saga/docs/model/saga-docs-model.yaml`
- `.agents/skills/port-claude-plugins/SKILL.md`
