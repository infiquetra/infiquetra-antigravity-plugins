"""Semantic contract tests for evidence-bound ideation."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    terms = ("`seed`", "`alternative`", "`disagreement`", "`convergence`", "agy.agent.execution=passed", "agy.sequential.isolation=passed", "not called independent")
    forbidden = (
        "one response role play counts as independent",
        "self-issued fixtures prove independence",
        "alternatives may be omitted",
    )
    return all(term in text for term in terms) and not any(term in text.lower() for term in forbidden)


def test_ideation_preserves_seeds_alternatives_disagreement_and_artifact() -> None:
    command = (ROOT / "commands/ideate.md").read_text()
    skill = (ROOT / "skills/ideate/SKILL.md").read_text()
    artifact = (ROOT / "skills/ideate/references/ideation-artifact.md").read_text()
    assert "survivors" in command
    assert _valid(skill)
    assert "artifact" in artifact.lower()


def test_ideation_preserves_seeds_alternatives_disagreement_and_artifact_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/ideate/SKILL.md").read_text()
    assert not _valid(skill.replace("agy.agent.execution=passed", "agent narration", 1))
    assert not _valid(skill + "\nOne response role play counts as independent.\n")
    assert "self-issued fixtures" in skill
