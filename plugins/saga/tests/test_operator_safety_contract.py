"""Operator-facing Saga safety and portability contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import journal_triggers as triggers  # noqa: E402


def _reference(name: str) -> str:
    return (ROOT / "references" / name).read_text(encoding="utf-8")


def _has_ungated_high_thinking_gemini(text: str) -> bool:
    return any(
        "high-thinking Gemini" in line and "capability-gated" not in line
        for line in text.splitlines()
    )


def test_operator_safety_preserves_choice_escalation_escape_and_formatting() -> None:
    escape_hatches = _reference("escape_hatches.md")
    dry_runs = _reference("command_dry_runs.md")
    escalation = _reference("harness-escalation-policy.md")
    operator_choice = _reference("operator-choice.md")
    formatting = _reference("formatting-style.md")

    assert "canonical repository `docs/` artifacts" in escape_hatches
    assert "A note written into a file is not an approval receipt." in escape_hatches
    assert "Do not synthesize or relabel evidence." in escape_hatches
    assert "brain copy is staging only" in dry_runs
    assert "capability-gated high-thinking Gemini" in escalation
    assert not _has_ungated_high_thinking_gemini(escalation)
    assert "`agy.agent.execution=passed`" in escalation
    assert "`inline`" in operator_choice
    assert "`multi-agent-consensus`" in operator_choice
    assert "Never stack bold labels." in formatting
    assert triggers.detect_targets(
        "Root cause validated; adopt the fix later.",
        [],
    ) == [
        "docs/engineering-journal/LEARNINGS.md",
        "docs/engineering-journal/DECISIONS.md",
        "docs/engineering-journal/QUEUED.md",
    ]


def test_operator_safety_preserves_choice_escalation_escape_and_formatting_rejects_negative_cases() -> (
    None
):
    combined = "\n".join(
        _reference(name)
        for name in (
            "escape_hatches.md",
            "command_dry_runs.md",
            "harness-escalation-policy.md",
        )
    )
    forbidden_instructions = (
        "Manually delete the `## Open Questions`",
        "Changes were manually verified by the operator.",
        "execute it immediately without planning",
        "Brain State Impact:",
    )

    assert all(instruction not in combined for instruction in forbidden_instructions)
    escalation = _reference("harness-escalation-policy.md")
    ungated = escalation.replace(
        "capability-gated high-thinking Gemini",
        "high-thinking Gemini",
    )
    assert _has_ungated_high_thinking_gemini(ungated)
    assert triggers.detect_targets("Routine maintenance completed.", []) == []
