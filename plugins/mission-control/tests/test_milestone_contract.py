"""Acceptance contract for evidence-backed milestone operations."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _valid(skill: str, reference: str) -> bool:
    combined = skill + "\n" + reference
    required = ("progress", "risk evidence", "explicit operator approval", "linked work")
    forbidden = (
        "progress reports authorize milestone creation",
        "missing risk evidence may be ignored",
    )
    return all(term in combined for term in required) and not any(
        term in combined.lower() for term in forbidden
    )


def test_milestone_skill_requires_objective_progress_and_risk_evidence() -> None:
    skill = (PLUGIN_ROOT / "skills/milestones/SKILL.md").read_text(encoding="utf-8")
    reference = (PLUGIN_ROOT / "skills/milestones/references/objective-workflow.md").read_text(
        encoding="utf-8"
    )

    for term in ("Objective", "progress", "risk evidence", "linked work"):
        assert term in skill or term in reference
    assert "Listing and progress checks are read-only evidence" in skill
    assert "obtain explicit operator approval" in skill
    assert "--project campps" in skill
    assert "--project campps" in reference
    assert _valid(skill, reference)


def test_milestone_skill_requires_objective_progress_and_risk_evidence_rejects_negative_cases() -> (
    None
):
    skill = (PLUGIN_ROOT / "skills/milestones/SKILL.md").read_text(encoding="utf-8")
    reference = (PLUGIN_ROOT / "skills/milestones/references/objective-workflow.md").read_text(
        encoding="utf-8"
    )

    assert "Never infer approval from a progress report" in skill
    assert "Missing progress or risk evidence stops\ncreation" in reference
    assert "infiquetra-claude-plugins" not in skill
    assert "--project mount-olympus" not in skill
    assert "--project mount-olympus" not in reference
    assert not _valid(skill + "\nProgress reports authorize milestone creation.\n", reference)
