"""Content-stable local lease broker with an injected clock."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

LEASE_SCHEMA = "antigravity.local-lease.v1"
SNAPSHOT_SCHEMA = "antigravity.local-lease-snapshot.v1"


class LeaseError(ValueError):
    """Base local lease failure."""


class LeaseConflictError(LeaseError):
    """A non-expired owner already holds the resource."""


class LeaseCapacityError(LeaseError):
    """The configured number of local ownership slots is full."""


class UnknownLeaseError(LeaseError):
    """No matching local ownership lease exists."""


class LeasePolicy(Protocol):
    lease_ttl_s: float

    def admits(self, active_count: int) -> bool: ...


@dataclass(frozen=True)
class Lease:
    lease_id: str
    resource_id: str
    owner_id: str
    acquired_at: float
    renewed_at: float
    expires_at: float

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "schema": LEASE_SCHEMA,
            "lease_id": self.lease_id,
            "resource_id": self.resource_id,
            "owner_id": self.owner_id,
            "acquired_at": self.acquired_at,
            "renewed_at": self.renewed_at,
            "expires_at": self.expires_at,
        }


def _lease_id(resource_id: str, owner_id: str, acquired_at: float) -> str:
    payload = f"{resource_id}\0{owner_id}\0{acquired_at:.9f}".encode()
    return hashlib.sha256(payload).hexdigest()


class LeaseBroker:
    """Manage local ownership leases; persistence is an explicit JSON snapshot."""

    def __init__(self, policy: LeasePolicy, *, clock: Callable[[], float]) -> None:
        self.policy = policy
        self.clock = clock
        self._leases: dict[str, Lease] = {}

    def _now(self) -> float:
        value = self.clock()
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise LeaseError("clock must return a finite number")
        return float(value)

    def active(self, *, now: float | None = None) -> tuple[Lease, ...]:
        if now is None:
            instant = self._now()
        elif isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
            raise LeaseError("now must be a finite number")
        else:
            instant = float(now)
        self._leases = {
            resource_id: lease
            for resource_id, lease in self._leases.items()
            if lease.expires_at > instant
        }
        return tuple(self._leases[key] for key in sorted(self._leases))

    def claim(self, resource_id: str, owner_id: str) -> Lease:
        if not resource_id or not owner_id:
            raise LeaseError("resource_id and owner_id must be non-empty")
        now = self._now()
        active = self.active(now=now)
        current = self._leases.get(resource_id)
        if current is not None:
            raise LeaseConflictError(f"resource {resource_id!r} already has an active owner")
        if not self.policy.admits(len(active)):
            raise LeaseCapacityError("local ownership capacity is full")
        lease = Lease(
            lease_id=_lease_id(resource_id, owner_id, now),
            resource_id=resource_id,
            owner_id=owner_id,
            acquired_at=now,
            renewed_at=now,
            expires_at=now + self.policy.lease_ttl_s,
        )
        self._leases[resource_id] = lease
        return lease

    def renew(self, resource_id: str, owner_id: str) -> Lease:
        now = self._now()
        self.active(now=now)
        current = self._leases.get(resource_id)
        if current is None:
            raise UnknownLeaseError("cannot renew an absent or expired lease")
        if current.owner_id != owner_id:
            raise LeaseConflictError("only the current owner may renew a lease")
        renewed = Lease(
            lease_id=current.lease_id,
            resource_id=current.resource_id,
            owner_id=current.owner_id,
            acquired_at=current.acquired_at,
            renewed_at=now,
            expires_at=now + self.policy.lease_ttl_s,
        )
        self._leases[resource_id] = renewed
        return renewed

    def release(self, resource_id: str, owner_id: str) -> Lease:
        self.active()
        current = self._leases.get(resource_id)
        if current is None:
            raise UnknownLeaseError("cannot release an absent or expired lease")
        if current.owner_id != owner_id:
            raise LeaseConflictError("only the current owner may release a lease")
        return self._leases.pop(resource_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "leases": [lease.to_jsonable() for lease in self.active()],
        }

    def load_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        errors = validate_snapshot(snapshot)
        if errors:
            raise LeaseError("invalid lease snapshot: " + "; ".join(errors))
        loaded: dict[str, Lease] = {}
        for row in snapshot["leases"]:
            lease = Lease(
                lease_id=row["lease_id"],
                resource_id=row["resource_id"],
                owner_id=row["owner_id"],
                acquired_at=float(row["acquired_at"]),
                renewed_at=float(row["renewed_at"]),
                expires_at=float(row["expires_at"]),
            )
            loaded[lease.resource_id] = lease
        self._leases = loaded
        self.active()


def validate_snapshot(snapshot: object) -> list[str]:
    if not isinstance(snapshot, Mapping):
        return ["snapshot must be an object"]
    errors: list[str] = []
    if set(snapshot) != {"schema", "leases"}:
        errors.append("snapshot fields must be exactly schema and leases")
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        errors.append("snapshot schema is invalid")
    rows = snapshot.get("leases")
    if not isinstance(rows, list):
        return [*errors, "leases must be a list"]
    resources: set[str] = set()
    lease_ids: set[str] = set()
    expected = {
        "schema",
        "lease_id",
        "resource_id",
        "owner_id",
        "acquired_at",
        "renewed_at",
        "expires_at",
    }
    for index, row in enumerate(rows):
        prefix = f"leases[{index}]"
        if not isinstance(row, dict) or set(row) != expected:
            errors.append(f"{prefix} has an invalid shape")
            continue
        if row.get("schema") != LEASE_SCHEMA:
            errors.append(f"{prefix}.schema is invalid")
        for field in ("lease_id", "resource_id", "owner_id"):
            if not isinstance(row.get(field), str) or not row[field]:
                errors.append(f"{prefix}.{field} must be a non-empty string")
        times = [row.get(field) for field in ("acquired_at", "renewed_at", "expires_at")]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in times):
            errors.append(f"{prefix} timestamps must be numeric")
        else:
            acquired_at, renewed_at, expires_at = cast(tuple[float, float, float], tuple(times))
            assert isinstance(acquired_at, (int, float))
            assert isinstance(renewed_at, (int, float))
            assert isinstance(expires_at, (int, float))
            if not all(math.isfinite(value) for value in (acquired_at, renewed_at, expires_at)):
                errors.append(f"{prefix} timestamps must be finite")
            elif not (acquired_at <= renewed_at < expires_at):
                errors.append(f"{prefix} timestamps are out of order")
        resource = row.get("resource_id")
        lease_id = row.get("lease_id")
        if resource in resources or lease_id in lease_ids:
            errors.append(f"{prefix} duplicates an ownership identity")
        if isinstance(resource, str):
            resources.add(resource)
        if isinstance(lease_id, str):
            lease_ids.add(lease_id)
    return errors


def canonical_snapshot_bytes(snapshot: Mapping[str, Any]) -> bytes:
    errors = validate_snapshot(snapshot)
    if errors:
        raise LeaseError("invalid lease snapshot: " + "; ".join(errors))
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
