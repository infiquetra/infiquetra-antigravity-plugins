# Antigravity Plugin Specification

This repository uses Antigravity's flat plugin layout. The canonical validator is `scripts/validate_plugins.py`; `marketplace/validator/validate.py` is only a compatibility wrapper.

## Layout

```text
plugins/<plugin-name>/
├── plugin.json
├── agents/
│   └── <agent>.md
├── commands/
│   └── <command>.md
├── skills/
│   └── <skill>/
│       └── SKILL.md
├── config/
│   └── optional-config.json
├── README.md
└── CHANGELOG.md
```

Only `plugin.json` is mandatory. A useful plugin should expose at least one skill, command, agent, tool entry, or config file.

## Manifest

`plugin.json` lives at the plugin root.

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Short description of what the plugin does"
}
```

Required fields:

| field | rule |
|-------|------|
| `name` | Must match the plugin directory name. |
| `version` | Semver-like string, such as `1.0.0`. |
| `description` | Non-empty summary. |

Optional fields include `author`, `repository`, `keywords`, and `tools`.

## Validation

Run the doctor before relying on a plugin in Antigravity:

```bash
uv run python scripts/validate_plugins.py
```

For machine-readable output:

```bash
uv run python scripts/validate_plugins.py --json
```

The doctor reports manifest errors, surface counts, inert empty agents, install
state under `~/.gemini/config/plugins`, stale current-spec text, capability
catalog and receipt status, promotable-receipt privacy, active host-contract
findings, and next actions.

The default `repository-validation` profile makes no `agy` subprocess call.
Use `--observe-host` to request registered bounded local observations. Use
`--capability-profile PROFILE --capability-receipt PATH` to evaluate a named
consumer against a strict `antigravity.capabilities.v1` receipt. Required
`failed`, `unknown`, or `unavailable` capabilities return exit 1. A declared
optional fallback may produce `degraded` with exit 0; it cannot downgrade a
required failure.

The JSON result contains separate `catalog`, `capability`,
`receipt_privacy`, and `host_contract` sections. The marketplace validator
remains a byte-for-byte output and exit-status compatibility wrapper.

Saga's production-facing adapter is
`plugins/saga/scripts/host_capability_gate.py`. It requires a declared
`--consumer` and a promotable `--receipt`, resolves the canonical catalog
through fleet-core, and emits fleet-core's evaluation unchanged. Exit 0 means
the named consumer is `passed` or validly `degraded`; exit 1 means blocked or
invalid evidence. The adapter does not write Saga state or mark a lifecycle
phase complete.

Rich local diagnostics live only under the ignored
`.gemini/saga/capability-doctor/` root. A local diagnostic is not a promoted
receipt and is rejected at every consumer gate. Ignoring the directory prevents
normal source-control promotion; it does not make the contents non-sensitive.
Diagnostic writers expire JSON files after seven days and retain at most 20 by
default. Writer-owned temporary files left by interrupted atomic writes expire
on the same schedule and are included in explicit purge. Call
`antigravity_diagnostics.purge_local_diagnostics(repository_root)` for immediate
purge. Filesystem snapshots and repository backups require their own retention
policy.
