from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

POLICY = fleet_commons_shim.load("concurrency_policy")
BROKER = fleet_commons_shim.load("lease_broker")


def test_lease_snapshot_round_trip_is_deterministic() -> None:
    now = [1.0]
    policy = POLICY.ConcurrencyPolicy(max_active=2, lease_ttl_s=10.0, heartbeat_s=2.0)
    first = BROKER.LeaseBroker(policy, clock=lambda: now[0])
    first.claim("a", "owner-a")
    snapshot = first.snapshot()

    second = BROKER.LeaseBroker(policy, clock=lambda: now[0])
    second.load_snapshot(copy.deepcopy(snapshot))

    assert second.snapshot() == snapshot
    assert BROKER.canonical_snapshot_bytes(second.snapshot()) == BROKER.canonical_snapshot_bytes(
        snapshot
    )


def test_lease_snapshot_rejects_duplicate_resources() -> None:
    policy = POLICY.ConcurrencyPolicy(max_active=2, lease_ttl_s=10.0, heartbeat_s=2.0)
    broker = BROKER.LeaseBroker(policy, clock=lambda: 1.0)
    lease = broker.claim("a", "owner-a").to_jsonable()
    duplicate = {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [lease, lease]}

    with pytest.raises(BROKER.LeaseError):
        broker.load_snapshot(duplicate)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_lease_snapshot_rejects_non_finite_timestamps(invalid: float) -> None:
    policy = POLICY.ConcurrencyPolicy(max_active=2, lease_ttl_s=10.0, heartbeat_s=2.0)
    broker = BROKER.LeaseBroker(policy, clock=lambda: 1.0)
    lease = broker.claim("a", "owner-a").to_jsonable()
    lease["expires_at"] = invalid
    with pytest.raises(BROKER.LeaseError, match="finite"):
        broker.load_snapshot({"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [lease]})


def test_lease_broker_enforces_ownership_capacity_and_lifecycle() -> None:
    now = [1.0]
    policy = POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=10.0, heartbeat_s=2.0)
    broker = BROKER.LeaseBroker(policy, clock=lambda: now[0])
    with pytest.raises(BROKER.LeaseError, match="non-empty"):
        broker.claim("", "owner")
    lease = broker.claim("a", "owner-a")
    with pytest.raises(BROKER.LeaseConflictError):
        broker.claim("a", "owner-b")
    with pytest.raises(BROKER.LeaseCapacityError):
        broker.claim("b", "owner-b")
    with pytest.raises(BROKER.LeaseConflictError, match="current owner"):
        broker.renew("a", "owner-b")
    now[0] = 2.0
    assert broker.renew("a", "owner-a").lease_id == lease.lease_id
    with pytest.raises(BROKER.LeaseConflictError, match="current owner"):
        broker.release("a", "owner-b")
    assert broker.release("a", "owner-a").resource_id == "a"
    with pytest.raises(BROKER.UnknownLeaseError):
        broker.renew("a", "owner-a")
    with pytest.raises(BROKER.UnknownLeaseError):
        broker.release("a", "owner-a")


def test_lease_broker_rejects_invalid_clocks_and_snapshot_shapes() -> None:
    policy = POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=10.0, heartbeat_s=2.0)
    for invalid in (True, "now", float("nan")):
        broker = BROKER.LeaseBroker(policy, clock=lambda invalid=invalid: invalid)
        with pytest.raises(BROKER.LeaseError, match="clock"):
            broker.active()
    broker = BROKER.LeaseBroker(policy, clock=lambda: 1.0)
    for invalid in (True, "now", float("inf")):
        with pytest.raises(BROKER.LeaseError, match="now"):
            broker.active(now=invalid)

    assert BROKER.validate_snapshot(None) == ["snapshot must be an object"]
    assert "leases must be a list" in BROKER.validate_snapshot({"schema": "wrong", "leases": None})
    lease = broker.claim("a", "owner-a").to_jsonable()
    cases = [
        {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [{"bad": True}]},
        {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [{**lease, "schema": "wrong"}]},
        {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [{**lease, "owner_id": ""}]},
        {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [{**lease, "acquired_at": True}]},
        {"schema": BROKER.SNAPSHOT_SCHEMA, "leases": [{**lease, "renewed_at": 50.0}]},
    ]
    for snapshot in cases:
        assert BROKER.validate_snapshot(snapshot)
    with pytest.raises(BROKER.LeaseError, match="invalid lease snapshot"):
        BROKER.canonical_snapshot_bytes(cases[0])
