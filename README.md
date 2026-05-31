# Infiquetra Antigravity Plugins

Google Antigravity plugins and specialized skills for Infiquetra engineering workflows and autonomous development pipelines.

## Available Plugins

This repository contains 11 powerful, production-ready plugins designed specifically to work natively with the **Google Antigravity** agentic ecosystem.

| Plugin | Description | Category | Layout |
|--------|-------------|----------|--------|
| [splunk](plugins/splunk/) | Splunk log querying and deep operations analysis | Operations | CLI & Skills |
| [identity-toolkit](plugins/identity-toolkit/) | Identity architecture guidance (NIST, W3C VCs, custody models) | Security | Skills-Only |
| [test-suite](plugins/test-suite/) | Parallel quality check orchestrator (pytest, ruff, mypy, bandit) | Development | CLI & Skills |
| [docs-generator](plugins/docs-generator/) | Automated README, API specs, and architecture generator | Development | CLI & Skills |
| [python-toolkit](plugins/python-toolkit/) | Production patterns for Python, Lambda, DynamoDB, and robust handler models | Development | Skills-Only |
| [sdk-lifecycle](plugins/sdk-lifecycle/) | Package scaffolding, security review, docs and release workflows | Development | Skills-Only |
| [sdlc-manager](plugins/sdlc-manager/) | Board tracking, milestones, objective synchronization, and issue triage | Development | CLI & Skills |
| [home-lab-ops](plugins/home-lab-ops/) | Local server orchestration, hardware inventory, and system status tracking | Operations | Skills-Only |
| [blueprint-reviewer](plugins/blueprint-reviewer/) | Multi-agent architectural blueprint validation | Architecture | Skills-Only |
| [team-execution](plugins/team-execution/) | Structured team review cycles and consensus protocol workflows | Orchestration | CLI & Skills |
| [unifi](plugins/unifi/) | Ubiquiti UniFi network and camera protect controllers monitoring | Operations | CLI & Skills |

---

## Restructured Flat Layout

Antigravity plugins utilize a clean, flat directory layout where the manifest `plugin.json` resides directly at the root of the plugin directory.

```
plugins/my-plugin/
├── plugin.json             # Plugin manifest (id, description, permissions)
├── README.md               # Documentation and usage
├── src/                    # Python script implementations (if CLI-based)
├── skills/                 # Declarative skills containing SKILL.md
│   └── my-skill/
│       ├── SKILL.md        # Skill instructions with frontmatter
│       └── references/     # Markdown architectural templates
└── tests/                  # Pytest suite validating plugin logic
```

---

## Installation & Setup

To equip your Antigravity agent sessions with these plugins, you can use the automated **install-plugin.sh** utility. This script automatically handles creating symlinks or directory backups in your Antigravity configurations.

### Option 1: Automated Script (Highly Recommended)
We provide a helper script inside the `tools` folder to easily list, install, and uninstall plugins.

```bash
# 1. List all available and installed plugins
./tools/install-plugin.sh list

# 2. Install a specific plugin (e.g., Slack)
./tools/install-plugin.sh install slack

# 3. Install ALL 11 plugins at once
./tools/install-plugin.sh install-all

# 4. Uninstall a specific plugin (e.g., Splunk)
./tools/install-plugin.sh uninstall splunk

# 5. Uninstall all plugins
./tools/install-plugin.sh uninstall-all
```

### Option 2: Manual Symlink
If you prefer to link individual plugins manually, run:

```bash
ln -s /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/<plugin-name> ~/.gemini/config/plugins/<plugin-name>
```

### Activating the Plugins
Once symlinked, simply start a new Antigravity agent session. The agent will automatically scan `~/.gemini/config/plugins/`, read `plugin.json` from the root of each plugin folder, and load its associated skills, subagents, and commands natively. You do **not** need to manually execute them in an external terminal!

---

## Development & Contribution

### Prerequisites
- Python 3.12+
- `uv` Python package manager

### Scaffolding a New Plugin
To create a new Antigravity plugin structured natively with a flat layout, use the scaffolding tool:
```bash
./tools/create-plugin.sh my-new-plugin "Infiquetra New Plugin"
```

### Running Quality Checks
Always run the test suite and quality guardrails before pushing any modifications:

```bash
# Sync dependency environment
uv sync --locked --extra dev

# Run pytest suite
uv run pytest

# Run Ruff linter and formatter
uv run ruff check .

# Run Mypy type validation
uv run mypy plugins/

# Run Bandit security scanner
uv run bandit -r plugins/
```

---

## License

This repository is licensed under the MIT License.
