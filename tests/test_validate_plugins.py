from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hermes-profile-evolution"
VALIDATOR = ROOT / "scripts/validate_plugins.py"
RECEIPT = ROOT / "docs/ports/2026-08-01-hermes-profile-evolution/receipt.yaml"


def _load_validator():
    spec = importlib.util.spec_from_file_location("antigravity_validator_for_u5", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_native_validator_discovers_manifest_command_and_skill(tmp_path: Path) -> None:
    validator = _load_validator()

    status = validator.inspect_plugin(PLUGIN / "plugin.json", tmp_path / "install", False)

    assert status.name == "hermes-profile-evolution"
    assert status.version == "0.1.1"
    assert status.commands == 1
    assert status.skills == 1
    assert status.agents == 0
    assert status.tools == 0
    assert status.errors == []


def test_plugin_uses_existing_validator_without_global_special_case() -> None:
    validator_source = VALIDATOR.read_text()

    assert "hermes-profile-evolution" not in validator_source
    assert 'plugins_root.glob("*/plugin.json")' in validator_source
    assert '(plugin_dir / "commands").glob("*.md")' in validator_source
    assert '(plugin_dir / "skills").glob("*/SKILL.md")' in validator_source


def test_compact_receipt_names_native_surfaces_and_exclusions() -> None:
    receipt = RECEIPT.read_text()

    assert len(receipt.splitlines()) < 90
    for value in (
        "9440dc744afc6553927fbde7f979ad433e0d1378",
        "04a73d33bec429081606b58851b53053059f2b90a9511f94d6ab26bbcaa34bfc",
        "292c62eb4dbff9a2b0d2683501a1cd00ed119f7b",
        "b651eff9ac155758719f0fee59ad7dcf22fc6a81f11f27bc1668da0720eaf61c",
        "commands/hermes-profile-evolution.md",
        "skills/hermes-profile-evolution/SKILL.md",
        "hooks",
        "direct profile mutation",
        "offline queue",
    ):
        assert value in receipt
    assert "semantic-port ledger" in receipt
    assert "ledger.yaml" not in receipt


def test_plugin_tree_has_no_hook_cache_or_semantic_port_ledger() -> None:
    assert not (PLUGIN / "hooks").exists()
    assert not list(PLUGIN.rglob("__pycache__"))
    assert not list(PLUGIN.rglob("*.pyc"))
    assert not list(PLUGIN.rglob("ledger.yaml"))
