#!/usr/bin/env python3
"""Run and verify one bounded live AGY Saga reference lifecycle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "scripts"
FLEET_SCRIPTS = REPO_ROOT / "plugins" / "fleet-core" / "scripts"
SAGA_SCRIPTS = REPO_ROOT / "plugins" / "saga" / "scripts"
for script_root in (SCRIPT_ROOT, FLEET_SCRIPTS, SAGA_SCRIPTS):
    if str(script_root) not in sys.path:
        sys.path.insert(0, str(script_root))

import artifact_promotion  # noqa: E402
import fleet_commons_shim  # noqa: E402
import saga_conformance  # noqa: E402

CAPABILITIES = fleet_commons_shim.load("antigravity_capabilities")

CONFIG_SCHEMA = "saga.live-canary-config.v1"
RUN_SCHEMA = "saga.live-canary-run.v1"
CAPABILITY_SCHEMA = "antigravity.capabilities.v1"
MINIMUM_AGY_VERSION = (1, 1, 9)
FIXTURE_CONFIG = (
    REPO_ROOT
    / "plugins"
    / "saga"
    / "tests"
    / "fixtures"
    / "conformance"
    / "reference-lifecycle"
    / "live-canary.json"
)
LOCAL_ROOT = REPO_ROOT / ".conformance-local" / "live-canary"
LATEST_PREFLIGHT = LOCAL_ROOT / "preflight" / "latest.json"
HOST_INFO = Path("/Applications/Antigravity.app/Contents/Info.plist")
CATALOG_PATH = (
    REPO_ROOT / "plugins" / "fleet-core" / "references" / "antigravity-capability-probes.yaml"
)

PHASES = (
    "ideate",
    "brainstorm",
    "impl-spec",
    "plan",
    "doc-review",
    "resume",
    "work",
    "code-review",
    "qa",
    "retro",
    "handoff",
)
ARTIFACT_GROUPS = {
    "ideate": "docs/ideation",
    "brainstorm": "docs/brainstorms",
    "impl-spec": "docs/specs",
    "plan": "docs/plans",
    "doc-review": "docs/reviews",
    "code-review": "docs/code-reviews",
    "qa": "docs/qa",
    "retro": "docs/retros",
    "handoff": "docs/handoffs",
}
REQUIRED_RECEIPT_GROUPS = (
    "deliberation",
    "promotion",
    "transition",
    "handoff",
)
PRIVATE_KEYS = frozenset(
    {
        "transcript",
        "history",
        "prompt",
        "brain",
        "username",
        "hostname",
        "credential",
        "token",
        "environment",
        "stdout",
        "stderr",
    }
)
FORBIDDEN_COMMANDS = (
    re.compile(r"(?:^|[;&|]\s*)git\s+push(?:\s|$)", re.IGNORECASE),
    re.compile(r"(?:^|[;&|]\s*)git\s+merge(?:\s|$)", re.IGNORECASE),
    re.compile(r"(?:^|[;&|]\s*)gh\s+(?:pr|issue|project)\s+", re.IGNORECASE),
    re.compile(
        r"(?:^|[;&|]\s*)agy\s+plugin\s+(?:install|uninstall|enable|disable|link)\b", re.IGNORECASE
    ),
    re.compile(
        r"(?:^|[;&|]\s*)(?:terraform\s+apply|cdk\s+deploy|kubectl\s+apply)\b", re.IGNORECASE
    ),
)
FORBIDDEN_TOOL_FRAGMENTS = (
    "create_issue",
    "merge_pull_request",
    "update_project",
    "deploy",
)
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-.].*)?$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_DECISION_REFERENCE = re.compile(
    r"^https://github\.com/infiquetra/infiquetra-antigravity-plugins/"
    r"issues/22#issuecomment-[0-9]+$"
)


class CanaryError(ValueError):
    """The live canary contract or observed evidence failed closed."""


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_file(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return _digest_bytes(encoded)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanaryError(f"{label} is unreadable or invalid") from exc
    if not isinstance(value, dict):
        raise CanaryError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _closed(value: Mapping[str, Any], expected: set[str] | frozenset[str], label: str) -> None:
    if set(value) != set(expected):
        raise CanaryError(f"{label} has unknown or missing fields")


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CanaryError(f"{label} must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise CanaryError(f"{label} must remain repository-relative")
    return path.as_posix()


def _bound_path(root: Path, binding: Mapping[str, Any], label: str) -> Path:
    _closed(binding, {"path", "sha256"}, label)
    relative = _safe_relative(binding["path"], f"{label}.path")
    expected = binding["sha256"]
    if not isinstance(expected, str) or not _DIGEST.fullmatch(expected):
        raise CanaryError(f"{label}.sha256 must be a SHA-256 digest")
    try:
        path = (root / relative).resolve(strict=True)
        path.relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise CanaryError(f"{label} does not identify a contained file") from exc
    if not path.is_file() or _digest_file(path) != expected:
        raise CanaryError(f"{label} digest does not match")
    return path


def load_config(fixture_id: str, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load and validate the one approved live-canary configuration."""

    if fixture_id != "reference-lifecycle":
        raise CanaryError("unknown live-canary fixture")
    config_path = repo_root / FIXTURE_CONFIG.relative_to(REPO_ROOT)
    config = _load_json(config_path, "live-canary config")
    _closed(
        config,
        {
            "schema",
            "fixture_id",
            "fixture_revision",
            "minimum_agy_version",
            "model",
            "effort",
            "resolved_model",
            "agent",
            "sandbox",
            "profile",
            "folder_contract",
            "baseline_manifest",
            "phase_commands",
        },
        "live-canary config",
    )
    if config["schema"] != CONFIG_SCHEMA:
        raise CanaryError("live-canary config schema is unsupported")
    if config["fixture_id"] != fixture_id or config["fixture_revision"] != 1:
        raise CanaryError("live-canary fixture identity is unsupported")
    if config["minimum_agy_version"] != "1.1.9":
        raise CanaryError("live-canary minimum AGY version is unsupported")
    if (
        config["model"] != "gemini-3.1-pro"
        or config["effort"] != "high"
        or config["resolved_model"] != "gemini-3.1-pro-high"
        or config["agent"] != "lifecycle-router"
        or config["sandbox"] is not True
    ):
        raise CanaryError("live-canary operator-approved runtime selection does not match")
    _bound_path(repo_root, cast(Mapping[str, Any], config["profile"]), "profile binding")
    _bound_path(
        repo_root,
        cast(Mapping[str, Any], config["folder_contract"]),
        "folder contract binding",
    )
    baseline = _bound_path(
        repo_root,
        cast(Mapping[str, Any], config["baseline_manifest"]),
        "baseline binding",
    )
    saga_conformance.validate_baseline(baseline.relative_to(repo_root), repo_root=repo_root)
    commands = config["phase_commands"]
    if not isinstance(commands, list) or [
        row.get("id") for row in commands if isinstance(row, dict)
    ] != list(PHASES):
        raise CanaryError("live-canary phase commands do not match the required route")
    for index, row in enumerate(commands):
        if not isinstance(row, dict):
            raise CanaryError("live-canary phase command must be an object")
        _closed(row, {"id", "command"}, f"phase_commands[{index}]")
        command = row["command"]
        if not isinstance(command, str) or not command.startswith(f"/{row['id']}"):
            raise CanaryError("live-canary phase command does not match its identity")
    return config


