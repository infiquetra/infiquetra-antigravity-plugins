"""Cross-consumer acceptance tests for proof-carrying lifecycle reconciliation."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lifecycle_obligations as obligations  # noqa: E402
import lifecycle_reconciliation as reconciliation  # noqa: E402
import load_saga_context  # noqa: E402
import manifest_store  # noqa: E402
import outcome  # noqa: E402
import outcome_orchestrator  # noqa: E402
import outcome_spec  # noqa: E402
import outcome_store  # noqa: E402
import transition_receipts as receipts  # noqa: E402


def _contract() -> obligations.ObligationContract:
    return obligations.ObligationContract.from_dict(
        {
            "schema": obligations.SCHEMA_VERSION,
            "contract_id": "shared-route",
            "workstream_id": "issue-14",
            "stored_lifecycle_phases": ["plan", "review", "qa"],
            "off_chain_obligations": [],
            "obligations": [
                {
                    "obligation_id": phase,
                    "kind": "stored-phase",
                    "subject": phase,
                    "requirement": "required",
                    "producer": f"{phase}-producer",
                    "required_evidence": [{"kind": "github-fact"}],
                    "phase": phase,
                }
                for phase in ("plan", "review", "qa")
            ],
        }
    )


def _evidence(
    subject: str,
    evidence_id: str,
    *,
    state: obligations.VerificationState = obligations.VerificationState.VERIFIED,
) -> obligations.Evidence:
    return obligations.Evidence(
        evidence_id=evidence_id,
        kind=obligations.EvidenceKind.GITHUB_FACT,
        subject=subject,
        producer="github",
        reference=f"https://example.invalid/{evidence_id}",
        digest="sha256:" + hashlib.sha256(evidence_id.encode()).hexdigest(),
        verification_state=state,
    )


def _receipt(
    contract: obligations.ObligationContract,
    obligation_id: str,
    *,
    attempt: int = 1,
    state: obligations.VerificationState = obligations.VerificationState.VERIFIED,
    claimed: obligations.SettlementState | None = None,
) -> receipts.TransitionReceipt:
    evidence = _evidence(obligation_id, f"{obligation_id}-{attempt}", state=state)
    return receipts.build_transition_receipt(
        contract=contract,
        transition_id=f"settle-{obligation_id}",
        obligation_id=obligation_id,
        attempt=attempt,
        external_facts=[evidence],
        claimed_settlement=claimed,
    )


def _write_json(root: Path, reference: str, value: dict[str, object]) -> None:
    path = root / reference
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _outcome_node(
    contract_ref: str,
    receipt_refs: list[str],
) -> outcome_spec.Node:
    manifest_input = {"objective": "reconcile"}
    manifest_output = {"changed_paths": ["plugins/saga/scripts/lifecycle_reconciliation.py"]}
    manifest = manifest_store.build_evidence_manifest(
        execution_id="reconcile",
        saga_ref="issue-14",
        assignment_id="reconcile",
        owner_id="issue-14",
        input_value=manifest_input,
        output_value=manifest_output,
        created_at="2026-08-01T00:00:00+00:00",
    )
    return outcome_spec.Node.from_dict(
        {
            "subplot_id": "reconcile",
            "title": "Reconcile lifecycle evidence",
            "kind": "non-code",
            "leaf_saga_id": "issue-14",
            "obligation_contract_ref": contract_ref,
            "transition_receipt_refs": receipt_refs,
            "evidence": {
                "manifest": manifest,
                "manifest_assignment_id": "reconcile",
                "manifest_owner_id": "issue-14",
                "manifest_input": manifest_input,
                "manifest_output": manifest_output,
            },
        }
    )


def test_resume_preserves_satisfied_work_and_routes_earliest_unproven_obligation() -> None:
    contract = _contract()
    plan = _receipt(contract, "plan")
    qa = _receipt(contract, "qa")

    result = reconciliation.reconcile_required_obligations(contract, [qa, plan])

    assert result.obligation_id == "review"
    assert result.settlement_state.value == "unsatisfied"
    assert result.destination == "/review"
    assert result.operator_adjudication_required is False


def test_outcome_loop_and_resume_use_the_same_reconciliation_result(tmp_path: Path) -> None:
    contract = _contract()
    plan = _receipt(contract, "plan")
    contract_ref = "docs/outcomes/issue-14/contract.json"
    receipt_ref = "docs/outcomes/issue-14/plan.json"
    _write_json(tmp_path, contract_ref, contract.to_dict())
    _write_json(tmp_path, receipt_ref, plan.to_dict())

    resume_result = reconciliation.reconcile_repository_refs(tmp_path, contract_ref, [receipt_ref])
    loop_result = load_saga_context.route_earliest_unsettled_required_obligation(
        contract, [plan], repo_root=tmp_path
    )
    outcome_result = outcome_orchestrator.verified_lifecycle_settlement(
        _outcome_node(contract_ref, [receipt_ref]), repo_root=tmp_path
    )
    node = _outcome_node(contract_ref, [receipt_ref])
    outcome_status = outcome.status(
        tmp_path,
        "issue-14",
        spec=outcome_spec.OutcomeSpec(
            outcome_id="issue-14",
            objective="Reconcile lifecycle evidence",
            nodes=[node],
        ),
        store=outcome_store.Store(root=tmp_path / "store").ensure(),
    )

    expected = {
        "complete": False,
        "obligation_id": "review",
        "settlement_state": "unsatisfied",
        "destination": "/review",
    }
    assert {key: resume_result.to_dict()[key] for key in expected} == expected
    assert loop_result == expected
    assert outcome_result is not None and outcome_result.satisfied is False
    assert outcome_result.evidence["reconciliation"] == resume_result.to_dict()
    assert outcome_status["reconciliations"]["reconcile"] == resume_result.to_dict()


def test_conflict_stops_for_operator_adjudication_regardless_of_receipt_order() -> None:
    contract = _contract()
    satisfied = _receipt(contract, "plan")
    conflicting = _receipt(
        contract,
        "plan",
        attempt=2,
        claimed=obligations.SettlementState.UNSATISFIED,
    )
    assert conflicting.settlement_state.value == "conflicting"

    first = reconciliation.reconcile_required_obligations(contract, [satisfied, conflicting])
    second = reconciliation.reconcile_required_obligations(contract, [conflicting, satisfied])

    assert first == second
    assert first.obligation_id == "plan"
    assert first.settlement_state.value == "conflicting"
    assert first.operator_adjudication_required is True


def test_retry_is_read_only_and_does_not_duplicate_canonical_evidence(tmp_path: Path) -> None:
    contract = _contract()
    plan = _receipt(contract, "plan")
    contract_ref = "docs/outcomes/issue-14/contract.json"
    receipt_ref = "docs/outcomes/issue-14/plan.json"
    _write_json(tmp_path, contract_ref, contract.to_dict())
    _write_json(tmp_path, receipt_ref, plan.to_dict())
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    first = reconciliation.reconcile_repository_refs(tmp_path, contract_ref, [receipt_ref])
    second = reconciliation.reconcile_repository_refs(tmp_path, contract_ref, [receipt_ref])
    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert first == second
    assert after == before


def test_narration_or_unrelated_github_completion_cannot_settle_required_evidence() -> None:
    contract = obligations.ObligationContract.from_dict(
        {
            "schema": obligations.SCHEMA_VERSION,
            "contract_id": "canonical-output",
            "workstream_id": "issue-14",
            "stored_lifecycle_phases": ["work"],
            "off_chain_obligations": [],
            "obligations": [
                {
                    "obligation_id": "work",
                    "kind": "stored-phase",
                    "subject": "work",
                    "requirement": "required",
                    "producer": "worker",
                    "required_evidence": [{"kind": "canonical-output"}],
                    "phase": "work",
                }
            ],
        }
    )
    github_only = receipts.build_transition_receipt(
        contract=contract,
        transition_id="narrated-done",
        obligation_id="work",
        attempt=1,
        external_facts=[_evidence("work", "closed-issue")],
    )

    result = reconciliation.reconcile_required_obligations(contract, [github_only])

    assert result.complete is False
    assert result.obligation_id == "work"
    assert result.settlement_state.value == "unsatisfied"
    assert result.destination == "/work"


def test_outcome_with_no_receipts_reports_the_same_earliest_obligation(tmp_path: Path) -> None:
    contract = _contract()
    contract_ref = "docs/outcomes/issue-14/contract.json"
    _write_json(tmp_path, contract_ref, contract.to_dict())

    resume_result = reconciliation.reconcile_repository_refs(tmp_path, contract_ref, [])
    outcome_result = outcome_orchestrator.verified_lifecycle_settlement(
        _outcome_node(contract_ref, []), repo_root=tmp_path
    )

    assert resume_result.obligation_id == "plan"
    assert outcome_result is not None and outcome_result.satisfied is False
    assert outcome_result.evidence["reconciliation"] == resume_result.to_dict()


def test_unknown_evidence_is_unavailable_and_receipt_order_is_stable() -> None:
    contract = _contract()
    unknown = _receipt(
        contract,
        "plan",
        state=obligations.VerificationState.UNKNOWN,
    )
    missing = receipts.build_transition_receipt(
        contract=contract,
        transition_id="missing-plan",
        obligation_id="plan",
        attempt=2,
    )

    first = reconciliation.reconcile_required_obligations(contract, [unknown, missing])
    second = reconciliation.reconcile_required_obligations(contract, [missing, unknown])

    assert first == second
    assert first.settlement_state.value == "unavailable"


def test_cli_prints_the_shared_result_without_writing(tmp_path: Path, capsys: object) -> None:
    contract = _contract()
    contract_ref = "docs/outcomes/issue-14/contract.json"
    _write_json(tmp_path, contract_ref, contract.to_dict())
    before = (tmp_path / contract_ref).read_bytes()

    exit_code = reconciliation.main(["--repo-root", str(tmp_path), "--contract", contract_ref])
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    assert exit_code == 0
    assert json.loads(captured.out)["obligation_id"] == "plan"
    assert (tmp_path / contract_ref).read_bytes() == before


def test_unknown_obligation_receipt_and_noncanonical_refs_fail_closed(tmp_path: Path) -> None:
    contract = _contract()
    foreign_contract = obligations.ObligationContract.from_dict(
        {
            "schema": obligations.SCHEMA_VERSION,
            "contract_id": contract.contract_id,
            "workstream_id": contract.workstream_id,
            "stored_lifecycle_phases": ["work"],
            "off_chain_obligations": [],
            "obligations": [
                {
                    "obligation_id": "unknown",
                    "kind": "stored-phase",
                    "subject": "unknown",
                    "requirement": "required",
                    "producer": "worker",
                    "required_evidence": [{"kind": "github-fact"}],
                    "phase": "work",
                }
            ],
        }
    )
    unknown = _receipt(foreign_contract, "unknown")
    with pytest.raises(ValueError, match="has no obligation"):
        reconciliation.reconcile_required_obligations(contract, [unknown])

    contract_ref = "docs/outcomes/issue-14/contract.json"
    _write_json(tmp_path, contract_ref, contract.to_dict())
    with pytest.raises(ValueError, match="canonical repository-relative"):
        reconciliation.reconcile_repository_refs(
            tmp_path, "docs/outcomes/issue-14/../issue-14/contract.json", []
        )
