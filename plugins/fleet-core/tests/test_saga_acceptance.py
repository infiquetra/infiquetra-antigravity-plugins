from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

ACCEPTANCE = fleet_commons_shim.load("saga_acceptance")
CONTRACT_PATH = FLEET_CORE / "references" / "saga-acceptance-contract.json"


def _receipts():
    contract = ACCEPTANCE.load_contract(CONTRACT_PATH)
    facts = {
        "outcome": "prepared",
        "authority": "local-only",
        "evidence_sha256": "a" * 64,
    }
    left = ACCEPTANCE.emit_receipt(
        contract=contract,
        canary_id="canary-1",
        runtime_id="antigravity",
        input_payload={"task": "bounded"},
        facts=facts,
        observed_at=100.0,
    )
    right = ACCEPTANCE.emit_receipt(
        contract=contract,
        canary_id="canary-1",
        runtime_id="reference-fixture",
        input_payload={"task": "bounded"},
        facts=facts,
        observed_at=101.0,
    )
    return contract, left, right


def test_saga_acceptance_compares_bounded_semantic_receipts() -> None:
    contract, left, right = _receipts()

    result = ACCEPTANCE.compare_receipts(contract, left, right, evaluated_at=110.0)

    assert result == {
        "schema": "antigravity.saga-acceptance-result.v1",
        "compatible": True,
        "errors": [],
    }


def test_saga_acceptance_compares_bounded_semantic_receipts_rejects_negative_cases() -> None:
    contract, left, right = _receipts()
    cases = []
    missing = copy.deepcopy(right)
    del missing["facts"]["authority"]
    cases.append((left, missing, 110.0))
    stale = copy.deepcopy(right)
    stale["observed_at"] = -1000.0
    cases.append((left, stale, 110.0))
    differently_bound = copy.deepcopy(right)
    differently_bound["input_sha256"] = "b" * 64
    cases.append((left, differently_bound, 110.0))
    disagreement = copy.deepcopy(right)
    disagreement["facts"]["outcome"] = "completed"
    cases.append((left, disagreement, 110.0))
    cases.append((left, left, 110.0))
    same_runtime = copy.deepcopy(right)
    same_runtime["runtime_id"] = left["runtime_id"]
    cases.append((left, same_runtime, 110.0))
    empty_runtime = copy.deepcopy(right)
    empty_runtime["runtime_id"] = ""
    cases.append((left, empty_runtime, 110.0))
    malformed_input = copy.deepcopy(right)
    malformed_input["input_sha256"] = "not-a-digest"
    cases.append((left, malformed_input, 110.0))
    malformed_evidence = copy.deepcopy(right)
    malformed_evidence["facts"]["evidence_sha256"] = "not-a-digest"
    cases.append((left, malformed_evidence, 110.0))
    non_finite = copy.deepcopy(right)
    non_finite["observed_at"] = float("nan")
    cases.append((left, non_finite, 110.0))
    unknown_fact = copy.deepcopy(right)
    unknown_fact["facts"]["unexpected"] = "value"
    cases.append((left, unknown_fact, 110.0))

    for candidate_left, candidate_right, evaluated_at in cases:
        assert ACCEPTANCE.compare_receipts(
            contract,
            candidate_left,
            candidate_right,
            evaluated_at=evaluated_at,
        )["compatible"] is False


def test_acceptance_contract_and_emission_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(ACCEPTANCE.SagaAcceptanceError, match="could not load"):
        ACCEPTANCE.load_contract(missing)
    malformed = tmp_path / "contract.json"
    malformed.write_text("{}", encoding="utf-8")
    with pytest.raises(ACCEPTANCE.SagaAcceptanceError, match="invalid Saga"):
        ACCEPTANCE.load_contract(malformed)

    assert ACCEPTANCE.validate_contract(None) == ["contract must be an object"]
    contract = ACCEPTANCE.load_contract(CONTRACT_PATH)
    for mutation in (
        lambda row: row.update(schema="wrong"),
        lambda row: row.update(contract_id=""),
        lambda row: row.update(required_facts=[]),
        lambda row: row.update(max_age_s=float("nan")),
        lambda row: row.update(extra=True),
    ):
        candidate = copy.deepcopy(contract)
        mutation(candidate)
        assert ACCEPTANCE.validate_contract(candidate)

    invalid_contract = copy.deepcopy(contract)
    invalid_contract["schema"] = "wrong"
    with pytest.raises(ACCEPTANCE.SagaAcceptanceError, match="invalid Saga"):
        ACCEPTANCE.emit_receipt(
            contract=invalid_contract,
            canary_id="canary",
            runtime_id="runtime",
            input_payload={},
            facts={},
            observed_at=1.0,
        )
    with pytest.raises(ACCEPTANCE.SagaAcceptanceError, match="receipt"):
        ACCEPTANCE.emit_receipt(
            contract=contract,
            canary_id="",
            runtime_id="runtime",
            input_payload={},
            facts={"outcome": None, "authority": "local", "evidence_sha256": "bad"},
            observed_at=1.0,
        )


def test_acceptance_receipt_validation_reports_shape_and_binding_errors() -> None:
    contract, left, right = _receipts()
    assert ACCEPTANCE.compare_receipts(contract, None, right, evaluated_at=110.0)["errors"]
    invalid_shape = copy.deepcopy(left)
    invalid_shape["extra"] = True
    assert ACCEPTANCE.compare_receipts(contract, invalid_shape, right, evaluated_at=110.0)["errors"]
    invalid = copy.deepcopy(left)
    invalid.update(schema="wrong", contract_sha256="bad", canary_id="other")
    invalid["facts"]["authority"] = None
    errors = ACCEPTANCE.compare_receipts(contract, invalid, right, evaluated_at=True)["errors"]
    assert any("evaluated_at" in error for error in errors)
    assert any("schema" in error for error in errors)
    assert any("contract binding" in error for error in errors)
