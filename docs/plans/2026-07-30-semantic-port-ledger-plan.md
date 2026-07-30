---
title: Semantic Port Ledger and Read-Only Drift Workflow Implementation Plan
type: feat
status: active
date: 2026-07-30
origin: docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md
linked_issue: https://github.com/infiquetra/infiquetra-antigravity-plugins/issues/16
reviewed: 2026-07-30
review_status: ready
review_artifact: docs/reviews/2026-07-30-semantic-port-ledger-plan-doc-review.md
workflow_revision: 3
---

# Semantic Port Ledger and Read-Only Drift Workflow Implementation Plan

## Summary

Replace the current bulk-port procedure with a committed, schema-versioned semantic ledger and
read-only discovery workflow. The first campaign will pin the current Claude, Codex, and
Antigravity snapshots, inventory the complete relevant Saga-family surface, cluster source edits
under stable capability IDs, record a four-factor advisory ranking, and stop for Jeff's explicit
survivor decision before the issue can merge.

This issue creates the governance artifact and tooling. It does not implement any survivor, derive
migration units, update installed plugins, or mutate either sibling source repository.

## Problem Frame

The target repository records Claude commit `099ec4c` as its last broad synchronization marker, but
that marker is historical rather than proof of current semantic coverage. Claude has since advanced
through many changes, Codex contains native capabilities that never existed in the recorded Claude
range, and Antigravity has continued to evolve independently. File-count parity or a new bulk copy
would therefore hide repeated edits, Codex-only behavior, intentional target divergence, and
capabilities already superseded by Antigravity-native designs.

GitHub issue #16 owns requirements R8-R14 and R18 plus the pre-approval portion of flow F1 and
acceptance example AE3. It must produce a complete decision surface without making the operator's
decision.

## Grounded Current State

The campaign ID is `2026-07-30-saga-reliability`. Its planning-time inputs are:

| role | repository and surface | pinned planning snapshot | notes |
|---|---|---|---|
| Claude source | `../infiquetra-claude-plugins`: `saga`, `fleet-core`, `mission-control`, and `team-execution`, plus directly consumed shared scripts/tools | `0a572448556252c499752e5132617b4c9aa9c1a5` | `099ec4c` remains a discovery seed, not an authoritative coverage claim; the selected history after it contains 113 commits and 229 changed paths |
| Codex comparison | `../infiquetra-codex-plugins`: `saga`, `fleet-core`, `mission-control`, `verified-workflows`, and current portability manifests | `12b5f2c72ff6954cbdbcda8e93408ab2bc518c45` | Codex-native capabilities must be considered even when Claude has no corresponding change |
| Antigravity target | this repository: `saga`, `fleet-core`, `mission-control`, and `multi-agent-consensus` | `6565ddbafb12e794104bdd11e52596bcc993febd` | target product boundaries are authoritative; source `team-execution` semantics map to existing target boundaries |
| host contract | merged GitHub issue #20 and PR #24 | merge commit `b3c9855778ef776364860437b63ebc2bea53bc48` | final fit claims consume the shared capability receipt vocabulary and may not invent host support |

Implementation must read all three local `HEAD` and `origin/main` refs before discovery without
fetching, pulling, or updating either sibling repository. Claude and Codex discovery stops when
their local `HEAD` and `origin/main` disagree. Antigravity is intentionally implemented on this
feature branch, so its inventory snapshot is the pinned local `origin/main` commit while its
separate working `HEAD` is recorded as implementation context and may differ. If any local
`origin/main` differs from the planning snapshot, the ledger records both the planning snapshot and
the actual inventory snapshot. This comparison is disclosure, not permission to broaden the
selected surface. The release-drift check repeats the same local read-only comparison against each
inventory commit.

The existing uncommitted `.serena/project.yml` change belongs to the operator and is excluded from
every write set and commit.

## Requirements

### Campaign and schema

R1. Create `docs/ports/2026-07-30-saga-reliability/ledger.yaml` with schema identity
`antigravity.semantic-port-ledger.v1`. It must record the campaign ID, selected surfaces, Claude,
Codex, and Antigravity inventory snapshots, the historical Claude discovery seed, host-capability
receipt digest and sanitized state summary, a normalized raw edit-packet inventory, and a
release-drift disclosure. Covers origin R8-R10.

R2. The ledger loader must use a closed top-level and candidate schema. Unknown schema versions,
unknown fields, duplicate candidate IDs, unsafe repository paths, missing snapshot commits, invalid
states, duplicate edit-packet IDs, duplicate source-edit ownership, unmatched edit packets, and
incomplete decisions fail with actionable errors.
PyYAML is already a repository dependency; no new dependency is allowed. Covers origin R9, R11,
and R14.

