# Live Saga Release-Review Rubric

Use this rubric only after the issue #22 run passes mechanical verification. Compare the Gemini
workspace with both approved artifacts under `docs/conformance/baselines/reference-lifecycle/`.
File presence, strategy counts, and successful commands are not evidence of substantive quality.

| Dimension | Approve when | Reject when |
|---|---|---|
| Depth | The work covers the profile-backed specification, plan, implementation, reviews, quality assurance, reconciliation, and handoff with explicit failure handling. | Important decisions, failure paths, or lifecycle stages are superficial or absent. |
| Evidence use | Completion claims point to repository artifacts, checks, receipts, or observed facts. | The work relies on narration, assumptions, or unbound claims. |
| Seed retention | The reference profile, folder contract, seed constraints, review gates, and remote-mutation prohibition remain visible in the delivered work. | A material operator seed is dropped, weakened, or replaced. |
| Adjudication | Conflicting meaningful work is preserved and routed for an operator decision. | The run chooses a winner by convenience, timestamp, or unsupported judgment. |
| Lifecycle completeness | Every required phase settles before the validated local handoff is produced. | Handoff or completion is claimed while a required phase, review, receipt, or quality gate remains unsettled. |

Record one decision for every dimension. An approved release requires all five values to be
`approved`; a rejected release requires at least one `rejected` value. The decision reference must
be a canonical comment on issue #22. A pending decision has no reference and keeps all five values
at `pending`.

The reviewer must reject a mechanically green run when its reasoning is materially shallower than
both approved baselines, it loses an operator seed, it mishandles conflict, or it narrates completion
without bound evidence. A rejected run is replaced by a new passing run; do not edit model output to
manufacture a pass.
