"""Semantic contract tests for operator-owned strategy."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(
        term in text
        for term in (
            "operator's chosen direction",
            "considered alternatives",
            "constraints",
            "revisit conditions",
            "Rejected alternatives",
            "decision artifact",
            "delivery approval",
        )
    )


def test_strategy_records_choice_alternatives_constraints_and_revisit_trigger() -> None:
    command = (ROOT / "commands/strategy.md").read_text()
    skill = (ROOT / "skills/strategy/SKILL.md").read_text()
    template = (ROOT / "skills/strategy/references/strategy-template.md").read_text()
    assert "records" in command
    assert _valid(skill)
    assert "Not working on" in template


def test_strategy_records_choice_alternatives_constraints_and_revisit_trigger_rejects_negative_cases() -> (
    None
):
    skill = (ROOT / "skills/strategy/SKILL.md").read_text()
    assert not _valid(skill.replace("revisit conditions", "permanent", 1))
