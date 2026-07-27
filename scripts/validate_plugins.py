#!/usr/bin/env python3
"""Read-only Antigravity plugin doctor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]
FLEET_CORE_SCRIPTS = REPO_ROOT / "plugins" / "fleet-core" / "scripts"
if str(FLEET_CORE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FLEET_CORE_SCRIPTS))

import fleet_commons_shim  # noqa: E402

SEMVER = re.compile(r"^\d+\.\d+\.\d+([-.][A-Za-z0-9.]+)?$")
STALE_PHRASES = ("Claude Plugin Manifest", ".claude-plugin", "Claude Code plugin")
CURRENT_SPEC_FILES = (
    "README.md",
    "ANTIGRAVITY.md",
    "docs/PLUGIN_SPEC.md",
    "docs/MARKETPLACE_GUIDE.md",
    "marketplace/validator/schema.json",
)
CATALOG_PATH = Path("plugins/fleet-core/references/antigravity-capability-probes.yaml")
HOST_CONTRACT_SELECTOR_PATH = Path(
    "plugins/fleet-core/references/antigravity-host-contract-surfaces.json"
)


class ProbeRunner(Protocol):
    safe_for_passive_observation: bool
    safe_for_stateful_observation: bool

    def run(self, argv: list[str] | tuple[str, ...], *, timeout_s: float) -> Any: ...


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
class CatalogStatus:
    status: str = "not-applicable"
    schema: str | None = None
    revision: int | None = None
    digest: str | None = None
    capabilities: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class CapabilityStatus:
    status: str = "not-applicable"
    profile: str = "repository-validation"
    source: str = "none"
    evaluation: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class PrivacyStatus:
    status: str = "not-applicable"
    promotable: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class HostContractStatus:
    status: str = "not-applicable"
    selector_digest: str | None = None
    finding_count: int = 0
    unresolved_count: int = 0
    findings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DoctorResult:
    ok: bool
    plugins: list[PluginStatus]
    warnings: list[str]
    errors: list[str]
    next_actions: list[str]
    catalog: CatalogStatus = field(default_factory=CatalogStatus)
    capability: CapabilityStatus = field(default_factory=CapabilityStatus)
    receipt_privacy: PrivacyStatus = field(default_factory=PrivacyStatus)
    host_contract: HostContractStatus = field(default_factory=HostContractStatus)


def default_install_dir() -> Path:
    return Path.home() / ".gemini" / "config" / "plugins"


def _contract_modules() -> tuple[ModuleType, ModuleType, ModuleType]:
    return (
        fleet_commons_shim.load("antigravity_capabilities"),
        fleet_commons_shim.load("antigravity_probes"),
        fleet_commons_shim.load("host_contract_lint"),
    )


def _contract_is_applicable(repo_root: Path) -> bool:
    return (repo_root / "plugins" / "fleet-core" / "plugin.json").is_file()


def _known_profiles(catalog: dict[str, Any]) -> set[str]:
    profiles = {"repository-validation"}
    for row in catalog["capabilities"]:
        profiles.update(row["required_for"])
        fallback = row.get("fallback")
        if isinstance(fallback, dict):
            profiles.update(fallback["for_consumers"])
    return profiles


def evaluate_host_contract(
    repo_root: Path,
    install_root: Path,
    *,
    capability_profile: str,
    capability_receipt: Path | None,
    observe_host: bool,
    runner: ProbeRunner | None,
    host_version_reader: Any,
    catalog_override: dict[str, Any] | None,
    receipt_override: dict[str, Any] | None,
    selector_override: dict[str, Any] | None,
) -> tuple[CatalogStatus, CapabilityStatus, PrivacyStatus, HostContractStatus]:
    catalog_status = CatalogStatus()
    capability_status = CapabilityStatus(profile=capability_profile)
    privacy_status = PrivacyStatus()
    host_status = HostContractStatus()
    if not _contract_is_applicable(repo_root):
        return catalog_status, capability_status, privacy_status, host_status

    capabilities, probes, host_lint = _contract_modules()
    catalog_path = repo_root / CATALOG_PATH
    try:
        catalog = (
            dict(catalog_override)
            if catalog_override is not None
            else capabilities.load_catalog(catalog_path)
        )
        catalog_errors = capabilities.validate_catalog(catalog)
        if catalog_errors:
            raise ValueError("capability catalog failed its closed schema")
    except (OSError, ValueError) as exc:
        catalog_status.status = "failed"
        catalog_status.errors.append(str(exc))
        capability_status.status = "blocked"
        capability_status.errors.append("capability evaluation requires a valid catalog")
        privacy_status.status = "blocked"
        privacy_status.errors.append("receipt privacy requires a valid catalog")
        host_status.status = "blocked"
        host_status.errors.append("host-contract lint requires a valid capability catalog")
        return catalog_status, capability_status, privacy_status, host_status

    catalog_status = CatalogStatus(
        status="passed",
        schema=catalog["catalog_schema"],
        revision=catalog["catalog_revision"],
        digest=capabilities.canonical_catalog_digest(catalog),
        capabilities=len(catalog["capabilities"]),
    )
    if capability_profile not in _known_profiles(catalog):
        capability_status.status = "blocked"
        capability_status.errors.append("unknown capability profile")
        privacy_status.status = "blocked"
        privacy_status.errors.append("no receipt was accepted")
        host_status.status = "blocked"
        host_status.errors.append("host-contract lint requires a known capability profile")
        return catalog_status, capability_status, privacy_status, host_status

    try:
        if receipt_override is not None:
            receipt = dict(receipt_override)
            source = "injected"
        elif capability_receipt is not None:
            receipt = capabilities.load_receipt(capability_receipt, catalog)
            source = "supplied"
        else:
            effective_runner = runner
            if observe_host and effective_runner is None:
                effective_runner = probes.SubprocessProbeRunner()
            expected_plugin_roots = {
                manifest.parent.name: manifest.parent
                for manifest in sorted((repo_root / "plugins").glob("*/plugin.json"))
            }
            runtime_roots = ["repository"]
            if install_root.is_dir():
                runtime_roots.append("plugin-install")
            if (repo_root / ".gemini" / "saga").is_dir():
                runtime_roots.append("saga-state")
            receipt = probes.probe_catalog(
                catalog,
                observe_host=observe_host,
                runner=effective_runner,
                host_version_reader=host_version_reader,
                plugin_root=install_root if observe_host else None,
                expected_plugin_roots=expected_plugin_roots if observe_host else None,
                runtime_roots=runtime_roots if observe_host else None,
            )
            source = "observed" if observe_host else "deterministic"
        receipt_errors = capabilities.validate_receipt(receipt, catalog)
        if receipt_errors:
            raise ValueError("receipt failed the strict promotable schema")
    except (OSError, ValueError) as exc:
        capability_status.status = "blocked"
        capability_status.source = (
            "supplied"
            if capability_receipt is not None
            else "injected"
            if receipt_override is not None
            else "observed"
            if observe_host
            else "deterministic"
        )
        capability_status.errors.append(str(exc))
        privacy_status.status = "failed"
        privacy_status.errors.append(
            "capability receipt failed strict schema and privacy validation"
        )
        host_status.status = "blocked"
        host_status.errors.append("host-contract lint requires a valid capability receipt")
        return catalog_status, capability_status, privacy_status, host_status

    evaluation = capabilities.evaluate_for_consumer(receipt, catalog, capability_profile)
    capability_status = CapabilityStatus(
        status=evaluation["state"],
        profile=capability_profile,
        source=source,
        evaluation=evaluation,
        receipt=receipt,
    )
    privacy_status = PrivacyStatus(status="passed", promotable=True)

    try:
        if selector_override is None:
            selector = host_lint.load_selector(repo_root / HOST_CONTRACT_SELECTOR_PATH, repo_root)
        else:
            selector = dict(selector_override)
            selector_errors = host_lint.validate_selector(selector, repo_root)
            if selector_errors:
                raise ValueError("host-contract selector failed its closed schema")
        capability_states = {result["id"]: result["state"] for result in receipt["results"]}
        lint_receipt = host_lint.scan_repository(
            repo_root,
            selector,
            known_capabilities=set(capability_states),
            capability_states=capability_states,
        )
        host_status = HostContractStatus(
            status="passed" if lint_receipt["unresolved_count"] == 0 else "failed",
            selector_digest=lint_receipt["selector_digest"],
            finding_count=len(lint_receipt["findings"]),
            unresolved_count=lint_receipt["unresolved_count"],
            findings=lint_receipt["findings"],
        )
        if host_status.unresolved_count:
            host_status.errors.append("active host-contract violations remain unresolved")
    except host_lint.HostContractError as exc:
        host_status.status = "failed"
        host_status.errors.append(str(exc))
    except (OSError, ValueError):
        host_status.status = "failed"
        host_status.errors.append("host-contract evaluation failed")

    return catalog_status, capability_status, privacy_status, host_status


def run_doctor(
    repo_root: Path,
    install_dir: Path | None = None,
    strict_install: bool = False,
    *,
    capability_profile: str = "repository-validation",
    capability_receipt: Path | None = None,
    observe_host: bool = False,
    runner: ProbeRunner | None = None,
    host_version_reader: Any = None,
    catalog: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    selector: dict[str, Any] | None = None,
) -> DoctorResult:
    repo_root = repo_root.resolve()
    plugins_root = repo_root / "plugins"
    install_root = install_dir if install_dir is not None else default_install_dir()
    statuses: list[PluginStatus] = []
    warnings: list[str] = []
    errors: list[str] = []
    next_actions: list[str] = []
    catalog_status = CatalogStatus()
    capability_status = CapabilityStatus(profile=capability_profile)
    privacy_status = PrivacyStatus()
    host_status = HostContractStatus()

    if not plugins_root.exists():
        errors.append("plugins/ directory is missing")
        return DoctorResult(
            False,
            statuses,
            warnings,
            errors,
            ["restore plugins/ directory"],
            catalog_status,
            capability_status,
            privacy_status,
            host_status,
        )

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

    catalog_status, capability_status, privacy_status, host_status = evaluate_host_contract(
        repo_root,
        install_root,
        capability_profile=capability_profile,
        capability_receipt=capability_receipt,
        observe_host=observe_host,
        runner=runner,
        host_version_reader=host_version_reader,
        catalog_override=catalog,
        receipt_override=receipt,
        selector_override=selector,
    )
    errors.extend(f"catalog: {item}" for item in catalog_status.errors)
    errors.extend(f"capability: {item}" for item in capability_status.errors)
    errors.extend(f"receipt privacy: {item}" for item in privacy_status.errors)
    errors.extend(f"host contract: {item}" for item in host_status.errors)
    if capability_status.status == "blocked" and not capability_status.errors:
        errors.append("capability: selected profile has required non-passing capabilities")
        next_actions.append("supply a valid passing capability receipt for the selected profile")
    if host_status.unresolved_count:
        next_actions.append("remediate or narrowly classify unresolved host-contract findings")

    return DoctorResult(
        not errors,
        statuses,
        warnings,
        errors,
        dedupe(next_actions),
        catalog_status,
        capability_status,
        privacy_status,
        host_status,
    )


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


def validate_manifest_basics(
    manifest: dict[str, Any], plugin_dir: Path, status: PluginStatus
) -> None:
    for field_name in ("name", "version", "description"):
        value = manifest.get(field_name)
        if not isinstance(value, str) or not value.strip():
            status.errors.append(f"missing or invalid manifest field: {field_name}")

    if isinstance(manifest.get("name"), str) and manifest["name"] != plugin_dir.name:
        status.errors.append(
            f"manifest name {manifest['name']!r} does not match directory {plugin_dir.name!r}"
        )

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
        status.warnings.append(
            "no Antigravity-facing skills, commands, agents, tools, or config files found"
        )
        status.next_actions.append("add a surface or confirm plugin is intentionally inert")


def inspect_install(
    plugin_dir: Path, install_root: Path, status: PluginStatus, strict_install: bool
) -> None:
    install_path = install_root / plugin_dir.name
    if not install_root.exists():
        add_install_issue(status, f"install directory not found: {install_root}", strict_install)
        return
    if not install_path.exists():
        add_install_issue(status, "plugin not installed or not loaded", strict_install)
        status.next_actions.append("install/link plugin or restart Antigravity")
        return

    status.installed = True
    if install_path.is_symlink():
        target = install_path.resolve()
        if target != plugin_dir.resolve():
            add_install_issue(
                status,
                f"symlink points at {target}, expected {plugin_dir.resolve()}",
                strict_install,
            )
        else:
            status.install_state = "linked"
    elif install_path.is_dir():
        status.install_state = "copied"
        status.warnings.append("plugin install is a copy, not a symlink")
        status.next_actions.append("replace copied install with symlink or reinstall")
    else:
        add_install_issue(
            status, "install path exists but is not a directory or symlink", strict_install
        )


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
    print(
        "catalog: "
        f"{result.catalog.status}"
        + (
            f" schema={result.catalog.schema} revision={result.catalog.revision} "
            f"capabilities={result.catalog.capabilities}"
            if result.catalog.status != "not-applicable"
            else ""
        )
    )
    print(
        f"capability: {result.capability.status} "
        f"profile={result.capability.profile} source={result.capability.source}"
    )
    if result.capability.evaluation is not None:
        blocking = result.capability.evaluation["blocking_capabilities"]
        degraded = result.capability.evaluation["degraded_capabilities"]
        if blocking:
            print(f"  blocking: {', '.join(blocking)}")
        if degraded:
            print(f"  degraded: {', '.join(degraded)}")
        for capability, fallback in result.capability.evaluation["fallbacks"].items():
            print(f"  fallback: {capability} -> {fallback}")
    print(
        f"receipt privacy: {result.receipt_privacy.status} "
        f"promotable={'yes' if result.receipt_privacy.promotable else 'no'}"
    )
    print(
        f"host contract: {result.host_contract.status} "
        f"findings={result.host_contract.finding_count} "
        f"unresolved={result.host_contract.unresolved_count}"
    )
    for finding in result.host_contract.findings:
        if finding["unresolved"]:
            print(
                f"  violation: path-sha256={finding['path_sha256']} line={finding['line']} "
                f"{finding['rule']} remediation={finding['remediation']}"
            )
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
    parser.add_argument("--capability-profile", default="repository-validation")
    parser.add_argument("--capability-receipt", type=Path)
    parser.add_argument("--observe-host", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_doctor(
        args.repo_root,
        args.install_dir,
        args.strict_install,
        capability_profile=args.capability_profile,
        capability_receipt=args.capability_receipt,
        observe_host=args.observe_host,
    )
    if args.json_output:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
