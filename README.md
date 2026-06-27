# Infiquetra Antigravity Plugins

Google Antigravity plugins for Infiquetra engineering workflows.

## Plugins

| plugin | surfaces |
|--------|----------|
| `deploy` | agent, commands, skill |
| `home-lab-ops` | agent, skills |
| `mission-control` | agent, commands, config |
| `multi-agent-consensus` | command, skills |
| `saga` | commands, skills |
| `todoist` | tool |
| `unifi` | agent, command, skills |

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
