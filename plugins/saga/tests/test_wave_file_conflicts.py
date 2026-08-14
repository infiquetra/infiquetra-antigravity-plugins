"""Concurrent-writer conflict detection across dependency waves (#671)."""

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


def _unit(unit_id: str, files: list[str], **over: Any) -> dict[str, Any]:
    unit: dict[str, Any] = {
        "unit_id": unit_id,
        "label": unit_id,
        "prompt": "do the thing",
        "tier": {"model": "gemini-3.1-pro", "effort": "high"},
        "files": files,
    }
    unit.update(over)
    return unit


def _spec(*units: dict[str, Any]) -> Any:
    return ES.ExecutionSpec.from_dict(
        {"name": "conflict-demo", "description": "d", "units": list(units)}
    )


# --- detection ---------------------------------------------------------------


def test_disjoint_files_in_one_wave_are_fine() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["b.py"]))
    assert ES.wave_file_conflicts(spec) == []


def test_same_file_in_one_wave_conflicts() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"]))
    (conflict,) = ES.wave_file_conflicts(spec)
    assert (conflict.wave, conflict.left, conflict.right) == (1, "U1", "U2")
    assert conflict.files == ("a.py",)


def test_a_dependency_edge_resolves_the_conflict() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"], depends_on=["U1"]))
    assert ES.wave_file_conflicts(spec) == []


def test_units_in_different_waves_never_conflict() -> None:
    spec = _spec(
        _unit("U1", ["a.py"]),
        _unit("U2", ["b.py"], depends_on=["U1"]),
        _unit("U3", ["a.py"], depends_on=["U2"]),
    )
    assert ES.wave_file_conflicts(spec) == []


def test_every_declared_path_participates_not_just_the_first() -> None:
    spec = _spec(_unit("U1", ["a.py", "shared.py"]), _unit("U2", ["b.py", "shared.py"]))
    (conflict,) = ES.wave_file_conflicts(spec)
    assert conflict.files == ("shared.py",)


def test_shared_file_across_different_plugin_directories_conflicts() -> None:
    spec = _spec(
        _unit("U1", ["plugins/saga/x.py", "tests/conftest.py"]),
        _unit("U2", ["plugins/mission-control/y.py", "tests/conftest.py"]),
    )
    (conflict,) = ES.wave_file_conflicts(spec)
    assert conflict.files == ("tests/conftest.py",)


def test_non_adjacent_units_in_the_same_wave_conflict() -> None:
    spec = _spec(
        _unit("U1", ["shared.py"]),
        _unit("U2", ["unrelated.py"]),
        _unit("U3", ["shared.py"]),
    )
    (conflict,) = ES.wave_file_conflicts(spec)
    assert (conflict.left, conflict.right) == ("U1", "U3")


def test_every_conflicting_pair_is_reported() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"]), _unit("U3", ["a.py"]))
    pairs = {(c.left, c.right) for c in ES.wave_file_conflicts(spec)}
    assert pairs == {("U1", "U2"), ("U1", "U3"), ("U2", "U3")}


def test_units_declaring_no_files_never_conflict() -> None:
    spec = _spec(_unit("U1", []), _unit("U2", []))
    assert ES.wave_file_conflicts(spec) == []


def test_a_single_unit_wave_cannot_conflict() -> None:
    assert ES.wave_file_conflicts(_spec(_unit("U1", ["a.py"]))) == []


# --- the halt ----------------------------------------------------------------


def test_assert_raises_and_names_both_units_and_the_file() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"]))
    with pytest.raises(ES.SpecError) as excinfo:
        ES.assert_no_wave_file_conflicts(spec)
    message = str(excinfo.value)
    assert "U1" in message and "U2" in message and "a.py" in message
    assert "depends_on" in message


def test_assert_is_silent_on_a_clean_spec() -> None:
    ES.assert_no_wave_file_conflicts(_spec(_unit("U1", ["a.py"]), _unit("U2", ["b.py"])))


def test_workflow_emit_halts_on_a_conflict() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"]))
    with pytest.raises(ES.SpecError, match="run concurrently declare the same file"):
        ES.emit_workflow_script(spec)


def test_workflow_emit_succeeds_once_sequenced() -> None:
    spec = _spec(_unit("U1", ["a.py"]), _unit("U2", ["a.py"], depends_on=["U1"]))
    assert "agent(" in ES.emit_workflow_script(spec)


def test_committed_specs_have_no_wave_conflicts() -> None:
    specs = sorted(ROOT.glob("docs/plans/*-spec.json"))
    for path in specs:
        spec = ES.ExecutionSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
        assert ES.wave_file_conflicts(spec) == [], path.name
