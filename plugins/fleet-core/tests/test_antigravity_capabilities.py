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