### Discovery and semantic clustering

R3. `scripts/port_ledger.py discover` must perform only read operations against the Claude and
Codex sibling repositories and the Antigravity target. Its only permitted write is the explicitly
named file beneath `docs/ports/<campaign-id>/`. The command must fail before execution when a
requested output escapes that campaign directory. Covers origin R18.

R4. Discovery must combine two inputs: history deltas from known lineage markers and a complete
current-tree manifest over the selected surfaces. The tree manifest prevents a stale or absent
history marker from hiding a current capability. Each normalized edit packet records a stable
packet ID, host, pinned commit, repository-relative path, change kind, and content identity.
Discovery emits those reviewable packets and candidate inputs; it does not assign value, approve a
survivor, install a plugin, or modify a sibling repository. Covers origin R8-R10 and R18.

R5. Semantic clustering is curated and reproducible. Each candidate has a stable human-readable ID,
and cites the exact edit-packet IDs it owns. Every packet belongs to exactly one candidate.
Repeated commits or paths for the same semantic behavior remain source evidence under one candidate
rather than becoming additional candidate rows. Unmatched edit packets and duplicate ownership make
the inventory incomplete. Covers origin R9 and the issue's duplicate-edit acceptance criterion.

### Candidate and decision contract

R6. Every candidate must record:

- stable ID and title;
- Claude and/or Codex provenance bound to pinned commits and repository-relative paths;
- the user-visible semantic contract;
- adjacent-plugin dependencies;
- current Antigravity state;
- proposed Antigravity-native disposition;
- operator value, Antigravity fit, proof feasibility, and maintenance cost;
- evidence expected from any later migration;
- decision rationale;
- concrete revisit trigger;
- explicit operator-decision state.

`antigravity_state` is one of `absent`, `partial`, `present`, `intentional-divergence`, or
`blocked-by-host`. `proposed_disposition` is one of `direct-port`, `antigravity-adapt`,
`metadata-only`, `reject`, `superseded`, or `blocked`.

Covers origin R10-R14.

R7. Ranking uses four visible integer inputs on a `1..5` scale. The report sorts by operator value,
Antigravity fit, proof feasibility, and inverse maintenance cost, then stable ID. The sort is
advisory only: no threshold, total, or rank may approve, reject, hide, or mutate a candidate.
Covers origin R12-R13 and AE3.

R8. Candidate decision states are `pending`, `approved-survivor`, `rejected`, `superseded`,
`metadata-only`, and `blocked`. Every non-pending state requires a rationale and revisit trigger;
every non-pending decision requires explicit operator identity and decision time. The plain
`validate` command exits nonzero while any candidate is pending or any scoped edit is unmatched.
`validate --inventory-only` succeeds only when schema, snapshots, raw-packet coverage, clustering,
ranking inputs, evidence expectations, rationales, revisit triggers, and release-drift disclosure
are complete; it permits `pending` solely so the reviewed operator packet can exist before Jeff's
decision. Covers origin R13-R14.

R9. Recording decisions is a separate command that accepts only the complete operator-provided
mapping for the current candidate ID set. It must reject partial, extra, or stale-ID mappings and
must not derive migration units, estimates, sequencing, or code changes. Covers origin R13 and the
hard handoff gate to issue #15.

### Runbook and compatibility boundary

R10. Update `.agents/skills/port-claude-plugins/SKILL.md` so new campaigns use the ledger workflow
and explicit decision gate. Keep `scripts/port_claude_plugin.py` only as a clearly marked legacy
bulk-copy utility; its normal entry point must not be used by the new discovery path, and tests
must prove discovery never invokes its copy/delete functions. Covers origin R18.

R11. `scripts/port_ledger.py report` must work for both pending and fully decided ledgers. It must
show all candidates, source hosts, four ranking inputs, proposed disposition, actual decision,
unmatched drift, and the exact validation state. It must not omit low-ranked or rejected entries.
Covers origin R11-R14 and AE3.

R12. The campaign README must explain the snapshots, selected surface, ranking rubric, validation
state, operator gate, release-refresh procedure, and the boundary between this issue and migration
issue #15. The engineering journal must record why current-tree comparison supplements the
historical source marker and why ranking is non-authoritative.

