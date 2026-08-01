"""Acceptance contract for read-only rollout census and approved mutation."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _valid(skill: str, reference: str) -> bool:
    combined = skill + "\n" + reference
    required = ("read-only census operations", "separate mutation", "explicit operator approval")
    forbidden = ("gap reports authorize deployment", "status requests authorize tracking updates")
    return all(term in combined for term in required) and not any(term in combined.lower() for term in forbidden)


def test_rollout_skill_separates_status_gap_analysis_and_mutation() -> None:
    skill = (PLUGIN_ROOT / "skills/rollout/SKILL.md").read_text(encoding="utf-8")
    reference = (
        PLUGIN_ROOT / "skills/rollout/references/work-hierarchy.md"
    ).read_text(encoding="utf-8")

    assert "`rollout status` and `rollout gap-analysis` are read-only census operations" in skill
    assert "Every `deploy-*` or\n`rollout update` operation is a separate mutation" in skill
    assert "obtain explicit operator approval" in skill
    assert "Rollout census and gap analysis are read-only views" in reference
    assert "`operations`, `asgard`, or `campps`" in skill
    assert _valid(skill, reference)


def test_rollout_skill_separates_status_gap_analysis_and_mutation_rejects_negative_cases() -> None:
    skill = (PLUGIN_ROOT / "skills/rollout/SKILL.md").read_text(encoding="utf-8")
    reference = (
        PLUGIN_ROOT / "skills/rollout/references/work-hierarchy.md"
    ).read_text(encoding="utf-8")

    assert "never deploy, create or edit an issue, or update tracking state" in skill
    assert "Never treat a gap report or status\nrequest as approval to mutate" in skill
    assert "do not authorize\ntemplate or label deployment, issue changes" in reference
    assert "infiquetra-claude-plugins" not in skill
    assert "mount-olympus" not in skill
    assert not _valid(skill + "\nGap reports authorize deployment.\n", reference)
