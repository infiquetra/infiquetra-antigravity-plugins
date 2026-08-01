#!/usr/bin/env python3
"""Read-only Saga diagnosis over a validated Fleet Core capability receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import host_capability_gate

REPORT_SCHEMA = "antigravity.saga-capability-diagnosis.v1"
BLOCKING_STATES = frozenset({"failed", "unknown", "unavailable"})
KNOWN_STATES = frozenset({"passed", *BLOCKING_STATES})


class FleetDoctorError(ValueError):
    """Capability evidence cannot support a Saga dispatch decision."""


def diagnose(
    receipt_path: Path,
    *,
    required_capabilities: Sequence[str],
    optional_capabilities: Sequence[str] = (),
) -> dict[str, Any]:
    """Load strict Fleet Core evidence and diagnose declared requirements."""

    catalog, receipt, states = host_capability_gate.load_capability_evidence(receipt_path)
    receipt_sha256 = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    return diagnose_states(
        states,
        catalog_digest=str(receipt["catalog_digest"]),
        receipt_sha256=receipt_sha256,
        known_capabilities={row["id"] for row in catalog["capabilities"]},
        required_capabilities=required_capabilities,
        optional_capabilities=optional_capabilities,
    )


def diagnose_states(
    states: Mapping[str, str],
    *,
    catalog_digest: str,
    receipt_sha256: str,
    known_capabilities: set[str],
    required_capabilities: Sequence[str],
    optional_capabilities: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a bounded report from sanitized capability IDs, states, and digests."""

    required = _unique_ids(required_capabilities, "required_capabilities")
    optional = _unique_ids(optional_capabilities, "optional_capabilities")
    if set(required) & set(optional):
        raise FleetDoctorError("a capability cannot be both required and optional")
    requested = set(required) | set(optional)
    unknown_ids = requested - known_capabilities
    if unknown_ids:
        raise FleetDoctorError("diagnosis names capabilities outside the canonical catalog")
    if set(states) != known_capabilities:
        raise FleetDoctorError("sanitized states do not cover the canonical capability set")
    if any(state not in KNOWN_STATES for state in states.values()):
        raise FleetDoctorError("sanitized receipt contains an invalid capability state")
    _digest(catalog_digest, "catalog_digest")
    _digest(receipt_sha256, "receipt_sha256")

    blocking = [
        {"capability": capability, "state": states[capability]}
        for capability in required
        if states[capability] in BLOCKING_STATES
    ]
    degraded = [
        {"capability": capability, "state": states[capability]}
        for capability in optional
        if states[capability] in BLOCKING_STATES
    ]
    return {
        "schema": REPORT_SCHEMA,
        "state": "blocked" if blocking else ("degraded" if degraded else "passed"),
        "catalog_digest": catalog_digest,
        "receipt_sha256": receipt_sha256,
        "required_capabilities": list(required),
        "optional_capabilities": list(optional),
        "blocking_capabilities": blocking,
        "degraded_capabilities": degraded,
    }


def _unique_ids(values: Sequence[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise FleetDoctorError(f"{field} must be a sequence")
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise FleetDoctorError(f"{field} must contain non-empty strings")
    if len(result) != len(set(result)):
        raise FleetDoctorError(f"{field} contains duplicates")
    return result


def _digest(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise FleetDoctorError(f"{field} must be a SHA-256 digest")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose declared Saga requirements from a sanitized Fleet Core receipt"
    )
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--required", action="append", default=[])
    parser.add_argument("--optional", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        report = diagnose(
            args.receipt,
            required_capabilities=args.required,
            optional_capabilities=args.optional,
        )
    except (FleetDoctorError, host_capability_gate.GateError) as exc:
        print(f"Saga fleet doctor failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["state"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
