from __future__ import annotations

import os
import sys
from pathlib import Path

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

COMPAT = fleet_commons_shim.load("workflow_compat")


def _contract(kind: str, inputs: list[str], outputs: list[str]):
    return {
        "schema": COMPAT.WORKFLOW_SCHEMA,
        "kind": kind,
        "inputs": inputs,
        "outputs": outputs,
    }


def test_target_workflow_contracts_compare_declared_inputs_and_outputs() -> None:
    producer = _contract("implementation", ["plan"], ["plan", "result", "checks"])
    consumer = _contract("implementation", ["result", "checks"], ["evidence"])

    assert COMPAT.validate_workflow_contract(producer) == []
    assert COMPAT.compatible(producer, consumer) is True


def test_target_workflow_contracts_reject_source_and_incompatible_vocabulary() -> None:
    source = _contract("Workflow", ["team-execution"], ["result"])
    incompatible = _contract("implementation", ["missing"], ["evidence"])
    producer = _contract("implementation", ["plan"], ["result"])

    assert COMPAT.validate_workflow_contract(source)
    assert COMPAT.compatible(producer, incompatible) is False
