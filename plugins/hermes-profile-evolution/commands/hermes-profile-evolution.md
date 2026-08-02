---
name: hermes-profile-evolution
description: Route profile-owned Team Mimir requests into target-owned Hermes dialogue
argument-hint: "request | reply | resume | status | census | doctor"
---

# Hermes Profile Evolution

Run the adapter through the active Antigravity plugin root and pass the Team Mimir repository root
separately. `AGY_PLUGIN_ROOT` is Antigravity's active-plugin location; the fallback is the standard
installation root used by this repository. Pass request content as one bounded JSON value on
standard input; do not interpolate intent, evidence, or dialogue text into a shell command.

```bash
TEAM_MIMIR_ROOT="${TEAM_MIMIR_ROOT:-$PWD}"
HERMES_PROFILE_EVOLUTION_PLUGIN_ROOT="${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/hermes-profile-evolution}"
python3 "$HERMES_PROFILE_EVOLUTION_PLUGIN_ROOT/scripts/profile_request.py" \
  --team-mimir-root "$TEAM_MIMIR_ROOT" request <<'JSON'
{
  "target": "brokkr",
  "requester": {"actor_kind": "operator", "actor_id": "operator", "verification": "claimed"},
  "delegation_chain": [
    {"actor_kind": "harness", "actor_id": "antigravity", "verification": "claimed"}
  ],
  "intent": "Consider refining your review preference.",
  "evidence_references": ["docs/proposal.md"],
  "paths": ["profiles/brokkr/SOUL.md"]
}
JSON
```

The `request` action calls the real classifier under `TEAM_MIMIR_ROOT` first. Ordinary repository
paths return a normal-work result without contacting Hermes. Profile-owned paths, or a mixed set
that names exactly one profile, become a canonical suggestion. Prohibited, unknown, external,
custodian-owned, and cross-target requests stop.

For `reply`, provide `{"envelope": <canonical-envelope>, "message": "..."}` on standard input.
For `resume`, provide the canonical envelope. For `status`, provide `proposal_id`, `revision`, and
`target` as one JSON object. For `census`, provide the canonical census input. For `doctor`, provide
`{"target": "profile-name"}`.

This is live chat dialogue, not queue submission. The target profile retains authorship and may
decline, defer, ask a question, or make no change. If classification, health, service, provenance,
or response validation fails, stop; never fall back to a direct profile edit.
