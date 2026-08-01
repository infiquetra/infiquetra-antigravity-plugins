"""Semantic contract tests for advisory office hours."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(term in text for term in ("settled decision frame", "recommended route", "operator override", "never claims implementation", "lifecycle"))


def test_office_hours_returns_frame_and_route_without_completion_claim() -> None:
    command = (ROOT / "commands/office-hours.md").read_text()
    skill = (ROOT / "skills/office-hours/SKILL.md").read_text()
    reference = (ROOT / "skills/office-hours/references/frame-diagnostic.md").read_text()
    assert "HARD GATE" in command
    assert _valid(skill)
    assert "Frame-note template" in reference


def test_office_hours_returns_frame_and_route_without_completion_claim_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/office-hours/SKILL.md").read_text()
    assert not _valid(skill.replace("never claims implementation", "claims implementation", 1))
