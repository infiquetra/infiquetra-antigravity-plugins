"""Contract tests for the bounded live AGY Saga canary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "run_agy_saga_canary.py"
CONFIG = (
    REPO_ROOT
    / "plugins"
    / "saga"
    / "tests"
    / "fixtures"
    / "conformance"
    / "reference-lifecycle"
    / "live-canary.json"
)
FAILURES = CONFIG.parents[1] / "canary-failures" / "cases.json"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_agy_saga_canary_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(root: Path, relative: str, content: str = "evidence") -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": relative, "sha256": _digest(path)}


def _capability_binding(root: Path) -> dict[str, str]:
    catalog = M.CAPABILITIES.load_catalog(M.CATALOG_PATH)
    requested = {
        "plugin-links": True,
        "plugin-load": True,
        "plugin-validation": True,
        "model-selection": "gemini-3.1-pro",
        "effort-selection": "high",
        "agent-execution": True,
        "conversation-resume": True,
        "plan-mode": None,
        "sandbox-isolation": True,
        "sequential-isolation": None,
    }
    receipt = {
        "schema": M.CAPABILITY_SCHEMA,
        "catalog_digest": M.CAPABILITIES.canonical_catalog_digest(catalog),
        "agy_cli_version": "1.1.9",
        "antigravity_host_version": "2.3.1",
        "supported_flags": ["--agent", "--conversation", "--effort", "--model", "--sandbox"],
        "runtime_roots": [
            "brain-artifacts",
            "conversation-artifacts",
            "plugin-install",
            "repository",
            "saga-state",
        ],
        "requested_facts": requested,
        "observed_facts": dict(requested),
        "results": [
            {
                "id": row["id"],
                "probe_revision": row["probe_revision"],
                "state": (
                    "unavailable"
                    if row["id"] in {"agy.plan.mode", "agy.sequential.isolation"}
                    else "passed"
                ),
                "evidence": (
                    []
                    if row["id"] in {"agy.plan.mode", "agy.sequential.isolation"}
                    else list(row["expected_evidence"])
                ),
            }
            for row in catalog["capabilities"]
        ],
    }
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    return _binding(root, "evidence/capability-receipt.json", payload)


def _manifest(root: Path) -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    artifacts = {
        phase: [_binding(root, f"{directory}/{phase}.json")]
        for phase, directory in M.ARTIFACT_GROUPS.items()
    }
    receipts = {
        group: [_binding(root, f"evidence/{group}-receipt.json")]
        for group in M.REQUIRED_RECEIPT_GROUPS
    }
    return {
        "schema": M.RUN_SCHEMA,
        "run_id": "reference-lifecycle-test",
        "fixture": {
            "id": "reference-lifecycle",
            "revision": 1,
            "config_sha256": _digest(CONFIG),
            "runner_sha256": _digest(SCRIPT),
        },
        "baseline": config["baseline_manifest"],
        "capability_receipt": _capability_binding(root),
        "runtime": {
            "agy_cli_version": "1.1.9",
            "antigravity_host_version": "2.3.1",
            "model": "gemini-3.1-pro",
            "effort": "high",
            "routing_agent": "lifecycle-router",
            "execution_agent_requested": "default",
            "execution_agent_observed": "unknown",
            "sandbox": True,
        },
        "conversation_sha256": "a" * 64,
        "phases": [
            {
                "id": phase,
                "status": "passed",
                "conversation_sha256": "a" * 64,
                "event_sha256": "b" * 64,
                "execution_agent_observed": "unknown",
                "changed_paths": ["docs/example.md"],
                "tool_event_count": 1,
            }
            for phase in M.PHASES
        ],
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


def _stream(*, command: str | None = None) -> str:
    init = {
        "event": "init",
        "conversation_id": "conversation-1",
        "init": {
            "agent": "lifecycle-router",
            "cwd": "/private/local",
            "model": "gemini-3.1-pro-high",
            "permission_mode": "always-proceed",
            "tools": ["run_command", "view_file"],
        },
    }
    events: list[dict[str, Any]] = [init]
    if command is not None:
        events.append(
            {
                "event": "step_update",
                "step_update": {
                    "conversation_id": "conversation-1",
                    "state": "DONE",
                    "step_index": 1,
                    "step_type": "tool",
                    "tool_name": "run_command",
                    "tool_info": {
                        "name": "run_command",
                        "parameters": {"command": command},
                        "output": "",
                    },
                },
            }
        )
    events.append(
        {
            "event": "result",
            "result": {
                "conversation_id": "conversation-1",
                "duration_seconds": 1,
                "num_turns": 1,
                "response": "done",
                "status": "SUCCESS",
                "usage": {},
            },
        }
    )
    return "\n".join(json.dumps(event) for event in events)


def test_config_binds_approved_inputs_and_exact_route() -> None:
    config = M.load_config("reference-lifecycle")

    assert config["fixture_revision"] == 1
    assert config["resolved_model"] == "gemini-3.1-pro-high"
    assert config["routing_agent"] == "lifecycle-router"
    assert config["execution_agent"] == "default"
    assert [row["id"] for row in config["phase_commands"]] == list(M.PHASES)


def test_phase_instruction_anchors_runtime_workspace_without_committed_host_path(
    tmp_path: Path,
) -> None:
    instruction = M.phase_instruction("/ideate Build from seed.md.", tmp_path)

    assert str(tmp_path) in instruction
    assert str(tmp_path / "seed.md") in instruction
    assert "/Users/" not in CONFIG.read_text(encoding="utf-8")


def test_live_canary_does_not_require_native_plan_mode() -> None:
    catalog = M.CAPABILITIES.load_catalog(M.CATALOG_PATH)
    rows = {row["id"]: row for row in catalog["capabilities"]}
    required_for = set(rows["agy.plan.mode"]["required_for"])

    assert "live-canary" not in required_for
    assert "saga.plan" in required_for


def test_stream_parser_extracts_observed_identity_without_private_output() -> None:
    summary = M.summarize_agy_events(M.parse_agy_events(_stream(command="pytest -q")))

    assert summary["model"] == "gemini-3.1-pro-high"
    assert summary["agent"] == "lifecycle-router"
    assert summary["conversation_sha256"] == hashlib.sha256(b"conversation-1").hexdigest()
    assert summary["tool_events"][0]["parameters_sha256"]
    assert "/private/local" not in json.dumps(summary)


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "gh pr create --fill",
        "gh issue close 22",
        "agy plugin install saga",
        "cdk deploy",
    ],
)
def test_mutation_audit_rejects_forbidden_remote_intent(command: str) -> None:
    summary = M.summarize_agy_events(M.parse_agy_events(_stream(command=command)))
    assert M.forbidden_mutation_attempts(summary)


def test_agy_version_floor_rejects_pre_headless_slash_release() -> None:
    with pytest.raises(M.CanaryError, match="1.1.9 or newer"):
        M.require_agy_version("1.1.8")
    assert M.require_agy_version("1.1.9\n") == "1.1.9"


def test_mechanical_manifest_passes_but_quality_stays_pending(tmp_path: Path) -> None:
    result = M.verify_run_manifest(_manifest(tmp_path), root=tmp_path, capability_root=tmp_path)

    assert result == {
        "fixture_id": "reference-lifecycle",
        "mechanical_passed": True,
        "release_approved": False,
    }


def test_approved_release_requires_every_dimension_and_canonical_decision(
    tmp_path: Path,
) -> None:
    approved = _manifest(tmp_path / "approved")
    approved["release_review"] = {
        "state": "approved",
        "dimensions": dict.fromkeys(approved["release_review"]["dimensions"], "approved"),
        "decision_reference": (
            "https://github.com/infiquetra/infiquetra-antigravity-plugins/"
            "issues/22#issuecomment-123"
        ),
    }

    assert (
        M.verify_run_manifest(
            approved, root=tmp_path / "approved", capability_root=tmp_path / "approved"
        )["release_approved"]
        is True
    )

    incomplete = _manifest(tmp_path / "incomplete")
    incomplete["release_review"]["state"] = "approved"
    incomplete["release_review"]["decision_reference"] = approved["release_review"][
        "decision_reference"
    ]
    incomplete["release_review"]["dimensions"] = dict.fromkeys(
        incomplete["release_review"]["dimensions"], "approved"
    )
    incomplete["release_review"]["dimensions"]["depth"] = "rejected"
    with pytest.raises(M.CanaryError, match="unapproved dimension"):
        M.verify_run_manifest(
            incomplete,
            root=tmp_path / "incomplete",
            capability_root=tmp_path / "incomplete",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("agy_cli_version", "1.1.8", "1.1.9 or newer"),
        ("antigravity_host_version", "unknown", "host version is invalid"),
        ("model", "gemini-3.1-pro-preview", "approved configuration"),
        ("effort", "medium", "approved configuration"),
        ("routing_agent", "default", "approved configuration"),
        ("execution_agent_requested", "lifecycle-router", "approved configuration"),
        ("execution_agent_observed", "lifecycle-router", "approved configuration"),
        ("sandbox", False, "approved configuration"),
    ],
)
def test_manifest_rejects_unapproved_runtime(
    tmp_path: Path, field: str, value: Any, message: str
) -> None:
    manifest = _manifest(tmp_path)
    manifest["runtime"][field] = value

    with pytest.raises(M.CanaryError, match=message):
        M.verify_run_manifest(manifest, root=tmp_path, capability_root=tmp_path)


def test_manifest_rejects_missing_phase_receipt_remote_attempt_and_private_field(
    tmp_path: Path,
) -> None:
    missing_phase = _manifest(tmp_path / "missing-phase")
    missing_phase["phases"].pop()
    with pytest.raises(M.CanaryError, match="required lifecycle"):
        M.verify_run_manifest(
            missing_phase,
            root=tmp_path / "missing-phase",
            capability_root=tmp_path / "missing-phase",
        )

    missing_receipt = _manifest(tmp_path / "missing-receipt")
    missing_receipt["receipts"]["deliberation"] = []
    with pytest.raises(M.CanaryError, match="receipt group deliberation is empty"):
        M.verify_run_manifest(
            missing_receipt,
            root=tmp_path / "missing-receipt",
            capability_root=tmp_path / "missing-receipt",
        )

    remote_attempt = _manifest(tmp_path / "remote")
    remote_attempt["mutation_audit"]["forbidden_attempts"] = ["forbidden-command"]
    with pytest.raises(M.CanaryError, match="mutation audit is not clean"):
        M.verify_run_manifest(
            remote_attempt,
            root=tmp_path / "remote",
            capability_root=tmp_path / "remote",
        )

    private = _manifest(tmp_path / "private")
    private["history"] = "private-value"
    with pytest.raises(M.CanaryError, match="forbidden private field") as captured:
        M.verify_run_manifest(
            private,
            root=tmp_path / "private",
            capability_root=tmp_path / "private",
        )
    assert "private-value" not in str(captured.value)


def test_failure_fixture_names_every_issue_required_case() -> None:
    cases = cast(dict[str, Any], json.loads(FAILURES.read_text(encoding="utf-8")))
    assert cases["schema"] == "saga.live-canary-failure-cases.v1"
    assert {row["id"] for row in cases["cases"]} == {
        "missing-profile-readme",
        "required-capability-failure",
        "missing-phase-or-strategy",
        "shallow-mechanical-success",
        "failed-resume",
        "invalid-handoff",
        "baseline-mismatch",
        "attempted-remote-mutation",
    }


def test_committed_canary_surfaces_are_sanitized_and_local_runs_are_ignored() -> None:
    for path in (CONFIG, FAILURES):
        M.artifact_promotion.sanitize_promoted_content(path.read_bytes())
    assert "/Users/" not in SCRIPT.read_text(encoding="utf-8")
    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".conformance-local/" in ignore
