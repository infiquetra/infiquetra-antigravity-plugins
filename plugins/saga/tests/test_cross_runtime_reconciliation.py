"""Mapped cross-runtime reconciliation acceptance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import override_rate_reader  # noqa: E402
import reconcile  # noqa: E402
import reconcile_controller  # noqa: E402


def test_reconciliation_keeps_repository_truth_authoritative(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    canonical_path = repo / "docs" / "state.json"
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text('{"phase":"work"}\n', encoding="utf-8")
    canonical = reconcile_controller.canonical_evidence(repo, "docs/state.json")
    projection = reconcile.build_projection(
        projection_id="projection-1",
        runtime="antigravity-session",
        canonical=canonical,
        receipt_sha256="a" * 64,
        facts={"phase": "work", "status": "active"},
    )

    before = canonical_path.read_bytes()
    receipt = reconcile_controller.run(repo, "docs/state.json", [projection])

    assert receipt["canonical"]["authority"] == "repository"
    assert receipt["projections"][0]["state"] == "accepted"
    assert canonical_path.read_bytes() == before
    assert override_rate_reader.summarize([receipt])["acceptance_rate"] == 1.0


def test_reconciliation_keeps_repository_truth_authoritative_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    canonical_path = repo / "docs" / "state.json"
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text('{"phase":"work"}\n', encoding="utf-8")
    canonical = reconcile_controller.canonical_evidence(repo, "docs/state.json")
    stale = reconcile.build_projection(
        projection_id="projection-1",
        runtime="antigravity-session",
        canonical=canonical,
        receipt_sha256="a" * 64,
        facts={"phase": "work"},
    )
    canonical_path.write_text('{"phase":"qa"}\n', encoding="utf-8")

    receipt = reconcile_controller.run(repo, "docs/state.json", [stale])
    assert receipt["projections"][0]["state"] == "rejected"
    assert receipt["projections"][0]["reasons"] == ["stale-canonical-digest"]

    takeover = dict(stale)
    takeover["authority"] = "canonical"
    with pytest.raises(reconcile.ReconciliationError, match="cannot claim"):
        reconcile.reconcile_projections(canonical, [takeover])

    with pytest.raises(reconcile.ReconciliationError, match="unique"):
        reconcile.reconcile_projections(canonical, [stale, stale])
