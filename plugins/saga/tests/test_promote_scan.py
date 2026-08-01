"""Repository-canonical artifact promotion transaction tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import promote_scan as promote  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    target = repo / "docs" / "plans" / "implementation-plan.md"
    staged = repo / ".gemini" / "brain" / "session" / "implementation_plan.md"
    target.parent.mkdir(parents=True)
    staged.parent.mkdir(parents=True)
    target.write_text("# Original plan\n", encoding="utf-8")
    staged.write_text("# Approved plan\n\nRepository-canonical content.\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Saga Test")
    _git(repo, "config", "user.email", "saga@example.invalid")
    _git(repo, "add", "docs/plans/implementation-plan.md")
    _git(repo, "commit", "-qm", "seed canonical plan")
    return repo, staged, target


def test_promotion_requires_canonical_target_provenance_and_no_conflict(
    tmp_path: Path,
) -> None:
    repo, staged, target = _repository(tmp_path)

    plan = promote.prepare_artifact_promotion(
        repo,
        staged,
        "docs/plans/implementation-plan.md",
    )
    receipt = promote.apply_artifact_promotion(
        plan,
        approval_receipt="operator-approval-2026-07-30",
    )

    assert plan.state == "prepared"
    assert receipt.state == "promoted"
    assert receipt.target_path == "docs/plans/implementation-plan.md"
    assert receipt.source_sha256 == receipt.output_sha256
    assert receipt.repository_revision == _git(repo, "rev-parse", "HEAD")
    assert target.read_bytes() == staged.read_bytes()


def test_promotion_requires_canonical_target_provenance_and_no_conflict_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    repo, staged, target = _repository(tmp_path)
    original = target.read_text(encoding="utf-8")

    plan = promote.prepare_artifact_promotion(
        repo,
        staged,
        "docs/plans/implementation-plan.md",
    )
    assert plan.state == "prepared"
    assert target.read_text(encoding="utf-8") == original

    with pytest.raises(promote.ArtifactPromotionError, match="approval receipt"):
        promote.apply_artifact_promotion(plan, approval_receipt="")
    assert target.read_text(encoding="utf-8") == original

    target.write_text("# Concurrent canonical edit\n", encoding="utf-8")
    with pytest.raises(promote.ArtifactPromotionError, match="changed after preparation"):
        promote.apply_artifact_promotion(plan, approval_receipt="operator-approved")

    with pytest.raises(promote.ArtifactPromotionError, match="under repository docs"):
        promote.prepare_artifact_promotion(repo, staged, ".gemini/brain/complete.md")
