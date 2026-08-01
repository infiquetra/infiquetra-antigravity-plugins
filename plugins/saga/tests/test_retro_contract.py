"""Semantic contract tests for retrospective learning."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    normalized = " ".join(text.split())
    return all(
        term in normalized
        for term in (
            "learning cites delivery evidence",
            "observation",
            "proposed system change",
            "accepts, skips, or modifies",
            "Retrospective analysis never writes Saga lifecycle state",
        )
    )


def test_retro_records_evidence_backed_learning_without_state_mutation() -> None:
    command = (ROOT / "commands/retro.md").read_text()
    skill = (ROOT / "skills/retro/SKILL.md").read_text()
    report = (ROOT / "skills/retro/references/retro-report.md").read_text()
    assert "never writes the saga" in command
    assert _valid(skill)
    assert "link every finding to evidence" in report


def test_retro_records_evidence_backed_learning_without_state_mutation_rejects_negative_cases() -> (
    None
):
    skill = (ROOT / "skills/retro/SKILL.md").read_text()
    assert not _valid(
        skill.replace("Retrospective analysis never writes", "Retrospective analysis writes", 1)
    )