R13. Final fit assessments must consume the merged host-contract vocabulary. The campaign records
only the promotable capability-receipt digest and sanitized capability states. A required failed or
unknown host capability makes the affected candidate `blocked-by-host`; raw paths, hostnames,
transcripts, or private diagnostic values may not enter the ledger.

## Key Technical Decisions

KTD1. **Use the old sync point as a seed, never as the coverage boundary.** The Claude range
`099ec4c..<inventory snapshot>` is useful evidence, but completeness is established by reconciling
that history with complete current-tree manifests from all three hosts.

KTD2. **Keep the ledger canonical and the raw packet format subordinate.** Candidate rows and their
source-edit references live in `ledger.yaml`. Temporary command output may help curation, but no
second tracked database or hidden cache may become decision authority.

KTD3. **Make semantic clustering explicitly human-curated.** Deterministic tooling normalizes edit
identity, detects duplicate ownership, preserves stable IDs, and reports unmatched inputs. It does
not pretend that a path or commit-message heuristic can make the semantic decision.

KTD4. **Separate recommendation from approval.** `proposed_disposition` and the four ranking inputs
are maintainers' reviewable assessments. `decision.state` is a different field and changes only
from Jeff's complete explicit mapping.

KTD5. **Treat Codex as an independent source of useful behavior.** The Codex inventory includes
`verified-workflows` and its portability manifests because those surfaces replaced Codex
`team-execution`; the Antigravity target remains `multi-agent-consensus` or another existing product
boundary unless a later product decision says otherwise.

KTD6. **Use subprocess only for read-only Git plumbing.** Discovery may run commands such as
`git rev-parse`, `git diff --name-status`, `git log`, and `git ls-tree` with argument arrays,
timeouts, captured output, and explicit repositories. It may not run checkout, fetch, pull, add,
commit, push, reset, clean, or any source-repository write command.

KTD7. **Preserve the one-hop autonomy boundary.** One directly blocking or implementation-caused
defect inside the approved files and one targeted recheck are allowed. A second issue, failed
recheck, new dependency, new public schema beyond v1, broader plugin boundary, new outcome edge,
credential need, deployment, installation, destructive action, or sibling-repository write returns
to Jeff.

## High-Level Design

```text
Claude history + current tree ----+
                                  |
Codex current tree + manifests ---+--> normalized edit packets
                                  |           |
Antigravity current tree ---------+           v
                                      curated stable candidates
                                                |
                                                v
                                  advisory ranked pending ledger
                                                |
                                     explicit Jeff decision gate
                                                |
                                                v
                                  fully decided canonical ledger
```

`port_ledger.py` has four commands:

| command | behavior |
|---|---|
| `discover` | read selected Git trees/history and create or refresh candidate inputs only under the campaign directory |
| `validate` | enforce schema, provenance, coverage, decision completeness, and read-only boundary declarations |
| `report` | render the complete ranked decision surface without making a decision |
| `record-decisions` | apply one complete operator-provided candidate-state mapping and reject partial or stale mappings |

The ledger keeps provenance and decision authority distinct:

```yaml
schema: antigravity.semantic-port-ledger.v1
campaign:
  id: 2026-07-30-saga-reliability
  snapshots: {}
  selected_surfaces: []
  edit_packets:
    - id: edit-claude-example
      host: claude
      commit: 0000000000000000000000000000000000000000
      path: plugins/saga/example.md
      change: modified
      content_sha256: 0000000000000000000000000000000000000000000000000000000000000000
  release_drift: {}
candidates:
  - id: port-example-stable-id
    edit_packet_ids: [edit-claude-example]
    provenance: []
    semantic_contract: ""
    adjacent_dependencies: []
    antigravity_state: absent
    proposed_disposition: antigravity-adapt
    ranking:
      operator_value: 1
      antigravity_fit: 1
      proof_feasibility: 1
      maintenance_cost: 1
    evidence_expectation: []
    decision:
      state: pending
      rationale: ""
      revisit_trigger: ""
      operator: null
      decided_at: null
```

The implementation may refine nested field names for clarity, but it may not weaken the required
data, closed vocabularies, stable identity, complete decision gate, or fixed canonical path.

## Requirement and Acceptance Traceability

| plan requirements | implementation units | decisive proof |
|---|---|---|
| R1-R2, R6-R9, R13 | U1 | complete, unclassified, unapproved, malformed, unsafe-receipt, and stale-decision fixtures |
| R3-R5 | U2 | temporary sibling repositories prove read-only Git discovery, complete tree coverage, stable clustering, duplicate ownership rejection, and release drift |
| R6-R9, R11 | U3 | committed pending campaign report, explicit operator pause, complete decision application, and final validation |
| R10-R12 | U4 | runbook, legacy-helper boundary, campaign README, journal entry, and canonical plugin validation |

