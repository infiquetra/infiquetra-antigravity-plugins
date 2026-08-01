from __future__ import annotations

import os
import sys
from pathlib import Path

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

AUDIT = fleet_commons_shim.load("delegation_audit")
STATE = fleet_commons_shim.load("delegation_state")


def _assignment(assignment_id: str, worker_id: str = "worker-1") -> dict[str, str]:
    return {"assignment_id": assignment_id, "worker_id": worker_id, "run_id": "run-1"}


def _completion(
    assignment_id: str,
    *,
    worker_id: str = "worker-1",
    event_id: str | None = None,
) -> dict[str, str]:
    return {
        "assignment_id": assignment_id,
        "worker_id": worker_id,
        "run_id": "run-1",
        "event_id": event_id or f"event-{assignment_id}",
        "output_sha256": "a" * 64,
    }


def test_delegation_audit_detects_missing_duplicate_and_wrong_owner_evidence(
    tmp_path: Path,
) -> None:
    assignments = [_assignment("a"), _assignment("b", "worker-2")]
    completions = [_completion("a"), _completion("b", worker_id="worker-2")]

    receipt = AUDIT.audit_assignment_evidence(assignments, completions)
    assert receipt["complete"] is True
    assert receipt["problems"] == []

    STATE.arm("agy", "session-1", "dispatcher", root=tmp_path, now=1.0)
    assert STATE.active("session-1", root=tmp_path, now=2.0) is not None
    STATE.disarm("session-1", root=tmp_path, now=3.0)
    assert STATE.active("session-1", root=tmp_path, now=4.0) is None


def test_delegation_audit_detects_missing_duplicate_and_wrong_owner_evidence_rejects_negative_cases() -> None:
    assignments = [_assignment("a"), _assignment("b", "worker-2")]
    completions = [
        _completion("a", worker_id="wrong", event_id="replay"),
        _completion("a", event_id="replay"),
        _completion("unknown"),
    ]

    receipt = AUDIT.audit_assignment_evidence(assignments, completions)

    assert receipt["complete"] is False
    rendered = "\n".join(receipt["problems"])
    assert "wrong owner" in rendered
    assert "duplicate completion" in rendered
    assert "replayed completion" in rendered
    assert "unknown assignment" in rendered
    assert "missing completion: b" in rendered
