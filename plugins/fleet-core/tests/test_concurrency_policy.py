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
LIVENESS = fleet_commons_shim.load("liveness_engine")


def test_bounded_leases_prevent_duplicate_and_abandoned_ownership() -> None:
    policy = POLICY.ConcurrencyPolicy(max_active=2, lease_ttl_s=5.0, heartbeat_s=1.0)
    assert policy.admits(0) is True
    assert policy.admits(1) is True
    assert policy.admits(2) is False

    # Verify liveness engine evaluation
    leases = [
        {"resource_id": "task-1", "owner_id": "worker-1", "expires_at": 15.0},
        {"resource_id": "task-2", "owner_id": "worker-2", "expires_at": 15.0},
    ]
    status = LIVENESS.evaluate_liveness(
        leases,
        now=10.0,
        known_owners={"worker-1", "worker-2"},
    )
    assert status == {
        "active": ["task-1", "task-2"],
        "expired": [],
        "unknown_owner": [],
    }

    expired_status = LIVENESS.evaluate_liveness(
        leases,
        now=20.0,
        known_owners={"worker-1", "worker-2"},
    )
    assert expired_status == {
        "active": [],
        "expired": ["task-1", "task-2"],
        "unknown_owner": [],
    }


def test_bounded_leases_prevent_duplicate_and_abandoned_ownership_rejects_negative_cases() -> None:
    policy = POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=4.0, heartbeat_s=1.0)

    for max_active in (1.5, True, 0, -1):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=max_active, lease_ttl_s=4.0, heartbeat_s=1.0)
    for active_count in (0.5, True, -1):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            policy.admits(active_count)
    for invalid in (float("nan"), float("inf"), float("-inf"), 0, -1.0):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=invalid, heartbeat_s=1.0)
    for invalid_hb in (float("nan"), float("inf"), float("-inf"), 0, -1.0, 4.0, 5.0):
        with pytest.raises(POLICY.ConcurrencyPolicyError):
            POLICY.ConcurrencyPolicy(max_active=1, lease_ttl_s=4.0, heartbeat_s=invalid_hb)
