"""Mapped Saga host-capability doctor acceptance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import fleet_doctor as doctor  # noqa: E402

CAPABILITIES = {
    "agy.agent.execution",
    "agy.sequential.isolation",
    "antigravity.plugin.validation",
}


def _report(
    states: dict[str, str],
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...] = (),
) -> dict:
    return doctor.diagnose_states(
        states,
        catalog_digest="a" * 64,
        receipt_sha256="b" * 64,
        known_capabilities=CAPABILITIES,
        required_capabilities=required,
        optional_capabilities=optional,
    )


def test_fleet_doctor_blocks_required_unknown_failed_and_unavailable() -> None:
    for state in ("unknown", "failed", "unavailable"):
        report = _report(
            {
                "agy.agent.execution": state,
                "agy.sequential.isolation": "passed",
                "antigravity.plugin.validation": "passed",
            },
            required=("agy.agent.execution",),
        )
        assert report["state"] == "blocked"
        assert report["blocking_capabilities"] == [
            {"capability": "agy.agent.execution", "state": state}
        ]

    passed = _report(
        {
            "agy.agent.execution": "passed",
            "agy.sequential.isolation": "passed",
            "antigravity.plugin.validation": "passed",
        },
        required=("agy.agent.execution",),
    )
    assert passed["state"] == "passed"


def test_fleet_doctor_blocks_required_unknown_failed_and_unavailable_rejects_negative_cases() -> (
    None
):
    states = {
        "agy.agent.execution": "unavailable",
        "agy.sequential.isolation": "passed",
        "antigravity.plugin.validation": "passed",
    }
    report = _report(
        states,
        required=("agy.agent.execution",),
        optional=("agy.sequential.isolation",),
    )
    assert report["state"] == "blocked"
    assert report["degraded_capabilities"] == []

    with pytest.raises(doctor.FleetDoctorError, match="both required and optional"):
        _report(
            states,
            required=("agy.agent.execution",),
            optional=("agy.agent.execution",),
        )
    with pytest.raises(doctor.FleetDoctorError, match="outside the canonical catalog"):
        _report(states, required=("agy.unknown.capability",))
    with pytest.raises(doctor.FleetDoctorError, match="do not cover"):
        _report({"agy.agent.execution": "passed"}, required=("agy.agent.execution",))
