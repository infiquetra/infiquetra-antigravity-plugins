# Impl-Spec Stage Contract

Each stage starts only after the previous exit criteria are satisfied. The orchestrator records a
scratch checkpoint after each exit but treats repository artifacts and receipts as the only durable
authority.

## Stage 1 — Research

Entry:

- a validated `saga.impl-spec-profile.v1`;
- a parsed folder contract and dependency waves;
- settled upstream requirements or an issue reference;
- repository and relevant context-library evidence available read-only.

Produce one grounding brief containing:

- settled decisions with source paths;
- entity, endpoint, event, actor, and integration inventories implied by current evidence;
- cross-spec obligations from already accepted specifications;
- divergences between the declared spec root and current implementation reality;
- open questions, each with a recommended resolution and the cost of deciding incorrectly.

Exit when every claim has a source and every open product decision is either resolved or explicitly
blocking. Autonomous mode may resolve mechanical questions from evidence but cannot silently choose a
product-visible behavior. Interactive mode pauses for the operator's decisions.

## Stage 2 — Author

Entry: the grounding brief is accepted and the host execution capability is proven.

For each dependency wave returned by `impl_spec.py discover`, issue one assignment per folder using
`authoring-subagent-prompt.md`. Native mode may launch the whole wave in one `invoke_subagent` call.
Isolated-sequential fallback uses a fresh conversation and identity receipt per assignment. Every
assignment writes only beneath the ignored mirrored workspace declared by the skill. A later wave
may read accepted staged outputs from earlier waves; same-wave authors do not share mutable files.

Every stateful spec includes the lifecycle-closure matrix from the shared template. Every author also
enforces:

- one canonical source for cross-record interaction rules;
- field, enum, error, endpoint, and event agreement in contract and prose both directions;
- repository-relative links and no machine-local paths or private transcript material;
- the folder's declared required files and completeness rule.

Exit when every assigned folder returns a complete receipt-backed result, required files exist in
staging, lifecycle cells are nonblank and noncontradictory, and the orchestrator has reconciled
cross-folder names and counts. Interactive mode pauses for a closure-matrix skim.

## Stage 3 — Assemble

Entry: every authoring wave is complete.

Rewrite the spec-set README last. It must retain the folder contract and index the documents that now
exist, with purpose, ownership, dependencies, and validation instructions. Do not weaken the folder
contract to match missing output.

Exit when every declared file is indexed and every README link resolves within the repository.

## Stage 4 — Verify

Entry: the root README represents the assembled set.

Run:

```bash
python3 plugins/saga/scripts/impl_spec.py validate \
  --repo-root .gemini/saga/impl-spec/<profile-id>/workspace \
  --profile <profile.json>
```

Also verify:

- every relative link resolves;
- entity, endpoint, event, actor, and error counts agree across documents;
- OpenAPI, JSON Schema, Mermaid, or other present contract formats pass their existing repository
  validators;
- contract fields and prose references agree both directions;
- no promoted-evidence sanitization rule is violated.

Exit only on a clean mechanical result. Verification failures return to the owning Stage 2 folder or
Stage 3 README; they do not proceed as review findings.

## Stage 5 — Review

Entry: Stage 4 is clean.

Run two separately evidenced lenses:

1. security/access-control — actors, authorization, tenant boundaries, secrets, threat cases, audit,
   revocation, and failure behavior;
2. consistency/standards — folder contract, shared terminology, lifecycle closure, contract/prose
   synchronization, context-library conventions, and operational ownership.

Each reviewer receives the spec set and shared standards, not the author's hidden reasoning. Fix every
actionable P0-P3 item or classify it non-actionable with concrete evidence. Interactive mode pauses
for finding review, but cannot waive a spec defect by calling it an implementation detail.

Exit when both review receipts exist and no actionable finding remains.

## Stage 6 — Probe+Remediate

Entry: Stage 5 is clean.

Invoke `/doc-review` buildability-probe mode with the exact input boundary in
`../../../references/buildability-probe-protocol.md`. Validate its machine result:

```bash
python3 plugins/saga/scripts/impl_spec.py probe-check <probe-result.json>
```

On FAIL, group defects by class. A remediation assignment sweeps the class across all folders,
updates the lifecycle matrix and contract/prose pairs, reruns Stage 4 checks, and returns to a fresh
probe conversation. Do not show a new probe prior probe artifacts, authoring context, or remediation
notes.

Round 1, 2, and 3 are allowed. A third FAIL exits `unavailable` with the unresolved structured
defects and requires operator direction; there is no fourth round.

Exit on a validated PASS, then build the spec-set manifest from the same mirrored workspace and
perform canonical promotion as defined by the skill. Promotion is the first write to canonical
`docs/specs/` content.
