# Fleet effort convention (#363)

The single reference for how `effort` is authored, validated, resolved, and honored across the
Infiquetra plugin fleet. Any plugin's agent frontmatter or multi-agent-consensus's A7 worker registry may
declare an `effort:` value — this doc is the one place that explains what happens to it. Do not
re-declare this convention per-plugin; link here instead.

## Vocabulary

Canonical vocabulary is `fleet_commons.tier_palette.EFFORTS = ("low", "medium", "high", "xhigh")`
(KTD3). Never hand-copy this tuple — resolve it via `fleet_commons_shim.load("tier_palette")`.

## Authoring

Any `plugins/*/agents/*.md` file MAY carry an `effort:` frontmatter field. If present, its value
MUST be one of `EFFORTS`. A required CI lint (`tests/test_agent_tier_lint.py`) globs every agent file and fails
on an out-of-vocabulary `effort:` (or `model:`) value. A file can opt out with `tiering_exempt: true`
frontmatter.

Example (from `plugins/multi-agent-consensus/agents/security-reviewer.md`):

```yaml
---
name: security-reviewer
model: gemini-3.1-pro
effort: high
---
```

## Resolution: the three-layer cascade

Most-specific wins, in this order:

1. Plan-authored per-unit tier (from `/plan`'s per-unit tier authoring).
2. Team-level default (an optional team-wide effort override; usually absent today).
3. Per-teammate agent-frontmatter default (`effort:`, layer 1 above).

The cascade wraps `fleet_commons.tier_resolver.resolve(role_kind, work_shape, envelope_ceiling,
operator_override)` (KTD4) — it is not a fourth standalone resolver. A plan-unit tier maps to
`operator_override={"effort": …}` when present, short-circuiting the wrap. Chaperone workers
(`Intent` = `offload` / `second-opinion` in the A7 worker table) are excluded from the cascade
entirely — their effort is an intent-driven default (`gemini-3.5-flash/medium` for offload, `gemini-3.1-pro/high` for
second-opinion), not a value to resolve or override (KTD5).

## Honoring: one seam, three spawn kinds

`fleet_commons.effort_rider.inject_effort(prompt, effort, spawn_kind)` is the single seam that
decides *how* a resolved effort is honored (KTD1). It understands three `spawn_kind` values:

| `spawn_kind`      | Mechanism                                                        | Real knob? |
|-------------------|-------------------------------------------------------------------|------------|
| `workflow`        | Pass-through — effort already rides in `agent(prompt, {effort})` (`execution_spec.py:982`) | Yes |
| `external-engine` | Pass-through — effort already passed as `effort=resolution.effort` (`external-engine-workers.md:155`) | Yes |
| `agent`           | Gemini generation config thinking level payload `{"generation_config": {"thinking_level": gemini_level}}` returned by `inject_effort` to the teammate spawn seam | Yes |

The `agent` branch maps resolved efforts ("low", "medium", "high", "xhigh") to Gemini-native
thinking levels ("low", "medium", "high") using a configuration payload. This allows the Antigravity
harness to control the reasoning effort of resident teammates natively through standard model API parameters.

Calling `inject_effort()` with an unknown `effort` or an unknown `spawn_kind` raises `ValueError`
rather than silently no-op'ing.

## Reconciliation

Post-run, each teammate's cascade-resolved effort is reconciled via
`fleet_commons.effort_rider.reconcile_effort(resolved_effort, spawn_kind, manifest_effort=..., spawn_payload=...)`.
A mismatch returns a named `tiering-drift[<spawn_kind>]` line; a match returns `None` (nothing emitted).
The comparison is honest per path (KTD7): on a real-knob path (`workflow` / `external-engine`) pass `manifest_effort` —
the manifest's effort value is compared directly against the resolved effort; on the `agent` path pass
`spawn_payload` instead — reconciliation confirms that the Gemini-native generation configuration payload contains
the correct `thinking_level` mapping for the resolved effort.


## Where to look

- Vocabulary: `plugins/fleet-core/scripts/fleet_commons/tier_palette.py`
- Cascade: `plugins/fleet-core/scripts/fleet_commons/tier_resolver.py`
- Honoring seam: `plugins/fleet-core/scripts/fleet_commons/effort_rider.py`
- CI lint: `tests/test_agent_tier_lint.py`
- Multi-agent consensus wiring: `plugins/saga/skills/work/SKILL.md`
- Chaperone dispatch / intent defaults: `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md` (planned / deferred)
- Worker manifest / provenance: `plugins/multi-agent-consensus/skills/multi-agent-consensus/references/external-engine-workers.md` (planned / deferred)
