"""Contract and settlement tests for lifecycle_obligations.py."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lifecycle_obligations as M  # noqa: E402, N812

FIXTURES = Path(__file__).parent / "fixtures" / "lifecycle-obligations"


def _contract() -> M.ObligationContract:
    return M.ObligationContract.from_dict(
        json.loads((FIXTURES / "valid-contract.json").read_text(encoding="utf-8"))
    )


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_evidence(
    tmp_path: Path,
    evidence_id: str,
    kind: str,
    *,
    producer: str,
    content: str | None = None,
) -> M.Evidence:
    relative = Path("docs") / f"{evidence_id}.json"
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind in {"execution-receipt", "review-finding", "qa-result"}:
        body = {
            "schema": M.INDEPENDENCE_RECEIPT_SCHEMA,
            "evidence_kind": kind,
            "subject": "issue-21",
            "producer_id": producer,
            "attester_id": "external-attester",
            "origin": "imported-external",
            "host_capability": None,
            "host_capability_state": None,
            "artifact_sha256": hashlib.sha256((content or evidence_id).encode()).hexdigest(),
        }
        receipt = {
            **body,
            "receipt_id": hashlib.sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        target.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
    else:
        target.write_text(content or evidence_id, encoding="utf-8")
    return M.Evidence.from_dict(
        {
            "evidence_id": evidence_id,
            "kind": kind,
            "subject": "issue-21",
            "producer": producer,
            "reference": relative.as_posix(),
            "digest": _digest(target),
            "verification_state": "verified",
            "assertion": "",
        }
    )


def _github_evidence(
    *,
    state: str = "verified",
    assertion: str = "closed",
    evidence_id: str = "github-closed",
) -> M.Evidence:
    payload = f"issue-21:{assertion}".encode()
    return M.Evidence.from_dict(
        {
            "evidence_id": evidence_id,
            "kind": "github-fact",
            "subject": "issue-21",
            "producer": "github",
            "reference": "https://github.com/infiquetra/repo/issues/21",
            "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "verification_state": state,
            "assertion": assertion,
        }
    )


def test_contract_round_trips_and_keeps_off_chain_commands_out_of_stored_phases() -> None:
    contract = _contract()
    assert contract.to_dict() == M.ObligationContract.from_dict(contract.to_dict()).to_dict()
    assert "retro" not in contract.stored_lifecycle_phases
    assert contract.off_chain_obligations == ("impl-spec", "retro")
    assert contract.obligation("impl-spec").command == "impl-spec"
    assert contract.obligation("impl-spec").phase == ""


@pytest.mark.parametrize("name", ["schema-less-contract.json", "future-contract.json"])
def test_legacy_and_unknown_schema_versions_fail_closed(name: str) -> None:
    data = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    with pytest.raises(M.ObligationError, match="unsupported lifecycle obligation schema"):
        M.ObligationContract.from_dict(data)


def test_unknown_fields_and_duplicate_obligations_fail_closed() -> None:
    data = _contract().to_dict()
    data["surprise"] = True
    with pytest.raises(M.ObligationError, match="unknown keys"):
        M.ObligationContract.from_dict(data)

    data = _contract().to_dict()
    data["obligations"].append(dict(data["obligations"][0]))
    with pytest.raises(M.ObligationError, match="duplicate obligation_id"):
        M.ObligationContract.from_dict(data)


def test_direct_contract_and_evidence_objects_cannot_bypass_validation(
    tmp_path: Path,
) -> None:
    contract = replace(_contract(), schema="saga.lifecycle-obligation.v2")
    with pytest.raises(M.ObligationError, match="unsupported lifecycle obligation schema"):
        M.evaluate_obligation(contract, "work-proof", [], repo_root=tmp_path)

    evidence = _repo_evidence(
        tmp_path,
        "output",
        "canonical-output",
        producer="work-agent",
    )
    invalid = replace(evidence, verification_state="verified")  # type: ignore[arg-type]
    with pytest.raises(M.ObligationError, match="must be a VerificationState"):
        M.evaluate_obligation(_contract(), "work-proof", [invalid], repo_root=tmp_path)


def test_required_obligation_cannot_degrade_and_independent_roles_are_mandatory() -> None:
    data = _contract().to_dict()
    required = data["obligations"][1]
    required["fallback"] = {
        "state": "degraded",
        "evidence": [{"kind": "fallback-receipt", "minimum_count": 1, "independent": False}],
    }
    with pytest.raises(M.ObligationError, match="required obligation.*cannot"):
        M.ObligationContract.from_dict(data)

    data = _contract().to_dict()
    data["obligations"][1]["required_evidence"][0]["independent"] = False
    with pytest.raises(M.ObligationError, match="must be declared independent"):
        M.ObligationContract.from_dict(data)


def test_required_obligation_accepts_only_complete_independent_repository_evidence(
    tmp_path: Path,
) -> None:
    evidence = [
        _repo_evidence(tmp_path, "execution", "execution-receipt", producer="runner"),
        _repo_evidence(tmp_path, "output", "canonical-output", producer="work-agent"),
        _repo_evidence(tmp_path, "check", "check-result", producer="pytest"),
        _repo_evidence(tmp_path, "review", "review-finding", producer="reviewer"),
        _repo_evidence(tmp_path, "qa", "qa-result", producer="qa-agent"),
    ]
    result = M.evaluate_obligation(
        _contract(),
        "work-proof",
        evidence,
        repo_root=tmp_path,
    )
    assert result.state is M.SettlementState.SATISFIED
    assert set(result.evidence_ids) == {item.evidence_id for item in evidence}


def test_lifecycle_advances_only_when_required_obligations_have_independent_receipts(
    tmp_path: Path,
) -> None:
    evidence = [
        _repo_evidence(tmp_path, "execution", "execution-receipt", producer="runner"),
        _repo_evidence(tmp_path, "output", "canonical-output", producer="work-agent"),
        _repo_evidence(tmp_path, "check", "check-result", producer="pytest"),
        _repo_evidence(tmp_path, "review", "review-finding", producer="reviewer"),
        _repo_evidence(tmp_path, "qa", "qa-result", producer="qa-agent"),
    ]

    result = M.evaluate_obligation(_contract(), "work-proof", evidence, repo_root=tmp_path)

    assert result.state is M.SettlementState.SATISFIED
    assert set(result.evidence_ids) == {item.evidence_id for item in evidence}


def test_lifecycle_advances_only_when_required_obligations_have_independent_receipts_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    contract = _contract()
    complete = [
        _repo_evidence(tmp_path, "execution", "execution-receipt", producer="runner"),
        _repo_evidence(tmp_path, "output", "canonical-output", producer="work-agent"),
        _repo_evidence(tmp_path, "check", "check-result", producer="pytest"),
        _repo_evidence(tmp_path, "review", "review-finding", producer="reviewer"),
        _repo_evidence(tmp_path, "qa", "qa-result", producer="qa-agent"),
    ]

    assert (
        M.evaluate_obligation(contract, "work-proof", complete[:-1], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    self_certified = [
        replace(item, producer="work-agent")
        if item.kind is M.EvidenceKind.EXECUTION_RECEIPT
        else item
        for item in complete
    ]
    assert (
        M.evaluate_obligation(contract, "work-proof", self_certified, repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    forged = _repo_evidence(tmp_path, "forged-review", "review-finding", producer="reviewer")
    forged_path = tmp_path / forged.reference
    forged_receipt = json.loads(forged_path.read_text())
    forged_receipt["producer_id"] = "different-reviewer"
    forged_path.write_text(json.dumps(forged_receipt, sort_keys=True, separators=(",", ":")))
    forged = replace(forged, digest=_digest(forged_path))
    assert (
        M.evaluate_obligation(contract, "work-proof", [forged], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    host_created = _repo_evidence(tmp_path, "host-created", "execution-receipt", producer="runner")
    host_path = tmp_path / host_created.reference
    host_receipt = json.loads(host_path.read_text())
    body = {
        **{key: value for key, value in host_receipt.items() if key != "receipt_id"},
        "origin": "saga-host-created",
        "host_capability": "agy.agent.execution",
        "host_capability_state": "unavailable",
    }
    host_receipt = {
        **body,
        "receipt_id": hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    host_path.write_text(json.dumps(host_receipt, sort_keys=True, separators=(",", ":")))
    host_created = replace(host_created, digest=_digest(host_path))
    assert (
        M.evaluate_obligation(contract, "work-proof", [host_created], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    fallback = _repo_evidence(
        tmp_path,
        "fallback-only",
        "fallback-receipt",
        producer="work-agent",
    )
    assert (
        M.evaluate_obligation(contract, "work-proof", [fallback], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    one = _github_evidence(assertion="closed", evidence_id="github-one")
    two = _github_evidence(assertion="open", evidence_id="github-two")
    assert (
        M.evaluate_obligation(contract, "github-closed", [one, two]).state
        is M.SettlementState.CONFLICTING
    )


def test_independent_minimum_count_reports_one_evidence_per_producer(
    tmp_path: Path,
) -> None:
    data = _contract().to_dict()
    data["obligations"][1]["required_evidence"] = [
        {"kind": "execution-receipt", "minimum_count": 2, "independent": True}
    ]
    contract = M.ObligationContract.from_dict(data)
    evidence = [
        _repo_evidence(tmp_path, "runner-one-a", "execution-receipt", producer="runner-one"),
        _repo_evidence(tmp_path, "runner-one-b", "execution-receipt", producer="runner-one"),
        _repo_evidence(tmp_path, "runner-two", "execution-receipt", producer="runner-two"),
    ]
    result = M.evaluate_obligation(
        contract,
        "work-proof",
        evidence,
        repo_root=tmp_path,
    )
    assert result.state is M.SettlementState.SATISFIED
    assert result.evidence_ids == ("runner-one-a", "runner-two")


@pytest.mark.parametrize("kind", ["execution-receipt", "review-finding", "qa-result"])
def test_producer_cannot_satisfy_its_own_independent_gate(tmp_path: Path, kind: str) -> None:
    evidence = [
        _repo_evidence(tmp_path, "execution", "execution-receipt", producer="runner"),
        _repo_evidence(tmp_path, "output", "canonical-output", producer="work-agent"),
        _repo_evidence(tmp_path, "check", "check-result", producer="pytest"),
        _repo_evidence(tmp_path, "review", "review-finding", producer="reviewer"),
        _repo_evidence(tmp_path, "qa", "qa-result", producer="qa-agent"),
    ]
    evidence = [
        M.Evidence(
            **{
                **item.__dict__,
                "producer": "work-agent",
            }
        )
        if item.kind.value == kind
        else item
        for item in evidence
    ]
    result = M.evaluate_obligation(
        _contract(),
        "work-proof",
        evidence,
        repo_root=tmp_path,
    )
    assert result.state is M.SettlementState.UNSATISFIED


def test_optional_obligation_degrades_only_through_predeclared_fallback(tmp_path: Path) -> None:
    fallback = _repo_evidence(
        tmp_path,
        "fallback",
        "fallback-receipt",
        producer="work-agent",
    )
    result = M.evaluate_obligation(
        _contract(),
        "deliberation",
        [fallback],
        repo_root=tmp_path,
    )
    assert result.state is M.SettlementState.DEGRADED

    missing = M.evaluate_obligation(_contract(), "deliberation", [], repo_root=tmp_path)
    assert missing.state is M.SettlementState.UNSATISFIED


@pytest.mark.parametrize("state", ["unknown", "unavailable"])
def test_unknown_or_unavailable_source_stays_unavailable(state: str) -> None:
    result = M.evaluate_obligation(
        _contract(),
        "github-closed",
        [_github_evidence(state=state)],
    )
    assert result.state is M.SettlementState.UNAVAILABLE


def test_missing_or_digest_mismatched_repository_evidence_is_unsatisfied(
    tmp_path: Path,
) -> None:
    evidence = _repo_evidence(tmp_path, "output", "canonical-output", producer="work-agent")
    missing = M.Evidence(
        **{
            **evidence.__dict__,
            "reference": "docs/missing.json",
        }
    )
    contract_data = _contract().to_dict()
    contract_data["obligations"][1]["required_evidence"] = [
        {"kind": "canonical-output", "minimum_count": 1, "independent": False}
    ]
    contract = M.ObligationContract.from_dict(contract_data)
    assert (
        M.evaluate_obligation(contract, "work-proof", [missing], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )

    mismatch = M.Evidence(
        **{
            **evidence.__dict__,
            "digest": "sha256:" + ("0" * 64),
        }
    )
    assert (
        M.evaluate_obligation(contract, "work-proof", [mismatch], repo_root=tmp_path).state
        is M.SettlementState.UNSATISFIED
    )


def test_conflicting_verified_authorities_do_not_settle() -> None:
    one = _github_evidence(assertion="closed", evidence_id="github-one")
    two = _github_evidence(assertion="open", evidence_id="github-two")
    result = M.evaluate_obligation(_contract(), "github-closed", [one, two])
    assert result.state is M.SettlementState.CONFLICTING


def test_github_completion_settles_only_the_external_fact_obligation() -> None:
    github = _github_evidence()
    assert (
        M.evaluate_obligation(_contract(), "github-closed", [github]).state
        is M.SettlementState.SATISFIED
    )
    assert (
        M.evaluate_obligation(_contract(), "work-proof", [github]).state
        is M.SettlementState.UNSATISFIED
    )


@pytest.mark.parametrize(
    "reference",
    ["/tmp/proof.json", "../proof.json", "docs/../proof.json", "docs\\proof.json"],
)
def test_repository_evidence_rejects_unsafe_paths(reference: str) -> None:
    data: dict[str, Any] = {
        "evidence_id": "proof",
        "kind": "canonical-output",
        "subject": "issue-21",
        "producer": "worker",
        "reference": reference,
        "digest": "sha256:" + ("0" * 64),
        "verification_state": "verified",
        "assertion": "",
    }
    with pytest.raises(M.ObligationError, match="repository-relative"):
        M.Evidence.from_dict(data)


def test_rule_fallback_and_obligation_types_fail_closed() -> None:
    with pytest.raises(M.ObligationError, match="unsupported kind"):
        M.EvidenceRule.from_dict({"kind": "unknown", "independent": False})
    with pytest.raises(M.ObligationError, match="positive integer"):
        M.EvidenceRule.from_dict({"kind": "input", "minimum_count": True, "independent": False})
    with pytest.raises(M.ObligationError, match="must be a boolean"):
        M.EvidenceRule.from_dict({"kind": "input", "independent": "yes"})
    for rule in (
        M.EvidenceRule(kind="input"),  # type: ignore[arg-type]
        M.EvidenceRule(kind=M.EvidenceKind.INPUT, minimum_count=0),
        M.EvidenceRule(kind=M.EvidenceKind.INPUT, independent="yes"),  # type: ignore[arg-type]
        M.EvidenceRule(kind=M.EvidenceKind.QA_RESULT, independent=False),
    ):
        with pytest.raises(M.ObligationError):
            rule.validate()

    with pytest.raises(M.ObligationError, match="unsupported state"):
        M.DegradedFallback.from_dict({"state": "wrong", "evidence": []})
    with pytest.raises(M.ObligationError, match="must be 'degraded'"):
        M.DegradedFallback.from_dict({"state": "satisfied", "evidence": []})
    with pytest.raises(M.ObligationError, match="at least one"):
        M.DegradedFallback.from_dict({"state": "degraded", "evidence": []})
    for fallback in (
        M.DegradedFallback(evidence=(), state=M.SettlementState.SATISFIED),
        M.DegradedFallback(evidence=()),
        M.DegradedFallback(evidence=("bad",)),  # type: ignore[arg-type]
        M.DegradedFallback(
            evidence=(
                M.EvidenceRule(M.EvidenceKind.INPUT),
                M.EvidenceRule(M.EvidenceKind.INPUT),
            )
        ),
    ):
        with pytest.raises(M.ObligationError):
            fallback.validate()

    data = _contract().to_dict()["obligations"][0]
    for field, value, message in (
        ("kind", "wrong", "unsupported enum"),
        ("fallback", [], "fallback must be an object"),
    ):
        mapping_candidate = dict(data)
        mapping_candidate[field] = value
        with pytest.raises(M.ObligationError, match=message):
            M.Obligation.from_dict(mapping_candidate)

    obligation = _contract().obligations[0]
    invalid = [
        replace(obligation, kind="bad"),  # type: ignore[arg-type]
        replace(obligation, requirement="bad"),  # type: ignore[arg-type]
        replace(obligation, producer=""),
        replace(obligation, required_evidence=()),
        replace(obligation, required_evidence=("bad",)),  # type: ignore[arg-type]
        replace(
            obligation,
            required_evidence=(
                M.EvidenceRule(M.EvidenceKind.INPUT),
                M.EvidenceRule(M.EvidenceKind.INPUT),
            ),
        ),
        replace(obligation, phase="not-a-phase"),
    ]
    for obligation_candidate in invalid:
        with pytest.raises(M.ObligationError):
            obligation_candidate.validate()


def test_contract_and_evidence_dataclasses_reject_invalid_direct_construction() -> None:
    data = _contract().to_dict()
    for field, value, message in (
        ("stored_lifecycle_phases", ["wrong"], "unsupported values"),
        ("off_chain_obligations", ["wrong"], "unsupported values"),
        ("obligations", [], "non-empty obligations"),
    ):
        mapping_candidate = dict(data)
        mapping_candidate[field] = value
        with pytest.raises(M.ObligationError, match=message):
            M.ObligationContract.from_dict(mapping_candidate)

    contract = _contract()
    for contract_candidate in (
        replace(contract, stored_lifecycle_phases=("work", "work")),
        replace(contract, off_chain_obligations=("retro", "retro")),
        replace(contract, obligations=()),
        replace(contract, obligations=("bad",)),  # type: ignore[arg-type]
        replace(contract, obligations=(contract.obligations[0], contract.obligations[0])),
        replace(
            contract,
            obligations=(replace(contract.obligations[0], phase="qa"),),
            stored_lifecycle_phases=("work",),
        ),
    ):
        with pytest.raises(M.ObligationError):
            contract_candidate.validate()
    with pytest.raises(M.ObligationError, match="has no obligation"):
        contract.obligation("missing")

    evidence = _github_evidence()
    for evidence_candidate in (
        replace(evidence, kind="bad"),  # type: ignore[arg-type]
        replace(evidence, verification_state="bad"),  # type: ignore[arg-type]
        replace(evidence, producer=""),
        replace(evidence, digest="bad"),
        replace(evidence, assertion=1),  # type: ignore[arg-type]
    ):
        with pytest.raises(M.ObligationError):
            evidence_candidate.validate()
    with pytest.raises(M.ObligationError, match="unsupported enum"):
        M.Evidence.from_dict({**evidence.to_dict(), "kind": "wrong"})
    with pytest.raises(M.ObligationError, match="Evidence values"):
        M.evaluate_obligation(contract, "github-closed", ["bad"])  # type: ignore[list-item]


def test_repository_and_independence_verifiers_report_edge_failures(tmp_path: Path) -> None:
    github = _github_evidence()
    assert M.verify_repository_evidence(github, repo_root=None) == (True, "")
    repo = M.Evidence.from_dict(
        {
            **github.to_dict(),
            "evidence_id": "repo-proof",
            "kind": "canonical-output",
            "reference": "docs/proof.json",
        }
    )
    assert M.verify_repository_evidence(repo, repo_root=None)[0] is False
    directory = tmp_path / "docs/proof.json"
    directory.mkdir(parents=True)
    assert M.verify_repository_evidence(repo, repo_root=tmp_path)[0] is False
    assert (
        M.verify_independent_receipt(repo, obligation_producer="worker", repo_root=tmp_path)[0]
        is False
    )

    receipt = _repo_evidence(tmp_path, "review-edge", "review-finding", producer="reviewer")
    assert (
        M.verify_independent_receipt(receipt, obligation_producer="worker", repo_root=None)[0]
        is False
    )
    path = tmp_path / receipt.reference
    base = json.loads(path.read_text())
    mutations = [
        lambda row: row.update(schema="wrong"),
        lambda row: row.update(receipt_id="bad"),
        lambda row: row.update(evidence_kind="qa-result"),
        lambda row: row.update(subject="other"),
        lambda row: row.update(producer_id="other"),
        lambda row: row.update(attester_id="reviewer"),
        lambda row: row.update(artifact_sha256="bad"),
        lambda row: row.update(origin="wrong"),
        lambda row: row.update(origin="imported-external", host_capability="agy.agent.execution"),
    ]
    for mutation in mutations:
        candidate = dict(base)
        mutation(candidate)
        if candidate.get("receipt_id") != "bad":
            body = {key: value for key, value in candidate.items() if key != "receipt_id"}
            candidate["receipt_id"] = hashlib.sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        path.write_text(json.dumps(candidate), encoding="utf-8")
        assert (
            M.verify_independent_receipt(receipt, obligation_producer="worker", repo_root=tmp_path)[
                0
            ]
            is False
        )
