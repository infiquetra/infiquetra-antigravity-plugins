"""Mapped acceptance for Saga's Fleet Core dependency resolver."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import plugin_dependency_resolver as resolver  # noqa: E402


def _plugin(repo: Path, name: str) -> Path:
    root = repo / "plugins" / name
    root.mkdir(parents=True)
    (root / "plugin.json").write_text(
        json.dumps({"name": name, "version": "1.0.0"}) + "\n",
        encoding="utf-8",
    )
    return root


def _workflow() -> dict:
    return {
        "schema": "antigravity.workflow-contract.v1",
        "kind": "implementation",
        "inputs": ["approved-plan"],
        "outputs": ["assignment-result"],
    }


def test_plugin_readiness_resolves_target_plugins_and_consensus_mapping(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _plugin(repo, "saga")
    consensus = _plugin(repo, "multi-agent-consensus")

    assert resolver.source_lineage_to_target("team-execution") == (
        "plugin",
        "multi-agent-consensus",
    )
    assert resolver.source_lineage_to_target("verified-workflows") == (
        "workflow",
        "antigravity.workflow-contract.v1",
    )
    report = resolver.check_readiness(
        required_plugins=("multi-agent-consensus",),
        required_backends=("inline", "multi-agent-consensus"),
        repository_root=repo.resolve(),
        workflow_contract=_workflow(),
    )
    assert report["plugins"]["multi-agent-consensus"] == consensus.resolve().as_posix()
    assert report["workflow_schema"] == "antigravity.workflow-contract.v1"


def test_plugin_readiness_resolves_target_plugins_and_consensus_mapping_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _plugin(repo, "saga")

    with pytest.raises(resolver.DependencyResolutionError, match="source package name"):
        resolver.resolve_target_plugin("team-execution", repository_root=repo.resolve())
    with pytest.raises(resolver.DependencyResolutionError, match="could not resolve"):
        resolver.resolve_target_plugin(
            "multi-agent-consensus",
            repository_root=repo.resolve(),
        )
    with pytest.raises(resolver.DependencyResolutionError, match="unsupported"):
        resolver.check_readiness(
            required_plugins=(),
            required_backends=("source-workflow",),
            repository_root=repo.resolve(),
            workflow_contract=_workflow(),
        )
    invalid = _workflow()
    invalid["schema"] = "source.workflow.v1"
    with pytest.raises(resolver.DependencyResolutionError, match="incompatible"):
        resolver.check_readiness(
            required_plugins=(),
            required_backends=("inline",),
            repository_root=repo.resolve(),
            workflow_contract=invalid,
        )
