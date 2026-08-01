"""Semantic contract tests for decision-complete planning."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    terms = ("decisions", "literal write paths", "unit dependencies", "positive and negative", "test node IDs", "authority gates", "operator approves")
    return all(term in text for term in terms)


def test_plan_contract_requires_decisions_files_dependencies_tests_and_authority() -> None:
    command = (ROOT / "commands/plan.md").read_text()
    skill = (ROOT / "skills/plan/SKILL.md").read_text()
    sections = (ROOT / "skills/plan/references/plan-sections.md").read_text()
    assert "durable" in command
    assert _valid(skill)
    assert "Implementation Units" in sections


def test_plan_contract_requires_decisions_files_dependencies_tests_and_authority_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/plan/SKILL.md").read_text()
    assert not _valid(skill.replace("authority gates", "implicit authority", 1))
