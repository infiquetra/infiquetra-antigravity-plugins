# Hermes profile evolution

This Antigravity plugin routes proposed Team Mimir profile-behavior changes to the named profile's
Hermes dialogue. It does not edit profile behavior, grant target authority, or process requests as
an offline queue.

The adapter receives an explicit Team Mimir repository root and calls that checkout's real path
classifier. Its own executable and conformance files remain under the Antigravity plugin root.
Ordinary repository work continues without contacting Hermes. A profile-owned or mixed request
with exactly one named profile is encoded as the canonical version-1 proposal envelope and sent on
standard input to `hermes profile-request`. The target profile remains free to decline, defer, ask
questions, or take no action.

## Native surfaces

- `/hermes-profile-evolution` is the Antigravity command front door.
- The `hermes-profile-evolution` skill explains routing and dialogue continuation.
- `scripts/profile_request.py` is a standard-library-only transport adapter.

The plugin has no hook. Antigravity has no proven native hook contract in this repository, so the
plugin does not claim to intercept direct edits. It also has no classifier copy, credentials,
routing configuration, mutation code, background processor, or Saga semantic-port ledger.

## Requirements

Run the command from a Team Mimir checkout that contains `scripts/classify_profile_change.py`, or
set `TEAM_MIMIR_ROOT` to that checkout. Resolve the adapter through
`${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/hermes-profile-evolution}`; do not expect plugin
source inside Team Mimir. The canonical `hermes profile-request` command, route, credentials, and
service must already be available outside this plugin. Failure or contract drift stops the request
without printing its contents.

## Validation

```bash
uv run pytest tests/test_hermes_profile_evolution.py tests/test_validate_plugins.py
uv run python scripts/validate_plugins.py
```

## Operator guide

- [Install and use the plugin](docs/usage.md)
- [Understand the trust boundaries](docs/architecture.md)
- [Develop and release the adapter](docs/development.md)
- [Troubleshoot requests](docs/troubleshooting.md)

The [Team Mimir operator hub](https://github.com/infiquetra/team-mimir/tree/main/docs/team/profile-evolution)
covers deployment and activation. The
[Hermes producer documentation](https://github.com/infiquetra/infiquetra-hermes-plugins/tree/main/docs/profile-evolution)
owns dialogue and compatibility semantics.
