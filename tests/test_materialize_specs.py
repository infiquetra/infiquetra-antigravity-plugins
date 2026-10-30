"""Loader guards and serialization contract for team spec materialization."""

from __future__ import annotations

import importlib.util
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/home-lab-ops/skills/team-scaffold/scripts/materialize_specs.py"
)


@pytest.fixture
def materializer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("materialize_specs", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_teams_rejects_unloadable_path(materializer: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "generator.unsupported"
    path.write_text("TEAMS = {}\n")
    with pytest.raises(ImportError, match="Cannot load team generator"):
        materializer.load_teams(path)


def test_load_teams_rejects_missing_loader(
    materializer: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        materializer.importlib.util,
        "spec_from_file_location",
        lambda name, location: ModuleSpec(name, loader=None),
    )
    with pytest.raises(ImportError, match="Cannot load team generator"):
        materializer.load_teams(tmp_path / "generator.py")


@pytest.mark.parametrize("teams_source", ["[]", "None", "'invalid'"])
def test_load_teams_rejects_non_dict(
    materializer: ModuleType, tmp_path: Path, teams_source: str
) -> None:
    path = tmp_path / "generator.py"
    path.write_text(f"TEAMS = {teams_source}\n")
    with pytest.raises(TypeError, match="Team generator TEAMS must be a dict"):
        materializer.load_teams(path)


def test_materialize_preserves_team_inventory_profiles_and_yaml(
    materializer: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    generator = tmp_path / "generator.py"
    generator.write_text(
        "TEAMS = {'team-demo': {'team': 'Demo', 'hosts': 'agent_vms', "
        "'limit': 'demo', 'pin': False, 'coresident': 'team-helper', "
        "'roles': [('hermes', ['hermes', 'services'])]}}\n"
    )
    fixtures = tmp_path / "fixtures"
    deploy = fixtures / "team-demo/deploy"
    deploy.mkdir(parents=True)
    (deploy / "team_profiles.yml").write_text(
        "hermes_team_profiles:\n"
        "- name: demo\n"
        "  persona: guide\n"
        "  discord_token_var: vault_discord_bot_token_demo\n"
        "- name: worker\n"
        "  headless: true\n"
    )
    hosts = tmp_path / "hosts.yml"
    hosts.write_text(
        "all:\n"
        "  children:\n"
        "    agent_vms:\n"
        "      hosts:\n"
        "        demo:\n"
        "          ansible_host: 192.0.2.10\n"
        "          ansible_user: agent\n"
        "          unrelated: omitted\n"
    )
    output = tmp_path / "specs"
    monkeypatch.setattr(materializer, "HERE", tmp_path / "scripts")
    monkeypatch.setattr(materializer, "SPECS_DIR", output)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--gen-harness",
            str(generator),
            "--fixtures",
            str(fixtures),
            "--hosts",
            str(hosts),
        ],
    )
    assert materializer.main() == 0
    assert (output / "team-demo.yaml").read_text() == (
        "team:\n"
        "  name: demo\n"
        "  display: Demo\n"
        "  host_group: agent_vms\n"
        "  limit_host: demo\n"
        "  pin_runtime: false\n"
        "  coresident: team-helper\n"
        "  roles:\n"
        "  - role: hermes\n"
        "    tags:\n"
        "    - hermes\n"
        "    - services\n"
        "inventory:\n"
        "  ansible_host: 192.0.2.10\n"
        "  ansible_user: agent\n"
        "profiles:\n"
        "- name: demo\n"
        "  persona: guide\n"
        "  discord_token_var: vault_discord_bot_token_demo\n"
        "- name: worker\n"
        "  headless: true\n"
    )
