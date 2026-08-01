# Live Receipt Commands

Use these commands when a Saga phase runs from a target repository that does not contain the plugin
source. The current working directory stays at the target repository root.

## Resolve installed helpers

```bash
SAGA_PLUGIN_ROOT="${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/saga}"
CONSENSUS_PLUGIN_ROOT="$(dirname "$SAGA_PLUGIN_ROOT")/multi-agent-consensus"
test -f "$SAGA_PLUGIN_ROOT/scripts/transition_receipts.py"
test -f "$SAGA_PLUGIN_ROOT/scripts/artifact_promotion.py"
```

For a phase with a `saga.deliberation-phase.v1` declaration, also require:

```bash
test -f "$CONSENSUS_PLUGIN_ROOT/scripts/deliberation.py"
```

Stop as `unavailable` when a required helper is absent. Do not search the target repository for a
copy and do not replace the command with a direct canonical document write.

## Stage explicit inputs

Write phase-local input files under `.gemini/saga/receipts/<phase>/`. This directory is disposable
staging, not canonical evidence. Use the phase declaration for the manifest and strategy result
requirements. Requested model or effort must not be copied into observed fields when the host did not
report it.

A deliberation phase writes `manifest.json`, `results.json`, `convergence.json`, and
`escalation.json`, then runs:

```bash
python3 "$CONSENSUS_PLUGIN_ROOT/scripts/deliberation.py" evaluate \
  --repo-root . \
  --outcome-id <outcome-id> \
  --manifest .gemini/saga/receipts/<phase>/manifest.json \
  --results .gemini/saga/receipts/<phase>/results.json \
  --convergence .gemini/saga/receipts/<phase>/convergence.json \
  --escalation .gemini/saga/receipts/<phase>/escalation.json
```

Exit status `2` means the deliberation is incomplete or invalid and blocks the phase. The JSON output
names the repository-relative receipt path. Do not continue from a narrated claim of coverage.

## Build the transition receipt

Write `evidence.json` with exactly these eight arrays:

```json
{
  "input_refs": [],
  "operator_decisions": [],
  "execution_receipts": [],
  "canonical_outputs": [],
  "check_results": [],
  "review_findings": [],
  "lifecycle_evidence": [],
  "external_facts": []
}
```

Every item uses the existing `saga` evidence shape: `evidence_id`, `kind`, `subject`, `producer`,
repository-relative `reference`, `digest` as `sha256:<hex>`, `verification_state`, and `assertion`.
A phase with deliberation adds the completed receipt as `kind: deliberation-receipt` under
`lifecycle_evidence`; the command revalidates its closed shape and identity. A phase without declared
deliberation binds its staged artifact through the evidence kind required by the supplied obligation
contract. Never fabricate independent execution, review, or quality-assurance receipts.

```bash
python3 "$SAGA_PLUGIN_ROOT/scripts/transition_receipts.py" build \
  --repo-root . \
  --outcome-id <outcome-id> \
  --contract <repository-relative-obligation-contract.json> \
  --transition-id <phase>-complete \
  --obligation-id <phase-obligation-id> \
  --evidence .gemini/saga/receipts/<phase>/evidence.json
```

Exit status `2` means the obligation is not satisfied or an input is invalid. The JSON output names
the repository-relative transition receipt path.

## Promote the staged artifact

Only after the transition receipt is satisfied, promote the staged file:

```bash
python3 "$SAGA_PLUGIN_ROOT/scripts/artifact_promotion.py" promote \
  --repo-root . \
  --outcome-id <outcome-id> \
  --phase <phase> \
  --source-role antigravity-runtime \
  --source-ref .gemini/saga/receipts/<phase>/artifact.md \
  --staged-file .gemini/saga/receipts/<phase>/artifact.md \
  --target-ref <canonical-docs-path> \
  --transition-receipt <repository-relative-transition-receipt.json>
```

For `/impl-spec`, repeat promotion for each required staged file and promote the set manifest last.
Exit status `2` means unsatisfied evidence or a preserved conflict. Stop for operator adjudication on
conflict. These commands perform local file work only; they do not grant commit, push, PR, issue,
board, merge, plugin-installation, or deployment authority.