## Implementation Units

### U1. Define the ledger contract and decision commands

**Goal:** Add a strict v1 loader, validator, reporter, and complete decision-recording command.

**Requirements:** R1-R2, R6-R9, R11.

**Dependencies:** None.

**Files:**

- `scripts/port_ledger.py`
- `plugins/saga/tests/test_port_ledger.py`
- `plugins/saga/tests/fixtures/port-ledger/complete.yaml`
- `plugins/saga/tests/fixtures/port-ledger/unclassified.yaml`
- `plugins/saga/tests/fixtures/port-ledger/duplicate-source-edits.yaml`
- `plugins/saga/tests/fixtures/port-ledger/unapproved-survivors.yaml`
- `plugins/saga/tests/fixtures/port-ledger/release-drift.yaml`

**Approach:** Use explicit allowed-key sets, closed enums, repository-relative path validation,
stable sorting, and deterministic YAML serialization. Keep business decisions as data supplied to
`record-decisions`; the command verifies exact candidate-set equality before writing atomically.

**Test scenarios:**

- Complete ledger validates and round-trips deterministically.
- Unknown schema, unknown field, unsafe path, invalid score, missing host snapshot, missing required
  candidate field, or duplicate candidate ID fails with a precise message.
- Two commits and multiple paths assigned to one stable capability remain one report row.
- One source edit assigned to two candidates fails duplicate-ownership validation.
- Pending, partial, extra-ID, or stale-ID decision mappings fail; one complete explicit mapping
  succeeds, records actor/time on every decision, and preserves every rejection or block.
- Report ordering is deterministic and cannot omit low-ranked, rejected, or blocked candidates.
- Inventory-only validation permits `pending` decisions but still rejects missing packets, rankings,
  rationales, revisit triggers, receipt state, or release-drift disclosure.
- Unknown fields such as migration units, estimates, or implementation order are rejected.

### U2. Implement read-only discovery and drift refresh

**Goal:** Produce complete, reviewable source-edit packets without changing source or installed
state.

**Requirements:** R3-R5 and R10.

**Dependencies:** U1.

**Files:**

- `scripts/port_ledger.py`
- `scripts/port_claude_plugin.py`
- `plugins/saga/tests/test_port_ledger.py`
- `plugins/saga/tests/fixtures/port-ledger/`

**Approach:** Add an injected Git command runner with a strict read-only subcommand allowlist.
Normalize commit/path/change/content identity and read local `HEAD` and `origin/main` without
updating refs. Claude and Codex inventory their matching `HEAD`/`origin/main`; Antigravity records
the feature-branch `HEAD` but inventories its pinned `origin/main` target baseline so planning and
implementation commits do not become false port candidates. Compare the historical Claude seed
with all three inventory trees and preserve existing stable IDs during refresh. Reject output
outside the selected campaign directory. Keep the legacy copy helper isolated and prove it is never
imported or invoked by discovery.

**Test scenarios:**

- Temporary Claude, Codex, and Antigravity repositories yield pinned snapshots and normalized
  packets without worktree, index, ref, or untracked-file changes.
- Divergent Claude or Codex local `HEAD` and `origin/main` stop discovery; Antigravity feature-branch
  divergence is recorded while its inventory remains bound to local `origin/main`.
- No fetch, pull, checkout, or ref update is attempted.
- An absent or stale history seed still yields the complete current-tree inventory.
- Repeated edits refresh under the existing stable candidate ID.
- A new unmatched edit creates disclosed release drift and blocks final validation.
- A source write command, escaped output path, sibling mutation, install-root write, or Git metadata
  change fails the discovery check.

### U3. Curate and decide the first campaign ledger

**Goal:** Produce the complete pending candidate set, present it to Jeff, and record only his exact
decision mapping.

**Requirements:** R1 and R4-R9.

**Dependencies:** U1-U2 and the merged host-contract capability.

**Files:**

- `docs/ports/2026-07-30-saga-reliability/ledger.yaml`
- `docs/ports/2026-07-30-saga-reliability/README.md`
- `docs/engineering-journal/DECISIONS.md`

