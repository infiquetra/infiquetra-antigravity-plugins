from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

CAPS = fleet_commons_shim.load("antigravity_capabilities")
PROBES = fleet_commons_shim.load("antigravity_probes")
DIAGNOSTICS = fleet_commons_shim.load("antigravity_diagnostics")
FIXTURES = Path(__file__).parent / "fixtures" / "antigravity-capabilities"


def _catalog() -> dict[str, Any]:
    return CAPS.load_catalog(FIXTURES / "catalog-valid.yaml")


def _receipt(
    catalog: dict[str, Any],
    *,
    agent_state: str = "passed",
    sequential_state: str = "passed",
) -> dict[str, Any]:
    return {
        "schema": CAPS.RECEIPT_SCHEMA,
        "catalog_digest": CAPS.canonical_catalog_digest(catalog),
        "agy_cli_version": "9.8.7",
        "antigravity_host_version": "10.2.0",
        "supported_flags": ["--agent", "--effort", "--model"],
        "runtime_roots": ["plugin-install", "saga-state"],
        "requested_facts": {"agent-execution": True},
        "observed_facts": {"agent-execution": agent_state == "passed"},
        "results": [
            {
                "id": "agy.agent.execution",
                "probe_revision": 1,
                "state": agent_state,
                "evidence": ["agent-execution-proof"],
            },
            {
                "id": "agy.sequential.isolation",
                "probe_revision": 1,
                "state": sequential_state,
                "evidence": ["sequential-isolation-proof"],
            },
        ],
    }


def test_catalog_loads_with_standard_library_json() -> None:
    raw = (FIXTURES / "catalog-valid.yaml").read_text(encoding="utf-8")
    assert json.loads(raw)["catalog_schema"] == CAPS.CATALOG_SCHEMA
    assert CAPS.validate_catalog(_catalog()) == []


def test_repository_catalog_is_valid() -> None:
    catalog = CAPS.load_catalog(
        FLEET_CORE / "references" / "antigravity-capability-probes.yaml"
    )
    assert len(catalog["capabilities"]) >= 10
    assert CAPS.validate_catalog(catalog) == []


def test_catalog_rejects_executable_fields_before_execution() -> None:
    unsafe = json.loads((FIXTURES / "catalog-invalid-command.yaml").read_text())
    errors = CAPS.validate_catalog(unsafe)
    assert any("unknown field 'command'" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda row: row.update({"probe_revision": 99}), "registered revision"),
        (lambda row: row.update({"probe_method": "shell-command"}), "unknown registered method"),
        (lambda row: row.update({"state": "passed"}), "unknown field 'state'"),
        (lambda row: row.update({"required_for": "live-canary"}), "expected a list"),
    ],
)
def test_catalog_rejects_invalid_contract_shapes(mutation, message: str) -> None:
    catalog = _catalog()
    mutation(catalog["capabilities"][0])
    assert any(message in error for error in CAPS.validate_catalog(catalog))


def test_unseen_versions_pass_when_required_behavior_passes() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog)
    assert CAPS.validate_receipt(receipt, catalog) == []
    evaluation = CAPS.evaluate_for_consumer(receipt, catalog, "live-canary")
    assert evaluation["state"] == "passed"
    assert evaluation["blocking_capabilities"] == []


@pytest.mark.parametrize("state", ["failed", "unknown", "unavailable"])
def test_required_nonpassing_behavior_blocks_known_or_unknown_versions(state: str) -> None:
    catalog = _catalog()
    receipt = _receipt(catalog, agent_state=state)
    receipt["agy_cli_version"] = "1.1.7"
    evaluation = CAPS.evaluate_for_consumer(receipt, catalog, "live-canary")
    assert evaluation["state"] == "blocked"
    assert evaluation["blocking_capabilities"] == ["agy.agent.execution"]
    assert evaluation["degraded_capabilities"] == []


def test_optional_fallback_is_explicitly_degraded() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog, agent_state="unavailable", sequential_state="passed")
    evaluation = CAPS.evaluate_for_consumer(receipt, catalog, "saga.ideate")
    assert evaluation == {
        "schema": CAPS.EVALUATION_SCHEMA,
        "consumer": "saga.ideate",
        "state": "degraded",
        "blocking_capabilities": [],
        "degraded_capabilities": ["agy.agent.execution"],
        "fallbacks": {"agy.agent.execution": "agy.sequential.isolation"},
    }


def test_optional_fallback_does_not_hide_required_failure() -> None:
    catalog = _catalog()
    catalog["capabilities"][0]["required_for"].append("saga.ideate")
    catalog["capabilities"][0]["fallback"]["for_consumers"] = []
    receipt = _receipt(catalog, agent_state="unavailable", sequential_state="passed")
    receipt["catalog_digest"] = CAPS.canonical_catalog_digest(catalog)
    evaluation = CAPS.evaluate_for_consumer(receipt, catalog, "saga.ideate")
    assert evaluation["state"] == "blocked"
    assert evaluation["blocking_capabilities"] == ["agy.agent.execution"]


