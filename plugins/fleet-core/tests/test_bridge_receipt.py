from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

BRIDGE = fleet_commons_shim.load("bridge_receipt")
DIGEST = "a" * 64


def _receipt():
    return BRIDGE.emit_portable_receipt(
        request_id="request-1",
        producer="dispatcher",
        requested_facts={"model": "configured", "execution": "requested"},
        observed_facts={
            "model": {
                "state": "passed",
                "value": "gemini-3.1-pro",
                "observer": "host-probe",
                "evidence_sha256": DIGEST,
            },
            "execution": {
                "state": "unknown",
                "observer": "host-probe",
                "evidence_sha256": DIGEST,
            },
        },
        evidence=[DIGEST],
    )


def test_bridge_receipt_distinguishes_requested_observed_and_unknown() -> None:
    receipt = _receipt()

    assert BRIDGE.validate_portable_receipt(receipt) == []
    assert receipt["requested_facts"]["execution"] == "requested"
    assert receipt["observed_facts"]["execution"] == {
        "state": "unknown",
        "observer": "host-probe",
        "evidence_sha256": DIGEST,
    }


def test_bridge_receipt_distinguishes_requested_observed_and_unknown_rejects_negative_cases() -> (
    None
):
    malformed = _receipt()
    malformed["observed_facts"]["model"]["evidence_sha256"] = "not-a-digest"
    self_attested = _receipt()
    self_attested["observed_facts"]["model"]["observer"] = "dispatcher"
    invented_unknown = _receipt()
    invented_unknown["observed_facts"]["execution"]["value"] = "completed"
    unbound = _receipt()
    unbound["observed_facts"]["model"]["evidence_sha256"] = "b" * 64

    for receipt in (malformed, self_attested, invented_unknown, unbound):
        assert BRIDGE.validate_portable_receipt(copy.deepcopy(receipt))