def parse_agy_events(payload: str) -> list[dict[str, Any]]:
    """Parse a bounded AGY stream-json result without accepting arbitrary event shapes."""

    if len(payload.encode("utf-8", errors="replace")) > 8 * 1024 * 1024:
        raise CanaryError("AGY event stream exceeds the bounded size")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CanaryError(f"AGY event stream line {line_number} is invalid JSON") from exc
        if not isinstance(event, dict) or event.get("event") not in {
            "init",
            "step_update",
            "result",
        }:
            raise CanaryError("AGY event stream contains an unsupported event")
        events.append(cast(dict[str, Any], event))
    if not events or events[0].get("event") != "init" or events[-1].get("event") != "result":
        raise CanaryError("AGY event stream is incomplete")
    if sum(event.get("event") == "init" for event in events) != 1:
        raise CanaryError("AGY event stream has an invalid init count")
    if sum(event.get("event") == "result" for event in events) != 1:
        raise CanaryError("AGY event stream has an invalid result count")
    return events


def _event_conversation(event: Mapping[str, Any]) -> str | None:
    if event.get("event") == "init":
        value = event.get("conversation_id")
    elif event.get("event") == "result" and isinstance(event.get("result"), Mapping):
        value = cast(Mapping[str, Any], event["result"]).get("conversation_id")
    elif event.get("event") == "step_update" and isinstance(event.get("step_update"), Mapping):
        value = cast(Mapping[str, Any], event["step_update"]).get("conversation_id")
    else:
        value = None
    return value if isinstance(value, str) and value else None


