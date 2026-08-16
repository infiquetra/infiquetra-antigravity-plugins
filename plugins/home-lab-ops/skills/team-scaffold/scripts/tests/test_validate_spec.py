"""Validation contract tests for the ``validate-spec`` surface."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


from team_scaffold import cli, spec

ROOT = pathlib.Path(__file__).resolve().parents[1].parent  # skills/team-scaffold
SPECS = ROOT / "specs"


def _write_spec(tmp_path: pathlib.Path, team: dict) -> pathlib.Path:
    path = tmp_path / "team-bad.yaml"
    path.write_text(
        "team:\n"
        f"  name: {team['name']}\n"
        f"  display: {team['display']}\n"
        f"  host_group: {team['host_group']}\n"
        f"  limit_host: {team['limit_host']}\n"
        f"  roles: {team['roles']}\n"
        "profiles: []\n",
        encoding="utf-8",
    )
    return path


def test_spec_validate_reports_clear_problems(tmp_path: pathlib.Path) -> None:
    path = _write_spec(
        tmp_path,
        {
            "name": "bad-team",
            "display": "Bad Team",
            "host_group": "agent_vms",
            "limit_host": "h1",
            "roles": [],
        },
    )
    problems = spec.load_spec(path).validate()
    assert "team.roles is empty" in problems
    assert "team.roles must include the 'hermes' role" in problems


def test_cli_validate_spec_rejects_an_invalid_spec(tmp_path: pathlib.Path, capsys) -> None:
    path = _write_spec(
        tmp_path,
        {
            "name": "bad-team",
            "display": "Bad Team",
            "host_group": "agent_vms",
            "limit_host": "h1",
            "roles": [],
        },
    )
    assert cli.main(["validate-spec", str(path)]) == 1
    out = capsys.readouterr().out
    assert "invalid spec" in out
    assert "team.roles is empty" in out


def test_cli_validate_spec_accepts_a_golden_spec(capsys) -> None:
    golden = next(SPECS.glob("team-*.yaml"))
    assert cli.main(["validate-spec", str(golden)]) == 0
    out = capsys.readouterr().out
    assert "spec valid" in out
