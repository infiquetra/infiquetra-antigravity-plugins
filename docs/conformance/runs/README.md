# Live Saga Conformance Runs

The live canary qualifies one integrated Antigravity release against the deterministic
`reference-lifecycle` fixture. It is a release check, not a model benchmark or general transcript
collector.

Run the three commands in order:

```bash
uv run python scripts/run_agy_saga_canary.py preflight --fixture reference-lifecycle
uv run python scripts/run_agy_saga_canary.py run --fixture reference-lifecycle
uv run python scripts/run_agy_saga_canary.py verify \
  .conformance-local/live-canary/runs/<run-id>/run-manifest.json
```

Preflight runs the deterministic fixture before any model call. It then proves the approved AGY
version, Antigravity host version, model, effort, lifecycle-router execution, conversation resume,
plugin state, runtime roots, and sandbox boundary. Native AGY plan mode is not required: the canary
uses the Saga `/plan` command in edit-enabled sandbox mode because a durable plan is an expected
output.

The run creates a fresh local Git repository with no remote. Raw stream events, prompts, workspace
files, and machine paths remain under the ignored `.conformance-local/` directory. The runner stops
on the first failed phase, missing canonical artifact, changed conversation identity, or forbidden
remote, plugin-management, credential, merge, or deployment attempt.

A mechanically valid run remains release-blocking while `release_review.state` is `pending`. Jeff
reviews the workspace against [the release-review rubric](../release-review-rubric.md), records each
dimension as `approved` or `rejected`, and supplies the canonical issue #22 comment URL. Approval
requires every dimension to be approved. Only the sanitized manifest, receipt identities, validator
results, comparison summary, and decision may be promoted after sanitization; raw events remain
local.