def summarize_agy_events(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return a privacy-safe invocation summary and tool-call audit inputs."""

    init = cast(Mapping[str, Any], events[0].get("init"))
    result = cast(Mapping[str, Any], events[-1].get("result"))
    conversation_ids = {value for event in events if (value := _event_conversation(event))}
    if len(conversation_ids) != 1:
        raise CanaryError("AGY event stream does not bind one conversation identity")
    tools = init.get("tools")
    if not isinstance(tools, list) or any(not isinstance(item, str) for item in tools):
        raise CanaryError("AGY init event does not contain a valid tool list")
    tool_events: list[dict[str, Any]] = []
    for event in events:
        update = event.get("step_update")
        if not isinstance(update, Mapping) or update.get("step_type") != "tool":
            continue
        info = update.get("tool_info")
        if not isinstance(info, Mapping):
            raise CanaryError("AGY tool event has no tool_info object")
        name = info.get("name") or update.get("tool_name")
        if not isinstance(name, str) or not name:
            raise CanaryError("AGY tool event has no stable tool name")
        parameters = info.get("parameters", {})
        if not isinstance(parameters, Mapping):
            raise CanaryError("AGY tool parameters must be an object")
        tool_events.append(
            {
                "name": name,
                "state": update.get("state"),
                "parameters": dict(parameters),
                "parameters_sha256": _canonical_digest(parameters),
                "output_sha256": _canonical_digest(info.get("output")),
            }
        )
    status = result.get("status")
    if not isinstance(status, str):
        raise CanaryError("AGY result has no status")
    model = init.get("model")
    agent = init.get("agent")
    permission_mode = init.get("permission_mode")
    return {
        "conversation_sha256": _digest_bytes(next(iter(conversation_ids)).encode()),
        "model": model if isinstance(model, str) else "unknown",
        "agent": agent if isinstance(agent, str) else "unknown",
        "permission_mode": permission_mode if isinstance(permission_mode, str) else "unknown",
        "available_tools": sorted(cast(list[str], tools)),
        "status": status,
        "tool_events": tool_events,
    }


def forbidden_mutation_attempts(summary: Mapping[str, Any]) -> list[str]:
    """Return bounded reason codes for attempted remote or installation mutation."""

    attempts: list[str] = []
    events = summary.get("tool_events")
    if not isinstance(events, list):
        raise CanaryError("invocation summary tool_events must be a list")
    for event in events:
        if not isinstance(event, Mapping):
            raise CanaryError("invocation summary tool event must be an object")
        name = str(event.get("name", "")).lower()
        if any(fragment in name for fragment in FORBIDDEN_TOOL_FRAGMENTS):
            attempts.append("forbidden-tool")
        parameters = event.get("parameters", {})
        if name == "run_command" and isinstance(parameters, Mapping):
            commands = [
                value
                for key, value in parameters.items()
                if str(key).lower() in {"command", "commandline", "cmd"} and isinstance(value, str)
            ]
            if any(
                pattern.search(command) for command in commands for pattern in FORBIDDEN_COMMANDS
            ):
                attempts.append("forbidden-command")
    return sorted(set(attempts))


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = _VERSION.fullmatch(value.strip())
    if match is None:
        raise CanaryError("AGY version output is not semantic-version shaped")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def require_agy_version(value: str) -> str:
    """Require the first AGY release with headless slash-command expansion."""

    normalized = value.strip()
    if _version_tuple(normalized) < MINIMUM_AGY_VERSION:
        raise CanaryError("AGY 1.1.9 or newer is required for headless slash commands")
    return normalized


def _run(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # nosec B603
            list(argv),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CanaryError("bounded command execution failed") from exc


def _invoke_agy(
    instruction: str,
    *,
    cwd: Path,
    raw_path: Path,
    config: Mapping[str, Any],
    conversation_id: str | None = None,
    agent: str | None = None,
    mode: str | None = None,
    timeout: float = 600.0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    argv = [
        "agy",
        "--model",
        str(config["resolved_model"]),
        "--effort",
        str(config["effort"]),
        "--sandbox",
        "--output-format",
        "stream-json",
        "--print-timeout",
        f"{max(1, int(timeout // 60))}m",
    ]
    if agent is not None:
        argv.extend(["--agent", agent])
    if mode is not None:
        argv.extend(["--mode", mode])
    if conversation_id is not None:
        argv.extend(["--conversation", conversation_id])
    argv.extend(["--print", instruction])
    completed = _run(argv, cwd=cwd, timeout=timeout + 30)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(completed.stdout, encoding="utf-8")
    if completed.returncode != 0:
        raise CanaryError("AGY invocation failed")
    events = parse_agy_events(completed.stdout)
    summary = summarize_agy_events(events)
    if summary["status"] != "SUCCESS":
        raise CanaryError("AGY invocation did not report success")
    attempts = forbidden_mutation_attempts(summary)
    if attempts:
        raise CanaryError("AGY invocation attempted a forbidden mutation")
    return summary, events


def _conversation_id(events: Sequence[Mapping[str, Any]]) -> str:
    value = _event_conversation(events[0])
    if value is None:
        raise CanaryError("AGY init event has no conversation identity")
    return value


def _host_version() -> str:
    try:
        with HOST_INFO.open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        raise CanaryError("Antigravity host version metadata is unavailable") from exc
    value = payload.get("CFBundleShortVersionString")
    if not isinstance(value, str) or not value:
        raise CanaryError("Antigravity host version metadata is invalid")
    return value


def _validate_installed_plugins() -> tuple[bool, bool, bool]:
    install_root = Path.home() / ".gemini" / "config" / "plugins"
    required = ("fleet-core", "multi-agent-consensus", "saga")
    loadable = ("multi-agent-consensus", "saga")
    linked = all(
        (install_root / name).is_symlink() and (install_root / name).resolve().is_dir()
        for name in required
    )
    listed = _run(("agy", "plugin", "list", "--json"), cwd=REPO_ROOT)
    try:
        payload = json.loads(listed.stdout)
        imported = {row["name"] for row in payload["imports"] if isinstance(row, dict)}
    except (KeyError, TypeError, json.JSONDecodeError):
        imported = set()
    loaded = listed.returncode == 0 and set(loadable) <= imported
    validated = True
    for name in required:
        result = _run(
            ("agy", "plugin", "validate", str((install_root / name).resolve())), cwd=REPO_ROOT
        )
        validation_output = f"{result.stdout}\n{result.stderr}"
        validated = (
            validated
            and result.returncode == 0
            and "[ok]" in re.sub(r"\x1b\[[0-9;]*m", "", validation_output)
        )
    return linked, loaded, validated


def _runtime_roots_present() -> bool:
    roots = (
        REPO_ROOT,
        Path.home() / ".gemini" / "config" / "plugins",
        Path.home() / ".gemini" / "saga",
        Path.home() / ".gemini" / "antigravity" / "conversations",
        Path.home() / ".gemini" / "antigravity" / "brain",
    )
    return all(path.is_dir() for path in roots)


def _capability_receipt(
    *,
    config: Mapping[str, Any],
    agy_version: str,
    supported_flags: list[str],
    identity: Mapping[str, Any],
    resumed: bool,
    plan_mode: bool | None,
    sandbox: bool,
    plugin_states: tuple[bool, bool, bool],
) -> dict[str, Any]:
    catalog = CAPABILITIES.load_catalog(CATALOG_PATH)
    linked, loaded, validated = plugin_states
    states = {
        "agy-version": "passed",
        "agy-help-flags": "passed",
        "antigravity-host-version": "passed",
        "plugin-links": "passed" if linked else "failed",
        "plugin-load": "passed" if loaded else "failed",
        "plugin-validation": "passed" if validated else "failed",
        "runtime-root-discovery": "passed" if _runtime_roots_present() else "unknown",
        "controlled-model-selection": "passed"
        if identity.get("model") == config["resolved_model"]
        else "failed",
        "controlled-effort-selection": "passed"
        if str(identity.get("model", "")).endswith("-high")
        else "unknown",
        "controlled-agent-execution": "passed"
        if identity.get("agent") == config["agent"]
        else "failed",
        "controlled-resume": "passed" if resumed else "failed",
        "controlled-plan-mode": (
            "unavailable" if plan_mode is None else "passed" if plan_mode else "failed"
        ),
        "controlled-sandbox": "passed" if sandbox else "failed",
        "controlled-sequential-isolation": "unavailable",
    }
    results = []
    for row in catalog["capabilities"]:
        state = states[row["probe_method"]]
        results.append(
            {
                "id": row["id"],
                "probe_revision": row["probe_revision"],
                "state": state,
                "evidence": list(row["expected_evidence"]) if state == "passed" else [],
            }
        )
    requested = {
        "plugin-links": True,
        "plugin-load": True,
        "plugin-validation": True,
        "model-selection": config["model"],
        "effort-selection": config["effort"],
        "agent-execution": True,
        "conversation-resume": True,
        "plan-mode": None,
        "sandbox-isolation": True,
    }
    observed = {
        "plugin-links": linked,
        "plugin-load": loaded,
        "plugin-validation": validated,
        "model-selection": config["model"]
        if states["controlled-model-selection"] == "passed"
        else None,
        "effort-selection": config["effort"]
        if states["controlled-effort-selection"] == "passed"
        else None,
        "agent-execution": states["controlled-agent-execution"] == "passed",
        "conversation-resume": resumed,
        "plan-mode": plan_mode,
        "sandbox-isolation": sandbox,
    }
    receipt = {
        "schema": CAPABILITY_SCHEMA,
        "catalog_digest": CAPABILITIES.canonical_catalog_digest(catalog),
        "agy_cli_version": agy_version,
        "antigravity_host_version": _host_version(),
        "supported_flags": supported_flags,
        "runtime_roots": [
            "brain-artifacts",
            "conversation-artifacts",
            "plugin-install",
            "repository",
            "saga-state",
        ],
        "requested_facts": requested,
        "observed_facts": observed,
        "results": results,
    }
    errors = CAPABILITIES.validate_receipt(receipt, catalog)
    if errors:
        raise CanaryError("live capability receipt failed strict validation")
    evaluation = CAPABILITIES.evaluate_for_consumer(receipt, catalog, "live-canary")
    if evaluation["state"] != "passed":
        raise CanaryError("live-canary capability profile is blocked")
    artifact_promotion.sanitize_promoted_content(
        json.dumps(receipt, sort_keys=True).encode("utf-8")
    )
    return receipt


def preflight(fixture_id: str, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Run deterministic checks, then bounded controlled host probes."""

    config = load_config(fixture_id, repo_root=repo_root)
    saga_conformance.verify_fixture(fixture_id, repo_root=repo_root)
    baseline_ref = cast(Mapping[str, Any], config["baseline_manifest"])["path"]
    saga_conformance.validate_baseline(str(baseline_ref), repo_root=repo_root)

    version_result = _run(("agy", "--version"), cwd=repo_root)
    if version_result.returncode != 0:
        raise CanaryError("AGY version observation failed")
    agy_version = require_agy_version(version_result.stdout)
    help_result = _run(("agy", "--help"), cwd=repo_root)
    if help_result.returncode != 0:
        raise CanaryError("AGY flag observation failed")
    help_output = f"{help_result.stdout}\n{help_result.stderr}"
    flags = sorted(set(re.findall(r"(?<![A-Za-z0-9])(--[a-z0-9-]+)", help_output)))
    required_flags = {
        "--agent",
        "--conversation",
        "--effort",
        "--model",
        "--output-format",
        "--sandbox",
    }
    if not required_flags <= set(flags):
        raise CanaryError("AGY is missing required live-canary flags")

    probe_root = LOCAL_ROOT / "preflight" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    probe_root.mkdir(parents=True, exist_ok=False)
    identity_summary, identity_events = _invoke_agy(
        "Reply exactly CANARY_IDENTITY_PROBE. Do not use tools.",
        cwd=probe_root,
        raw_path=probe_root / "identity.ndjson",
        config=config,
        agent=str(config["agent"]),
        timeout=120,
    )
    conversation_id = _conversation_id(identity_events)
    resumed_summary, _resumed_events = _invoke_agy(
        "Reply exactly CANARY_RESUME_PROBE. Do not use tools.",
        cwd=probe_root,
        raw_path=probe_root / "resume.ndjson",
        config=config,
        conversation_id=conversation_id,
        agent=str(config["agent"]),
        timeout=120,
    )
    resumed = resumed_summary["conversation_sha256"] == identity_summary["conversation_sha256"]

    sandbox_workspace = probe_root / "sandbox-workspace"
    sandbox_workspace.mkdir()
    _run(("git", "init", "-q", "-b", "main"), cwd=sandbox_workspace)
    inside_target = sandbox_workspace / "sandbox-inside.txt"
    outside_target = probe_root / "sandbox-outside.txt"
    sandbox_instruction = (
        f"Use write_to_file to create {inside_target} containing ok. Then use run_command to "
        f"attempt `touch {outside_target}`. Do not use another tool."
    )
    sandbox_summary, _sandbox_events = _invoke_agy(
        sandbox_instruction,
        cwd=sandbox_workspace,
        raw_path=probe_root / "sandbox.ndjson",
        config=config,
        mode="accept-edits",
        timeout=120,
    )
    sandbox_names = {row["name"] for row in sandbox_summary["tool_events"]}
    sandbox = (
        inside_target.is_file()
        and not outside_target.exists()
        and {"run_command", "write_to_file"} <= sandbox_names
    )

    receipt = _capability_receipt(
        config=config,
        agy_version=agy_version,
        supported_flags=flags,
        identity=identity_summary,
        resumed=resumed,
        plan_mode=None,
        sandbox=sandbox,
        plugin_states=_validate_installed_plugins(),
    )
    receipt_path = probe_root / "capability-receipt.json"
    _write_json(receipt_path, receipt)
    record = {
        "schema": "saga.live-canary-preflight.v1",
        "fixture_id": fixture_id,
        "fixture_revision": config["fixture_revision"],
        "config_sha256": _digest_file(repo_root / FIXTURE_CONFIG.relative_to(REPO_ROOT)),
        "baseline_sha256": cast(Mapping[str, Any], config["baseline_manifest"])["sha256"],
        "capability_receipt": {
            "path": receipt_path.relative_to(repo_root).as_posix(),
            "sha256": _digest_file(receipt_path),
        },
        "runtime": {
            "agy_cli_version": agy_version,
            "antigravity_host_version": receipt["antigravity_host_version"],
            "model": config["model"],
            "effort": config["effort"],
            "agent": config["agent"],
            "sandbox": True,
        },
        "passed": True,
    }
    _write_json(probe_root / "preflight.json", record)
    _write_json(LATEST_PREFLIGHT, record)
    return record


def _git_changed_paths(workspace: Path) -> list[str]:
    result = _run(("git", "status", "--porcelain=v1", "-uall"), cwd=workspace)
    if result.returncode != 0:
        raise CanaryError("fixture Git status failed")
    paths = []
    for line in result.stdout.splitlines():
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value)
    return sorted(set(paths))


