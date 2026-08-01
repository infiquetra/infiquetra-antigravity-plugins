---
name: pulse
description: Report provider quality and drift from supplied sanitized receipts
argument-hint: "--receipts-json PATH --as-of ISO-8601"
---

Load `saga/skills/pulse/SKILL.md` and render one deterministic provider-telemetry report.
The command accepts only a caller-supplied JSON list of existing `run_fact.v1` engine records. It
does not call a provider, read credentials, select a model, change routing, or write lifecycle state.

Run `python3 plugins/saga/scripts/pulse.py $ARGUMENTS`. Sparse, stale, future-dated, malformed, or
sensitive receipts fail closed. The report exposes quality ratings, control-chart drift, and provider
disagreement as advisory evidence. The operator chooses what, if anything, to do with those signals.
