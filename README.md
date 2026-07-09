# Infiquetra Antigravity Plugins

Google Antigravity plugins for Infiquetra engineering workflows.

## Plugins

| plugin | surfaces |
|--------|----------|
| `deploy` | agent, commands, skill |
| `fleet-core` | scripts |
| `home-lab-ops` | agent, skills |
| `mission-control` | agent, commands, config |
| `multi-agent-consensus` | command, skills |
| `saga` | commands, skills |
| `todoist` | tool |
| `unifi` | agent, command, skills |

## Portability Matrix

This repository natively ports the `infiquetra-claude-plugins` ecosystem to Google Antigravity.
Current upstream sync state:

| Plugin | Upstream Source Repo | Synced Commit (SHA) |
|--------|----------------------|---------------------|
| `deploy` | `infiquetra-claude-plugins` | `099ec4c` |
| `fleet-core` | `infiquetra-claude-plugins` | `099ec4c` |
| `home-lab-ops` | `infiquetra-claude-plugins` | `3987510` |
| `mission-control` | `infiquetra-claude-plugins` | `099ec4c` |
| `multi-agent-consensus` | `infiquetra-claude-plugins` | `099ec4c` |
| `saga` | `infiquetra-claude-plugins` | `099ec4c` |
| `todoist` | `infiquetra-claude-plugins` | `3987510` |
| `unifi` | `infiquetra-claude-plugins` | `3987510` |

## Layout

```text
plugins/<plugin-name>/
├── plugin.json
├── agents/
├── commands/
├── skills/
└── config/
```

`plugin.json` lives at the plugin root. See [docs/PLUGIN_SPEC.md](docs/PLUGIN_SPEC.md).

## Install

```bash
./tools/install-plugin.sh list
./tools/install-plugin.sh install saga
./tools/install-plugin.sh install-all
```

Manual install uses Antigravity's plugin directory:

```bash
mkdir -p ~/.gemini/config/plugins
ln -s "$(pwd)/plugins/saga" ~/.gemini/config/plugins/saga
```

Restart Antigravity after changing plugin links.

## Verify

Run the read-only doctor before blaming model behavior:

```bash
uv run python scripts/validate_plugins.py
```

Machine-readable output:

```bash
uv run python scripts/validate_plugins.py --json
```

The legacy marketplace validator path remains as a compatibility wrapper:

```bash
uv run python marketplace/validator/validate.py
```

## Quality Checks

```bash
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run mypy plugins/ scripts/ tests/
uv run bandit -r plugins/ scripts/ tests/ -ll
```
