"""Subprocess tests for receipt commands used by live Antigravity phases."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DELIBERATION = REPO_ROOT / "plugins/multi-agent-consensus/scripts/deliberation.py"
TRANSITION = REPO_ROOT / "plugins/saga/scripts/transition_receipts.py"
PROMOTION = REPO_ROOT / "plugins/saga/scripts/artifact_promotion.py"
CANARY = REPO_ROOT / "scripts/run_agy_saga_canary.py"
ARTIFACT_PHASES = (
    "ideate",
    "brainstorm",
    "impl-spec",
    "plan",
    "doc-review",
    "work",
    "code-review",
    "qa",
    "retro",
    "handoff",
)
DELIBERATION_PHASES = ("ideate", "brainstorm", "plan", "doc-review", "code-review", "qa")


def _load_canary() -> ModuleType:
    spec = importlib.util.spec_from_file_location("live_receipt_command_canary", CANARY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _run(script: Path, workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        [sys.executable, str(script), *args],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )


def _deliberation_inputs(workspace: Path) -> None:
    host = workspace / "docs/evidence/host.json"
    _write(host, {"state": "passed"})
    _write(
        workspace / "inputs/manifest.json",
        {
            "schema": "multi-agent-consensus.deliberation-manifest.v1",
            "manifest_id": "reference-ideate",
            "phase": "ideate",
            "strategies": [
                {
                    "strategy_id": "constraint-frame",
                    "role": "Constraint frame",
                    "applicable": True,
                    "applicability_reason": "required by the phase contract",
                    "applicability_rule": "reference lifecycle",
                    "operator_decision_ref": "",
                }
            ],
            "minimum_coverage": 1,
            "requested": {"model": "gemini-3.1-pro", "effort": "high"},
            "allowed_tools": ["read", "search"],
            "execution_bounds": {"max_workers": 1, "max_turns_per_strategy": 3},
            "expected_result_fields": ["summary", "claims"],
            "convergence": {"rule": "adjudicated-synthesis", "preserve_disagreement": True},
            "recovery": {"max_attempts_per_strategy": 2},
            "escalation": {"mode": "fixed", "escalated_model": "", "triggers": []},
            "host_capability_receipt": {
                "reference": "docs/evidence/host.json",
                "sha256": _sha(host),
                "states": {
                    "agy.model.selection": "passed",
                    "agy.agent.execution": "unavailable",
                    "agy.sequential.isolation": "passed",
                },
            },
        },
    )
    _write(
        workspace / "inputs/results.json",
        [
            {
                "execution_id": "ideate-execution-1",
                "strategy_id": "constraint-frame",
                "attempt": 1,
                "mode": "isolated-sequential",
                "status": "succeeded",
                "requested": {
                    "model": "gemini-3.1-pro",
                    "effort": "high",
                    "tools": ["read"],
                },
                "observed": {
                    "model": "unknown",
                    "effort": "unknown",
                    "tools": "unknown",
                    "isolation": "isolated-sequential",
                    "worker_count": "unknown",
                },
                "output": {"summary": "constraints retained", "claims": ["no remote"]},
                "evidence_refs": ["seed.md"],
            }
        ],
    )
    _write(
        workspace / "inputs/convergence.json",
        {"summary": "constraints retained", "disagreements": [], "adjudication": ""},
    )
    _write(
        workspace / "inputs/escalation.json",
        {"selected_model": "gemini-3.1-pro", "trigger_evidence": []},
    )


def _contract(workspace: Path) -> None:
    _write(
        workspace / "docs/outcomes/reference-lifecycle/obligation-contract.json",
        {
            "schema": "saga.lifecycle-obligation.v1",
            "contract_id": "reference-lifecycle-v1",
            "workstream_id": "reference-lifecycle",
            "stored_lifecycle_phases": ["ideation"],
            "off_chain_obligations": [],
            "obligations": [
                {
                    "obligation_id": "ideate",
                    "kind": "stored-phase",
                    "subject": "reference-lifecycle",
                    "requirement": "required",
                    "producer": "phase-worker",
                    "required_evidence": [
                        {
                            "kind": "deliberation-receipt",
                            "minimum_count": 1,
                            "independent": False,
                        }
                    ],
                    "phase": "ideation",
                }
            ],
        },
    )


def _run_deliberation(workspace: Path) -> dict[str, Any]:
    result = _run(
        DELIBERATION,
        workspace,
        "evaluate",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--manifest",
        "inputs/manifest.json",
        "--results",
        "inputs/results.json",
        "--convergence",
        "inputs/convergence.json",
        "--escalation",
        "inputs/escalation.json",
    )
    assert result.returncode == 0, result.stderr
    return cast(dict[str, Any], json.loads(result.stdout))


def _run_transition(workspace: Path, deliberation: dict[str, Any]) -> dict[str, Any]:
    receipt_path = workspace / deliberation["receipt_path"]
    _write(
        workspace / "inputs/evidence.json",
        {
            "input_refs": [],
            "operator_decisions": [],
            "execution_receipts": [],
            "canonical_outputs": [],
            "check_results": [],
            "review_findings": [],
            "lifecycle_evidence": [
                {
                    "evidence_id": "ideate-deliberation",
                    "kind": "deliberation-receipt",
                    "subject": "reference-lifecycle",
                    "producer": "phase-worker",
                    "reference": deliberation["receipt_path"],
                    "digest": _sha(receipt_path),
                    "verification_state": "verified",
                    "assertion": "complete",
                }
            ],
            "external_facts": [],
        },
    )
    result = _run(
        TRANSITION,
        workspace,
        "build",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--contract",
        "docs/outcomes/reference-lifecycle/obligation-contract.json",
        "--transition-id",
        "ideate-complete",
        "--obligation-id",
        "ideate",
        "--evidence",
        "inputs/evidence.json",
    )
    assert result.returncode == 0, result.stderr
    return cast(dict[str, Any], json.loads(result.stdout))


def test_commands_emit_valid_receipt_chain_in_no_remote_repository(tmp_path: Path) -> None:
    _deliberation_inputs(tmp_path)
    _contract(tmp_path)
    staged = tmp_path / ".gemini/saga/staging/ideate.md"
    staged.parent.mkdir(parents=True)
    staged.write_text("# Reference idea\n\nNo remote mutation.\n", encoding="utf-8")

    deliberation = _run_deliberation(tmp_path)
    transition = _run_transition(tmp_path, deliberation)
    promotion_result = _run(
        PROMOTION,
        tmp_path,
        "promote",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--phase",
        "ideate",
        "--source-role",
        "antigravity-runtime",
        "--source-ref",
        ".gemini/saga/staging/ideate.md",
        "--staged-file",
        ".gemini/saga/staging/ideate.md",
        "--target-ref",
        "docs/ideation/reference-idea.md",
        "--transition-receipt",
        transition["receipt_path"],
    )

    assert promotion_result.returncode == 0, promotion_result.stderr
    promotion = json.loads(promotion_result.stdout)
    assert promotion["state"] == "satisfied"
    assert (tmp_path / "docs/ideation/reference-idea.md").is_file()
    assert not (tmp_path / ".git/config").exists()
    bindings = _load_canary()._receipt_bindings(tmp_path)
    assert all(bindings[group] for group in ("deliberation", "transition", "promotion"))


def test_commands_fail_closed_for_invalid_input_path_and_conflict(tmp_path: Path) -> None:
    _deliberation_inputs(tmp_path)
    escaped = _run(
        DELIBERATION,
        tmp_path,
        "evaluate",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--manifest",
        "../manifest.json",
        "--results",
        "inputs/results.json",
        "--convergence",
        "inputs/convergence.json",
        "--escalation",
        "inputs/escalation.json",
    )
    assert escaped.returncode == 2
    assert "repository-relative" in escaped.stderr

    malformed = tmp_path / "inputs/malformed.json"
    malformed.write_text("not-json", encoding="utf-8")
    invalid = _run(
        DELIBERATION,
        tmp_path,
        "evaluate",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--manifest",
        "inputs/malformed.json",
        "--results",
        "inputs/results.json",
        "--convergence",
        "inputs/convergence.json",
        "--escalation",
        "inputs/escalation.json",
    )
    assert invalid.returncode == 2
    assert "invalid JSON" in invalid.stderr

    _write(tmp_path / "inputs/bad-contract.json", {})
    _write(
        tmp_path / "inputs/empty-evidence.json",
        {
            name: []
            for name in (
                "input_refs",
                "operator_decisions",
                "execution_receipts",
                "canonical_outputs",
                "check_results",
                "review_findings",
                "lifecycle_evidence",
                "external_facts",
            )
        },
    )
    bad_contract = _run(
        TRANSITION,
        tmp_path,
        "build",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--contract",
        "inputs/bad-contract.json",
        "--transition-id",
        "ideate-complete",
        "--obligation-id",
        "ideate",
        "--evidence",
        "inputs/empty-evidence.json",
    )
    assert bad_contract.returncode == 2
    assert "Traceback" not in bad_contract.stderr

    _contract(tmp_path)
    deliberation = _run_deliberation(tmp_path)
    transition = _run_transition(tmp_path, deliberation)
    staged = tmp_path / ".gemini/saga/staging/ideate.md"
    staged.parent.mkdir(parents=True)
    staged.write_text("# New candidate\n", encoding="utf-8")
    canonical = tmp_path / "docs/ideation/reference-idea.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# Existing decision\n", encoding="utf-8")
    conflict = _run(
        PROMOTION,
        tmp_path,
        "promote",
        "--repo-root",
        ".",
        "--outcome-id",
        "reference-lifecycle",
        "--phase",
        "ideate",
        "--source-role",
        "antigravity-runtime",
        "--source-ref",
        ".gemini/saga/staging/ideate.md",
        "--staged-file",
        ".gemini/saga/staging/ideate.md",
        "--target-ref",
        "docs/ideation/reference-idea.md",
        "--transition-receipt",
        transition["receipt_path"],
    )
    assert conflict.returncode == 2
    assert json.loads(conflict.stdout)["state"] == "conflicting"
    assert canonical.read_text(encoding="utf-8") == "# Existing decision\n"
    assert list((tmp_path / "docs/outcomes/reference-lifecycle/conflicts").glob("*.md"))


def test_reference_skills_contain_complete_installed_receipt_commands() -> None:
    for phase in ARTIFACT_PHASES:
        text = (REPO_ROOT / f"plugins/saga/skills/{phase}/SKILL.md").read_text(encoding="utf-8")
        assert 'SAGA_PLUGIN_ROOT="${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/saga}"' in text
        assert 'test -f "$SAGA_PLUGIN_ROOT/scripts/artifact_promotion.py"' in text
        assert 'test -f "$SAGA_PLUGIN_ROOT/scripts/transition_receipts.py"' in text
        assert "references/live-receipt-commands.md" in text
    for phase in DELIBERATION_PHASES:
        text = (REPO_ROOT / f"plugins/saga/skills/{phase}/SKILL.md").read_text(encoding="utf-8")
        assert (
            'CONSENSUS_PLUGIN_ROOT="$(dirname "$SAGA_PLUGIN_ROOT")/multi-agent-consensus"' in text
        )
        assert 'test -f "$CONSENSUS_PLUGIN_ROOT/scripts/deliberation.py"' in text

    reference = (REPO_ROOT / "plugins/saga/references/live-receipt-commands.md").read_text(
        encoding="utf-8"
    )
    assert '"$CONSENSUS_PLUGIN_ROOT/scripts/deliberation.py" evaluate' in reference
    assert '"$SAGA_PLUGIN_ROOT/scripts/transition_receipts.py" build' in reference
    assert '"$SAGA_PLUGIN_ROOT/scripts/artifact_promotion.py" promote' in reference


@pytest.mark.parametrize("script", [DELIBERATION, TRANSITION, PROMOTION])
def test_receipt_commands_expose_help(script: Path, tmp_path: Path) -> None:
    result = _run(script, tmp_path, "--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout
