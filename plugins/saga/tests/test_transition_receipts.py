"""Contract, evaluation, and persistence tests for transition_receipts.py."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lifecycle_obligations as O  # noqa: E402, N812
import transition_receipts as M  # noqa: E402, N812

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "lifecycle-obligations"
    / "valid-contract.json"
)


def _contract() -> O.ObligationContract:
    return O.ObligationContract.from_dict(
        json.loads(FIXTURE.read_text(encoding="utf-8"))
    )


def _repository_evidence(
    tmp_path: Path,
    evidence_id: str,
    kind: str,
    producer: str,
    *,
    subject: str = "issue-21",
) -> O.Evidence:
    reference = Path("docs") / f"{evidence_id}.json"
    target = tmp_path / reference
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(evidence_id, encoding="utf-8")
    return O.Evidence.from_dict(
        {
            "evidence_id": evidence_id,
            "kind": kind,
            "subject": subject,
            "producer": producer,
            "reference": reference.as_posix(),
            "digest": "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest(),
            "verification_state": "verified",
            "assertion": "",
        }
    )


def _github_fact() -> O.Evidence:
    return O.Evidence.from_dict(
        {
            "evidence_id": "github-fact",
            "kind": "github-fact",
            "subject": "issue-21",
            "producer": "github",
            "reference": "https://github.com/infiquetra/repo/issues/21",
            "digest": "sha256:" + hashlib.sha256(b"closed").hexdigest(),
            "verification_state": "verified",
            "assertion": "closed",
        }
    )


def _receipt(tmp_path: Path) -> M.TransitionReceipt:
    return M.build_transition_receipt(
        contract=_contract(),
        transition_id="work-to-qa",
        obligation_id="work-proof",
        attempt=1,
        input_refs=[
            _repository_evidence(tmp_path, "input", "input", "planner")
        ],
        operator_decisions=[
            _repository_evidence(
                tmp_path,
                "decision",
                "operator-decision",
                "operator",
            )
        ],
        execution_receipts=[
            _repository_evidence(
                tmp_path,
                "execution",
                "execution-receipt",
                "runner",
            )
        ],
        canonical_outputs=[
            _repository_evidence(
                tmp_path,
                "output",
                "canonical-output",
                "work-agent",
            )
        ],
        check_results=[
            _repository_evidence(tmp_path, "check", "check-result", "pytest"),
            _repository_evidence(tmp_path, "qa", "qa-result", "qa-agent"),
        ],
        review_findings=[
            _repository_evidence(
                tmp_path,
                "review",
                "review-finding",
                "reviewer",
            )
        ],
        lifecycle_evidence=[
            _repository_evidence(
                tmp_path,
                "lifecycle",
                "lifecycle-state",
                "saga",
            )
        ],
        external_facts=[_github_fact()],
        repo_root=tmp_path,
    )


def test_receipt_binds_every_category_and_round_trips(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    assert receipt.settlement_state is O.SettlementState.SATISFIED
    assert receipt.claimed_settlement is O.SettlementState.SATISFIED
    assert M.TransitionReceipt.from_dict(receipt.to_dict()).to_json() == receipt.to_json()
    assert all(
        category in receipt.to_dict()
        for category in (
            "input_refs",
            "operator_decisions",
            "execution_receipts",
            "canonical_outputs",
            "check_results",
            "review_findings",
            "lifecycle_evidence",
            "external_facts",
        )
    )


def test_reference_schemas_validate_current_contract_and_receipt(tmp_path: Path) -> None:
    contract_schema = json.loads(
        (ROOT / "references" / "lifecycle-obligation-schema.json").read_text(
            encoding="utf-8"
        )
    )
    receipt_schema = json.loads(
        (ROOT / "references" / "transition-receipt-schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(contract_schema)
    Draft202012Validator.check_schema(receipt_schema)
    Draft202012Validator(contract_schema).validate(_contract().to_dict())
    Draft202012Validator(receipt_schema).validate(_receipt(tmp_path).to_dict())

    invalid = _contract().to_dict()
    invalid["contract_id"] = "."
    with pytest.raises(ValidationError):
        Draft202012Validator(contract_schema).validate(invalid)


def test_receipt_identity_is_stable_for_unchanged_inputs(tmp_path: Path) -> None:
    first = _receipt(tmp_path)
    second = _receipt(tmp_path)
    assert first.receipt_id == second.receipt_id
    assert first.to_json() == second.to_json()


def test_deserialized_receipt_identity_cannot_be_forged(tmp_path: Path) -> None:
    data = _receipt(tmp_path).to_dict()
    data["receipt_id"] = "tr-forged"
    with pytest.raises(M.TransitionReceiptError, match="identity mismatch"):
        M.TransitionReceipt.from_dict(data)


def test_claimed_success_cannot_override_computed_settlement(tmp_path: Path) -> None:
    receipt = M.build_transition_receipt(
        contract=_contract(),
        transition_id="work-to-qa",
        obligation_id="work-proof",
        attempt=1,
        claimed_settlement="satisfied",
        external_facts=[_github_fact()],
        repo_root=tmp_path,
    )
    assert receipt.claimed_settlement is O.SettlementState.SATISFIED
    assert receipt.settlement_state is O.SettlementState.CONFLICTING
    assert "disagrees with computed settlement" in receipt.settlement_reasons[-1]


def test_missing_or_unknown_input_identity_prevents_satisfied_receipt(
    tmp_path: Path,
) -> None:
    input_evidence = _repository_evidence(tmp_path, "input", "input", "planner")
    (tmp_path / input_evidence.reference).unlink()
    missing = M.build_transition_receipt(
        contract=_contract(),
        transition_id="github-transition",
        obligation_id="github-closed",
        attempt=1,
        input_refs=[input_evidence],
        external_facts=[_github_fact()],
        claimed_settlement="satisfied",
        repo_root=tmp_path,
    )
    assert missing.settlement_state is O.SettlementState.CONFLICTING
    assert "missing repository evidence" in missing.settlement_reasons[0]

    unknown_input = replace(
        input_evidence,
        verification_state=O.VerificationState.UNKNOWN,
    )
    unavailable = M.build_transition_receipt(
        contract=_contract(),
        transition_id="github-transition",
        obligation_id="github-closed",
        attempt=1,
        input_refs=[unknown_input],
        external_facts=[_github_fact()],
        repo_root=tmp_path,
    )
    assert unavailable.settlement_state is O.SettlementState.UNAVAILABLE


def test_serialized_receipt_is_recomputed_against_contract(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    assert (
        M.evaluate_transition_receipt(receipt, _contract(), repo_root=tmp_path).state
        is O.SettlementState.SATISFIED
    )
    forged = replace(receipt, settlement_state=O.SettlementState.DEGRADED)
    assert (
        M.evaluate_transition_receipt(forged, _contract(), repo_root=tmp_path).state
        is O.SettlementState.CONFLICTING
    )


def test_write_is_idempotent_and_does_not_duplicate_receipts(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    first = M.write_transition_receipt(tmp_path, "outcome-21", receipt)
    second = M.write_transition_receipt(tmp_path, "outcome-21", receipt)
    assert first == second
    assert list(first.parent.glob("*.json")) == [first]


def test_write_rejects_different_content_at_the_same_identity(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    M.write_transition_receipt(tmp_path, "outcome-21", receipt)
    divergent = replace(receipt, settlement_reasons=("different",))
    with pytest.raises(M.TransitionReceiptConflictError, match="different content"):
        M.write_transition_receipt(tmp_path, "outcome-21", divergent)
    assert M.TransitionReceipt.from_dict(
        json.loads(
            M.receipt_path(tmp_path, "outcome-21", receipt.receipt_id).read_text(
                encoding="utf-8"
            )
        )
    ) == receipt


def test_direct_receipt_object_cannot_bypass_schema_validation(tmp_path: Path) -> None:
    receipt = replace(_receipt(tmp_path), schema="saga.transition-receipt.v2")
    with pytest.raises(M.TransitionReceiptError, match="unsupported transition receipt schema"):
        M.write_transition_receipt(tmp_path, "outcome-21", receipt)


@pytest.mark.parametrize("schema", [None, "saga.transition-receipt.v2"])
def test_schema_less_and_unknown_receipts_fail_closed(
    tmp_path: Path,
    schema: str | None,
) -> None:
    data = _receipt(tmp_path).to_dict()
    if schema is None:
        data.pop("schema")
    else:
        data["schema"] = schema
    with pytest.raises(M.TransitionReceiptError, match="unsupported transition receipt schema"):
        M.TransitionReceipt.from_dict(data)


def test_missing_category_and_wrong_category_kind_fail_closed(tmp_path: Path) -> None:
    data = _receipt(tmp_path).to_dict()
    data.pop("review_findings")
    with pytest.raises(M.TransitionReceiptError, match="requires review_findings"):
        M.TransitionReceipt.from_dict(data)

    data = _receipt(tmp_path).to_dict()
    data["review_findings"] = data["execution_receipts"]
    with pytest.raises(M.TransitionReceiptError, match="review_findings cannot contain"):
        M.TransitionReceipt.from_dict(data)


@pytest.mark.parametrize("value", ["../outcome", "a/b", "", "."])
def test_receipt_destination_rejects_unsafe_outcome_ids(tmp_path: Path, value: str) -> None:
    with pytest.raises(M.TransitionReceiptError, match="outcome_id must be a slug"):
        M.receipt_path(tmp_path, value, "tr-valid")
