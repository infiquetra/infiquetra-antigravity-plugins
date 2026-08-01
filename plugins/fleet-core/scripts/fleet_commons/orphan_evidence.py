"""Validate worker output ownership, shape, uniqueness, and run attestation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import fleet_commons_shim

OUTPUT_ATTESTATION = fleet_commons_shim.load("output_attestation")

EVIDENCE_SCHEMA = "antigravity.orphan-evidence.v1"


class OrphanEvidenceError(ValueError):
    """Evidence could not be loaded under the closed contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OrphanEvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_evidence(path: Path | str) -> dict[str, Any]:
    try:
        parsed = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise OrphanEvidenceError("could not load orphan evidence") from exc
    if not isinstance(parsed, dict):
        raise OrphanEvidenceError("orphan evidence must be an object")
    return parsed


def validate_evidence(
    evidence: object,
    *,
    expected_run_id: str,
    expected_owners: Mapping[str, str],
) -> list[str]:
    if not isinstance(evidence, dict):
        return ["evidence must be an object"]
    errors: list[str] = []
    if set(evidence) != {"schema", "run_id", "records"}:
        errors.append("evidence fields must be exactly schema, run_id, and records")
    if evidence.get("schema") != EVIDENCE_SCHEMA:
        errors.append("evidence schema is invalid")
    if evidence.get("run_id") != expected_run_id:
        errors.append("evidence run_id does not match")
    records = evidence.get("records")
    if not isinstance(records, list):
        return [*errors, "records must be a list"]
    seen_assignments: set[str] = set()
    seen_bindings: set[str] = set()
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(record) != {"assignment_id", "worker_id", "output", "attestation"}:
            errors.append(f"{prefix} has an invalid shape")
            continue
        assignment_id = record.get("assignment_id")
        worker_id = record.get("worker_id")
        if (
            not isinstance(assignment_id, str)
            or not assignment_id
            or not isinstance(worker_id, str)
            or not worker_id
        ):
            errors.append(f"{prefix} has invalid ownership identifiers")
            continue
        if assignment_id not in expected_owners:
            errors.append(f"{prefix} names an unknown assignment")
            continue
        if assignment_id in seen_assignments:
            errors.append(f"{prefix} duplicates assignment evidence")
        seen_assignments.add(assignment_id)
        if worker_id != expected_owners[assignment_id]:
            errors.append(f"{prefix} has the wrong owner")
        if record.get("output") is None:
            errors.append(f"{prefix} is missing output")
        attestation = record.get("attestation")
        if isinstance(attestation, dict):
            binding = attestation.get("binding_sha256")
            if binding in seen_bindings:
                errors.append(f"{prefix} replays an attestation")
            if isinstance(binding, str):
                seen_bindings.add(binding)
        errors.extend(
            f"{prefix}: {error}"
            for error in OUTPUT_ATTESTATION.validate_attestation(
                attestation,
                run_id=expected_run_id,
                assignment_id=assignment_id,
                worker_id=worker_id,
                output=record.get("output"),
            )
        )
    missing = sorted(set(expected_owners) - seen_assignments)
    if missing:
        errors.append("missing assignment evidence: " + ", ".join(missing))
    return errors