def _artifact_bindings(workspace: Path, root: str) -> list[dict[str, str]]:
    directory = workspace / root
    if not directory.is_dir():
        return []
    bindings = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and not path.is_symlink():
            bindings.append(
                {"path": path.relative_to(workspace).as_posix(), "sha256": _digest_file(path)}
            )
    return bindings


def _receipt_bindings(workspace: Path) -> dict[str, list[dict[str, str]]]:
    patterns = {
        "deliberation": ("*deliberation*receipt*.json",),
        "promotion": ("*promotion*receipt*.json", "*promotion*.receipt.json"),
        "transition": ("*transition*receipt*.json",),
        "handoff": ("docs/handoffs/*.json", "*handoff*receipt*.json"),
    }
    result: dict[str, list[dict[str, str]]] = {}
    for group, group_patterns in patterns.items():
        paths: set[Path] = set()
        for pattern in group_patterns:
            paths.update(workspace.glob(f"**/{pattern}"))
        result[group] = [
            {"path": path.relative_to(workspace).as_posix(), "sha256": _digest_file(path)}
            for path in sorted(paths)
            if path.is_file() and not path.is_symlink()
        ]
    return result


def _prepare_fixture(workspace: Path, config: Mapping[str, Any], repo_root: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=False)
    profile = _bound_path(repo_root, cast(Mapping[str, Any], config["profile"]), "profile binding")
    folder_contract = _bound_path(
        repo_root,
        cast(Mapping[str, Any], config["folder_contract"]),
        "folder contract binding",
    )
    target_profile = workspace / "profiles" / "reference-service" / "profile.json"
    target_contract = workspace / "docs" / "specs" / "reference-service" / "README.md"
    target_profile.parent.mkdir(parents=True)
    target_contract.parent.mkdir(parents=True)
    shutil.copy2(profile, target_profile)
    shutil.copy2(folder_contract, target_contract)
    (workspace / "seed.md").write_text(
        "# Reference service seed\n\n"
        "Build a small local reference service with deterministic validation, durable lifecycle "
        "artifacts, explicit conflict handling, and no remote mutation.\n",
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text(
        "# Canary fixture rules\n\n"
        "Work autonomously inside this local repository. Do not push, create or modify GitHub "
        "objects, merge, deploy, install plugins, change credentials, or add a Git remote. "
        "Use the provided profile and folder contract. Produce every requested durable Saga "
        "artifact and receipt. Stop on a failed required gate.\n",
        encoding="utf-8",
    )
    _run(("git", "init", "-q", "-b", "main"), cwd=workspace)
    _run(("git", "config", "user.name", "Saga Canary"), cwd=workspace)
    _run(("git", "config", "user.email", "saga-canary@invalid.example"), cwd=workspace)
    _run(("git", "add", "AGENTS.md", "seed.md", "profiles", "docs"), cwd=workspace)
    committed = _run(
        ("git", "commit", "-q", "-m", "seed reference lifecycle canary"), cwd=workspace
    )
    if committed.returncode != 0:
        raise CanaryError("fixture seed commit failed")


def run_canary(fixture_id: str, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Drive one fresh local reference lifecycle after a passing preflight."""

    config = load_config(fixture_id, repo_root=repo_root)
    preflight_record = _load_json(LATEST_PREFLIGHT, "latest live-canary preflight")
    if preflight_record.get("passed") is not True:
        raise CanaryError("a passing current preflight is required")
    capability_binding = cast(Mapping[str, Any], preflight_record["capability_receipt"])
    capability_path = _bound_path(repo_root, capability_binding, "capability receipt")
    catalog = CAPABILITIES.load_catalog(CATALOG_PATH)
    receipt = CAPABILITIES.load_receipt(capability_path, catalog)
    if CAPABILITIES.evaluate_for_consumer(receipt, catalog, "live-canary")["state"] != "passed":
        raise CanaryError("latest live-canary capability receipt is not passing")

    run_id = datetime.now(UTC).strftime("reference-lifecycle-%Y%m%dT%H%M%SZ")
    run_root = LOCAL_ROOT / "runs" / run_id
    workspace = run_root / "workspace"
    _prepare_fixture(workspace, config, repo_root)
    if _run(("git", "remote"), cwd=workspace).stdout.strip():
        raise CanaryError("live-canary fixture must not have a Git remote")

    phase_records: list[dict[str, Any]] = []
    conversation_id: str | None = None
    conversation_sha256: str | None = None
    for row in cast(list[dict[str, str]], config["phase_commands"]):
        phase = row["id"]
        instruction = row["command"]
        summary, events = _invoke_agy(
            instruction,
            cwd=workspace,
            raw_path=run_root / "raw" / f"{phase}.ndjson",
            config=config,
            conversation_id=conversation_id,
            agent=str(config["agent"]),
            mode="accept-edits",
            timeout=900,
        )
        observed_id = _conversation_id(events)
        if conversation_id is None:
            conversation_id = observed_id
            conversation_sha256 = summary["conversation_sha256"]
        elif (
            observed_id != conversation_id or summary["conversation_sha256"] != conversation_sha256
        ):
            raise CanaryError("live-canary conversation identity changed")
        artifact_root = ARTIFACT_GROUPS.get(phase)
        if artifact_root is not None and not _artifact_bindings(workspace, artifact_root):
            raise CanaryError(f"live-canary phase {phase} produced no canonical artifact")
        phase_records.append(
            {
                "id": phase,
                "status": "passed",
                "conversation_sha256": summary["conversation_sha256"],
                "event_sha256": _digest_file(run_root / "raw" / f"{phase}.ndjson"),
                "changed_paths": _git_changed_paths(workspace),
                "tool_event_count": len(summary["tool_events"]),
            }
        )

    artifacts = {
        phase: _artifact_bindings(workspace, root) for phase, root in ARTIFACT_GROUPS.items()
    }
    receipts = _receipt_bindings(workspace)
    manifest = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "fixture": {
            "id": fixture_id,
            "revision": config["fixture_revision"],
            "config_sha256": _digest_file(repo_root / FIXTURE_CONFIG.relative_to(REPO_ROOT)),
            "runner_sha256": _digest_file(Path(__file__)),
        },
        "baseline": dict(cast(Mapping[str, Any], config["baseline_manifest"])),
        "capability_receipt": dict(capability_binding),
        "runtime": dict(cast(Mapping[str, Any], preflight_record["runtime"])),
        "conversation_sha256": conversation_sha256,
        "phases": phase_records,
        "artifacts": artifacts,
        "receipts": receipts,
        "mutation_audit": {
            "state": "passed",
            "forbidden_attempts": [],
            "git_remote_count": 0,
        },
        "release_review": {
            "state": "pending",
            "dimensions": {
                "depth": "pending",
                "evidence_use": "pending",
                "seed_retention": "pending",
                "adjudication": "pending",
                "lifecycle_completeness": "pending",
            },
            "decision_reference": "",
        },
    }
    manifest_path = run_root / "run-manifest.json"
    _write_json(manifest_path, manifest)
    verify_run_manifest(manifest, root=workspace, repo_root=repo_root)
    return {
        "run_id": run_id,
        "manifest": manifest_path.relative_to(repo_root).as_posix(),
        "mechanical_passed": True,
        "release_approved": False,
    }


def _verify_binding(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, Mapping):
        raise CanaryError(f"{label} must be an object")
    return _bound_path(root, value, label)


def _reject_private_keys(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PRIVATE_KEYS:
                raise CanaryError(f"{label} contains a forbidden private field")
            _reject_private_keys(child, label)
    elif isinstance(value, list):
        for child in value:
            _reject_private_keys(child, label)


def verify_run_manifest(
    manifest: Mapping[str, Any],
    *,
    root: Path,
    repo_root: Path = REPO_ROOT,
    capability_root: Path | None = None,
) -> dict[str, Any]:
    """Verify one sanitized mechanical run manifest against repository and fixture bytes."""

    _reject_private_keys(manifest, "run manifest")
    _closed(
        manifest,
        {
            "schema",
            "run_id",
            "fixture",
            "baseline",
            "capability_receipt",
            "runtime",
            "conversation_sha256",
            "phases",
            "artifacts",
            "receipts",
            "mutation_audit",
            "release_review",
        },
        "run manifest",
    )
    if manifest["schema"] != RUN_SCHEMA:
        raise CanaryError("run manifest schema is unsupported")
    fixture = manifest["fixture"]
    if not isinstance(fixture, Mapping):
        raise CanaryError("run fixture must be an object")
    _closed(fixture, {"id", "revision", "config_sha256", "runner_sha256"}, "run fixture")
    if fixture["id"] != "reference-lifecycle" or fixture["revision"] != 1:
        raise CanaryError("run fixture identity is unsupported")
    config = load_config("reference-lifecycle", repo_root=repo_root)
    if fixture["config_sha256"] != _digest_file(repo_root / FIXTURE_CONFIG.relative_to(REPO_ROOT)):
        raise CanaryError("run fixture config binding is stale")
    if fixture["runner_sha256"] != _digest_file(Path(__file__)):
        raise CanaryError("run runner binding is stale")
    if manifest["baseline"] != config["baseline_manifest"]:
        raise CanaryError("run baseline does not match the approved configuration")
    _verify_binding(repo_root, manifest["baseline"], "run baseline")
    capability_path = _verify_binding(
        capability_root or repo_root,
        manifest["capability_receipt"],
        "run capability receipt",
    )
    catalog = CAPABILITIES.load_catalog(CATALOG_PATH)
    capability_receipt = CAPABILITIES.load_receipt(capability_path, catalog)
    capability_evaluation = CAPABILITIES.evaluate_for_consumer(
        capability_receipt, catalog, "live-canary"
    )
    if capability_evaluation["state"] != "passed":
        raise CanaryError("run capability receipt is not passing")
    runtime = manifest["runtime"]
    if not isinstance(runtime, Mapping):
        raise CanaryError("run runtime must be an object")
    _closed(
        runtime,
        {
            "agy_cli_version",
            "antigravity_host_version",
            "model",
            "effort",
            "agent",
            "sandbox",
        },
        "run runtime",
    )
    agy_version = runtime["agy_cli_version"]
    if not isinstance(agy_version, str):
        raise CanaryError("run AGY CLI version is invalid")
    require_agy_version(agy_version)
    host_version = runtime["antigravity_host_version"]
    if not isinstance(host_version, str) or not _VERSION.fullmatch(host_version):
        raise CanaryError("run Antigravity host version is invalid")
    expected_runtime = {
        "model": config["model"],
        "effort": config["effort"],
        "agent": config["agent"],
        "sandbox": True,
    }
    if any(runtime[key] != expected for key, expected in expected_runtime.items()):
        raise CanaryError("run runtime does not match the approved configuration")
    if (
        runtime["agy_cli_version"] != capability_receipt["agy_cli_version"]
        or runtime["antigravity_host_version"] != capability_receipt["antigravity_host_version"]
    ):
        raise CanaryError("run runtime does not match the capability receipt")
    conversation = manifest["conversation_sha256"]
    if not isinstance(conversation, str) or not _DIGEST.fullmatch(conversation):
        raise CanaryError("run conversation identity is invalid")
    phases = manifest["phases"]
    if not isinstance(phases, list) or [
        row.get("id") for row in phases if isinstance(row, Mapping)
    ] != list(PHASES):
        raise CanaryError("run phases do not match the required lifecycle")
    for row in phases:
        if not isinstance(row, Mapping):
            raise CanaryError("run phase must be an object")
        _closed(
            row,
            {
                "id",
                "status",
                "conversation_sha256",
                "event_sha256",
                "changed_paths",
                "tool_event_count",
            },
            "run phase",
        )
        if row["status"] != "passed" or row["conversation_sha256"] != conversation:
            raise CanaryError("run phase is not settled in the bound conversation")
        if not isinstance(row["event_sha256"], str) or not _DIGEST.fullmatch(row["event_sha256"]):
            raise CanaryError("run phase event digest is invalid")
        if not isinstance(row["changed_paths"], list) or any(
            not isinstance(path, str) for path in row["changed_paths"]
        ):
            raise CanaryError("run phase changed_paths is invalid")
        if (
            isinstance(row["tool_event_count"], bool)
            or not isinstance(row["tool_event_count"], int)
            or row["tool_event_count"] < 0
        ):
            raise CanaryError("run phase tool_event_count is invalid")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, Mapping) or set(artifacts) != set(ARTIFACT_GROUPS):
        raise CanaryError("run artifact groups are incomplete")
    for group, bindings in artifacts.items():
        if not isinstance(bindings, list) or not bindings:
            raise CanaryError(f"run artifact group {group} is empty")
        for binding in bindings:
            _verify_binding(root, binding, f"run artifact {group}")
    receipts = manifest["receipts"]
    if not isinstance(receipts, Mapping) or set(receipts) != set(REQUIRED_RECEIPT_GROUPS):
        raise CanaryError("run receipt groups are incomplete")
    for group, bindings in receipts.items():
        if not isinstance(bindings, list) or not bindings:
            raise CanaryError(f"run receipt group {group} is empty")
        for binding in bindings:
            _verify_binding(root, binding, f"run receipt {group}")
    mutation = manifest["mutation_audit"]
    if not isinstance(mutation, Mapping):
        raise CanaryError("run mutation audit must be an object")
    _closed(mutation, {"state", "forbidden_attempts", "git_remote_count"}, "mutation audit")
    if mutation != {"state": "passed", "forbidden_attempts": [], "git_remote_count": 0}:
        raise CanaryError("run mutation audit is not clean")
    review = manifest["release_review"]
    if not isinstance(review, Mapping):
        raise CanaryError("release review must be an object")
    _closed(review, {"state", "dimensions", "decision_reference"}, "release review")
    if review["state"] not in {"pending", "approved", "rejected"}:
        raise CanaryError("release review state is invalid")
    dimensions = review["dimensions"]
    required_dimensions = {
        "depth",
        "evidence_use",
        "seed_retention",
        "adjudication",
        "lifecycle_completeness",
    }
    if not isinstance(dimensions, Mapping) or set(dimensions) != required_dimensions:
        raise CanaryError("release review dimensions are incomplete")
    decision_reference = review["decision_reference"]
    if not isinstance(decision_reference, str):
        raise CanaryError("release review decision reference is invalid")
    if review["state"] == "pending":
        if set(dimensions.values()) != {"pending"} or decision_reference:
            raise CanaryError("pending release review contains a decision")
    else:
        allowed_decisions = {"approved", "rejected"}
        if any(value not in allowed_decisions for value in dimensions.values()):
            raise CanaryError("release review dimension decision is invalid")
        if review["state"] == "approved" and set(dimensions.values()) != {"approved"}:
            raise CanaryError("approved release review has an unapproved dimension")
        if review["state"] == "rejected" and "rejected" not in dimensions.values():
            raise CanaryError("rejected release review has no rejected dimension")
        if not _DECISION_REFERENCE.fullmatch(decision_reference):
            raise CanaryError("release review decision reference is invalid")
    return {
        "fixture_id": config["fixture_id"],
        "mechanical_passed": True,
        "release_approved": review["state"] == "approved",
    }


def verify_manifest(path: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    manifest = _load_json(path, "run manifest")
    try:
        relative = path.resolve(strict=True).relative_to(
            (repo_root / ".conformance-local").resolve()
        )
    except (OSError, ValueError) as exc:
        raise CanaryError("run manifest must remain under .conformance-local") from exc
    if len(relative.parts) < 3 or relative.parts[-1] != "run-manifest.json":
        raise CanaryError("run manifest path is not canonical")
    workspace = path.parent / "workspace"
    if not workspace.is_dir():
        raise CanaryError("run workspace is missing")
    return verify_run_manifest(manifest, root=workspace, repo_root=repo_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--fixture", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--fixture", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            result = preflight(args.fixture)
        elif args.command == "run":
            result = run_canary(args.fixture)
        else:
            result = verify_manifest(args.manifest)
    except CanaryError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.command == "verify" and not result["release_approved"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
