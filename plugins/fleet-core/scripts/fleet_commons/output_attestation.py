"""Content-addressed output binding issued by the local run ledger."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

ATTESTATION_SCHEMA = "antigravity.output-attestation.v1"
TRUSTED_ATTESTER = "run-ledger"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def attest_output(
    *,
    run_id: str,
    assignment_id: str,
    worker_id: str,
    output: Any,
) -> dict[str, Any]:
    output_digest = canonical_digest(output)
    binding = {
        "run_id": run_id,
        "assignment_id": assignment_id,
        "worker_id": worker_id,
        "output_sha256": output_digest,
    }
    return {
        "schema": ATTESTATION_SCHEMA,
        "attester": TRUSTED_ATTESTER,
        **binding,
        "binding_sha256": canonical_digest(binding),
    }


def validate_attestation(
    attestation: object,
    *,
    run_id: str,
    assignment_id: str,
    worker_id: str,
    output: Any,
) -> list[str]:
    if not isinstance(attestation, Mapping):
        return ["attestation must be an object"]
    expected_fields = {
        "schema",
        "attester",
        "run_id",
        "assignment_id",
        "worker_id",
        "output_sha256",
        "binding_sha256",
    }
    errors = ["attestation has unknown or missing fields"] if set(attestation) != expected_fields else []
    if attestation.get("schema") != ATTESTATION_SCHEMA:
        errors.append("attestation schema is invalid")
    if attestation.get("attester") != TRUSTED_ATTESTER:
        errors.append("output is not attested by the run ledger")
    expected = {
        "run_id": run_id,
        "assignment_id": assignment_id,
        "worker_id": worker_id,
        "output_sha256": canonical_digest(output),
    }
    for field, value in expected.items():
        if attestation.get(field) != value:
            errors.append(f"attestation {field} does not match expected ownership")
    binding_digest = attestation.get("binding_sha256")
    if not isinstance(binding_digest, str) or not _DIGEST_RE.fullmatch(binding_digest):
        errors.append("attestation binding_sha256 is invalid")
    elif binding_digest != canonical_digest(expected):
        errors.append("attestation binding does not match its content")
    return errors
