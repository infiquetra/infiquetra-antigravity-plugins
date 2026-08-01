"""Semantic contract tests for bounded optimization."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(
        term in text
        for term in (
            "approved metric",
            "baseline",
            "one-variable change",
            "measured result",
            "stopping condition",
            "never authorizes deployment",
        )
    )


def test_optimization_requires_baseline_change_measurement_and_stop_condition() -> None:
    command = (ROOT / "commands/optimize.md").read_text()
    skill = (ROOT / "skills/optimize/SKILL.md").read_text()
    experiment = (ROOT / "skills/optimize/references/experiment-loop.md").read_text()
    assert "one-variable experiments" in command
    assert _valid(skill)
    assert "seven stopping rules" in experiment


def test_optimization_requires_baseline_change_measurement_and_stop_condition_rejects_negative_cases() -> (
    None
):
    skill = (ROOT / "skills/optimize/SKILL.md").read_text()
    assert not _valid(skill.replace("stopping condition", "continue forever", 1))
