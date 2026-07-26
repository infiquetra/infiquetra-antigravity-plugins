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
