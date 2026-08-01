"""Logical target-plugin resolution without machine-specific install assumptions."""

from __future__ import annotations

import re
from pathlib import Path

TARGET_PLUGINS = frozenset(
    {"fleet-core", "mission-control", "multi-agent-consensus", "saga"}
)
SOURCE_PLUGIN_NAMES = frozenset({"team-execution", "verified-workflows"})
_PLUGIN_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class PluginResolutionError(ValueError):
    """A logical target plugin could not be resolved safely."""


def validate_plugin_name(plugin_name: str) -> None:
    if not _PLUGIN_RE.fullmatch(plugin_name):
        raise PluginResolutionError("plugin name must be a logical lowercase identifier")
    if plugin_name in SOURCE_PLUGIN_NAMES:
        raise PluginResolutionError("source package names are not target plugin identities")
    if plugin_name not in TARGET_PLUGINS:
        raise PluginResolutionError("plugin is outside the approved target portfolio")


def resolve_plugin_root(
    plugin_name: str,
    *,
    repository_root: Path | str | None = None,
    active_plugin_root: Path | str | None = None,
) -> Path:
    """Resolve a target plugin from a repository or active plugin sibling set."""

    validate_plugin_name(plugin_name)
    candidates: list[Path] = []
    if repository_root is not None:
        root = Path(repository_root)
        if root.is_absolute():
            candidates.append(root / "plugins" / plugin_name)
    if active_plugin_root is not None:
        active = Path(active_plugin_root)
        if active.is_absolute():
            candidates.append(active.parent / plugin_name)
    for candidate in candidates:
        if (
            candidate.is_dir()
            and (candidate / "plugin.json").is_file()
        ):
            return candidate.resolve()
    raise PluginResolutionError(f"could not resolve logical plugin {plugin_name!r}")
