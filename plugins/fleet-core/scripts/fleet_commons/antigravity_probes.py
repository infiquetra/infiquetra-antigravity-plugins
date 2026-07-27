"""Closed, bounded Antigravity capability probe registry.

Only definitions in ``PROBE_REGISTRY`` may execute. Catalog data selects a
method and revision; it never supplies argv, paths, parsers, or timeouts.
Controlled behavior probes consume accepted fixture/canary evidence and never
start a model interaction.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

MAX_OUTPUT_BYTES = 64 * 1024
DEFAULT_TIMEOUT_S = 5.0
REQUIRED_RUNTIME_ROOT_ROLES = frozenset(
    {
        "repository",
        "plugin-install",
        "saga-state",
        "conversation-artifacts",
        "brain-artifacts",
    }
)

_VERSION_RE = re.compile(r"(?<![0-9])([0-9]+(?:[.][0-9A-Za-z+-]+)+)")
_FLAG_RE = re.compile(r"(?<![A-Za-z0-9])(--[a-z0-9]+(?:-[a-z0-9]+)*)")


@dataclass(frozen=True)
class CommandResult:
    """Bounded result from a fixed command vector."""

    returncode: int
    stdout: str


class ProbeRunner(Protocol):
    """Execution seam used by registered command probes."""

    safe_for_passive_observation: bool
    safe_for_stateful_observation: bool

    def run(self, argv: Sequence[str], *, timeout_s: float) -> CommandResult: ...


@dataclass(frozen=True)
class ProbeDefinition:
    method: str
    revision: int
    execution_class: str
    evidence_id: str
    argv: tuple[str, ...] | None
    timeout_s: float = DEFAULT_TIMEOUT_S


@dataclass(frozen=True)
class ProbeOutcome:
    state: str
    evidence: tuple[str, ...] = ()
    value: Any = None


class SubprocessProbeRunner:
    """Disabled-by-default subprocess runner.

    A caller must inject a runner that proves its passive-observation boundary.
    The generic process environment cannot provide that proof.
    """

    safe_for_passive_observation = False
    safe_for_stateful_observation = False

    def run(self, argv: Sequence[str], *, timeout_s: float) -> CommandResult:
        del argv, timeout_s
        raise PermissionError(
            "generic subprocess observation cannot prove a no-write, no-network boundary"
        )


def _definition(
    method: str,
    execution_class: str,
    evidence_id: str,
    argv: tuple[str, ...] | None = None,
) -> ProbeDefinition:
    return ProbeDefinition(
        method=method,
        revision=1,
        execution_class=execution_class,
        evidence_id=evidence_id,
        argv=argv,
    )


PROBE_REGISTRY: dict[str, ProbeDefinition] = {
    "agy-version": _definition("agy-version", "passive", "agy-cli-version", ("agy", "--version")),
    "agy-help-flags": _definition(
        "agy-help-flags", "passive", "supported-flags", ("agy", "--help")
    ),
    "antigravity-host-version": _definition(
        "antigravity-host-version", "metadata", "antigravity-host-version"
    ),
    "plugin-links": _definition("plugin-links", "filesystem", "plugin-link-state"),
    "plugin-load": _definition(
        "plugin-load",
        "passive-conditional",
        "plugin-load-state",
        ("agy", "plugin", "list", "--json"),
    ),
    "plugin-validation": _definition(
        "plugin-validation",
        "passive-conditional",
        "plugin-validation-state",
        ("agy", "plugin", "validate", "--json"),
    ),
    "runtime-root-discovery": _definition(
        "runtime-root-discovery", "filesystem", "runtime-root-roles"
    ),
    "controlled-model-selection": _definition(
        "controlled-model-selection", "controlled", "model-selection-proof"
    ),
    "controlled-effort-selection": _definition(
        "controlled-effort-selection", "controlled", "effort-selection-proof"
    ),
    "controlled-agent-execution": _definition(
        "controlled-agent-execution", "controlled", "agent-execution-proof"
    ),
    "controlled-resume": _definition("controlled-resume", "controlled", "resume-proof"),
    "controlled-plan-mode": _definition("controlled-plan-mode", "controlled", "plan-mode-proof"),
    "controlled-sandbox": _definition("controlled-sandbox", "controlled", "sandbox-proof"),
    "controlled-sequential-isolation": _definition(
        "controlled-sequential-isolation", "controlled", "sequential-isolation-proof"
    ),
}

_METHOD_FACT_IDS = {
    "controlled-model-selection": "model-selection",
    "controlled-effort-selection": "effort-selection",
    "controlled-agent-execution": "agent-execution",
    "controlled-resume": "conversation-resume",
    "controlled-plan-mode": "plan-mode",
    "controlled-sandbox": "sandbox-isolation",
    "controlled-sequential-isolation": "sequential-isolation",
}
_OBSERVATION_FACT_IDS = {
    "plugin-links": "plugin-links",
    "plugin-load": "plugin-load",
    "plugin-validation": "plugin-validation",
}


def registry_revisions() -> dict[str, int]:
    return {method: definition.revision for method, definition in PROBE_REGISTRY.items()}


def _bounded_output(result: CommandResult) -> str | None:
    encoded = result.stdout.encode("utf-8", errors="replace")
    if len(encoded) > MAX_OUTPUT_BYTES:
        return None
    return result.stdout


def _run_fixed(definition: ProbeDefinition, runner: ProbeRunner | None) -> CommandResult | None:
    if runner is None or definition.argv is None:
        return None
    try:
        return runner.run(definition.argv, timeout_s=definition.timeout_s)
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired, OSError):
        return None


def _version_outcome(result: CommandResult | None, evidence_id: str) -> ProbeOutcome:
    if result is None:
        return ProbeOutcome("unavailable")
    output = _bounded_output(result)
    if output is None:
        return ProbeOutcome("unknown")
    if result.returncode != 0:
        return ProbeOutcome("failed")
    match = _VERSION_RE.search(output)
    if match is None:
        return ProbeOutcome("unknown")
    return ProbeOutcome("passed", (evidence_id,), match.group(1))


def _flags_outcome(result: CommandResult | None, evidence_id: str) -> ProbeOutcome:
    if result is None:
        return ProbeOutcome("unavailable")
    output = _bounded_output(result)
    if output is None:
        return ProbeOutcome("unknown")
    if result.returncode != 0:
        return ProbeOutcome("failed")
    flags = sorted(set(_FLAG_RE.findall(output)))
    if not flags:
        return ProbeOutcome("unknown")
    return ProbeOutcome("passed", (evidence_id,), flags)


def _json_ok_outcome(result: CommandResult | None, evidence_id: str) -> ProbeOutcome:
    if result is None:
        return ProbeOutcome("unavailable")
    output = _bounded_output(result)
    if output is None:
        return ProbeOutcome("unknown")
    if result.returncode != 0:
        return ProbeOutcome("failed")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return ProbeOutcome("unknown")
    if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
        return ProbeOutcome("unknown")
    return ProbeOutcome(
        "passed" if payload["ok"] else "failed",
        (evidence_id,),
        payload["ok"],
    )


def _host_version_outcome(
    reader: Callable[[], str | None] | None, evidence_id: str
) -> ProbeOutcome:
    if reader is None:
        return ProbeOutcome("unavailable")
    try:
        value = reader()
    except (OSError, PermissionError):
        return ProbeOutcome("unavailable")
    if not isinstance(value, str):
        return ProbeOutcome("unknown")
    match = _VERSION_RE.fullmatch(value)
    if match is None:
        return ProbeOutcome("unknown")
    return ProbeOutcome("passed", (evidence_id,), value)


def _plugin_links_outcome(
    plugin_root: Path | None,
    expected_plugin_roots: Mapping[str, Path] | None,
    evidence_id: str,
) -> ProbeOutcome:
    if plugin_root is None or not expected_plugin_roots:
        return ProbeOutcome("unavailable")
    try:
        plugin_root.resolve(strict=True)
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
        return ProbeOutcome("unavailable")

    link_states: dict[str, bool] = {}
    try:
        for name, expected_root in sorted(expected_plugin_roots.items()):
            link = plugin_root / name
            link_states[name] = link.is_symlink() and link.resolve(
                strict=True
            ) == expected_root.resolve(strict=True)
    except (FileNotFoundError, PermissionError, OSError):
        return ProbeOutcome("failed", (evidence_id,), False)
    all_resolve = bool(link_states) and all(link_states.values())
    return ProbeOutcome(
        "passed" if all_resolve else "failed",
        (evidence_id,),
        all_resolve,
    )


def _runtime_roots_outcome(
    runtime_roots: Sequence[str] | None,
    evidence_id: str,
) -> ProbeOutcome:
    if runtime_roots is None:
        return ProbeOutcome("unavailable")
    roots = sorted(set(runtime_roots))
    if not roots:
        return ProbeOutcome("unknown")
    if not REQUIRED_RUNTIME_ROOT_ROLES.issubset(roots):
        return ProbeOutcome("unknown", value=roots)
    return ProbeOutcome("passed", (evidence_id,), roots)


def _controlled_outcome(
    method: str,
    evidence_id: str,
    controlled_evidence: Mapping[str, Mapping[str, Any]],
) -> ProbeOutcome:
    evidence = controlled_evidence.get(method)
    if evidence is None:
        return ProbeOutcome("unavailable")
    if set(evidence) != {"requested", "observed"}:
        return ProbeOutcome("unknown")
    requested = evidence.get("requested")
    observed = evidence.get("observed")
    if requested is None or observed is None:
        return ProbeOutcome("unknown", value={"requested": requested, "observed": observed})
    if method in {"controlled-model-selection", "controlled-effort-selection"}:
        valid_types = isinstance(requested, str) and isinstance(observed, str)
    else:
        valid_types = isinstance(requested, bool) and isinstance(observed, bool)
    if not valid_types:
        return ProbeOutcome("unknown", value={"requested": requested, "observed": observed})
    if method not in {"controlled-model-selection", "controlled-effort-selection"} and (
        requested is not True
    ):
        return ProbeOutcome("unknown")
    state = "passed" if requested == observed else "failed"
    return ProbeOutcome(
        state,
        (evidence_id,),
        {"requested": requested, "observed": observed},
    )


def execute_probe(
    method: str,
    *,
    observe_host: bool,
    runner: ProbeRunner | None = None,
    host_version_reader: Callable[[], str | None] | None = None,
    plugin_root: Path | None = None,
    expected_plugin_roots: Mapping[str, Path] | None = None,
    runtime_roots: Sequence[str] | None = None,
    controlled_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> ProbeOutcome:
    """Execute one immutable registered method or fail closed."""

    try:
        definition = PROBE_REGISTRY[method]
    except KeyError as exc:
        raise ValueError(f"unknown registered probe method {method!r}") from exc
    fixtures = controlled_evidence or {}

    if definition.execution_class == "controlled":
        return _controlled_outcome(method, definition.evidence_id, fixtures)
    if not observe_host:
        return ProbeOutcome("unavailable")
    if definition.execution_class == "metadata":
        return _host_version_outcome(host_version_reader, definition.evidence_id)
    if definition.execution_class == "filesystem":
        if method == "plugin-links":
            return _plugin_links_outcome(
                plugin_root,
                expected_plugin_roots,
                definition.evidence_id,
            )
        return _runtime_roots_outcome(runtime_roots, definition.evidence_id)
    if runner is None or not getattr(runner, "safe_for_passive_observation", False):
        return ProbeOutcome("unavailable")
    if definition.execution_class == "passive-conditional" and (
        not getattr(runner, "safe_for_stateful_observation", False)
    ):
        return ProbeOutcome("unavailable")

    result = _run_fixed(definition, runner)
    if method == "agy-version":
        return _version_outcome(result, definition.evidence_id)
    if method == "agy-help-flags":
        return _flags_outcome(result, definition.evidence_id)
    return _json_ok_outcome(result, definition.evidence_id)


def _catalog_digest(catalog: Mapping[str, Any]) -> str:
    encoded = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def probe_catalog(
    catalog: Mapping[str, Any],
    *,
    observe_host: bool = False,
    runner: ProbeRunner | None = None,
    host_version_reader: Callable[[], str | None] | None = None,
    plugin_root: Path | None = None,
    expected_plugin_roots: Mapping[str, Path] | None = None,
    runtime_roots: Sequence[str] | None = None,
    controlled_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate catalog rows into a strict promotable receipt."""

    results: list[dict[str, Any]] = []
    agy_cli_version: str | None = None
    antigravity_host_version: str | None = None
    supported_flags: list[str] = []
    requested_facts: dict[str, Any] = {}
    observed_facts: dict[str, Any] = {}

    for row in catalog["capabilities"]:
        method = row["probe_method"]
        outcome = execute_probe(
            method,
            observe_host=observe_host,
            runner=runner,
            host_version_reader=host_version_reader,
            plugin_root=plugin_root,
            expected_plugin_roots=expected_plugin_roots,
            runtime_roots=runtime_roots,
            controlled_evidence=controlled_evidence,
        )
        results.append(
            {
                "id": row["id"],
                "probe_revision": row["probe_revision"],
                "state": outcome.state,
                "evidence": list(outcome.evidence),
            }
        )
        if method == "agy-version" and isinstance(outcome.value, str):
            agy_cli_version = outcome.value
        elif method == "antigravity-host-version" and isinstance(outcome.value, str):
            antigravity_host_version = outcome.value
        elif method == "agy-help-flags" and isinstance(outcome.value, list):
            supported_flags = list(outcome.value)
        elif method == "runtime-root-discovery" and isinstance(outcome.value, list):
            runtime_roots = list(outcome.value)
        elif method in _OBSERVATION_FACT_IDS and isinstance(outcome.value, bool):
            fact_id = _OBSERVATION_FACT_IDS[method]
            requested_facts[fact_id] = True
            observed_facts[fact_id] = outcome.value
        elif method in _METHOD_FACT_IDS and isinstance(outcome.value, Mapping):
            fact_id = _METHOD_FACT_IDS[method]
            requested_facts[fact_id] = outcome.value.get("requested")
            observed_facts[fact_id] = outcome.value.get("observed")

    roots = sorted(set(runtime_roots or []))
    return {
        "schema": "antigravity.capabilities.v1",
        "catalog_digest": _catalog_digest(catalog),
        "agy_cli_version": agy_cli_version,
        "antigravity_host_version": antigravity_host_version,
        "supported_flags": supported_flags,
        "runtime_roots": roots,
        "requested_facts": requested_facts,
        "observed_facts": observed_facts,
        "results": results,
    }