**Approach:** Consume the Git operator's three-host discovery output, with Claude and Codex bound to
their matching local `HEAD`/`origin/main` and Antigravity bound to its local `origin/main` target
baseline. Curate every scoped edit into one stable candidate or an explicit metadata-only
candidate. Run the host doctor through its safe observation interface and retain only the
promotable receipt digest and sanitized capability states. Assess the four ranking inputs with
evidence and leave every decision `pending`. After `validate --inventory-only`, focused checks, and
independent review, root presents the complete report to Jeff and does not release the
`record-decisions` assignment until he supplies the complete survivor/non-survivor mapping.

The decision assignment applies only that mapping, records operator identity and time, validates
zero pending or unmatched entries, and stops. It does not create issue #15 migration units,
estimates, dependency order, code, or new outcome edges.

**Test scenarios:**

- The pending report contains every candidate and fails final validation only for the explicit
  operator gate.
- The final mapping contains every current candidate ID exactly once.
- Rejected, superseded, metadata-only, and blocked rows retain rationale and a concrete revisit
  trigger.
- An approved survivor has explicit operator identity/time but no migration unit or estimate.

### U4. Replace the operational runbook

**Goal:** Make future port requests begin with semantic reconciliation rather than bulk copy.

**Requirements:** R10-R12.

**Dependencies:** U1-U3.

**Files:**

- `.agents/skills/port-claude-plugins/SKILL.md`
- `scripts/port_claude_plugin.py`
- `docs/ports/2026-07-30-saga-reliability/README.md`
- `docs/engineering-journal/DECISIONS.md`
- `plugins/saga/tests/test_port_ledger.py`

**Approach:** Document the snapshot, discover, curate, report, explicit-decision, and release-refresh
sequence. Mark the older helper as legacy and unsafe for ordinary campaigns without deleting its
existing callable functions. Record the current-tree and non-authoritative-ranking decisions in the
engineering journal.

**Test scenarios:**

- The runbook names the canonical ledger path and explicit operator gate.
- The runbook forbids source mutation, installed-plugin writes, auto-approval, and pre-approval
  migration planning.
- The legacy helper cannot be reached from the discovery command.
- Canonical plugin validation still passes.

## Workflow Structure

Issue #16 uses a root-orchestrated Codex Verified Workflow. All implementation, testing, review,
remediation, and Git work are executable assignments. Root only releases dependencies, verifies
runtime and typed-result receipts, enforces the operator decision pause, and reports gates.

Workflow revision 1 stopped safely after its implementation worker built the ledger tooling and
fixtures but could not run the Git-backed campaign discovery that its role forbids. Revision 2
starts from that preserved approved-path work. It first repairs the target snapshot rule without
running Git, then delegates actual discovery and cleanliness proof to a Git integration operator,
then delegates semantic curation to an implementation worker. No completed gate, review, or
delivery evidence is carried forward from the blocked attempt.

The independent review is one Devil's Advocate review at `review_high`. A second reviewer would be
disproportionate for this personal plugin-governance tool unless implementation reveals a concrete
risk and Jeff approves a contract amendment. The review occurs before the survivor decision so Jeff
receives a tested and reviewed candidate packet. One remediation attempt and one targeted recheck
are allowed.

Revision 2 used that remediation and recheck allowance. The recheck passed the 50 focused tests,
all four adversarial review checks, the real campaign inventory, the deterministic report, and the
complete 80-candidate decision packet, but it failed because two test helpers returned untyped
PyYAML values from functions with concrete return annotations. Jeff approved revision 3 as a
narrow exception after that mandatory stop. The exception may change only the focused test module,
must use explicit type narrowing rather than weaken mypy, and receives one independent rerun of the
focused mypy command and 50-test suite. The passing revision-2 recheck evidence remains bound to its
validated receipt; no other failed check, production change, second remediation, or second recheck
is permitted by this amendment.

The `record-decisions` assignment has a deliberate manual release condition: approval of this
Workflow Contract does not approve any port candidate. Root must pause after
`confirm-recheck-typing` and obtain Jeff's complete candidate disposition mapping before launching
it.

## Workflow Contract

