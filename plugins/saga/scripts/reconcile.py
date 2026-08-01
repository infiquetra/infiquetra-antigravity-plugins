#!/usr/bin/env python3
"""Reconcile advisory runtime projections against canonical repository bytes."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PROJECTION_SCHEMA = "antigravity.saga-runtime-projection.v1"
RECONCILIATION_SCHEMA = "antigravity.saga-reconciliation.v1"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PROJECTION_FIELDS = frozenset(
    {
        "schema",
        "projection_id",
        "runtime",
        "canonical_reference",
        "canonical_sha256",
        "receipt_sha256",
        "authority",
        "facts",
    }
)


class ReconciliationError(ValueError):
    """Canonical evidence or an advisory projection is malformed."""


@dataclass(frozen=True)
class CanonicalEvidence:
    reference: str
    sha256: str

    def validate(self) -> None:
        if (
            not self.reference
            or self.reference.startswith("/")
            or ".." in self.reference.split("/")
        ):
            raise ReconciliationError("canonical reference must be repository-relative")
        _digest(self.sha256, "canonical sha256")


def build_projection(
    *,
    projection_id: str,
    runtime: str,
    canonical: CanonicalEvidence,
    receipt_sha256: str,
    facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one advisory projection bound to exact canonical bytes."""

    canonical.validate()
    projection = {
        "schema": PROJECTION_SCHEMA,
        "projection_id": projection_id,
        "runtime": runtime,
        "canonical_reference": canonical.reference,
        "canonical_sha256": canonical.sha256,
        "receipt_sha256": receipt_sha256,
        "authority": "advisory",
        "facts": dict(facts),
    }
    validate_projection(projection)
    return projection


def validate_projection(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _PROJECTION_FIELDS:
        raise ReconciliationError("runtime projection has unknown or missing fields")
    if value.get("schema") != PROJECTION_SCHEMA:
        raise ReconciliationError("runtime projection schema is invalid")
    for field in ("projection_id", "runtime", "canonical_reference"):
        item = value.get(field)
        if not isinstance(item, str) or not item:
            raise ReconciliationError(f"runtime projection {field} must be non-empty")
    if value.get("authority") != "advisory":
        raise ReconciliationError("runtime projection cannot claim canonical authority")
    if not isinstance(value.get("facts"), Mapping):
        raise ReconciliationError("runtime projection facts must be an object")
    _digest(value.get("canonical_sha256"), "runtime projection canonical_sha256")
    _digest(value.get("receipt_sha256"), "runtime projection receipt_sha256")
    return value


def reconcile_projections(
    canonical: CanonicalEvidence,
    projections: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Classify projections without allowing any projection to alter truth."""

    canonical.validate()
    if not isinstance(projections, Sequence) or isinstance(projections, (str, bytes)):
        raise ReconciliationError("projections must be a sequence")
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in projections:
        projection = validate_projection(raw)
        projection_id = str(projection["projection_id"])
        if projection_id in seen:
            raise ReconciliationError("runtime projection identities must be unique")
        seen.add(projection_id)
        reasons: list[str] = []
        if projection["canonical_reference"] != canonical.reference:
            reasons.append("canonical-reference-mismatch")
        if projection["canonical_sha256"] != canonical.sha256:
            reasons.append("stale-canonical-digest")
        results.append(
            {
                "projection_id": projection_id,
                "runtime": projection["runtime"],
                "state": "accepted" if not reasons else "rejected",
                "reasons": reasons,
                "receipt_sha256": projection["receipt_sha256"],
            }
        )
    return {
        "schema": RECONCILIATION_SCHEMA,
        "canonical": {
            "reference": canonical.reference,
            "sha256": canonical.sha256,
            "authority": "repository",
        },
        "projections": results,
    }


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _digest(value: object, field: str) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ReconciliationError(f"{field} must be a SHA-256 digest")
