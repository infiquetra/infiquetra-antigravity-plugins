"""Semantic contract tests for identity-bound quality assurance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import qa_health_score  # noqa: E402


def _valid(text: str) -> bool:
    terms = (
        "producer_id",
        "tester_id",
        "test_node_ids",
        "must differ",
        "agy.agent.execution=passed",
        "cannot certify its own work",
    )
    forbidden = (
        "producer and tester may be the same",
        "the producer may certify its own work",
        "failed tests may be accepted",
    )
    return all(term in text for term in terms) and not any(
        term in text.lower() for term in forbidden
    )


def test_qa_requires_risk_scenarios_checks_failure_disposition_and_independence() -> None:
    command = (ROOT / "commands/qa.md").read_text()
    skill = (ROOT / "skills/qa/SKILL.md").read_text()
    taxonomy = (ROOT / "skills/qa/references/risk-taxonomy.md").read_text()
    assert "acceptance-evidence GATE" in command
    assert _valid(skill)
    assert "9-way risk router" in taxonomy
    score = qa_health_score.score_findings({"behavior": {"high": 1}, "docs": {}})
    assert score["overall"] == 87


def test_qa_requires_risk_scenarios_checks_failure_disposition_and_independence_rejects_negative_cases() -> (
    None
):
    skill = (ROOT / "skills/qa/SKILL.md").read_text()
    assert not _valid(skill.replace("must differ", "may match", 1))
    assert not _valid(skill + "\nThe producer and tester may be the same.\n")
    with pytest.raises(ValueError, match="unknown risk classes"):
        qa_health_score.score_findings({"invented": {}})
    with pytest.raises(ValueError, match="non-negative integers"):
        qa_health_score.score_findings({"behavior": {"high": -1}})