| id | depends | role | profile | writes | completion | fallback |
|---|---|---|---|---|---|---|
| repair-discovery-boundary | - | implementation-worker | work_high | scripts/port_ledger.py,plugins/saga/tests/test_port_ledger.py,plugins/saga/tests/fixtures/port-ledger,docs/ports/2026-07-30-saga-reliability/README.md | adopt the blocked attempt's approved-path tooling, allow Antigravity feature-branch HEAD while binding its inventory to origin/main, resolve the scoped Bandit warning, and pass focused non-Git tests | none |
| discover-campaign | repair-discovery-boundary | git-integration-operator | work_medium | docs/ports/2026-07-30-saga-reliability/ledger.yaml | run only the approved read-only Git discovery against the three local repositories, write the raw pending ledger, prove Claude and Codex HEAD equal origin/main, bind Antigravity inventory to origin/main while recording feature-branch HEAD, and run git diff --name-only to prove only the approved ledger path changed and sibling repositories remained clean | none |
| curate-campaign | discover-campaign | implementation-worker | work_high | scripts/port_ledger.py,scripts/port_claude_plugin.py,.agents/skills/port-claude-plugins/SKILL.md,plugins/saga/tests/test_port_ledger.py,plugins/saga/tests/fixtures/port-ledger,docs/ports/2026-07-30-saga-reliability,docs/engineering-journal/DECISIONS.md | U1-U4 produce a complete pending campaign ledger, deterministic report, sanitized host-receipt binding, stable semantic curation of every packet, and focused passing checks without sibling or installed-plugin changes | none |
| validate-preapproval | curate-campaign | scenario-tester | test_medium | none | focused pytest, Ruff, mypy, inventory-only validation, pending-ledger report, snapshot disclosure, and recorded Git-operator sibling-cleanliness proofs pass | work_high@terminal-failure |
| review-ledger | validate-preapproval | devils-advocate-reviewer | review_high | none | reviewer-result.v1 adjudicates requirements, completeness, read-only boundaries, ranking authority, decision gating, failure handling, and scope with concrete P0-P3 findings | review_max@terminal-failure-or-ambiguity |
| remediate-ledger | review-ledger | remediation-worker | work_high | scripts/port_ledger.py,scripts/port_claude_plugin.py,.agents/skills/port-claude-plugins/SKILL.md,plugins/saga/tests/test_port_ledger.py,plugins/saga/tests/fixtures/port-ledger,docs/ports/2026-07-30-saga-reliability,docs/engineering-journal/DECISIONS.md,docs/code-reviews/2026-07-30-semantic-port-ledger-code-review.md | every actionable P0-P3 finding is fixed or evidence-reclassified, the durable code-review artifact records dispositions, and affected focused checks pass in one remediation attempt | none |
| recheck-preapproval | remediate-ledger | scenario-tester | test_medium | none | one targeted recheck proves the remediated pending ledger is complete except for operator decisions and produces the exact ranked decision packet with clean sibling repositories | work_high@terminal-failure |
| repair-recheck-typing | recheck-preapproval | remediation-worker | work_high | plugins/saga/tests/test_port_ledger.py | after the failed recheck and Jeff's explicit amendment approval, type-narrow only the two PyYAML-derived test-helper returns without changing production code or weakening mypy, then pass the focused test-module mypy command and the 50-test suite | none |
| confirm-recheck-typing | repair-recheck-typing | scenario-tester | test_medium | none | independently rerun mypy on the focused test module and the 50-test suite, confirm both pass, and bind the unchanged complete decision packet from the validated failed-recheck receipt | none |
| record-decisions | confirm-recheck-typing | implementation-worker | work_medium | docs/ports/2026-07-30-saga-reliability/ledger.yaml,docs/ports/2026-07-30-saga-reliability/README.md,docs/engineering-journal/DECISIONS.md | after root receives Jeff's complete candidate mapping, only that mapping is recorded, zero candidates remain pending, and no migration units, estimates, sequencing, sibling writes, installs, or outcome edges are created | none |
| validate-final | record-decisions | scenario-tester | test_medium | none | final validate and report commands, focused tests, Ruff, mypy, plugin validation, and full pytest pass with zero unmatched drift and clean sibling repositories | work_high@terminal-failure |
| integrate-reviewed-branch | validate-final | git-integration-operator | work_medium | none | run git diff --name-only and prove the final diff equals the approved write-path union excluding .serena/project.yml, then commit, push, open or update the issue-linked PR, wait for required CI, squash-merge, and verify the merge commit is an ancestor of origin/main | none |

### Blocking Checks

