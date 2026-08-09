# Develop the Antigravity adapter

Keep this plugin a standard-library transport. Team Mimir owns classifier
policy, and Hermes owns dialogue, health, routing, credentials, and mutation.

## Local checks

From the repository root:

```bash
uv sync --locked --extra dev
uv run pytest -q \
  tests/test_hermes_profile_evolution.py \
  tests/test_hermes_profile_evolution_docs.py \
  tests/test_validate_plugins.py
uv run ruff check \
  plugins/hermes-profile-evolution \
  tests/test_hermes_profile_evolution.py \
  tests/test_hermes_profile_evolution_docs.py
uv run mypy plugins/hermes-profile-evolution tests/test_hermes_profile_evolution.py
```

Exercise documented inputs with temporary Team Mimir checkouts and fake Hermes
processes. Tests must not need live credentials or contact a real target.

## Compatibility and release

Pinned files in `conformance/` come from released Team Mimir and Hermes producer
sources. Update them with provenance when a producer schema changes; do not
invent fields or retain an implicit fallback.

For a real release, update `plugin.json` and `CHANGELOG.md`, run repository
validation and tests, then install through `tools/install-plugin.sh`. Restart
Antigravity and verify the installed manifest. Do not edit installed plugin
files as maintained source.

See [usage](usage.md), [architecture](architecture.md), and
[troubleshooting](troubleshooting.md).
