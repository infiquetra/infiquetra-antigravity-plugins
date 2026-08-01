"""Deterministic local admission policy for durable ownership leases."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class ConcurrencyPolicyError(ValueError):
    """The local ownership policy is invalid."""


@dataclass(frozen=True)
class ConcurrencyPolicy:
    """Bound local ownership without claiming host scheduling or isolation."""

    max_active: int
    lease_ttl_s: float
    heartbeat_s: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_active, bool)
            or not isinstance(self.max_active, int)
            or self.max_active < 1
        ):
            raise ConcurrencyPolicyError("max_active must be a positive integer")
        if (
            isinstance(self.lease_ttl_s, bool)
            or not isinstance(self.lease_ttl_s, (int, float))
            or not isfinite(self.lease_ttl_s)
            or self.lease_ttl_s <= 0
        ):
            raise ConcurrencyPolicyError("lease_ttl_s must be a positive finite number")
        if (
            isinstance(self.heartbeat_s, bool)
            or not isinstance(self.heartbeat_s, (int, float))
            or not isfinite(self.heartbeat_s)
            or self.heartbeat_s <= 0
            or self.heartbeat_s >= self.lease_ttl_s
        ):
            raise ConcurrencyPolicyError("heartbeat_s must be positive and less than lease_ttl_s")

    def admits(self, active_count: int) -> bool:
        if isinstance(active_count, bool) or not isinstance(active_count, int) or active_count < 0:
            raise ConcurrencyPolicyError("active_count must be a non-negative integer")
        return active_count < self.max_active
