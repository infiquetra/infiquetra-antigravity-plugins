# Infiquetra Antigravity Plugins

Google Antigravity plugins and specialized skills for Infiquetra engineering workflows and autonomous development pipelines.

## Available Plugins

This repository contains 15 powerful, production-ready plugins designed specifically to work natively with the **Google Antigravity** agentic ecosystem.

| Plugin | Description | Category | Layout |
|--------|-------------|----------|--------|
| [todoist-manager](plugins/todoist-manager/) | Full-featured Todoist task, project, and sync management | Productivity | CLI & Skills |
| [pagerduty](plugins/pagerduty/) | Incident management, on-call orchestration, and service administration | Operations | CLI & Skills |
| [slack](plugins/slack/) | Slack channel messaging, thread tracking, and reactive alerts | Communication | CLI & Skills |
| [splunk](plugins/splunk/) | Splunk log querying and deep operations analysis | Operations | CLI & Skills |
| [identity-toolkit](plugins/identity-toolkit/) | Identity architecture guidance (NIST, W3C VCs, custody models) | Security | Skills-Only |
| [test-suite](plugins/test-suite/) | Parallel quality check orchestrator (pytest, ruff, mypy, bandit) | Development | CLI & Skills |
| [docs-generator](plugins/docs-generator/) | Automated README, API specs, and architecture generator | Development | CLI & Skills |
| [python-toolkit](plugins/python-toolkit/) | Production patterns for Python, Lambda, DynamoDB, and robust handler models | Development | Skills-Only |
| [sdk-lifecycle](plugins/sdk-lifecycle/) | Package scaffolding, security review, docs and release workflows | Development | Skills-Only |
| [sdlc-manager](plugins/sdlc-manager/) | Board tracking, milestones, objective synchronization, and issue triage | Development | CLI & Skills |
| [home-lab-ops](plugins/home-lab-ops/) | Local server orchestration, hardware inventory, and system status tracking | Operations | Skills-Only |
| [blueprint-reviewer](plugins/blueprint-reviewer/) | Multi-agent architectural blueprint validation | Architecture | Skills-Only |
| [marketplace-lister](plugins/marketplace-lister/) | Catalog management and plugin registry auditing | Operations | Skills-Only |
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

To equip your Antigravity agent sessions with these plugins, you can either **symlink** individual plugins (highly recommended for live development) or **copy** them directly into the Antigravity plugins directory.

### Prerequisites

Verify your Antigravity config directory exists on macOS:
```bash
ls -la ~/.gemini/config/plugins/
```

### Option 1: Symlink (Recommended)
This links the plugins in your local repository clone directly into the Antigravity system configuration, allowing your changes to be instantly active.

```bash
# General Syntax:
ln -s /path/to/infiquetra-antigravity-plugins/plugins/<plugin-name> ~/.gemini/config/plugins/<plugin-name>

# Example - Install Slack:
ln -s /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/slack ~/.gemini/config/plugins/slack

# Example - Install PagerDuty:
ln -s /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/pagerduty ~/.gemini/config/plugins/pagerduty
```

### Option 2: Direct Copy
If you prefer a standalone copy without linking to the repository:

```bash
cp -r /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/slack ~/.gemini/config/plugins/
```

### Activating the Plugins
Once symlinked or copied, simply start a new terminal session or initialize a new Antigravity agent. The session will automatically scan `~/.gemini/config/plugins/`, read `plugin.json` from the root of each plugin folder, and load its associated skills.

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
