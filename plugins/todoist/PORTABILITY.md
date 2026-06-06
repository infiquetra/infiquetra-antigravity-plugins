# Portability Ledger: Todoist Plugin

## Lineage
This plugin is a native Antigravity port of the `todoist-manager` plugin originally developed in the `infiquetra-claude-plugins` repository.

## Divergence
- **State Management:** The legacy `.claude/` state synchronization was removed entirely in favor of an ephemeral read-through architecture directly to the Todoist API.
- **Authentication:** Hardcoded environment variables were replaced with native MCP environment injection configuration.
- **Orchestration:** Monolithic markdown personas were replaced with flat executable python scripts and native MCP `plugin.json` schemas.
- **Terminology:** All references to "Claude", "Anthropic", and "boltArtifact" were purged to comply with Antigravity conventions.

## Constraints
Any updates to this plugin must adhere to the `tests/test_todoist_portability.py` structural checks to prevent accidental legacy concept drift.
