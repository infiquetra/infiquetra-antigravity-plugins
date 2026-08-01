"""Buildability-probe contract tests shared by `/impl-spec` and `/doc-review`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import impl_spec as M  # noqa: E402, N812

FIXTURE = Path(__file__).parent / "fixtures/impl-spec/buildability-failure/result.json"


def _passing() -> dict[str, object]:
    return {
        "schema": M.PROBE_SCHEMA,
        "subject": "reference-service",
        "round": 1,
        "implementation_breakdown": {
            "repositories": ["reference-repo"],
            "modules": ["reference_service"],
            "endpoints": [],
            "entities": ["Record"],
            "events_published": [],
            "events_consumed": [],
            "tests": ["contract validation"],
        },
        "questions": {
            "product": [],
            "architecture": [],
            "data": [],
            "api": [
                {
                    "question": "Which internal method name should be used?",
                    "classification": "execution-discovery",
                    "reasoning": "The choice is not externally visible.",
                }
            ],
            "operations": [],
        },
        "verdict": "PASS",
    }


def test_failure_fixture_is_structured_and_fails_on_boundary_defect() -> None:
    result = M.load_probe_result(FIXTURE)
    assert result.verdict == "FAIL"
    assert result.round == 1
    assert result.questions["api"][0]["classification"] == "spec-defect"


def test_zero_boundary_defects_is_a_hard_pass() -> None:
    result = M.ProbeResult.from_dict(_passing())
    assert result.verdict == "PASS"
    assert set(result.questions) == set(M.QUESTION_CATEGORIES)
    assert result.to_dict() == _passing()


def test_verdict_cannot_override_derived_boundary_result() -> None:
    failing = json.loads(FIXTURE.read_text(encoding="utf-8"))
    failing["verdict"] = "PASS"
    with pytest.raises(M.ImplSpecError, match="must be FAIL"):
        M.ProbeResult.from_dict(failing)

    passing = _passing()
    passing["verdict"] = "FAIL"
    with pytest.raises(M.ImplSpecError, match="must be PASS"):
        M.ProbeResult.from_dict(passing)


def test_every_question_category_must_be_present_even_when_empty() -> None:
    missing = _passing()
    source_questions = missing["questions"]
    assert isinstance(source_questions, dict)
    questions = dict(source_questions)
    questions.pop("operations")
    missing["questions"] = questions
    with pytest.raises(M.ImplSpecError, match="every question category"):
        M.ProbeResult.from_dict(missing)


@pytest.mark.parametrize("round_number", [0, 4, True])
def test_probe_remediation_round_is_bounded(round_number: int | bool) -> None:
    payload = _passing()
    payload["round"] = round_number
    with pytest.raises(M.ImplSpecError, match="between 1 and 3"):
        M.ProbeResult.from_dict(payload)


def test_probe_shape_is_closed() -> None:
    payload = _passing()
    payload["authoring_notes"] = "must not reach fresh probe"
    with pytest.raises(M.ImplSpecError, match="unknown or missing"):
        M.ProbeResult.from_dict(payload)


def test_doc_review_exposes_reusable_fresh_context_buildability_mode() -> None:
    skill = (ROOT / "skills/doc-review/SKILL.md").read_text(encoding="utf-8")
    protocol = (ROOT / "references/buildability-probe-protocol.md").read_text(encoding="utf-8")

    for marker in (
        "## Buildability Probe Mode",
        "operator explicitly requests a buildability probe",
        "`/impl-spec` invokes it",
        "profile-backed multi-document spec set",
        "agy.agent.execution=passed",
        "agy.sequential.isolation=passed",
        "Same-context roleplay cannot produce",
        "saga.buildability-probe.v1",
        "PASS requires zero `spec-defect` questions",
    ):
        assert marker in skill
    for category in M.QUESTION_CATEGORIES:
        assert category in protocol.casefold()
    assert "at most three rounds" in " ".join(protocol.split())
    assert "does not replace" in skill
