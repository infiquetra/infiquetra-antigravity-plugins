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
