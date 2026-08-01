"""Receipt-backed deliberation contract tests."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

PLUGIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import deliberation as D  # noqa: E402, N812


def manifest(count: int = 6, *, sequential: bool = False) -> dict[str, Any]:
    states = {
        "agy.model.selection": "passed",
        "agy.agent.execution": "unavailable" if sequential else "passed",
        "agy.sequential.isolation": "passed" if sequential else "unknown",
    }
    return {
        "schema": D.MANIFEST_SCHEMA,
        "manifest_id": "ideate-broad-001",
        "phase": "ideate",
        "strategies": [
            {
                "strategy_id": f"frame-{number}",
                "role": f"Frame {number}",
                "applicable": True,
                "applicability_reason": "broad ideation requires every frame",
                "applicability_rule": "broad",
                "operator_decision_ref": "",
            }
            for number in range(1, count + 1)
        ],
        "minimum_coverage": count,
        "requested": {"model": "gemini-3.1-pro", "effort": "high"},
        "allowed_tools": ["read", "search"],
        "execution_bounds": {"max_workers": count, "max_turns_per_strategy": 3},
        "expected_result_fields": ["summary", "claims"],
        "convergence": {
            "rule": "adjudicated-synthesis",
            "preserve_disagreement": True,
        },
        "recovery": {"max_attempts_per_strategy": 2},
        "escalation": {"mode": "fixed", "escalated_model": "", "triggers": []},
        "host_capability_receipt": {
            "reference": "docs/evidence/host.json",
            "sha256": "sha256:" + ("a" * 64),
            "states": states,
        },
    }


def result(
    number: int,
    *,
    mode: str = "native-agent",
    attempt: int = 1,
    status: str = "succeeded",
) -> dict[str, Any]:
    isolation = "native-agent" if mode == "native-agent" else "isolated-sequential"
    return {
        "execution_id": f"execution-{number}-{attempt}",
        "strategy_id": f"frame-{number}",
        "attempt": attempt,
        "mode": mode,
        "status": status,
        "requested": {
            "model": "gemini-3.1-pro",
            "effort": "high",
            "tools": ["read"],
        },
        "observed": {
            "model": D.UNKNOWN,
            "effort": D.UNKNOWN,
            "tools": D.UNKNOWN,
            "isolation": isolation,
            "worker_count": D.UNKNOWN,
        },
        "output": {"summary": f"result {number}", "claims": [f"claim-{number}"]},
        "evidence_refs": [f"evidence-{number}"],
    }


def convergence(*, disagreement: bool = False) -> dict[str, Any]:
    return {
        "summary": "surviving synthesis" if disagreement else "",
        "disagreements": (
            [
                {
                    "topic": "tradeoff",
                    "strategy_ids": ["frame-1", "frame-2"],
                    "evidence_refs": ["evidence-1", "evidence-2"],
                }
            ]
            if disagreement
            else []
        ),
        "adjudication": "Frame 1 prevails because its repository evidence is current."
        if disagreement
        else "",
    }


def fixed_escalation() -> dict[str, Any]:
    return {"selected_model": "gemini-3.1-pro", "trigger_evidence": []}


def evaluate(contract: dict[str, Any], rows: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return D.evaluate_deliberation(
        contract,
        rows,
        convergence=kwargs.get("convergence", convergence()),
        escalation=kwargs.get("escalation", fixed_escalation()),
    )


def test_reference_schema_and_runtime_accept_the_same_manifest() -> None:
    schema = json.loads(
        (PLUGIN_ROOT / "references" / "deliberation-manifest-schema.json").read_text()
    )
    contract = manifest()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    assert D.DeliberationManifest.from_dict(contract).to_dict() == contract


def test_fixture_matrix_names_every_required_case() -> None:
    cases = json.loads(
        (Path(__file__).parent / "fixtures" / "deliberation" / "cases.json").read_text()
    )
    assert {row["case_id"] for row in cases} == {
        "one-call-six-headings",
        "six-isolated-sequential",
        "duplicate-strategy-ids",
        "malformed-results",
        "failed-recovery",
        "unknown-model-readback",
        "operator-authorized-applicability",
        "preserved-disagreement",
        "cheap-first-escalation",
    }


def test_one_response_with_six_headings_counts_as_one_execution() -> None:
    one_call = result(1)
    one_call["output"]["summary"] = "\n".join(f"## Frame {number}" for number in range(1, 7))

    receipt = evaluate(manifest(), [one_call])

    assert receipt["complete"] is False
    assert receipt["coverage"] == {
        "required": 6,
        "accepted": 1,
        "missing_strategy_ids": [f"frame-{number}" for number in range(2, 7)],
        "exhausted_strategy_ids": [],
    }
    assert len(receipt["recovery_requests"]) == 5


def test_six_isolated_sequential_results_satisfy_six_strategy_contract() -> None:
    contract = manifest(sequential=True)
    rows = [result(number, mode="isolated-sequential") for number in range(1, 7)]

    receipt = evaluate(contract, rows)

    assert receipt["complete"] is True
    assert receipt["coverage"]["accepted"] == 6
    assert receipt["observed"]["worker_count"] == 6
    assert receipt["observed"]["models"] == [D.UNKNOWN]
    D.validate_receipt(receipt)


def test_duplicate_execution_ids_cannot_count_twice() -> None:
    rows = [result(1), result(2)]
    rows[1]["execution_id"] = rows[0]["execution_id"]

    receipt = evaluate(manifest(count=2), rows)

    assert receipt["complete"] is False
    assert receipt["coverage"]["accepted"] == 0
    assert "duplicate execution IDs" in "\n".join(receipt["issues"])


def test_duplicate_strategy_results_do_not_replace_missing_coverage() -> None:
    duplicate = result(1, attempt=2)

    receipt = evaluate(manifest(count=2), [result(1), duplicate])

    assert receipt["complete"] is False
    assert receipt["coverage"]["accepted"] == 1
    assert receipt["coverage"]["missing_strategy_ids"] == ["frame-2"]
    assert any("duplicate strategy coverage" in item for item in receipt["issues"])
    assert receipt["recovery_requests"][0]["strategy_id"] == "frame-2"


def test_malformed_and_failed_results_recover_only_within_bound() -> None:
    malformed = result(1)
    malformed["output"] = None
    failed = result(1, attempt=2, status="failed")
    failed["output"] = None

    receipt = evaluate(manifest(count=1), [malformed, failed])

    assert receipt["complete"] is False
    assert receipt["recovery_requests"] == []
    assert receipt["coverage"]["exhausted_strategy_ids"] == ["frame-1"]
    assert any("successful strategy result needs an output" in item for item in receipt["issues"])


def test_malformed_attempts_consume_the_declared_retry_bound() -> None:
    first = result(1)
    first["output"] = None
    second = result(1, attempt=2)
    second["output"] = None

    receipt = evaluate(manifest(count=1), [first, second])

    assert receipt["recovery_requests"] == []
    assert receipt["coverage"]["exhausted_strategy_ids"] == ["frame-1"]


def test_requested_values_do_not_become_observed_values() -> None:
    receipt = evaluate(manifest(count=1), [result(1)])

    assert receipt["requested"]["model"] == "gemini-3.1-pro"
    assert receipt["observed"]["models"] == [D.UNKNOWN]
    assert receipt["observed"]["efforts"] == [D.UNKNOWN]
    assert receipt["observed"]["tools"] == D.UNKNOWN


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("model", "gpt-5", "observed model"),
        ("effort", "low", "observed effort"),
        ("isolation", "isolated-sequential", "observed isolation"),
        ("worker_count", 2, "exactly one observed worker"),
    ],
)
def test_observed_execution_mismatches_do_not_count(
    field: str, value: object, message: str
) -> None:
    row = result(1)
    row["observed"][field] = value

    receipt = evaluate(manifest(count=1), [row])

    assert receipt["complete"] is False
    assert any(message in issue for issue in receipt["issues"])


def test_incomplete_coverage_cannot_carry_convergence_output() -> None:
    with pytest.raises(D.DeliberationError, match="cannot carry convergence"):
        evaluate(
            manifest(count=2),
            [result(1)],
            convergence={"summary": "premature", "disagreements": [], "adjudication": ""},
        )


def test_reduced_applicability_requires_a_rule_or_operator_decision() -> None:
    contract = manifest(count=2)
    contract["strategies"][1].update(
        {
            "applicable": False,
            "applicability_reason": "operator narrowed the review to one component",
            "applicability_rule": "",
            "operator_decision_ref": "decision-42",
        }
    )
    contract["minimum_coverage"] = 1

    assert evaluate(contract, [result(1)])["complete"] is True

    contract["strategies"][1]["operator_decision_ref"] = ""
    with pytest.raises(D.DeliberationError, match="applicability rule or operator decision"):
        D.DeliberationManifest.from_dict(contract)


def test_convergence_preserves_disagreement_evidence_and_adjudication() -> None:
    receipt = evaluate(
        manifest(count=2),
        [result(1), result(2)],
        convergence=convergence(disagreement=True),
    )

    assert receipt["convergence"]["disagreements"][0]["evidence_refs"] == [
        "evidence-1",
        "evidence-2",
    ]
    assert receipt["convergence"]["adjudication"]

    invalid = convergence(disagreement=True)
    invalid["adjudication"] = ""
    with pytest.raises(D.DeliberationError, match="requires an adjudication"):
        evaluate(manifest(count=2), [result(1), result(2)], convergence=invalid)


def test_cheap_first_escalation_requires_declared_trigger_evidence() -> None:
    contract = manifest(count=1)
    contract["requested"]["model"] = "gemini-3.5-flash"
    contract["escalation"] = {
        "mode": "cheap-first",
        "escalated_model": "gemini-3.1-pro",
        "triggers": ["conformance-failed", "coverage-missing"],
    }
    row = result(1)

    receipt = evaluate(
        contract,
        [row],
        escalation={
            "selected_model": "gemini-3.1-pro",
            "trigger_evidence": ["conformance-failed"],
        },
    )
    assert receipt["escalation"]["trigger_evidence"] == ["conformance-failed"]

    with pytest.raises(D.DeliberationError, match="declared trigger evidence"):
        evaluate(
            contract,
            [row],
            escalation={"selected_model": "gemini-3.1-pro", "trigger_evidence": []},
        )


def test_receipt_identity_detects_tampering() -> None:
    receipt = evaluate(manifest(count=1), [result(1)])
    changed = copy.deepcopy(receipt)
    changed["complete"] = False

    with pytest.raises(D.DeliberationError, match="does not match"):
        D.validate_receipt(changed)
