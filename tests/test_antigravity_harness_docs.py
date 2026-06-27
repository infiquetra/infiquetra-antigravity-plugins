from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text()


def test_saga_router_agent_is_router_not_worker() -> None:
    text = read("plugins/saga/agents/lifecycle-router.md")

    assert "classify and route" in text
    assert "do not implement non-trivial work" in text
    assert "/office-hours" in text
    assert "/work" in text
    assert "/retro" in text


def test_loop_references_generic_ask_compiler() -> None:
    command = read("plugins/saga/commands/loop.md")
    skill = read("plugins/saga/skills/loop/SKILL.md")
    compiler = read("plugins/saga/skills/loop/references/generic-ask-compiler.md")

    assert "generic-ask-compiler.md" in command
    assert "generic-ask-compiler.md" in skill
    for field in ("target", "repo state", "saga phase", "proof", "scope boundary", "mutation boundary"):
        assert field in compiler


def test_doc_review_references_gemini_appliance() -> None:
    skill = read("plugins/saga/skills/doc-review/SKILL.md")
    appliance = read("plugins/saga/skills/doc-review/references/gemini-review-appliance.md")

    assert "gemini-review-appliance.md" in skill
    for phrase in (
        "fresh session",
        "DISAGREE:",
        "VERDICT:",
        "file:line evidence",
        "read-only",
        "Do not load it as global implementation personality",
    ):
        assert phrase in appliance


def test_escalation_policy_names_paths() -> None:
    text = read("plugins/saga/references/harness-escalation-policy.md")

    assert "inline" in text
    assert "high-thinking Gemini" in text
    assert "multi-agent consensus" in text
