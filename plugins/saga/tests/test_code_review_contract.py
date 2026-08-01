"""Semantic contract tests for plan-bound code review."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    terms = ("reviewer-result.v1", "reviewer identity differs", "plan", "implementation", "agy.agent.execution=passed", "not relabeled as independent review")
    forbidden = (
        "implementation author may act as the independent reviewer",
        "sequential narration counts as independent review",
        "unresolved findings may be accepted",
    )
    return all(term in text for term in terms) and not any(term in text.lower() for term in forbidden)


def test_code_review_requires_plan_comparison_typed_findings_and_disposition() -> None:
    command = (ROOT / "commands/code-review.md").read_text()
    skill = (ROOT / "skills/code-review/SKILL.md").read_text()
    validator = (ROOT / "skills/code-review/references/validator.md").read_text()
    assert "built-vs-planned" in command
    assert _valid(skill)
    assert "typed findings" in validator and "operator disposition" in validator


def test_code_review_requires_plan_comparison_typed_findings_and_disposition_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/code-review/SKILL.md").read_text()
    assert not _valid(skill.replace("reviewer-result.v1", "untyped review", 1))
    assert not _valid(skill + "\nThe implementation author may act as the independent reviewer.\n")
    assert "asked to originate an independent validator" in skill
