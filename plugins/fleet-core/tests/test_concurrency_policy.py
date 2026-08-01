from __future__ import annotations

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
LIVENESS = fleet_commons_shim.load("liveness_engine")


def test_bounded_leases_prevent_duplicate_and_abandoned_ownership() -> None:
    now = [10.0]
    policy = POLICY.ConcurrencyPolicy(max_active=2, lease_ttl_s=5.0, heartbeat_s=1.0)
    broker = BROKER.LeaseBroker(policy, clock=lambda: now[0])
    first = broker.claim("task-1", "worker-1")
    second = broker.claim("task-2", "worker-2")

    assert {lease.resource_id for lease in broker.active()} == {"task-1", "task-2"}
    status = LIVENESS.evaluate_liveness(
        [first.to_jsonable(), second.to_jsonable()],
        now=10.0,
        known_owners={"worker-1", "worker-2"},
    )
    assert status == {
        "active": ["task-1", "task-2"],
        "expired": [],
        "unknown_owner": [],
    }

    now[0] = 15.0
    replacement = broker.claim("task-1", "worker-3")
    assert replacement.owner_id == "worker-3"


def test_bounded_leases_prevent_duplicate_and_abandoned_ownership_rejects_negative_cases() -> None:
    now = [20.0]
    policy = POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=4.0, heartbeat_s=1.0)
    broker = BROKER.LeaseBroker(policy, clock=lambda: now[0])
    broker.claim("task-1", "worker-1")

    with pytest.raises(BROKER.LeaseConflictError):
        broker.claim("task-1", "worker-2")
    with pytest.raises(BROKER.LeaseCapacityError):
        broker.claim("task-2", "worker-2")
    with pytest.raises(BROKER.UnknownLeaseError):
        broker.release("unknown", "worker-1")
    with pytest.raises(BROKER.LeaseConflictError):
        broker.renew("task-1", "worker-2")

    now[0] = 24.0
    assert broker.active() == ()
    with pytest.raises(BROKER.UnknownLeaseError):
        broker.renew("task-1", "worker-1")

    bad_clock = BROKER.LeaseBroker(policy, clock=lambda: "tomorrow")
    with pytest.raises(BROKER.LeaseError):
        bad_clock.claim("task", "worker")

    for max_active in (1.5, True):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=max_active, lease_ttl_s=4.0, heartbeat_s=1.0)
    for active_count in (0.5, True):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            policy.admits(active_count)
    for invalid in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=invalid, heartbeat_s=1.0)
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=4.0, heartbeat_s=invalid)
        with pytest.raises(BROKER.LeaseError):
            BROKER.LeaseBroker(policy, clock=lambda value=invalid: value).active()
        with pytest.raises(BROKER.LeaseError):
            broker.active(now=invalid)
