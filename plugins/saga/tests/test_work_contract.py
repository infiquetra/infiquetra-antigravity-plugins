"""Semantic contract tests for approved work execution."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _valid(text: str) -> bool:
    terms = (
        "approved units",
        "literal write sets",
        "dependency order",
        "exact checks",
        "preserve unrelated changes",
        "authority gates",
        "Never self-certify",
    )
    forbidden = (
        "may edit outside the literal write sets",
        "may bypass authority gates",
        "may self-certify completion",
        "failed checks may be reported as complete",
    )
    return all(term in text for term in terms) and not any(
        term in text.lower() for term in forbidden
    )


def test_work_obeys_units_write_sets_checks_and_authority_gates() -> None:
    command = (ROOT / "commands/work.md").read_text()
    skill = (ROOT / "skills/work/SKILL.md").read_text()
    gates = (ROOT / "skills/work/references/test-and-gates.md").read_text()
    assert "explicit operator confirmation" in command
    assert _valid(skill)
    assert "no completion" in gates


def test_work_obeys_units_write_sets_checks_and_authority_gates_rejects_negative_cases() -> None:
    skill = (ROOT / "skills/work/SKILL.md").read_text()
    assert not _valid(skill.replace("literal write sets", "any path", 1))
    assert not _valid(skill + "\nThe worker may edit outside the literal write sets.\n")
    assert not _valid(skill + "\nThe worker may self-certify completion.\n")
