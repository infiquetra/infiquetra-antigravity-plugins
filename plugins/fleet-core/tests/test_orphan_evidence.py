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

ORPHAN = fleet_commons_shim.load("orphan_evidence")
ATTEST = fleet_commons_shim.load("output_attestation")
FIXTURES = Path(__file__).parent / "fixtures" / "orphan-evidence"


def _record(assignment_id: str = "assignment-1", worker_id: str = "worker-1"):
    output = {"terminal_status": "completed", "checks": ["focused"]}
    return {
        "assignment_id": assignment_id,
        "worker_id": worker_id,
        "output": output,
        "attestation": ATTEST.attest_output(
            run_id="run-1",
            assignment_id=assignment_id,
            worker_id=worker_id,
            output=output,
        ),
    }


def test_orphan_evidence_requires_owner_shape_and_run_attestation() -> None:
    evidence = {
        "schema": ORPHAN.EVIDENCE_SCHEMA,
        "run_id": "run-1",
        "records": [_record()],
    }

    assert ORPHAN.validate_evidence(
        evidence,
        expected_run_id="run-1",
        expected_owners={"assignment-1": "worker-1"},
    ) == []
    assert ORPHAN.load_evidence(FIXTURES / "valid.json")["records"] == []


def test_orphan_evidence_requires_owner_shape_and_run_attestation_rejects_negative_cases() -> None:
    valid = _record()
    wrong_owner = copy.deepcopy(valid)
    wrong_owner["worker_id"] = "worker-2"
    replay = copy.deepcopy(valid)
    replay["assignment_id"] = "assignment-2"
    evidence = {
        "schema": ORPHAN.EVIDENCE_SCHEMA,
        "run_id": "run-1",
        "records": [valid, wrong_owner, replay],
    }

    errors = ORPHAN.validate_evidence(
        evidence,
        expected_run_id="run-1",
        expected_owners={"assignment-1": "worker-1", "assignment-2": "worker-2"},
    )
    assert errors
    assert any("wrong owner" in error for error in errors)
    assert any("replays" in error for error in errors)

    missing = {"schema": ORPHAN.EVIDENCE_SCHEMA, "run_id": "run-1", "records": []}
    assert ORPHAN.validate_evidence(
        missing,
        expected_run_id="run-1",
        expected_owners={"assignment-1": "worker-1"},
    )
    with pytest.raises(ORPHAN.OrphanEvidenceError, match="duplicate JSON key"):
        ORPHAN.load_evidence(FIXTURES / "duplicate-schema.json")
