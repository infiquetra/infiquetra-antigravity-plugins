"""Deterministic liveness interpretation for local ownership leases."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def evaluate_liveness(
    leases: Iterable[dict[str, Any]],
    *,
    now: float,
    known_owners: set[str],
) -> dict[str, list[str]]:
    """Classify lease resources without performing or claiming host scheduling."""

    active: list[str] = []
    expired: list[str] = []
    unknown_owner: list[str] = []
    for lease in leases:
        resource = str(lease["resource_id"])
        if lease["owner_id"] not in known_owners:
            unknown_owner.append(resource)
        elif float(lease["expires_at"]) <= now:
            expired.append(resource)
        else:
            active.append(resource)
    return {
        "active": sorted(active),
        "expired": sorted(expired),
        "unknown_owner": sorted(unknown_owner),
    }
