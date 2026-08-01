"""Acceptance tests for canonical Saga artifact promotion."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import artifact_promotion as M  # noqa: E402, N812
import lifecycle_obligations as O  # noqa: E402, N812
import transition_receipts as T  # noqa: E402, N812

CONTRACT_FIXTURE = (
    Path(__file__).parent / "fixtures" / "lifecycle-obligations" / "valid-contract.json"
)


def _sha(value: str | bytes) -> str:
    raw = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _transition(tmp_path: Path) -> str:
    contract = O.ObligationContract.from_dict(
        json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    )
    fact = O.Evidence.from_dict(
        {
            "evidence_id": "github-fact",
            "kind": "github-fact",
            "subject": "issue-21",
            "producer": "github",
            "reference": "https://github.com/infiquetra/repo/issues/21",
            "digest": "sha256:" + _sha("closed"),
            "verification_state": "verified",
            "assertion": "closed",
        }
    )
    receipt = T.build_transition_receipt(
        contract=contract,
        transition_id="artifact-promotion",
        obligation_id="github-closed",
        attempt=1,
        external_facts=[fact],
        repo_root=tmp_path,
    )
    path = T.write_transition_receipt(tmp_path, "outcome-23", receipt)
    return path.relative_to(tmp_path).as_posix()


def _repository_evidence(
    tmp_path: Path,
    evidence_id: str,
    kind: str,
    producer: str,
) -> O.Evidence:
    reference = Path("docs/evidence") / f"{evidence_id}.json"
    target = tmp_path / reference
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind in {"execution-receipt", "review-finding", "qa-result"}:
        body = {
            "schema": O.INDEPENDENCE_RECEIPT_SCHEMA,
            "evidence_kind": kind,
            "subject": "issue-21",
            "producer_id": producer,
            "attester_id": "external-attester",
            "origin": "imported-external",
            "host_capability": None,
            "host_capability_state": None,
            "artifact_sha256": _sha(evidence_id),
        }
        payload = {
            **body,
            "receipt_id": _sha(json.dumps(body, sort_keys=True, separators=(",", ":"))),
        }
        target.write_text(json.dumps(payload), encoding="utf-8")
    else:
        target.write_text(json.dumps({"evidence_id": evidence_id}), encoding="utf-8")
    return O.Evidence.from_dict(
        {
            "evidence_id": evidence_id,
            "kind": kind,
            "subject": "issue-21",
            "producer": producer,
            "reference": reference.as_posix(),
            "digest": "sha256:" + _sha(target.read_bytes()),
            "verification_state": "verified",
            "assertion": "",
        }
    )


def _full_transition(tmp_path: Path) -> tuple[str, dict[str, str]]:
    contract = O.ObligationContract.from_dict(
        json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    )
    execution = _repository_evidence(tmp_path, "execution", "execution-receipt", "runner")
    review = _repository_evidence(tmp_path, "review", "review-finding", "reviewer")
    qa = _repository_evidence(tmp_path, "qa", "qa-result", "qa-agent")
    operator = _repository_evidence(tmp_path, "operator", "operator-decision", "operator")
    receipt = T.build_transition_receipt(
        contract=contract,
        transition_id="historical-artifact-promotion",
        obligation_id="work-proof",
        attempt=1,
        operator_decisions=[operator],
        execution_receipts=[execution],
        canonical_outputs=[
            _repository_evidence(tmp_path, "output", "canonical-output", "work-agent")
        ],
        check_results=[
            _repository_evidence(tmp_path, "check", "check-result", "pytest"),
            qa,
        ],
        review_findings=[review],
        repo_root=tmp_path,
    )
    path = T.write_transition_receipt(tmp_path, "outcome-23", receipt)
    evidence = {
        "execution": execution.reference,
        "review": review.reference,
        "qa": qa.reference,
        "operator": operator.reference,
    }
    return path.relative_to(tmp_path).as_posix(), evidence


def _promote(
    tmp_path: Path,
    *,
    content: str = "# Approved plan\n",
    target: str = "docs/plans/approved.md",
    predecessor: str | None = None,
    transition: str | None = None,
    projection_path: Path | None = None,
) -> M.PromotionResult:
    return M.promote_artifact(
        repo_root=tmp_path,
        outcome_id="outcome-23",
        phase="plan",
        source_role="antigravity-brain",
        source_ref="brain/plan-draft",
        staged_content=content,
        target_ref=target,
        expected_predecessor_sha256=predecessor,
        transition_receipt_ref=transition or _transition(tmp_path),
        projection_path=projection_path,
    )


def test_first_promotion_and_unchanged_retry_are_idempotent(tmp_path: Path) -> None:
    transition = _transition(tmp_path)
    first = _promote(tmp_path, transition=transition)
    second = _promote(tmp_path, transition=transition)

    assert first.receipt.state is O.SettlementState.SATISFIED
    assert first.receipt.promotion_id == second.receipt.promotion_id
    assert first.receipt_path == second.receipt_path
    assert first.artifact_path.read_text(encoding="utf-8") == "# Approved plan\n"
    assert M.PromotionReceipt.from_dict(json.loads(first.receipt_path.read_text())) == first.receipt
    assert list(first.receipt_path.parent.glob("*.json")) == [first.receipt_path]


def test_matching_predecessor_is_replaced_atomically(tmp_path: Path) -> None:
    target = tmp_path / "docs/plans/approved.md"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")

    result = _promote(tmp_path, content="new\n", predecessor=_sha("old\n"))

    assert result.receipt.state is O.SettlementState.SATISFIED
    assert result.receipt.expected_predecessor_sha256 == _sha("old\n")
    assert target.read_text(encoding="utf-8") == "new\n"


def test_divergent_predecessor_preserves_both_versions_and_blocks(tmp_path: Path) -> None:
    target = tmp_path / "docs/plans/approved.md"
    target.parent.mkdir(parents=True)
    target.write_text("canonical\n", encoding="utf-8")

    result = _promote(tmp_path, content="candidate\n", predecessor=_sha("expected\n"))

    assert result.receipt.state is O.SettlementState.CONFLICTING
    assert result.receipt.operator_adjudication_required is True
    assert result.receipt.canonical_sha256 == _sha("canonical\n")
    assert result.receipt.conflict_ref is not None
    assert target.read_text(encoding="utf-8") == "canonical\n"
    assert result.artifact_path.read_text(encoding="utf-8") == "candidate\n"
    assert result.artifact_path.is_relative_to(tmp_path / "docs/outcomes/outcome-23/conflicts")


def test_interrupted_receipt_write_recovers_without_duplicate_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transition = _transition(tmp_path)
    original = M._write_receipt
    attempts = 0

    def fail_once(path: Path, content: str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise M.ArtifactPromotionError("simulated receipt interruption")
        original(path, content)

    monkeypatch.setattr(M, "_write_receipt", fail_once)
    with pytest.raises(M.ArtifactPromotionError, match="simulated"):
        _promote(tmp_path, transition=transition)
    assert (tmp_path / "docs/plans/approved.md").read_text() == "# Approved plan\n"

    recovered = _promote(tmp_path, transition=transition)
    assert recovered.receipt.state is O.SettlementState.SATISFIED
    assert attempts == 2
    assert list(recovered.receipt_path.parent.glob("*.json")) == [recovered.receipt_path]


@pytest.mark.parametrize(
    "target",
    [
        "../outside.md",
        "/tmp/outside.md",
        "docs/qa/wrong-phase.md",
        "docs/plans/unsupported.txt",
    ],
)
def test_invalid_target_paths_fail_before_writing(tmp_path: Path, target: str) -> None:
    transition = _transition(tmp_path)
    with pytest.raises(M.ArtifactPromotionError):
        _promote(tmp_path, target=target, transition=transition)
    assert not (tmp_path / "outside.md").exists()


def test_symlinked_target_family_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/plans").symlink_to(outside, target_is_directory=True)

    with pytest.raises(M.ArtifactPromotionError, match="symlink"):
        _promote(tmp_path)
    assert not (outside / "approved.md").exists()


@pytest.mark.parametrize(
    ("content", "category"),
    [
        ("path: /Users/alice/private/file\n", "home path"),
        ("token=ghp_examplecredential\n", "credential"),
        ("host: secret-machine.local\n", "hostname"),
        ('{"transcript": "private prompt"}\n', "transcript"),
    ],
)
def test_sanitization_rejects_private_promoted_content_without_echo(
    tmp_path: Path, content: str, category: str
) -> None:
    transition = _transition(tmp_path)
    with pytest.raises(M.ArtifactPromotionError, match=category) as captured:
        _promote(tmp_path, content=content, transition=transition)
    assert content.strip() not in str(captured.value)
    assert not (tmp_path / "docs/plans/approved.md").exists()


def test_missing_or_invalid_transition_receipt_blocks_promotion(tmp_path: Path) -> None:
    missing = "docs/outcomes/outcome-23/receipts/missing.json"
    with pytest.raises(M.ArtifactPromotionError, match="missing or invalid"):
        _promote(tmp_path, transition=missing)
    assert not (tmp_path / "docs/plans/approved.md").exists()


def test_historical_import_retains_source_but_cannot_fabricate_evidence(tmp_path: Path) -> None:
    transition = _transition(tmp_path)
    imported = M.promote_artifact(
        repo_root=tmp_path,
        outcome_id="outcome-23",
        phase="plan",
        source_role="historical-import",
        source_ref="brain/legacy-plan",
        staged_content="# Legacy plan\n",
        target_ref="docs/plans/legacy.md",
        expected_predecessor_sha256=None,
        transition_receipt_ref=transition,
        historical_import=True,
    )

    assert imported.receipt.state is O.SettlementState.UNSATISFIED
    assert imported.receipt.evidence_refs == {}
    assert imported.receipt.missing_required_evidence == (
        "execution",
        "operator",
        "qa",
        "review",
    )
    assert imported.receipt.source_role == "historical-import"

    proven_transition, evidence = _full_transition(tmp_path)
    proven = M.promote_artifact(
        repo_root=tmp_path,
        outcome_id="outcome-23",
        phase="plan",
        source_role="historical-import",
        source_ref="brain/proven-legacy-plan",
        staged_content="# Proven legacy plan\n",
        target_ref="docs/plans/proven-legacy.md",
        expected_predecessor_sha256=None,
        transition_receipt_ref=proven_transition,
        historical_import=True,
        evidence_refs=evidence,
    )
    assert proven.receipt.state is O.SettlementState.SATISFIED
    assert set(proven.receipt.evidence_refs) == M.EVIDENCE_KINDS


def test_historical_import_rejects_unresolvable_claimed_evidence(tmp_path: Path) -> None:
    transition = _transition(tmp_path)
    with pytest.raises(M.ArtifactPromotionError, match="missing or escapes"):
        M.promote_artifact(
            repo_root=tmp_path,
            outcome_id="outcome-23",
            phase="plan",
            source_role="historical-import",
            source_ref="brain/legacy-plan",
            staged_content="# Legacy plan\n",
            target_ref="docs/plans/legacy.md",
            expected_predecessor_sha256=None,
            transition_receipt_ref=transition,
            historical_import=True,
            evidence_refs={"review": "docs/evidence/missing.json"},
        )
    assert not (tmp_path / "docs/plans/legacy.md").exists()


def test_historical_import_rejects_evidence_not_bound_by_transition(tmp_path: Path) -> None:
    transition = _transition(tmp_path)
    unbound = tmp_path / "docs/evidence/unbound.json"
    unbound.parent.mkdir(parents=True, exist_ok=True)
    unbound.write_text('{"kind": "review"}\n', encoding="utf-8")

    with pytest.raises(M.ArtifactPromotionError, match="not uniquely bound"):
        M.promote_artifact(
            repo_root=tmp_path,
            outcome_id="outcome-23",
            phase="plan",
            source_role="historical-import",
            source_ref="brain/unbound-legacy-plan",
            staged_content="# Legacy plan\n",
            target_ref="docs/plans/unbound-legacy.md",
            expected_predecessor_sha256=None,
            transition_receipt_ref=transition,
            historical_import=True,
            evidence_refs={"review": unbound.relative_to(tmp_path).as_posix()},
        )
    assert not (tmp_path / "docs/plans/unbound-legacy.md").exists()


def test_historical_import_rechecks_bound_evidence_identity(tmp_path: Path) -> None:
    transition, evidence = _full_transition(tmp_path)
    (tmp_path / evidence["review"]).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(M.ArtifactPromotionError, match="identity verification"):
        M.promote_artifact(
            repo_root=tmp_path,
            outcome_id="outcome-23",
            phase="plan",
            source_role="historical-import",
            source_ref="brain/tampered-legacy-plan",
            staged_content="# Legacy plan\n",
            target_ref="docs/plans/tampered-legacy.md",
            expected_predecessor_sha256=None,
            transition_receipt_ref=transition,
            historical_import=True,
            evidence_refs=evidence,
        )
    assert not (tmp_path / "docs/plans/tampered-legacy.md").exists()


def test_symlinked_receipt_directory_blocks_before_canonical_write(tmp_path: Path) -> None:
    outside = tmp_path / "outside-receipts"
    outside.mkdir()
    receipt_root = tmp_path / "docs/outcomes/outcome-23"
    receipt_root.mkdir(parents=True)
    (receipt_root / "promotion-receipts").symlink_to(outside, target_is_directory=True)

    with pytest.raises(M.ArtifactPromotionError, match="symlink"):
        _promote(tmp_path)
    assert not (tmp_path / "docs/plans/approved.md").exists()
    assert not list(outside.iterdir())


def test_terminal_no_save_is_narrow_non_settling_and_writes_nothing(tmp_path: Path) -> None:
    before = list(tmp_path.rglob("*"))
    receipt = M.terminal_abandonment(
        outcome_id="outcome-23",
        phase="ideate",
        source_role="antigravity-brain",
        source_ref="brain/abandoned-idea",
        reason="operator abandoned unfinished exploration",
        unfinished=True,
        explicitly_abandoned=True,
    )

    assert receipt["state"] == "abandoned"
    assert receipt["phase_complete"] is False
    assert receipt["resumable"] is False
    assert receipt["handoffable"] is False
    assert receipt["outcome_settled"] is False
    assert list(tmp_path.rglob("*")) == before

    with pytest.raises(M.ArtifactPromotionError, match="limited"):
        M.terminal_abandonment(
            outcome_id="outcome-23",
            phase="work",
            source_role="antigravity-brain",
            source_ref="brain/work",
            reason="discard",
            unfinished=True,
            explicitly_abandoned=True,
        )


def test_projection_is_disposable_and_not_authoritative(tmp_path: Path) -> None:
    projection = tmp_path / ".gemini/saga/active-artifact.json"
    result = _promote(tmp_path, projection_path=projection)
    assert result.projection_path == projection
    projection.unlink()
    assert result.artifact_path.exists()
    assert result.receipt_path.exists()
    assert result.receipt.state is O.SettlementState.SATISFIED


def test_projection_cannot_target_canonical_repository_evidence(tmp_path: Path) -> None:
    transition = _transition(tmp_path)
    with pytest.raises(M.ArtifactPromotionError, match="ignored .gemini"):
        _promote(
            tmp_path,
            transition=transition,
            projection_path=tmp_path / "docs/projection.json",
        )
    assert not (tmp_path / "docs/plans/approved.md").exists()


def test_deserialized_receipt_rejects_unsupported_promotion_state(tmp_path: Path) -> None:
    data = _promote(tmp_path).receipt.to_dict()
    data["state"] = "degraded"
    body = {key: value for key, value in data.items() if key != "promotion_id"}
    data["promotion_id"] = M._identity(body)
    with pytest.raises(M.ArtifactPromotionError, match="state is unsupported"):
        M.PromotionReceipt.from_dict(data)


def test_implementation_has_no_remote_command_surface() -> None:
    source = (ROOT / "scripts/artifact_promotion.py").read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "requests" not in source
    assert "urlopen" not in source
    assert "git push" not in source
    assert "gh pr" not in source


def test_artifact_producing_skills_require_canonical_promotion() -> None:
    expected_targets = {
        "ideate": "docs/ideation/",
        "brainstorm": "docs/brainstorms/",
        "plan": "docs/plans/",
        "doc-review": "docs/reviews/",
        "work": "docs/work-sessions/",
        "code-review": "docs/code-reviews/",
        "qa": "docs/qa/",
        "retro": "docs/retros/",
        "handoff": "docs/handoffs/",
    }
    for skill, target in expected_targets.items():
        text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "artifact_promotion.py" in text
        assert target in text
        assert "staging only" in text
        assert re.search(r"operator\s+adjudication", text)
