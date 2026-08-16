"""Tests for the execution-spec approval table (#668)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = ROOT / "plugins" / "saga" / "scripts"


def _load(name: str) -> ModuleType:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ES = _load("execution_spec")
ST = _load("spec_table")
OUTSPEC = _load("outcome_spec")


def _unit(
    unit_id: str, model: str = "gemini-3.1-pro", effort: str = "high", **over: Any
) -> dict[str, Any]:
    unit: dict[str, Any] = {
        "unit_id": unit_id,
        "label": f"do {unit_id}",
        "tier": {"model": model, "effort": effort},
        "prompt": f"work on {unit_id}",
        "returns": "a summary",
        "depends_on": [],
    }
    unit.update(over)
    return unit


def _spec(*units: dict[str, Any], **over: Any) -> Any:
    data: dict[str, Any] = {
        "name": "test-spec",
        "description": "a spec for tests",
        "repo": "infiquetra/example",
        "units": list(units),
    }
    data.update(over)
    return ES.ExecutionSpec.from_dict(data)


def test_every_unit_appears_with_its_declared_tier() -> None:
    spec = _spec(
        _unit("U1", "gemini-3.1-pro", "high"),
        _unit("U2", "gemini-3.5-flash", "low", depends_on=["U1"]),
    )
    out = ST.render(spec)
    assert "`U1`" in out and "`U2`" in out
    assert "`gemini-3.1-pro:high`" in out
    assert "`gemini-3.5-flash:low`" in out


def test_dependency_waves_show_what_runs_in_parallel() -> None:
    spec = _spec(_unit("U1"), _unit("U2", depends_on=["U1"]), _unit("U3", depends_on=["U1"]))
    out = ST.render(spec)
    assert "2 in parallel" in out


def test_serial_chain_reports_no_parallelism() -> None:
    spec = _spec(_unit("U1"), _unit("U2", depends_on=["U1"]))
    assert "— 2 in parallel" not in ST.render(spec)


def test_over_budget_is_called_out() -> None:
    spec = _spec(_unit("U1", "gemini-3.1-pro", "high"), cost_budget=1)
    assert "OVER BUDGET" in ST.render(spec)


def test_within_budget_is_not_flagged() -> None:
    spec = _spec(_unit("U1", "gemini-3.5-flash", "low"), cost_budget=10_000)
    out = ST.render(spec)
    assert "OVER BUDGET" not in out
    assert "/ 10000" in out


def test_fanout_without_targets_is_flagged_because_emit_will_fail() -> None:
    spec = _spec(_unit("U1", fanout=True, targets=[]))
    assert "no targets" in ST.render(spec)


def test_verify_panel_renders_n_and_pass_rule() -> None:
    spec = _spec(_unit("U1", verify={"n": 3, "pass_rule": "majority"}))
    assert "verify n=3/majority" in ST.render(spec)


def test_cycle_is_reported_not_raised() -> None:
    spec = _spec(_unit("U1", depends_on=["U2"]), _unit("U2", depends_on=["U1"]))
    out = ST.render(spec)
    assert "Cannot compute" in out


def test_inline_backend_enforces_sandbox_axes_for_a_verify_panel() -> None:
    spec = _spec(_unit("U1", verify={"n": 3, "pass_rule": "majority"}))
    out = ST.render(spec, backend="inline")
    assert "sandbox: read-only | enforced" in out
    assert "sandbox: disposable worktree | enforced" in out
    assert "NOT enforceable" not in out


def test_team_execution_enforces_neither_axis_for_the_same_spec() -> None:
    spec = _spec(_unit("U1", verify={"n": 3, "pass_rule": "majority"}))
    out = ST.render(spec, backend="team-execution")
    assert out.count("NOT enforceable") == 2
    assert "pick another backend" in out


def test_unknown_backend_enforces_nothing() -> None:
    spec = _spec(_unit("U1", verify={"n": 3, "pass_rule": "majority"}))
    rows = ST.enforcement_rows(spec, "some-future-backend")
    sandbox = [r for r in rows if r[0].startswith("sandbox:")]
    assert sandbox and all("NOT" in status for _, status, _ in sandbox)


def test_cli_renders_a_real_spec(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "spec.json"
    path.write_text(
        json.dumps(
            {
                "name": "cli-spec",
                "description": "d",
                "repo": "o/r",
                "units": [_unit("U1", "gemini-3.1-pro", "high")],
            }
        ),
        encoding="utf-8",
    )
    assert ST.main([str(path), "--backend", "inline"]) == 0
    out = capsys.readouterr().out
    assert "cli-spec" in out and "`gemini-3.1-pro:high`" in out


def test_cli_missing_file_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ST.main([str(tmp_path / "nope.json")]) == 2
    assert "no such spec" in capsys.readouterr().err


def test_cli_malformed_json_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert ST.main([str(path)]) == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_cli_rejects_an_unknown_backend(tmp_path: Path) -> None:
    path = tmp_path / "spec.json"
    path.write_text(
        json.dumps({"name": "n", "description": "d", "repo": "o/r", "units": [_unit("U1")]}),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        ST.main([str(path), "--backend", "not-a-backend"])


def _outcome_dict() -> dict[str, Any]:
    return {
        "outcome_id": "demo-42",
        "objective": "stand up the demo",
        "nodes": [
            {
                "subplot_id": "a-build",
                "title": "build it",
                "kind": "code",
                "backend": "inline",
                "state": "pending",
                "depends_on": [],
            },
            {
                "subplot_id": "b-deploy",
                "title": "deploy it",
                "kind": "non-code",
                "backend": "multi-agent-consensus",
                "state": "pending",
                "destructive": True,
                "gated": True,
                "sandbox": {
                    "mutation_policy": "read-only",
                    "workspace_isolation": "owned-worktree",
                },
                "depends_on": ["a-build"],
            },
        ],
    }


def test_outcome_table_names_nodes_flags_and_sandbox() -> None:
    table = ST.render_outcome(
        OUTSPEC.OutcomeSpec.from_dict(_outcome_dict()),
        backend="multi-agent-consensus",
    )
    assert "## Outcome approval — `demo-42`" in table
    assert "`a-build`" in table and "`b-deploy`" in table
    assert "destructive" in table and "gated" in table
    assert "owned-worktree/read-only" in table
    assert "`multi-agent-consensus`" in table


def test_outcome_table_warns_on_destructive_and_gated_nodes() -> None:
    table = ST.render_outcome(OUTSPEC.OutcomeSpec.from_dict(_outcome_dict()))
    assert "### Approval warnings" in table
    assert "`b-deploy`" in table
    assert "approve each explicitly" in table


def test_outcome_cli_renders_from_a_json_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "outcome-spec.json"
    path.write_text(json.dumps(_outcome_dict()), encoding="utf-8")
    assert ST.main([str(path), "--outcome", "--backend", "inline"]) == 0
    out = capsys.readouterr().out
    assert "## Outcome approval — `demo-42`" in out


def test_concurrent_writer_section_names_the_conflict_and_halts() -> None:
    spec = _spec(_unit("U1", files=["src/a.py"]), _unit("U2", files=["src/a.py"]))
    out = ST.render(spec)
    assert "### Concurrent-writer safety" in out
    assert "src/a.py" in out
    assert "⛔ **`emit` will HALT.**" in out


def test_concurrent_writer_section_marks_a_clean_wave_explicitly() -> None:
    spec = _spec(_unit("U1", files=["src/a.py"]), _unit("U2", files=["src/b.py"]))
    out = ST.render(spec)
    assert "### Concurrent-writer safety" in out
    assert "No two concurrent units declare the same file" in out


def test_outcome_cli_missing_file_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert ST.main([str(tmp_path / "nope.json"), "--outcome"]) == 2
    assert "no such spec" in capsys.readouterr().err


def test_outcome_cli_malformed_json_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert ST.main([str(path), "--outcome"]) == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_outcome_cli_invalid_spec_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "outcome-spec.json"
    path.write_text(json.dumps({"nodes": []}), encoding="utf-8")
    assert ST.main([str(path), "--outcome"]) == 2
    assert "invalid spec" in capsys.readouterr().err
