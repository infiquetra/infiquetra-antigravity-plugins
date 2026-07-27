# fleet-core

Canonical home for cross-plugin shared primitives in the Infiquetra plugin fleet, plus the
canonical copy of the resolution shim that sibling plugins vendor to reach it. Decision record:
`docs/engineering-journal/DECISIONS.md` `{#fleet-commons-mechanism-463}` (issue #463).

This is a **scripts-only library plugin** — no skills, commands, agents, or hooks. Installing it
contributes nothing to an Antigravity session directly; it exists so other installed plugins can
resolve shared code at a single canonical location instead of hand-copying it (the
`validate_card_body` drift incident, #222, is the failure mode this prevents).

## Antigravity capability catalog

`references/antigravity-capability-probes.yaml` is the canonical, schema-versioned
host capability catalog. Despite the `.yaml` suffix, it intentionally uses only
comment-free JSON syntax and is parsed with the Python standard library. Do not
add YAML comments, anchors, tags, shell commands, executable paths, or other
general YAML features.

Catalog rows select a fixed registered probe method and revision. The Python
registry owns argument vectors, timeouts, parsers, and sanitization. Consumer
requiredness is declared by profile; a required failed, unknown, or unavailable
capability blocks that consumer. Only an optional capability with a previously
declared and proven fallback can evaluate as degraded.

Controlled model-selection facts are valid only when the requested and observed
identifiers appear in that catalog row's closed `allowed_values` list. This
keeps arbitrary hostnames, credentials, and high-entropy strings out of
promotable receipts; add a reviewed canonical model to the catalog before using
it in evidence.

Passed runtime-base evidence is cross-bound to typed observations: normalized
CLI and host versions, the complete logical runtime-root set, and affirmative
requested/observed plugin link, load, and validation facts. Evidence identifier
strings alone cannot authorize a consumer.

Promotable evidence uses the strict `antigravity.capabilities.v1` schema. Raw
output, absolute runtime roots, transcripts, prompts, environment data, and
credentials belong only in ignored local diagnostics under
`.gemini/saga/capability-doctor/`. Use
`antigravity_diagnostics.sanitize_for_promotion` to cross that boundary; do not
copy diagnostic fields into a receipt. Ignored diagnostics can still contain
sensitive local evidence. Writers automatically remove files older than seven
days, including crash-left writer temporary files, and keep at most 20 completed
JSON files by default. Operators can immediately clear every writer-owned
artifact with `antigravity_diagnostics.purge_local_diagnostics(repo_root)`.
Repository backups and filesystem snapshots remain outside this retention
boundary.

Consumers load `antigravity_capabilities` through the shim, validate the
receipt against the canonical catalog, and call `evaluate_for_consumer`
directly. They may format the returned object or choose an exit status, but they
must not rename its states, collapse its blocking/degraded lists, or infer
lifecycle completion from it.

## Layout

```
fleet-core/
├── plugin.json
├── scripts/
│   ├── fleet_commons_shim.py     # canonical shim — consumers vendor a byte-identical copy
│   └── fleet_commons/            # the primitives, one stdlib-only module each
│       └── tier_palette.py       # MODELS / EFFORTS / CHEAP_MODELS / ENGINE_INTENTS + ranks
```

## How a consumer plugin uses it

1. Vendor `scripts/fleet_commons_shim.py` into your plugin's `scripts/` directory,
   byte-identical (a repo drift-guard test compares every vendored copy to the canonical file).
2. Resolve and load:

   ```python
   import fleet_commons_shim

   tier_palette = fleet_commons_shim.load("tier_palette")
   tier_palette.model_rank("gemini-3.5-flash")
   ```

The shim resolves the fleet-core root by the first rung that succeeds — `FLEET_COMMONS_ROOT`
env override → repo-checkout walk-up → `~/.gemini/config/plugins/fleet-core` lookup →
cache-sibling scan — and fails loud with an actionable message when none does. Set
`FLEET_COMMONS_DEBUG=1` to print the resolution provenance
(`fleet-commons: rung=<n> (<name>) root=<path>`) to stderr.

## What belongs in commons — and what does not

**Belongs:** small, stdlib-only, fleet-wide vocabulary and pure helpers that would otherwise be
hand-copied — tier palettes, shared constants, tiny pure functions. Additive-only change within
0.x: a consumer never breaks because fleet-core updated.

**Does not belong:** anything with third-party dependencies (the marketplace install runs no
pip/venv step); plugin-specific business logic; anything that churns with a single plugin's
release cadence; contract mirrors (those are being abolished, not centralized).
