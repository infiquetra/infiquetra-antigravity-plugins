from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "detect_deploy_strategy.py"
    spec = importlib.util.spec_from_file_location("detect_deploy_strategy_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_deploy_strategy_detects_intent_without_executing_release() -> None:
    module = _load()
    packet = module.build_deploy_intent(
        ["deploy-nonprod.yml", "deploy-staging.yml", "deploy-production.yml"],
        environment="staging",
        workspace_id="repo-15",
        requested_by="operator",
    )
    assert packet["owner"] == "deploy"
    assert packet["authority_required"] is True
    assert packet["executed"] is False
    assert packet["external_action_intent"]["operation"] == "promote"


def test_deploy_strategy_detects_intent_without_executing_release_rejects_negative_cases() -> None:
    module = _load()
    with pytest.raises(ValueError, match="unambiguous"):
        module.build_deploy_intent(
            ["deploy-nonprod.yml"],
            environment="production",
            workspace_id="repo-15",
            requested_by="operator",
        )
    with pytest.raises(ValueError, match="environment"):
        module.build_deploy_intent(
            ["deploy-production.yml"],
            environment="prod",
            workspace_id="repo-15",
            requested_by="operator",
        )
