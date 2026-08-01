from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
REPO_ROOT = FLEET_CORE.parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

RESOLUTION = fleet_commons_shim.load("plugin_resolution")


def test_shared_runtime_resolution_is_logical_portable_and_target_bound() -> None:
    for plugin_name in RESOLUTION.TARGET_PLUGINS:
        root = RESOLUTION.resolve_plugin_root(plugin_name, repository_root=REPO_ROOT)
        manifest = json.loads((root / "plugin.json").read_text())
        assert manifest["name"] == plugin_name

    assert fleet_commons_shim.resolve_root()[0] == FLEET_CORE
    assert fleet_commons_shim.load("workflow_compat").WORKFLOW_SCHEMA.startswith("antigravity.")


def test_shared_runtime_resolution_is_logical_portable_and_target_bound_rejects_negative_cases() -> None:
    for plugin_name in (
        "team-execution",
        "verified-workflows",
        "/Users/example/plugin",
        "../fleet-core",
        "unknown-plugin",
    ):
        with pytest.raises(RESOLUTION.PluginResolutionError):
            RESOLUTION.resolve_plugin_root(plugin_name, repository_root=REPO_ROOT)

    with pytest.raises(RuntimeError):
        fleet_commons_shim.load("../outside")
