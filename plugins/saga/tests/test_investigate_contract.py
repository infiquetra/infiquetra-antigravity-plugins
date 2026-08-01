"""Semantic contract tests for root-cause investigation."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(
        term in text
        for term in (
            "observed facts",
            "hypotheses",
            "experiments",
            "root cause",
            "unresolved uncertainty",
            "operator explicitly chooses",
        )
    )


def test_investigation_separates_observation_hypothesis_experiment_and_uncertainty() -> None:
    command = (ROOT / "commands/investigate.md").read_text()
    skill = (ROOT / "skills/investigate/SKILL.md").read_text()
    assert "ROOT CAUSE" in command
    assert _valid(skill)
    assert "unresolved uncertainty" in skill


def test_investigation_separates_observation_hypothesis_experiment_and_uncertainty_rejects_negative_cases() -> (
    None
):
    skill = (ROOT / "skills/investigate/SKILL.md").read_text()
    assert not _valid(skill.replace("unresolved uncertainty", "certainty", 1))
