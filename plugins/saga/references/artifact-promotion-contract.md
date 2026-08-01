# Canonical Artifact Promotion Contract

`artifact_promotion.py` is the local authority boundary between disposable Antigravity staging and
durable Saga evidence.

## Authority

Repository documents under the established `docs/` lifecycle families are authoritative. An
Antigravity brain, runtime file, or projection is staging only. A phase cannot claim durable
completion, resumability, handoff readiness, or outcome settlement until its applicable lifecycle
obligation binds the canonical artifact and its promotion receipt.

## Transaction

Promotion validates the target path, transition receipt, evidence references, and content before any
repository write. It then compares the canonical target with the declared predecessor while holding
an exclusive lock on the target directory.

- A missing target with no predecessor is created write-once.
- A target matching the staged content is an idempotent retry.
- A target matching the declared predecessor is replaced atomically.
- Any other state preserves the target, writes a content-addressed conflict candidate under the
  outcome directory, records `conflicting`, and requires operator adjudication.

The canonical document is written before its receipt. A document without the deterministic receipt
does not settle promotion. Retrying the same inputs completes the same receipt after an interrupted
write and creates no duplicate lifecycle state.

## Privacy

Promoted content must be UTF-8 text and must not contain absolute home paths, credential-shaped
values, private hostnames, or transcript payload fields. Errors identify only the unsafe category;
they do not echo the matched content. Source provenance is a logical role and reference, never an
absolute runtime path.

## Historical imports

A brain-only historical import may preserve useful content and source provenance. It cannot invent
execution, review, quality-assurance, or operator evidence. Required evidence kinds must resolve to
ordinary repository files and are content-addressed in the promotion receipt. Missing kinds leave
the promotion `unsatisfied`.

## Terminal no-save

Only explicitly abandoned unfinished ideation or brainstorming may end without promotion. Its
machine-readable abandonment record is not persisted as canonical evidence and declares
`phase_complete`, `resumable`, `handoffable`, and `outcome_settled` as false.

## External boundary

Promotion performs local file operations only. It does not run Git, push a branch, open or merge a
PR, mutate a GitHub issue or project board, deploy, or choose a conflict winner. Those actions remain
separate authority paths.

## Installed-plugin command

From a target repository, run `artifact_promotion.py promote` through the installed Saga plugin.
The complete locator, input, transition-receipt, and staged-file command is documented in
`references/live-receipt-commands.md`. A non-zero exit means the artifact is not durably promoted.
