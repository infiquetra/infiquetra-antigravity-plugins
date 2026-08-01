from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "handoff_envelope.py"
    spec = importlib.util.spec_from_file_location("handoff_envelope_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_handoff_names_artifacts_evidence_risks_and_external_authority(tmp_path: Path) -> None:
    module = _load()
    packet = module.build_handoff_envelope(
        "docs/plans/approved.md",
        artifacts=["docs/plans/approved.md", "docs/reviews/approved-review.md"],
        evidence=["pytest:14 passed", "review:accepted"],
        risks=["production release remains unverified"],
        root=tmp_path,
        now=lambda: datetime(2026, 7, 30, tzinfo=UTC),
    )
    assert module.validate_handoff_envelope(packet) == []
    assert packet["artifacts"] == [
        "docs/plans/approved.md",
        "docs/reviews/approved-review.md",
    ]
    assert packet["evidence"] == ["pytest:14 passed", "review:accepted"]
    assert packet["risks"] == ["production release remains unverified"]
    assert set(packet["still_unauthorized"]) == {
        "issue-create",
        "board-update",
        "pr-create",
        "merge",
        "deploy",
    }


def test_handoff_names_artifacts_evidence_risks_and_external_authority_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    module = _load()
    packet = module.build_handoff_envelope("docs/plans/approved.md", root=tmp_path)
    packet["evidence"] = []
    assert any(
        "evidence must be a non-empty string list" in error
        for error in module.validate_handoff_envelope(packet)
    )
    packet["evidence"] = ["present"]
    packet["still_unauthorized"] = []
    assert any(
        "still_unauthorized must be a non-empty string list" in error
        for error in module.validate_handoff_envelope(packet)
    )
