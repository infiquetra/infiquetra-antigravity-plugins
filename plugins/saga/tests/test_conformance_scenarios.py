"""Acceptance tests for the deterministic Saga conformance laboratory."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "saga_conformance.py"
FIXTURE = (
    REPO_ROOT
    / "plugins"
    / "saga"
    / "tests"
    / "fixtures"
    / "conformance"
    / "reference-lifecycle"
    / "fixture.json"
)
SCENARIOS = FIXTURE.with_name("scenarios.json")
BASELINE = REPO_ROOT / "docs" / "conformance" / "baselines" / "reference-lifecycle"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("saga_conformance_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def _manifest() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((BASELINE / "manifest.yaml").read_text(encoding="utf-8")),
    )


def test_reference_fixture_covers_every_required_semantic_scenario() -> None:
    fixture, nodes = M.load_fixture("reference-lifecycle")
    scenario_sets = [
        json.loads((REPO_ROOT / row["path"]).read_text(encoding="utf-8"))
        for row in fixture["scenario_sets"]
    ]
    scenarios = [scenario for group in scenario_sets for scenario in group["scenarios"]]

    assert len(nodes) == 18
    assert {scenario["scenario_id"] for scenario in scenarios} == M.REQUIRED_COVERAGE
    assert {
        scenario["scenario_id"] for scenario in scenarios if scenario["scenario_class"] == "failure"
    } == M.REQUIRED_FAILURE_SCENARIOS
    assert all(scenario["requirement_ids"] for scenario in scenarios)
    assert all(scenario["expected"]["observable"] for scenario in scenarios)


def test_verify_uses_one_fixed_pytest_vector_without_model_or_network_commands() -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def runner(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0)

    result = M.verify_fixture("reference-lifecycle", runner=runner)

    assert result == {
        "fixture_id": "reference-lifecycle",
        "fixture_revision": 1,
        "scenario_count": 18,
        "passed": True,
    }
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:6] == ["uv", "run", "--frozen", "python", "-m", "pytest"]
    assert argv[-1] == "-q"
    assert kwargs == {"cwd": REPO_ROOT, "check": False}
    command = " ".join(argv).lower()
    assert "agy" not in command and "gemini" not in command and "claude" not in command


def test_scenarios_reject_arbitrary_commands_private_fields_and_unsafe_content() -> None:
    scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"][0]
    unsafe_validator = copy.deepcopy(scenario)
    unsafe_validator["validator"]["node_id"] = "plugins/saga/tests/test_x.py; agy run"
    with pytest.raises(M.ConformanceError, match="exact plugin pytest node"):
        M._validate_scenario(
            unsafe_validator,
            repo_root=REPO_ROOT,
        )

    with pytest.raises(M.ConformanceError, match="forbidden private field"):
        M._reject_private_keys({"username": "private-value"}, "scenario")

    private_value = "/Users/example/private-file"
    with pytest.raises(M.ConformanceError) as captured:
        M._sanitize_bytes(json.dumps({"value": private_value}).encode(), "scenario")
    assert private_value not in str(captured.value)


def test_baseline_manifest_binds_fixture_contract_snapshots_artifacts_and_approval() -> None:
    approved = _manifest()
    assert M.validate_baseline_manifest(approved) == {
        "fixture_id": "reference-lifecycle",
        "fixture_revision": 1,
        "providers": ["claude", "codex"],
        "approved": True,
    }

    pending = copy.deepcopy(approved)
    pending["operator_approval"]["state"] = "pending"
    with pytest.raises(M.ConformanceError, match="not operator-approved"):
        M.validate_baseline_manifest(pending)

    stale = copy.deepcopy(approved)
    stale["operator_approval"]["binding_sha256"] = "0" * 64
    with pytest.raises(M.ConformanceError, match="does not bind"):
        M.validate_baseline_manifest(stale)

    unbound_reference = copy.deepcopy(approved)
    unbound_reference["operator_approval"]["reference"] = "chat approval"
    with pytest.raises(M.ConformanceError, match="canonical issue or comment"):
        M.validate_baseline_manifest(unbound_reference)


def test_baseline_rejects_changed_repository_identities_and_incomplete_quality() -> None:
    changed_fixture = _manifest()
    changed_fixture["fixture"]["sha256"] = "0" * 64
    with pytest.raises(M.ConformanceError, match="fixture binding digest"):
        M.validate_baseline_manifest(changed_fixture)

    artifact = json.loads((BASELINE / "claude" / "artifact.json").read_text(encoding="utf-8"))
    artifact["quality_dimensions"].pop("depth")
    with pytest.raises(M.ConformanceError, match="closed contract"):
        M._validate_baseline_artifact(
            artifact,
            provider="claude",
            fixture_id="reference-lifecycle",
            fixture_revision=1,
            source_snapshot=artifact["source_snapshot"],
        )


def test_committed_conformance_content_is_sanitized_and_local_discovery_is_ignored() -> None:
    paths = [
        FIXTURE,
        SCENARIOS,
        REPO_ROOT / "plugins/saga/tests/fixtures/conformance/failure-scenarios/scenarios.json",
        BASELINE / "manifest.yaml",
        BASELINE / "claude" / "artifact.json",
        BASELINE / "codex" / "artifact.json",
        REPO_ROOT / "docs/conformance/scenarios/README.md",
    ]
    for path in paths:
        M._sanitize_bytes(path.read_bytes(), path.name)
        if path.suffix in {".json", ".yaml"}:
            M._reject_private_keys(json.loads(path.read_text(encoding="utf-8")), path.name)

    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".conformance-local/" in ignore


def test_ci_runs_conformance_as_a_blocking_publish_dependency() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "  conformance:\n" in workflow
    assert "python scripts/saga_conformance.py verify --fixture reference-lifecycle" in workflow
    assert "python scripts/saga_conformance.py validate-baseline" in workflow
    assert "needs: [tests, validate, lint, type-check, security, conformance]" in workflow
