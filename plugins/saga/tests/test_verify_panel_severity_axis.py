"""Tests for refute-N verify panel severity axis and even-N quorum floor (#686)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

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


def _unit(unit_id: str, **over: Any) -> dict[str, Any]:
    unit: dict[str, Any] = {
        "unit_id": unit_id,
        "label": unit_id,
        "prompt": "do the thing",
        "tier": {"model": "gemini-3.1-pro", "effort": "high"},
    }
    unit.update(over)
    return unit


def _spec(*units: dict[str, Any]) -> Any:
    return ES.ExecutionSpec.from_dict(
        {"name": "severity-demo", "description": "d", "units": list(units)}
    )


def test_verifier_schema_requires_both_buckets() -> None:
    schema = ES._verifier_schema()
    props = schema["properties"]
    assert "refuted_deliverable" in props
    assert "advisory_corrections" in props
    assert "refuted" not in props
    reqs = schema["required"]
    assert "refuted_deliverable" in reqs
    assert "advisory_corrections" in reqs
    assert "refuted" not in reqs


def test_verifier_prompt_describes_severity_split() -> None:
    unit = ES.Unit.from_dict(_unit("U1"))
    prompt = ES._verifier_prompt(unit)
    assert "refuted_deliverable" in prompt
    assert "advisory_corrections" in prompt
    assert "VERDICT CONTRACT" in prompt


def test_quorum_floor_uses_strict_majority_for_even_n() -> None:
    # For even n=2 -> floor 2; n=4 -> floor 3; n=6 -> floor 4
    # For odd n=1 -> floor 1; n=3 -> floor 2; n=5 -> floor 3; n=7 -> floor 4
    for n, expected_floor in [(1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4)]:
        spec = _spec(_unit("U1", verify={"n": n, "pass_rule": "majority"}))
        script = ES.emit_workflow_script(spec)
        assert f"quorum floor {expected_floor}" in script


def test_emitted_harness_contains_advisory_helpers_and_return() -> None:
    spec = _spec(_unit("U1", verify={"n": 3, "pass_rule": "majority"}))
    script = ES.emit_workflow_script(spec)
    assert "const __advisories = []" in script
    assert "function __logAdvisory" in script
    assert "function __renderAdvisory" in script
    assert "function __halt" in script
    assert "Array.isArray(v.refuted_deliverable) && Array.isArray(v.advisory_corrections)" in script
    assert "v.refuted_deliverable.length > 0" in script
    assert "__logAdvisory(\"U1\"" in script
    assert "return { units: { \"U1\": U1 }, advisory_corrections: __advisories }" in script


def test_even_panel_under_strength_gate_never_fails_open() -> None:
    # n=2: floor 2 — a single reporting verifier triggers UNDER-STRENGTH, never quorum.
    script2 = ES.emit_workflow_script(_spec(_unit("U1", verify={"n": 2, "pass_rule": "majority"})))
    assert "(U1_reported.length < 2" in script2
    assert "verifier-under-strength" in script2
    # n=4: floor 3 — two reporting verifiers (the old ceil(n/2) floor) is under-strength.
    script4 = ES.emit_workflow_script(_spec(_unit("U1", verify={"n": 4, "pass_rule": "majority"})))
    assert "(U1_reported.length < 3" in script4


def test_malformed_verdict_missing_a_bucket_is_not_a_reporter() -> None:
    schema = ES._verifier_schema()
    required = set(schema["required"])
    valid = {
        "refuted_deliverable": [],
        "advisory_corrections": [],
        "upheld": [],
        "verifier_identity": "v1",
        "fallback_depth": 0,
        "examined_sha": "abc123",
    }
    assert required <= set(valid)
    for missing in ("refuted_deliverable", "advisory_corrections"):
        payload = {key: value for key, value in valid.items() if key != missing}
        assert not required <= set(payload), f"{missing}-less payload must not satisfy the schema"
    script = ES.emit_workflow_script(_spec(_unit("U1", verify={"n": 2, "pass_rule": "majority"})))
    assert "Array.isArray(v.refuted_deliverable) && Array.isArray(v.advisory_corrections)" in script
