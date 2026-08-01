#!/usr/bin/env python3
"""Resolve Saga dependencies through Fleet Core's logical target contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import fleet_commons_shim

TARGET_BACKENDS = frozenset({"inline", "multi-agent-consensus"})
SOURCE_PLUGIN_MAPPINGS = {
    "team-execution": ("plugin", "multi-agent-consensus"),
    "verified-workflows": ("workflow", "antigravity.workflow-contract.v1"),
}


class DependencyResolutionError(ValueError):
    """A Saga dependency is missing, source-only, or incompatible."""


def source_lineage_to_target(name: str) -> tuple[str, str]:
    """Translate an explicitly labeled source lineage name at the migration seam."""

    try:
        return SOURCE_PLUGIN_MAPPINGS[name]
    except KeyError as exc:
        raise DependencyResolutionError(
            "source lineage name has no approved target mapping"
        ) from exc


def resolve_target_plugin(
    name: str,
    *,
    repository_root: Path | str | None = None,
    active_plugin_root: Path | str | None = None,
) -> Path:
    """Resolve one actual Antigravity plugin; source package names are rejected."""

    if name in SOURCE_PLUGIN_MAPPINGS:
        raise DependencyResolutionError(
            "source package name must be translated before target plugin resolution"
        )
    resolver = fleet_commons_shim.load("plugin_resolution")
    try:
        return Path(
            resolver.resolve_plugin_root(
                name,
                repository_root=repository_root,
                active_plugin_root=active_plugin_root,
            )
        )
    except ValueError as exc:
        raise DependencyResolutionError(str(exc)) from exc


def check_readiness(
    *,
    required_plugins: Sequence[str],
    required_backends: Sequence[str],
    repository_root: Path | str | None = None,
    active_plugin_root: Path | str | None = None,
    workflow_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return resolved target dependencies and workflow compatibility evidence."""

    plugins = _unique(required_plugins, "required_plugins")
    backends = _unique(required_backends, "required_backends")
    unsupported = set(backends) - TARGET_BACKENDS
    if unsupported:
        raise DependencyResolutionError("requested workflow backend is unsupported")
    resolved = {
        name: resolve_target_plugin(
            name,
            repository_root=repository_root,
            active_plugin_root=active_plugin_root,
        ).as_posix()
        for name in plugins
    }
    workflow = fleet_commons_shim.load("workflow_compat")
    if workflow_contract is None:
        raise DependencyResolutionError("target workflow contract is required")
    errors = workflow.validate_workflow_contract(workflow_contract)
    if errors:
        raise DependencyResolutionError("target workflow contract is incompatible")
    return {
        "schema": "antigravity.saga-plugin-readiness.v1",
        "plugins": resolved,
        "backends": list(backends),
        "workflow_schema": workflow_contract["schema"],
    }


def _unique(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or any(
        not isinstance(value, str) or not value for value in values
    ):
        raise DependencyResolutionError(f"{field} must contain non-empty strings")
    result = tuple(values)
    if len(result) != len(set(result)):
        raise DependencyResolutionError(f"{field} contains duplicates")
    return result