def test_receipt_rejects_unknown_fields_states_and_duplicate_results() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog)
    receipt["stdout"] = "private"
    receipt["results"][0]["state"] = "degraded"
    receipt["results"].append(copy.deepcopy(receipt["results"][0]))
    errors = CAPS.validate_receipt(receipt, catalog)
    assert any("unknown field 'stdout'" in error for error in errors)
    assert any("expected one of" in error for error in errors)
    assert any("duplicate result" in error for error in errors)


def test_catalog_digest_drift_is_rejected() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog)
    changed = copy.deepcopy(catalog)
    changed["capabilities"][0]["description"] += " Changed."
    assert any(
        "does not match" in error for error in CAPS.validate_receipt(receipt, changed)
    )


def test_dotted_safe_values_are_accepted() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog)
    receipt["agy_cli_version"] = "3.1.0-rc1"
    assert CAPS.validate_receipt(receipt, catalog) == []


class FakeRunner:
    def __init__(
        self,
        *,
        safe_for_stateful_observation: bool = True,
        oversized: bool = False,
        fail: bool = False,
    ) -> None:
        self.safe_for_stateful_observation = safe_for_stateful_observation
        self.oversized = oversized
        self.fail = fail
        self.calls: list[tuple[tuple[str, ...], float]] = []

    def run(self, argv, *, timeout_s: float):
        self.calls.append((tuple(argv), timeout_s))
        if self.fail:
            raise FileNotFoundError("agy")
        if self.oversized:
            return PROBES.CommandResult(0, "x" * (PROBES.MAX_OUTPUT_BYTES + 1))
        if tuple(argv) == ("agy", "--version"):
            return PROBES.CommandResult(0, "agy 42.7.1\n")
        if tuple(argv) == ("agy", "--help"):
            return PROBES.CommandResult(0, "usage: agy [--model] [--effort] [--agent]\n")
        return PROBES.CommandResult(0, '{"ok": true}')


def test_probe_registry_matches_catalog_contract_and_has_fixed_vectors() -> None:
    assert PROBES.registry_revisions() == CAPS.PROBE_METHOD_REVISIONS
    for definition in PROBES.PROBE_REGISTRY.values():
        assert definition.revision == 1
        if definition.argv is not None:
            assert isinstance(definition.argv, tuple)
            assert definition.argv[0] == "agy"
            assert 0 < definition.timeout_s <= 5


def test_default_probe_profile_executes_no_subprocess() -> None:
    catalog = CAPS.load_catalog(
        FLEET_CORE / "references" / "antigravity-capability-probes.yaml"
    )
    runner = FakeRunner()
    receipt = PROBES.probe_catalog(catalog, runner=runner)
    assert runner.calls == []
    assert receipt["agy_cli_version"] is None
    assert CAPS.validate_receipt(receipt, catalog) == []


def test_observe_host_uses_only_registered_bounded_vectors(tmp_path: Path) -> None:
    catalog = CAPS.load_catalog(
        FLEET_CORE / "references" / "antigravity-capability-probes.yaml"
    )
    plugin_target = tmp_path / "plugin-source"
    plugin_target.mkdir()
    plugin_root = tmp_path / "plugins"
    plugin_root.mkdir()
    (plugin_root / "saga").symlink_to(plugin_target, target_is_directory=True)
    controlled = json.loads((FIXTURES / "probe-success.json").read_text())
    runner = FakeRunner()

    receipt = PROBES.probe_catalog(
        catalog,
        observe_host=True,
        runner=runner,
        host_version_reader=lambda: "11.4.0",
        plugin_root=plugin_root,
        controlled_evidence=controlled,
    )

    assert receipt["agy_cli_version"] == "42.7.1"
    assert receipt["antigravity_host_version"] == "11.4.0"
    assert receipt["supported_flags"] == ["--agent", "--effort", "--model"]
    assert receipt["runtime_roots"] == ["plugin-install"]
    assert all(isinstance(argv, tuple) for argv, _timeout in runner.calls)
    assert all(timeout <= 5 for _argv, timeout in runner.calls)
    assert CAPS.validate_receipt(receipt, catalog) == []


def test_stateful_observations_fail_closed_without_runner_safety_proof() -> None:
    runner = FakeRunner(safe_for_stateful_observation=False)
    load = PROBES.execute_probe(
        "plugin-load", observe_host=True, runner=runner
    )
    validation = PROBES.execute_probe(
        "plugin-validation", observe_host=True, runner=runner
    )
    assert load.state == validation.state == "unavailable"
    assert runner.calls == []


