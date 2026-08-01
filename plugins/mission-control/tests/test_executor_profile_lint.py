"""Acceptance tests for executor profiles resolved through Fleet Core."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import executor_profile_lint  # noqa: E402


def _body(model: str, effort: str, *, justification: str | None = None) -> str:
    lines = [
        "### Recommended Executor Profile",
        f"- **Model:** {model}",
        f"- **Effort:** {effort}",
        "- **Backend:** inline",
    ]
    if justification:
        lines.append(f"- **Justification:** {justification}")
    return "\n".join(lines)


def test_executor_profile_accepts_only_current_gemini_registry() -> None:
    code, messages = executor_profile_lint.lint_body(
        _body("gemini-3.1-pro", "high", justification="Complex bounded implementation")
    )
    assert code == 0
    assert messages == ["executor-profile-lint: ok (model=gemini-3.1-pro effort=high)"]

    code, messages = executor_profile_lint.lint_body(_body("gemini-3.5-flash", "low"))
    assert code == 0
    assert messages == ["executor-profile-lint: ok (model=gemini-3.5-flash effort=low)"]


def test_executor_profile_accepts_only_current_gemini_registry_rejects_negative_cases() -> None:
    invalid = [
        (_body("unknown-model", "high"), "unknown-model"),
        (_body("gemini-3.5-flash", "ultra"), "unknown-effort"),
        (_body("claude-sonnet", "high"), "unknown-model"),
        (_body("gemini-3.1-pro", "high"), "missing-justification"),
    ]
    for body, expected in invalid:
        code, messages = executor_profile_lint.lint_body(body)
        assert code == 1
        assert any(expected in message for message in messages)
