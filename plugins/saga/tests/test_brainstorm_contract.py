"""Semantic contract tests for requirements brainstorming."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(term in text for term in ("requirement IDs", "assumptions", "actors", "acceptance examples", "operator"))


def test_brainstorm_requires_requirements_assumptions_actors_and_acceptance_examples() -> None:
    command = (ROOT / "commands/brainstorm.md").read_text()
    skill = (ROOT / "skills/brainstorm/SKILL.md").read_text()
    reference = (ROOT / "skills/brainstorm/references/requirements-sections.md").read_text()
    assert "skills/brainstorm/SKILL.md" in command
    assert _valid(skill)
    assert "Hard floor" in reference


def test_brainstorm_requires_requirements_assumptions_actors_and_acceptance_examples_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/brainstorm/SKILL.md").read_text()
    assert not _valid(skill.replace("acceptance examples", "examples", 1))
