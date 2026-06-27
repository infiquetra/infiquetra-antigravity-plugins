#!/usr/bin/env python3
"""Read-only Antigravity plugin doctor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SEMVER = re.compile(r"^\d+\.\d+\.\d+([-.][A-Za-z0-9.]+)?$")
STALE_PHRASES = ("Claude Plugin Manifest", ".claude-plugin", "Claude Code plugin")
CURRENT_SPEC_FILES = (
    "README.md",
    "ANTIGRAVITY.md",
    "docs/PLUGIN_SPEC.md",
    "docs/MARKETPLACE_GUIDE.md",
    "marketplace/validator/schema.json",
)


@dataclass
class PluginStatus:
    name: str
    path: str
    version: str | None = None
    skills: int = 0
    commands: int = 0
    agents: int = 0
    tools: int = 0
    config_files: int = 0
    installed: bool = False
    install_state: str = "missing"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


@dataclass
class DoctorResult:
    ok: bool
    plugins: list[PluginStatus]
    warnings: list[str]
    errors: list[str]
    next_actions: list[str]


def default_install_dir() -> Path:
    return Path.home() / ".gemini" / "config" / "plugins"


def run_doctor(repo_root: Path, install_dir: Path | None = None, strict_install: bool = False) -> DoctorResult:
    repo_root = repo_root.resolve()
    plugins_root = repo_root / "plugins"
    install_root = install_dir if install_dir is not None else default_install_dir()
    statuses: list[PluginStatus] = []
    warnings: list[str] = []
    errors: list[str] = []
    next_actions: list[str] = []

    if not plugins_root.exists():
        errors.append("plugins/ directory is missing")
        return DoctorResult(False, statuses, warnings, errors, ["restore plugins/ directory"])

    for manifest_path in sorted(plugins_root.glob("*/plugin.json")):
        status = inspect_plugin(manifest_path, install_root, strict_install)
        status.path = manifest_path.parent.relative_to(repo_root).as_posix()
        statuses.append(status)
        errors.extend(f"{status.name}: {msg}" for msg in status.errors)
        warnings.extend(f"{status.name}: {msg}" for msg in status.warnings)
        next_actions.extend(f"{status.name}: {msg}" for msg in status.next_actions)

    if not statuses:
        errors.append("no plugin manifests found under plugins/*/plugin.json")

    stale_warnings = find_stale_contracts(repo_root)
    warnings.extend(stale_warnings)
    next_actions.extend("repair stale Claude-shaped current spec text" for _ in stale_warnings)

    return DoctorResult(not errors, statuses, warnings, errors, dedupe(next_actions))


def inspect_plugin(manifest_path: Path, install_root: Path, strict_install: bool) -> PluginStatus:
    plugin_dir = manifest_path.parent
    status = PluginStatus(name=plugin_dir.name, path=plugin_dir.as_posix())

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        status.errors.append(f"invalid JSON in plugin.json: {exc}")
        status.next_actions.append("repair plugin.json")
        return status

    if not isinstance(manifest, dict):
        status.errors.append("plugin.json must contain a JSON object")
        status.next_actions.append("repair plugin.json")
        return status

    status.name = str(manifest.get("name") or plugin_dir.name)
    status.version = manifest.get("version") if isinstance(manifest.get("version"), str) else None
    validate_manifest_basics(manifest, plugin_dir, status)
    count_surfaces(plugin_dir, manifest, status)
    inspect_install(plugin_dir, install_root, status, strict_install)
    return status


def validate_manifest_basics(manifest: dict[str, Any], plugin_dir: Path, status: PluginStatus) -> None:
    for field_name in ("name", "version", "description"):
        value = manifest.get(field_name)
        if not isinstance(value, str) or not value.strip():
            status.errors.append(f"missing or invalid manifest field: {field_name}")

    if isinstance(manifest.get("name"), str) and manifest["name"] != plugin_dir.name:
        status.errors.append(f"manifest name {manifest['name']!r} does not match directory {plugin_dir.name!r}")

    version = manifest.get("version")
    if isinstance(version, str) and not SEMVER.match(version):
        status.errors.append(f"manifest version {version!r} is not semver-like")

    if status.errors:
        status.next_actions.append("repair plugin manifest")


def count_surfaces(plugin_dir: Path, manifest: dict[str, Any], status: PluginStatus) -> None:
    status.skills = len(list((plugin_dir / "skills").glob("*/SKILL.md")))
    status.commands = len(list((plugin_dir / "commands").glob("*.md")))
    agent_files = list((plugin_dir / "agents").glob("*.md"))
    status.agents = len(agent_files)
    status.tools = len(manifest.get("tools", [])) if isinstance(manifest.get("tools"), list) else 0
    status.config_files = len([p for p in (plugin_dir / "config").glob("*") if p.is_file()])

    for agent_file in agent_files:
        if not agent_file.read_text().strip():
            status.warnings.append(f"inert empty agent file: {agent_file.relative_to(plugin_dir)}")
            status.next_actions.append("fill or remove empty agent file")

    if not any((status.skills, status.commands, status.agents, status.tools, status.config_files)):
        status.warnings.append("no Antigravity-facing skills, commands, agents, tools, or config files found")
        status.next_actions.append("add a surface or confirm plugin is intentionally inert")


def inspect_install(plugin_dir: Path, install_root: Path, status: PluginStatus, strict_install: bool) -> None:
    install_path = install_root / plugin_dir.name
    if not install_root.exists():
        add_install_issue(status, f"install directory not found: {install_root}", strict_install)
        return
    if not install_path.exists():
        add_install_issue(status, "plugin not installed or not loaded", strict_install)
        return

    status.installed = True
    if install_path.is_symlink():
        target = install_path.resolve()
        if target != plugin_dir.resolve():
            add_install_issue(status, f"symlink points at {target}, expected {plugin_dir.resolve()}", strict_install)
        else:
            status.install_state = "linked"
    elif install_path.is_dir():
        status.install_state = "copied"
        status.warnings.append("plugin install is a copy, not a symlink")
        status.next_actions.append("replace copied install with symlink or reinstall")
    else:
        add_install_issue(status, "install path exists but is not a directory or symlink", strict_install)


def add_install_issue(status: PluginStatus, message: str, strict_install: bool) -> None:
    if strict_install:
        status.errors.append(message)
    else:
        status.warnings.append(message)
    status.next_actions.append("install/link plugin or restart Antigravity")


def find_stale_contracts(repo_root: Path) -> list[str]:
    warnings: list[str] = []
    for rel_path in CURRENT_SPEC_FILES:
        path = repo_root / rel_path
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        for phrase in STALE_PHRASES:
            if phrase in text:
                warnings.append(f"{rel_path}: current spec text contains stale {phrase!r}")
                break
    return warnings


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def print_human(result: DoctorResult) -> None:
    print("Antigravity plugin doctor")
    print(f"status: {'ok' if result.ok else 'failed'}")
    plugin_names = {plugin.name for plugin in result.plugins}
    for plugin in result.plugins:
        print(
            f"- {plugin.name}: skills={plugin.skills} commands={plugin.commands} "
            f"agents={plugin.agents} tools={plugin.tools} config={plugin.config_files} "
            f"install={plugin.install_state}"
        )
        for error in plugin.errors:
            print(f"  error: {error}")
        for warning in plugin.warnings:
            print(f"  warning: {warning}")
    for warning in result.warnings:
        if warning.split(":", 1)[0] not in plugin_names:
            print(f"warning: {warning}")
    if result.next_actions:
        print("next actions:")
        for action in result.next_actions:
            print(f"- {action}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Antigravity plugin load/config truth")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--install-dir", type=Path, default=None)
    parser.add_argument("--strict-install", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_doctor(args.repo_root, args.install_dir, args.strict_install)
    if args.json_output:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