| id | owner | after | command-or-proof | blocking | failure |
|---|---|---|---|---|---|
| git-discovery-proof | discover-campaign | discover-campaign | read-only Git command log and final `git diff --name-only` prove the raw ledger is bound to the three approved local refs, Antigravity inventory uses origin/main despite feature-branch HEAD, and neither sibling repository changed | yes | stop before semantic curation; no non-Git role may replace or bypass the missing evidence |
| focused-preapproval | validate-preapproval | validate-preapproval | `uv run pytest plugins/saga/tests/test_port_ledger.py -q`; scoped Ruff and mypy; `python3 scripts/port_ledger.py validate --inventory-only docs/ports/2026-07-30-saga-reliability/ledger.yaml`; pending report; validated Git-operator proof shows no Claude, Codex, install-root, or unrelated target mutation | yes | return to the owning implementation unit; do not weaken schema, coverage, or read-only rules |
| reviewer-assurance | review-ledger | review-ledger | validated reviewer-result.v1 covers the full approved diff and reports every finding with a scope disposition | yes | block release; send all actionable planned findings to the single remediation assignment |
| remediation-recheck | confirm-recheck-typing | confirm-recheck-typing | the durable code-review artifact accounts for every P0-P3 review finding; the validated revision-2 recheck passes every substantive check and exposes only RC-001; Jeff explicitly approves the test-only repair; and the independent revision-3 mypy plus 50-test rerun passes | yes | stop for Jeff; no further repair, tester, or reviewer is launched automatically |
| explicit-survivor-decision | record-decisions | record-decisions | root readback binds the recorded complete candidate mapping to Jeff's explicit survivor and non-survivor decision; Workflow Contract approval alone is not decision approval | yes | keep every candidate pending and stop before final validation or Git integration |
| final-validation | validate-final | validate-final | issue verification commands plus `uv run pytest -q` pass; validate reports zero pending/unmatched candidates; release-drift disclosure is current; sibling repos remain clean relative to their pre-run state | yes | return to the owning unit only within the approved one-hop rule; otherwise stop for Jeff |
| delivery | integrate-reviewed-branch | integrate-reviewed-branch | final `git diff --name-only` matches the approved union; PR checks pass; squash merge succeeds; fetched `origin/main` contains the merge; `.serena/project.yml` is absent from every commit | yes | do not claim issue completion; repair only approved Git integration drift or stop |

### External Actions

`External actions: []` is the exact approved value.

No external model/provider action, deployment, installation, credential change, sibling-repository
write, or live Antigravity mutation is authorized. The issue-linked GitHub PR and merge are the
explicit repository delivery actions in `integrate-reviewed-branch`. Issue closure, Operations-board
progression, and outcome evidence harvesting occur after the Verified Workflow passes and the merge
is read back; they remain governed by the already approved outcome lifecycle and do not select port
survivors.

## Sequencing and Checkpoints

1. Repair the discovery snapshot rule and scoped Bandit warning through non-Git tests.
2. A Git integration operator runs the real read-only three-host discovery and proves sibling
   cleanliness.
3. U1 establishes the schema and decision semantics around the discovered packet set.
4. U2 preserves the Git-owned discovery boundary and proves mutation rules in temporary repositories.
5. U3 curates the complete pending campaign ledger against the pinned inventory snapshots.
6. U4 replaces the normal runbook and records the governance decisions.
7. Focused validation and independent review run before Jeff sees the decision packet.
8. One remediation and one targeted recheck close every actionable review finding.
9. After the targeted recheck stops on RC-001, the operator-approved revision 3 exception
   type-narrows only the two test helpers and independently reruns focused mypy and the 50-test suite.
10. Root presents the complete ranked report and pauses for Jeff's survivor mapping.
11. The exact mapping is recorded and the full validation ladder runs.
12. The final Git integration operator commits, pushes, verifies CI, merges, and proves `origin/main`.
13. Root closes issue #16, updates the Operations board and outcome evidence, and uses the approved
   stable IDs to unlock planning for issue #15 without inventing migration units.

## Prerequisite and Unlock Map

| relationship | issue or evidence | effect on this plan |
|---|---|---|
| completed prerequisite | GitHub issue #20 and PR #24 | supplies the versioned host-capability vocabulary, safe probe interface, and promotable receipt rules used by R13 |
| historical discovery seed | target README at Claude commit `099ec4c` | starts history discovery but cannot establish current semantic completeness |
| current source inputs | local Claude and Codex `HEAD == origin/main` plus Antigravity `origin/main` target baseline | remain read-only; Claude/Codex divergence stops discovery, while Antigravity feature-branch HEAD is recorded separately |
| operator gate | Jeff's complete candidate disposition mapping | required before `record-decisions`, final validation, merge, or issue closure |
| directly unlocked | GitHub issue #15 | may derive migration units and dependency order only from the fully decided stable ID set |
| later release consumers | GitHub issues #18 and #22 | consume release-drift disclosure and exact source snapshots for conformance and canary evidence |

No credential, deployment, installation, infrastructure, vendor, or specialist prerequisite is
required. A new source-host interface, outcome edge, or host capability would be a plan amendment.