@pytest.mark.parametrize(
    ("runner", "expected"),
    [
        (FakeRunner(fail=True), "unavailable"),
        (FakeRunner(oversized=True), "unknown"),
    ],
)
def test_runner_failures_are_bounded_without_raw_output(runner, expected: str) -> None:
    outcome = PROBES.execute_probe("agy-version", observe_host=True, runner=runner)
    assert outcome.state == expected
    assert outcome.evidence == ()
    assert outcome.value is None


def test_controlled_evidence_does_not_start_a_runner() -> None:
    runner = FakeRunner()
    controlled = json.loads((FIXTURES / "probe-known-broken.json").read_text())
    outcome = PROBES.execute_probe(
        "controlled-agent-execution",
        observe_host=True,
        runner=runner,
        controlled_evidence=controlled,
    )
    assert outcome.state == "failed"
    assert outcome.evidence == ("agent-execution-proof",)
    assert runner.calls == []


def test_unknown_probe_method_is_rejected_before_runner_call() -> None:
    runner = FakeRunner()
    with pytest.raises(ValueError, match="unknown registered probe"):
        PROBES.execute_probe("shell-command", observe_host=True, runner=runner)
    assert runner.calls == []


def test_local_diagnostic_is_atomic_bounded_and_rich(tmp_path: Path) -> None:
    root = tmp_path / ".gemini" / "saga" / "capability-doctor"
    path = DIAGNOSTICS.write_local_diagnostic(
        root,
        "latest",
        {
            "runtime_roots": {"plugin-install": "/Users/alice/.gemini/plugins"},
            "stdout": "bounded raw output",
        },
    )
    payload = json.loads(path.read_text())
    assert payload["schema"] == DIAGNOSTICS.LOCAL_DIAGNOSTIC_SCHEMA
    assert payload["runtime_roots"]["plugin-install"].startswith("/Users/")
    assert list(root.glob("*.tmp")) == []


def test_local_diagnostic_rejects_traversal_and_oversize(tmp_path: Path) -> None:
    with pytest.raises(DIAGNOSTICS.DiagnosticError, match="filename stem"):
        DIAGNOSTICS.write_local_diagnostic(tmp_path, "../escape", {})
    with pytest.raises(DIAGNOSTICS.DiagnosticError, match="exceeds"):
        DIAGNOSTICS.write_local_diagnostic(
            tmp_path,
            "large",
            {"stdout": "x" * 1024},
            max_bytes=64,
        )
    assert list(tmp_path.rglob("*.json")) == []


def test_local_diagnostic_write_failure_leaves_no_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def deny(*_args, **_kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(DIAGNOSTICS.tempfile, "NamedTemporaryFile", deny)
    with pytest.raises(DIAGNOSTICS.DiagnosticError, match="atomically"):
        DIAGNOSTICS.write_local_diagnostic(tmp_path, "denied", {"stdout": "raw"})
    assert list(tmp_path.iterdir()) == []


def test_sanitizer_drops_raw_and_absolute_local_evidence() -> None:
    catalog = _catalog()
    receipt = _receipt(catalog)
    diagnostic = {
        **receipt,
        "schema": DIAGNOSTICS.LOCAL_DIAGNOSTIC_SCHEMA,
        "runtime_roots": {
            "plugin-install": "/Users/alice/.gemini/config/plugins",
            "saga-state": "/Users/alice/repo/.gemini/saga",
        },
        "stdout": "raw output",
        "stderr": "raw error",
        "argv": ["agy", "--help"],
        "environment": {"TOKEN": "secret"},
        "transcript": "private prompt",
    }
    diagnostic.pop("catalog_digest")

    promoted = DIAGNOSTICS.sanitize_for_promotion(diagnostic, catalog)

    assert promoted["runtime_roots"] == ["plugin-install", "saga-state"]
    for forbidden in ("stdout", "stderr", "argv", "environment", "transcript"):
        assert forbidden not in promoted
    assert "/Users/" not in json.dumps(promoted)
    assert CAPS.validate_receipt(promoted, catalog) == []
    assert CAPS.validate_receipt(diagnostic, catalog)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "promoted-unsafe-home-path.json",
        "promoted-unsafe-credential.json",
        "promoted-unsafe-hostname.json",
        "promoted-unsafe-transcript.json",
    ],
)
def test_promoted_unsafe_fixtures_are_rejected_without_echo(fixture_name: str) -> None:
    receipt = json.loads((FIXTURES / fixture_name).read_text())
    errors = CAPS.validate_receipt(receipt)
    assert errors
    rendered_errors = json.dumps(errors)
    assert "/Users/alice" not in rendered_errors
    assert "ghp_super-secret-token" not in rendered_errors
    assert "jeffs-mac.local" not in rendered_errors
    assert "private prompt history" not in rendered_errors


def test_promoted_safe_fixture_accepts_dotted_values() -> None:
    receipt = json.loads((FIXTURES / "promoted-safe.json").read_text())
    assert CAPS.validate_receipt(receipt) == []
