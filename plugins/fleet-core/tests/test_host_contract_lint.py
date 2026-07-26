from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
REPO_ROOT = FLEET_CORE.parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

LINT = fleet_commons_shim.load("host_contract_lint")
CAPS = fleet_commons_shim.load("antigravity_capabilities")
FIXTURES = Path(__file__).parent / "fixtures" / "host-contract"
SELECTOR_PATH = FLEET_CORE / "references" / "antigravity-host-contract-surfaces.json"


def _selector():
    return LINT.load_selector(SELECTOR_PATH, REPO_ROOT)


def _known_capabilities() -> set[str]:
    catalog = CAPS.load_catalog(
        FLEET_CORE / "references" / "antigravity-capability-probes.yaml"
    )
    return {row["id"] for row in catalog["capabilities"]}


def test_selector_is_closed_and_declared_paths_exist() -> None:
    selector = _selector()
    assert LINT.validate_selector(selector, REPO_ROOT) == []
    assert LINT.selector_digest(selector) == LINT.selector_digest(copy.deepcopy(selector))
    paths = LINT.selected_active_paths(REPO_ROOT, selector)
    assert REPO_ROOT / "plugins/saga/skills/work/SKILL.md" in paths
    assert REPO_ROOT / ".agents/skills/port-claude-plugins/SKILL.md" in paths


def test_named_active_rules_emit_exact_ids_and_unresolved_findings() -> None:
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        (FIXTURES / "active-all.md").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert [finding["rule"] for finding in findings] == [
        "AGHC001",
        "AGHC002",
        "AGHC003",
        "AGHC004",
        "AGHC005",
        "AGHC006",
    ]
    assert all(finding["classification"] == "active" for finding in findings)
    assert all(finding["unresolved"] for finding in findings)
    assert all("excerpt" not in finding for finding in findings)


def test_historical_annotations_classify_only_the_adjacent_match() -> None:
    findings = LINT.scan_text(
        "docs/history.md",
        (FIXTURES / "historical-all.md").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert len(findings) == 6
    assert {finding["classification"] for finding in findings} == {"historical"}
    assert not any(finding["unresolved"] for finding in findings)


def test_markdown_quote_is_active_without_lineage_annotation() -> None:
    findings = LINT.scan_text(
        "plugins/saga/references/example.md",
        "> Run `Workflow(\"source\")` now.",
        known_capabilities=_known_capabilities(),
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "AGHC003"
    assert findings[0]["unresolved"] is True


def test_foreign_runtime_requires_read_only_and_does_not_hide_write() -> None:
    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        (FIXTURES / "executable-claude-path.py").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert findings[0]["classification"] == "foreign-runtime-input"
    assert findings[0]["unresolved"] is False
    assert findings[1]["classification"] == "active"
    assert findings[1]["unresolved"] is True


@pytest.mark.parametrize(("state", "unresolved"), [("passed", False), ("unknown", True)])
def test_capability_gate_requires_passing_evidence(state: str, unresolved: bool) -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"capability-gated",'
        '"rule":"AGHC006","reason":"runtime isolation is required",'
        '"revisit":"remove when host contract changes",'
        '"capability":"agy.sandbox.isolation"} -->\n'
        "The host guarantees isolated worktree execution."
    )
    findings = LINT.scan_text(
        "plugins/saga/skills/work/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
        capability_states={"agy.sandbox.isolation": state},
    )
    assert findings[0]["classification"] == "capability-gated"
    assert findings[0]["unresolved"] is unresolved


@pytest.mark.parametrize(
    "annotation",
    [
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC999",'
        '"reason":"legacy","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"foreign-runtime-input","rule":"AGHC003",'
        '"reason":"legacy","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"all * workflows","revisit":"later"} -->',
    ],
)
def test_exemption_abuse_fails_closed(annotation: str) -> None:
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        f"{annotation}\nRun `Workflow(\"source\")`.",
        known_capabilities=_known_capabilities(),
    )
    assert findings[0]["classification"] == "active"
    assert findings[0]["unresolved"] is True


def test_nonadjacent_annotation_is_an_unresolved_finding() -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"legacy","revisit":"later"} -->\n\n'
        "Run `Workflow(\"source\")`."
    )
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
    )
    assert {finding["rule"] for finding in findings} == {"AGHC000", "AGHC003"}
    assert all(finding["unresolved"] for finding in findings)


def test_false_positive_controls_do_not_match() -> None:
    text = "\n".join(
        [
            "The hermes-claude-code-router product name is historical.",
            "Schedules belong in the issue tracker.",
            "Networking isolation prose is descriptive.",
            "The test uses a generic workflow object.",
        ]
    )
    assert LINT.scan_text("plugins/saga/references/control.md", text) == []


def test_comparison_corpus_is_classified_not_silently_ignored() -> None:
    findings = LINT.scan_text(
        "tests/source_lineage.md",
        "The source called `AskUserQuestion`.",
        default_classification="historical",
    )
    assert findings[0]["classification"] == "historical"
    assert findings[0]["unresolved"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda selector: selector.update({"unknown": True}),
        lambda selector: selector["exact_paths"].append("/tmp/absolute"),
        lambda selector: selector["exact_paths"].append("../escape"),
        lambda selector: selector["exact_paths"].append("missing-file.md"),
        lambda selector: selector["active_globs"].append("**"),
        lambda selector: selector.update({"digest_inputs": ["schema"]}),
    ],
)
def test_selector_abuse_fails_before_scanning(mutation) -> None:
    selector = _selector()
    mutation(selector)
    assert LINT.validate_selector(selector, REPO_ROOT)


def test_lint_receipt_is_strict_excerpt_free_and_digest_bound() -> None:
    selector = _selector()
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        "Run `Workflow(\"source\")`.",
        known_capabilities=_known_capabilities(),
    )
    receipt = LINT.build_lint_receipt(selector, findings)
    assert receipt["schema"] == LINT.LINT_RECEIPT_SCHEMA
    assert receipt["unresolved_count"] == 1
    assert LINT.validate_lint_receipt(receipt) == []

    unsafe = copy.deepcopy(receipt)
    unsafe["findings"][0]["path"] = "/Users/alice/private.md"
    unsafe["findings"][0]["excerpt"] = "private prompt"
    errors = LINT.validate_lint_receipt(unsafe)
    assert errors
    assert "/Users/alice" not in json.dumps(errors)
    assert "private prompt" not in json.dumps(errors)
