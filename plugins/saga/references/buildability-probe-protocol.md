# Buildability Probe Protocol

The buildability probe asks whether two reasonable implementers can build the same externally visible
system from the specification set. It is a fresh-context quality gate shared by `/impl-spec` and
`/doc-review`.

## Input boundary

The probe receives only:

- the promoted or staging spec-set files under review;
- shared project and repository standards;
- the folder-contract README;
- this protocol.

It does not receive authoring transcripts, private prompts, author conclusions, prior probe reports,
remediation notes, or a desired verdict. Native probing requires `agy.agent.execution=passed`.
Receipt-backed isolated-sequential probing requires `agy.sequential.isolation=passed` and a separate
conversation identity. Same-context roleplay is not a fresh probe.

## Forced implementation breakdown

Enumerate these categories even when the correct value is an empty list:

- repositories;
- stacks or modules;
- every endpoint;
- every data entity;
- every event published and consumed;
- the implementation test plan.

The breakdown is evidence that the probe tried to implement the whole set rather than sampling its
headings.

## Forced questions

Enumerate questions under exactly five categories: product, architecture, data, API, and operations.
An empty category must be present as an empty list. For every question, record the question,
classification, and reasoning.

The allowed classifications are:

- `spec-defect` — two reasonable implementers could answer differently and the difference would be
  visible in API behavior, data shape, or user experience;
- `execution-discovery` — the difference is internal method naming, code organization, or operational
  configuration that the implementation can choose without changing the observable contract.

## Hard verdict

The machine result uses `saga.buildability-probe.v1`. PASS requires zero `spec-defect` questions.
Any boundary-test defect requires FAIL. Artifact presence, document length, a model's confidence, or a
mechanically complete folder set cannot override that rule.

Validate the result with:

```bash
python3 plugins/saga/scripts/impl_spec.py probe-check <probe-result.json>
```

Fix the specification, never the probe. A remediation sweep fixes the finding class across the set
and updates lifecycle and contract/prose evidence before a new isolated probe. `/impl-spec` allows at
most three rounds.

## Durable artifact

Write the human-readable report under
`docs/reviews/YYYY-MM-DD-<subject>-buildability-probe[-rN].md` and keep the validated JSON result
beside the applicable transition evidence. The report names the execution identity, input manifest,
question classifications, verdict, and unresolved findings without embedding transcripts or machine
paths.
