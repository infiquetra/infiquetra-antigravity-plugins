import os
import sys
from pathlib import Path

import pytest

# Pin FLEET_COMMONS_ROOT to fleet-core directory for testing
fleet_core_dir = Path(__file__).resolve().parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(fleet_core_dir)

# Add fleet-core/scripts to sys.path to load fleet_commons_shim
scripts_dir = fleet_core_dir / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import fleet_commons_shim  # noqa: E402


def test_tier_palette():
    palette = fleet_commons_shim.load("tier_palette")
    assert "gemini-3.1-pro" in palette.MODELS
    assert "gemini-3.5-flash" in palette.MODELS
    assert "low" in palette.EFFORTS
    assert "xhigh" in palette.EFFORTS

    assert palette.model_rank("gemini-3.1-pro") == 0
    assert palette.model_rank("gemini-3.5-flash") == 1
    assert palette.effort_rank("low") == 0
    assert palette.effort_rank("xhigh") == 3

    with pytest.raises(ValueError):
        palette.model_rank("non-existent-model")

    with pytest.raises(ValueError):
        palette.effort_rank("non-existent-effort")


def test_tier_resolver():
    resolver = fleet_commons_shim.load("tier_resolver")
    # Resolve basic judgment work shape
    res = resolver.resolve(role_kind=None, work_shape="judgment")
    assert res.model in ("gemini-3.1-pro", "gemini-3.5-flash")
    assert res.effort in ("low", "medium", "high", "xhigh")


def test_effort_rider():
    rider = fleet_commons_shim.load("effort_rider")
    # Workflow and external-engine pass-through
    assert rider.inject_effort("test prompt", "high", "workflow") == ("test prompt", {})
    assert rider.inject_effort("test prompt", "high", "external-engine") == ("test prompt", {})

    # Teammate spawns get the config payload (gemini level)
    prompt, payload = rider.inject_effort("test prompt", "high", "agent")
    assert prompt == "test prompt"
    assert payload == {"generation_config": {"thinking_level": "high"}}

    # xhigh maps to high thinking level for Gemini
    prompt, payload = rider.inject_effort("test prompt", "xhigh", "agent")
    assert prompt == "test prompt"
    assert payload == {"generation_config": {"thinking_level": "high"}}

    with pytest.raises(ValueError):
        rider.inject_effort("test prompt", "high", "invalid-spawn-kind")


def test_retry_backoff():
    backoff = fleet_commons_shim.load("retry_backoff")

    class FakeError(Exception):
        status_code = 429

    call_count = 0

    def failing_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise FakeError("Rate limited")
        return "success"

    # Test retry_with_backoff with a successful retry
    # We set base_delay/max_delay low so tests are fast
    result = backoff.retry_with_backoff(failing_fn, base_delay=0.01, max_delay=0.05, max_attempts=5)
    assert result == "success"
    assert call_count == 3
