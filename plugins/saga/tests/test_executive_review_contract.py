"""Semantic contract tests for founder and chief-executive review."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    return all(term in text for term in ("product clarity", "user value", "strategic coherence", "operator explicitly chooses", "never constitutes delivery approval"))


def test_executive_review_challenges_value_without_delivery_approval() -> None:
    founder_command = (ROOT / "commands/founder-review.md").read_text()
    alias_command = (ROOT / "commands/ceo-review.md").read_text()
    skill = (ROOT / "skills/founder-review/SKILL.md").read_text()
    assert "review, not an implementer" in founder_command
    assert "alias for `/founder-review`" in alias_command
    assert _valid(skill)


def test_executive_review_challenges_value_without_delivery_approval_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/founder-review/SKILL.md").read_text()
    assert not _valid(skill.replace("never constitutes delivery approval", "approves delivery", 1))