## Reviewability and Delivery Boundary

The delivery target is one issue-linked PR merged to `main`. The campaign ledger, tool, fixtures,
runbook, review artifact, and journal decision land together because the ledger would not be
governable without its validator and the validator would have no accepted campaign without the
operator decision.

Planning artifacts are committed before workflow execution and are not writable workflow paths.
The pre-existing `.serena/project.yml` change is excluded. No source repository, installed plugin,
user configuration, deployment, or production surface is part of delivery.

## Risks and Mitigations

| risk | consequence | mitigation |
|---|---|---|
| historical marker is treated as complete | older or Codex-only capabilities disappear | reconcile history with all three complete current trees |
| path heuristics are treated as semantics | repeated edits become fake features or distinct features collapse | curate stable IDs; tooling only normalizes and detects unmatched/duplicate edit ownership |
| ranking becomes an implicit decision | low-ranked candidates vanish without operator review | separate recommendation and decision fields; require complete explicit mapping |
| refreshed source drifts during the campaign | approval is bound to stale evidence | disclose planning and inventory snapshots; run release refresh and block on unmatched drift |
| discovery writes to a sibling or install root | source or local runtime changes unexpectedly | strict read-only Git allowlist, output containment, pre/post repository-state proofs |
| decision recording starts migration design | issue #16 absorbs issue #15 | prohibit migration units, estimates, sequencing, code, and outcome-edge changes |

## Scope Boundaries

### In Scope

- One v1 semantic port-ledger schema and CLI.
- Read-only three-host discovery and release refresh.
- Stable candidate IDs, provenance, ranking inputs, dispositions, rationale, and revisit triggers.
- The complete `2026-07-30-saga-reliability` campaign ledger.
- Explicit Jeff survivor/non-survivor decision recording.
- Runbook, focused fixtures/tests, review artifact, and engineering-journal decision.

### Deferred to Issue #15

- Migration units, estimates, dependency order, and implementation sequencing.
- Any Antigravity-native implementation of an approved survivor.
- Plugin version bumps caused by survivor implementation.

### Non-Goals

- Automatic semantic value judgments or automatic approval thresholds.
- Blind file copying or target `team-execution` creation.
- New dependencies, databases, services, schemas beyond v1, or cross-repository writes.
- Plugin installation, host configuration, deployment, or live canary execution.
- General cleanup outside the declared files.

## Validation Plan

Run the narrowest checks first, then the issue-level and repository integration checks:

```bash
python3 scripts/port_ledger.py report \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

python3 scripts/port_ledger.py validate --inventory-only \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

python3 scripts/port_ledger.py validate \
  docs/ports/2026-07-30-saga-reliability/ledger.yaml

uv run pytest plugins/saga/tests/test_port_ledger.py -q

uv run ruff check \
  scripts/port_claude_plugin.py \
  scripts/port_ledger.py \
  plugins/saga/tests/test_port_ledger.py

uv run mypy \
  scripts/port_claude_plugin.py \
  scripts/port_ledger.py

uv run bandit -q -c pyproject.toml \
  scripts/port_claude_plugin.py \
  scripts/port_ledger.py

python3 scripts/validate_plugins.py
uv run pytest -q
```

Read-only boundary proof captures `git status --porcelain=v2`, `HEAD`, index-tree identity, and
untracked paths for both sibling repositories before and after discovery. The same check verifies
that no installed-plugin root was written.

## Operator Decision and Handoff

The first operator pause is the exact Workflow Contract approval. The second is the substantive
candidate decision after the tested, reviewed pending report exists.

After Jeff supplies the complete candidate mapping and the merged ledger validates, issue #15 may
be updated with the approved stable IDs and current host-capability receipt. That later plan derives
migration units and ordering from the decided ledger. Issue #16 itself must not do so.

## Sources

- GitHub issue #16: `Inventory and rank semantic port candidates`
- `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`
- `docs/reviews/2026-07-26-antigravity-saga-reliability-system-requirements-review.md`
- `docs/ideation/2026-06-27-antigravity-harness-ideation.md`
- `.agents/skills/port-claude-plugins/SKILL.md`
- `scripts/port_claude_plugin.py`
- `docs/plans/2026-07-08-port-claude-july-updates-plan.md`
- `plugins/fleet-core/references/antigravity-capability-probes.yaml`
- `STRATEGY.md`
- `docs/engineering-journal/DECISIONS.md`
- `docs/engineering-journal/LEARNINGS.md`
