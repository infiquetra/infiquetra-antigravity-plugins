---
name: pulse
description: Derive advisory provider quality and drift from supplied sanitized receipts without live calls or automatic routing.
argument-hint: "--receipts-json PATH --as-of ISO-8601"
---

# Provider pulse

`/pulse` answers “what do the supplied provider observations show?” It is a read-only evidence
consumer, not a provider runner or routing engine.

## Input contract

Accept a JSON list of existing `run_fact.v1` records whose `kind` is `engine`. Each record names its
leaf `subplot_id`, observation time, provider, capability, observed quality, latency, cost, and an
evidence SHA-256 digest. Receipts must already be sanitized. Reject secret-bearing fields, invalid
digests, future observations, stale observations, and provider-capability groups below the declared
sample floor.

The operator supplies `--as-of`; the report does not read the wall clock. See
`references/manual-verification.md` for a local fixture recipe.

## Report contract

Run `scripts/pulse.py` to emit the existing `pulse_snapshot.v1` shape with:

- receipt count and source schema;
- deterministic per-provider capability ratings;
- quality, latency, and cost drift verdicts;
- material provider disagreements; and
- `routing_authority: false` and `recommended_provider: null`.

The measurements are advisory. Present the report and ask the operator whether to investigate,
collect more evidence, or make no change. Do not auto-select a provider, rewrite policy, dispatch a
model, or claim that a sparse sample proves quality.

## Stop conditions

Stop with a named error on malformed, sensitive, sparse, stale, or future-dated input. Stop after
rendering the report and the operator choice. `/pulse` never writes Saga state or a telemetry cache.
