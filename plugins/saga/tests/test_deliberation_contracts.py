"""Reference Saga phases declare deterministic deliberation coverage."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).parent.parent
SKILLS = {
    name: ROOT / "skills" / name / "SKILL.md"
    for name in ("ideate", "brainstorm", "plan", "doc-review", "code-review", "qa")
}

EXPECTED_STRATEGIES = {
    "ideate": {
        "pain-friction",
        "inversion-removal-automation",
        "assumption-reframing",
        "leverage-compounding",
        "cross-domain-analogy",
        "constraint-flipping",
    },
    "brainstorm": {
        "evidence-gap",
        "specificity-gap",
        "counterfactual-gap",
        "attachment-gap",
        "durability-gap",
    },
    "plan": {
        "requirements",
        "technical-decisions",
        "implementation-units",
        "system-impact",
        "risks-dependencies",
    },
    "doc-review": {
        "verification",
        "assumptions",
        "requirement-mapping",
        "completeness",
        "open-choice-pressure",
        "adversarial-failure-modes",
    },
    "code-review": {
        "correctness",
        "security",
        "testing",
        "maintainability",
        "deploy-migration",
        "reliability",
        "performance",
        "api-contract",
        "adversarial",
        "agent-native",
        "previous-comments",
    },
    "qa": {
        "behavior",
        "security",
        "infra",
        "api",
        "deployment",
        "data",
        "config",
        "docs",
        "trivial",
    },
}


def _contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<!-- saga-deliberation-phase\n(.*?)\n-->", text, re.DOTALL)
    assert match is not None, f"{path} has no deliberation contract"
    return cast(dict[str, Any], json.loads(match.group(1)))


def test_every_reference_phase_declares_approved_minimum_and_applicability() -> None:
    for phase, path in SKILLS.items():
        contract = _contract(path)
        assert set(contract) == {
            "schema",
            "phase",
            "strategies",
            "minimum_coverage",
            "applicability_rule",
            "completion_quality",
            "cheap_first_escalation",
        }
        assert contract["schema"] == "saga.deliberation-phase.v1"
        assert contract["phase"] == phase
        assert contract["minimum_coverage"]["rule"] == "all-applicable"
        assert contract["minimum_coverage"]["floor"] >= 1
        assert "operator decision" in contract["applicability_rule"].lower()
        assert contract["completion_quality"].strip()
        assert isinstance(contract["cheap_first_escalation"]["allowed"], bool)

        strategies = contract["strategies"]
        strategy_ids = [row["strategy_id"] for row in strategies]
        assert set(strategy_ids) == EXPECTED_STRATEGIES[phase]
        assert len(strategy_ids) == len(set(strategy_ids))
        assert all(row["role"].strip() and row["applies_when"].strip() for row in strategies)


def test_phase_contracts_require_receipts_and_block_incomplete_coverage() -> None:
    for path in SKILLS.values():
        text = path.read_text(encoding="utf-8")
        assert "deliberation.py" in text
        assert "receipt" in text.lower()
        assert "incomplete" in text.lower()
