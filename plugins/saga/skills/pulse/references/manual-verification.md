# Provider pulse manual verification

Use only synthetic, sanitized `run_fact.v1` engine records in a temporary JSON file. Include at least
three records for every provider-capability pair, unique evidence digests, explicit UTC timestamps,
and observed `quality`, `latency_seconds`, and `cost` values.

Run:

```bash
python3 plugins/saga/scripts/pulse.py \
  --receipts-json /tmp/provider-receipts.json \
  --as-of 2026-07-31T12:00:00Z
```

Confirm the output names `pulse_snapshot.v1`, reports the supplied receipt count, leaves
`recommended_provider` null, and sets `routing_authority` false. Then remove one provider's records,
make one record older than the maximum age, and add an `api_key` field in separate negative runs.
Each must fail closed without a live provider call or any repository write.
