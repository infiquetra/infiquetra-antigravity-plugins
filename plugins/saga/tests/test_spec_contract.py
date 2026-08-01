"""Semantic contract tests for outcome-first specifications."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    terms = ("required outcome", "scope boundaries", "failure modes", "observable", "acceptance behavior", "excludes implementation choices", "block finalization")
    return all(term in text for term in terms)


def test_spec_defines_outcome_scope_failures_and_acceptance_without_how() -> None:
    command = (ROOT / "commands/spec.md").read_text()
    skill = (ROOT / "skills/spec/SKILL.md").read_text()
    template = (ROOT / "skills/spec/references/spec-template.md").read_text()
    assert "WHAT" in command
    assert _valid(skill)
    assert "Acceptance Criteria" in template and "Failure Modes" in template


def test_spec_defines_outcome_scope_failures_and_acceptance_without_how_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/spec/SKILL.md").read_text()
    assert not _valid(skill.replace("excludes implementation choices", "chooses implementation", 1))
