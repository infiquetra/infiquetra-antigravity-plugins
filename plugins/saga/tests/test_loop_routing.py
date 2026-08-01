from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lifecycle_obligations as obligations  # noqa: E402
import transition_receipts as receipts  # noqa: E402


def _load():
    path = SCRIPTS / "load_saga_context.py"
    spec = importlib.util.spec_from_file_location("load_saga_context_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _contract() -> obligations.ObligationContract:
    return obligations.ObligationContract.from_dict(
        {
            "schema": obligations.SCHEMA_VERSION,
            "contract_id": "loop-contract",
            "workstream_id": "issue-15",
            "stored_lifecycle_phases": ["plan", "work"],
            "off_chain_obligations": [],
            "obligations": [
                {
                    "obligation_id": "plan-ready",
                    "kind": "stored-phase",
                    "subject": "plan",
                    "requirement": "required",
                    "producer": "planner",
                    "required_evidence": [{"kind": "github-fact"}],
                    "phase": "plan",
                },
                {
                    "obligation_id": "work-ready",
                    "kind": "stored-phase",
                    "subject": "work",
                    "requirement": "required",
                    "producer": "worker",
                    "required_evidence": [{"kind": "github-fact"}],
                    "phase": "work",
                },
            ],
        }
    )


def _evidence(subject: str, evidence_id: str) -> obligations.Evidence:
    return obligations.Evidence(
        evidence_id=evidence_id,
        kind=obligations.EvidenceKind.GITHUB_FACT,
        subject=subject,
        producer="fixture",
        reference=f"https://example.invalid/{subject}",
        digest="sha256:" + "a" * 64,
        verification_state=obligations.VerificationState.VERIFIED,
    )


def _receipt(contract: obligations.ObligationContract, obligation_id: str, subject: str):
    return receipts.build_transition_receipt(
        contract=contract,
        transition_id=f"settle-{obligation_id}",
        obligation_id=obligation_id,
        attempt=1,
        external_facts=[_evidence(subject, f"evidence-{obligation_id}")],
    )


def test_loop_routes_to_earliest_unsettled_required_obligation_idempotently() -> None:
    module = _load()
    contract = _contract()
    first = _receipt(contract, "plan-ready", "plan")
    expected = {
        "complete": False,
        "obligation_id": "work-ready",
        "settlement_state": "unsatisfied",
        "destination": "/work",
    }
    assert module.route_earliest_unsettled_required_obligation(contract, [first]) == expected
    assert module.route_earliest_unsettled_required_obligation(contract, [first]) == expected


def test_loop_routes_to_earliest_unsettled_required_obligation_idempotently_rejects_negative_cases() -> (
    None
):
    module = _load()
    contract = _contract()
    later = _receipt(contract, "work-ready", "work")
    result = module.route_earliest_unsettled_required_obligation(contract, [later])
    assert result["obligation_id"] == "plan-ready"
    duplicate = receipts.TransitionReceipt.from_dict(later.to_dict())
    result = module.route_earliest_unsettled_required_obligation(contract, [later, duplicate])
    assert result["obligation_id"] == "plan-ready"
