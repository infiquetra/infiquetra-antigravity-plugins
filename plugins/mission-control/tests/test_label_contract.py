"""Acceptance contract for taxonomy-bound, approval-gated label operations."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _valid(skill: str, reference: str) -> bool:
    required = (
        "`labels audit` and field discovery are read-only",
        "explicit operator approval",
        "an audit result alone is never mutation authority",
    )
    forbidden = ("audit results authorize mutation", "unknown labels may be created implicitly")
    combined = skill + "\n" + reference
    return all(term in combined for term in required) and not any(
        term in combined.lower() for term in forbidden
    )


def test_label_skill_preserves_taxonomy_and_mutation_gate() -> None:
    skill = (PLUGIN_ROOT / "skills/labels/SKILL.md").read_text(encoding="utf-8")
    reference = (PLUGIN_ROOT / "skills/labels/references/labels-reference.md").read_text(
        encoding="utf-8"
    )

    for label in ("capability", "enhancement", "defect", "exploration", "context-update"):
        assert f"`{label}`" in skill or f"`{label}`" in reference
    assert "`labels audit` and field discovery are read-only" in skill
    assert "show the\nmutation plan, and obtain explicit operator approval" in skill
    assert "an audit result alone is never mutation authority" in reference
    assert _valid(skill, reference)


def test_label_skill_preserves_taxonomy_and_mutation_gate_rejects_negative_cases() -> None:
    skill = (PLUGIN_ROOT / "skills/labels/SKILL.md").read_text(encoding="utf-8")
    reference = (PLUGIN_ROOT / "skills/labels/references/labels-reference.md").read_text(
        encoding="utf-8"
    )

    assert "Reject unknown labels" in skill
    assert "never create one\nimplicitly from free-form text" in skill
    assert "Unknown requested labels fail validation" in reference
    assert "Audit stops at this report" in skill
    assert not _valid(skill + "\nAudit results authorize mutation.\n", reference)
