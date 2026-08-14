"""Output attestation contract tests (orphan-fencing refactor, U7).

The orphan-evidence module was deleted with the lease broker in U7; the surviving
attestation surface is `output_attestation.py`. These tests prove a worker's output is
accepted only when ownership, expected shape, and attestation bind it to the originating
run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

ATTEST = fleet_commons_shim.load("output_attestation")


def test_output_attestation_requires_owner_shape_and_run_binding() -> None:
    attestation = ATTEST.attest_output(
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done", "result": 42},
    )
    errors = ATTEST.validate_attestation(
        attestation,
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done", "result": 42},
    )
    assert errors == []


def test_output_attestation_requires_owner_shape_and_run_binding_rejects_negative_cases() -> None:
    attestation = ATTEST.attest_output(
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    )
    assert ATTEST.validate_attestation(
        None,
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    ) == ["attestation must be an object"]

    assert ATTEST.validate_attestation(
        {**attestation, "schema": "bad"},
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    ) == ["attestation schema is invalid"]

    assert ATTEST.validate_attestation(
        {**attestation, "attester": "rogue"},
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    ) == ["output is not attested by the run ledger"]

    assert ATTEST.validate_attestation(
        attestation,
        run_id="run-2",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    ) == [
        "attestation run_id does not match expected ownership",
        "attestation binding does not match its content",
    ]

    assert ATTEST.validate_attestation(
        {**attestation, "binding_sha256": "invalid"},
        run_id="run-1",
        assignment_id="unit-a",
        worker_id="worker-1",
        output={"status": "done"},
    ) == ["attestation binding_sha256 is invalid"]
