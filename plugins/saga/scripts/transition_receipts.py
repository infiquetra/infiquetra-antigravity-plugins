#!/usr/bin/env python3
"""Versioned transition receipts with deterministic, write-once persistence."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lifecycle_obligations import (  # noqa: E402
    REPOSITORY_EVIDENCE_KINDS,
    Evidence,
    EvidenceKind,
    ObligationContract,
    ObligationError,
    SettlementResult,
    SettlementState,
    VerificationState,
    evaluate_obligation,
    verify_repository_evidence,
)

SCHEMA_VERSION = "saga.transition-receipt.v1"
DELIBERATION_RECEIPT_SCHEMA = "multi-agent-consensus.deliberation-receipt.v1"
_SLUG = re.compile(r"[A-Za-z0-9._-]+")

_CATEGORY_KINDS: dict[str, frozenset[EvidenceKind]] = {
    "input_refs": frozenset({EvidenceKind.INPUT}),
    "operator_decisions": frozenset({EvidenceKind.OPERATOR_DECISION}),
    "execution_receipts": frozenset({EvidenceKind.EXECUTION_RECEIPT}),
    "canonical_outputs": frozenset({EvidenceKind.CANONICAL_OUTPUT}),
    "check_results": frozenset({EvidenceKind.CHECK_RESULT, EvidenceKind.QA_RESULT}),
    "review_findings": frozenset({EvidenceKind.REVIEW_FINDING}),
    "lifecycle_evidence": frozenset(
        {
            EvidenceKind.LIFECYCLE_STATE,
            EvidenceKind.CEREMONY_ARTIFACT,
            EvidenceKind.DELIBERATION_RECEIPT,
            EvidenceKind.FALLBACK_RECEIPT,
            EvidenceKind.HANDOFF_RECEIPT,
        }
    ),
    "external_facts": frozenset({EvidenceKind.GITHUB_FACT}),
}


class TransitionReceiptError(ObligationError):
    """A transition receipt is malformed or cannot be persisted safely."""


class TransitionReceiptConflictError(TransitionReceiptError):
    """A write-once receipt identity already contains different bytes."""


@dataclass(frozen=True)
class TransitionReceipt:
    """One attempted lifecycle transition and all evidence used to settle it."""

    receipt_id: str
    contract_id: str
    workstream_id: str
    transition_id: str
    obligation_id: str
    attempt: int
    input_refs: tuple[Evidence, ...]
    operator_decisions: tuple[Evidence, ...]
    execution_receipts: tuple[Evidence, ...]
    canonical_outputs: tuple[Evidence, ...]
    check_results: tuple[Evidence, ...]
    review_findings: tuple[Evidence, ...]
    lifecycle_evidence: tuple[Evidence, ...]
    external_facts: tuple[Evidence, ...]
    claimed_settlement: SettlementState
    settlement_state: SettlementState
    settlement_reasons: tuple[str, ...] = ()
    schema: str = field(default=SCHEMA_VERSION)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TransitionReceipt:
        _reject_unknown(
            data,
            {
                "schema",
                "receipt_id",
                "contract_id",
                "workstream_id",
                "transition_id",
                "obligation_id",
                "attempt",
                "input_refs",
                "operator_decisions",
                "execution_receipts",
                "canonical_outputs",
                "check_results",
                "review_findings",
                "lifecycle_evidence",
                "external_facts",
                "claimed_settlement",
                "settlement_state",
                "settlement_reasons",
            },
            "transition receipt",
        )
        schema = data.get("schema")
        if schema != SCHEMA_VERSION:
            raise TransitionReceiptError(
                f"unsupported transition receipt schema {schema!r}; expected {SCHEMA_VERSION!r}"
            )
        attempt = data.get("attempt")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise TransitionReceiptError("transition receipt attempt must be a positive integer")
        try:
            claimed = SettlementState(
                _required_str(data, "claimed_settlement", "transition receipt")
            )
            settled = SettlementState(_required_str(data, "settlement_state", "transition receipt"))
        except ValueError as exc:
            raise TransitionReceiptError(
                f"transition receipt has unsupported settlement state: {exc}"
            ) from exc
        reasons_raw = data.get("settlement_reasons")
        if not isinstance(reasons_raw, list) or any(
            not isinstance(item, str) or not item for item in reasons_raw
        ):
            raise TransitionReceiptError(
                "transition receipt settlement_reasons must be a list of non-empty strings"
            )
        receipt = cls(
            receipt_id=_slug_value(data, "receipt_id", "transition receipt"),
            contract_id=_slug_value(data, "contract_id", "transition receipt"),
            workstream_id=_slug_value(data, "workstream_id", "transition receipt"),
            transition_id=_slug_value(data, "transition_id", "transition receipt"),
            obligation_id=_slug_value(data, "obligation_id", "transition receipt"),
            attempt=attempt,
            input_refs=_evidence_list(data, "input_refs"),
            operator_decisions=_evidence_list(data, "operator_decisions"),
            execution_receipts=_evidence_list(data, "execution_receipts"),
            canonical_outputs=_evidence_list(data, "canonical_outputs"),
            check_results=_evidence_list(data, "check_results"),
            review_findings=_evidence_list(data, "review_findings"),
            lifecycle_evidence=_evidence_list(data, "lifecycle_evidence"),
            external_facts=_evidence_list(data, "external_facts"),
            claimed_settlement=claimed,
            settlement_state=settled,
            settlement_reasons=tuple(reasons_raw),
        )
        receipt.validate_shape()
        return receipt

    def validate_shape(self) -> None:
        if self.schema != SCHEMA_VERSION:
            raise TransitionReceiptError(
                f"unsupported transition receipt schema {self.schema!r}; "
                f"expected {SCHEMA_VERSION!r}"
            )
        for field_name, value in (
            ("receipt_id", self.receipt_id),
            ("contract_id", self.contract_id),
            ("workstream_id", self.workstream_id),
            ("transition_id", self.transition_id),
            ("obligation_id", self.obligation_id),
        ):
            _validate_slug(value, f"transition receipt.{field_name}")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int) or self.attempt < 1:
            raise TransitionReceiptError("transition receipt attempt must be a positive integer")
        if not isinstance(self.claimed_settlement, SettlementState):
            raise TransitionReceiptError(
                "transition receipt claimed_settlement must be a SettlementState"
            )
        if not isinstance(self.settlement_state, SettlementState):
            raise TransitionReceiptError(
                "transition receipt settlement_state must be a SettlementState"
            )
        if not isinstance(self.settlement_reasons, tuple) or any(
            not isinstance(reason, str) or not reason for reason in self.settlement_reasons
        ):
            raise TransitionReceiptError(
                "transition receipt settlement_reasons must contain non-empty strings"
            )
        for category, allowed in _CATEGORY_KINDS.items():
            items = getattr(self, category)
            if not isinstance(items, tuple):
                raise TransitionReceiptError(f"transition receipt {category} must be a tuple")
            for item in items:
                if not isinstance(item, Evidence):
                    raise TransitionReceiptError(
                        f"transition receipt {category} must contain Evidence values"
                    )
                item.validate()
                if item.kind not in allowed:
                    expected = ", ".join(sorted(kind.value for kind in allowed))
                    raise TransitionReceiptError(
                        f"{category} cannot contain {item.kind.value}; expected {expected}"
                    )
        evidence = self.all_evidence(include_inputs=True)
        ids = [item.evidence_id for item in evidence]
        if len(ids) != len(set(ids)):
            raise TransitionReceiptError(
                "transition receipt contains duplicate evidence_id values across categories"
            )
        expected_id = _derive_receipt_id(self.identity_payload())
        if self.receipt_id != expected_id:
            raise TransitionReceiptError(
                f"transition receipt identity mismatch: got {self.receipt_id!r}, "
                f"expected {expected_id!r}"
            )

    def all_evidence(self, *, include_inputs: bool = False) -> tuple[Evidence, ...]:
        categories: tuple[tuple[Evidence, ...], ...] = (
            self.operator_decisions,
            self.execution_receipts,
            self.canonical_outputs,
            self.check_results,
            self.review_findings,
            self.lifecycle_evidence,
            self.external_facts,
        )
        if include_inputs:
            categories = (self.input_refs, *categories)
        return tuple(item for category in categories for item in category)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "receipt_id": self.receipt_id,
            "contract_id": self.contract_id,
            "workstream_id": self.workstream_id,
            "transition_id": self.transition_id,
            "obligation_id": self.obligation_id,
            "attempt": self.attempt,
            "input_refs": [item.to_dict() for item in self.input_refs],
            "operator_decisions": [item.to_dict() for item in self.operator_decisions],
            "execution_receipts": [item.to_dict() for item in self.execution_receipts],
            "canonical_outputs": [item.to_dict() for item in self.canonical_outputs],
            "check_results": [item.to_dict() for item in self.check_results],
            "review_findings": [item.to_dict() for item in self.review_findings],
            "lifecycle_evidence": [item.to_dict() for item in self.lifecycle_evidence],
            "external_facts": [item.to_dict() for item in self.external_facts],
            "claimed_settlement": self.claimed_settlement.value,
            "settlement_state": self.settlement_state.value,
            "settlement_reasons": list(self.settlement_reasons),
        }

    def identity_payload(self) -> dict[str, Any]:
        """Return the normalized fields that determine receipt identity."""

        return {
            "contract_id": self.contract_id,
            "workstream_id": self.workstream_id,
            "transition_id": self.transition_id,
            "obligation_id": self.obligation_id,
            "attempt": self.attempt,
            "input_refs": [item.to_dict() for item in self.input_refs],
            "operator_decisions": [item.to_dict() for item in self.operator_decisions],
            "execution_receipts": [item.to_dict() for item in self.execution_receipts],
            "canonical_outputs": [item.to_dict() for item in self.canonical_outputs],
            "check_results": [item.to_dict() for item in self.check_results],
            "review_findings": [item.to_dict() for item in self.review_findings],
            "lifecycle_evidence": [item.to_dict() for item in self.lifecycle_evidence],
            "external_facts": [item.to_dict() for item in self.external_facts],
            "claimed_settlement": self.claimed_settlement.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n"


def build_transition_receipt(
    *,
    contract: ObligationContract,
    transition_id: str,
    obligation_id: str,
    attempt: int,
    input_refs: Sequence[Evidence] = (),
    operator_decisions: Sequence[Evidence] = (),
    execution_receipts: Sequence[Evidence] = (),
    canonical_outputs: Sequence[Evidence] = (),
    check_results: Sequence[Evidence] = (),
    review_findings: Sequence[Evidence] = (),
    lifecycle_evidence: Sequence[Evidence] = (),
    external_facts: Sequence[Evidence] = (),
    claimed_settlement: SettlementState | str | None = None,
    repo_root: Path | None = None,
) -> TransitionReceipt:
    """Build a receipt whose settlement is derived from its evidence."""

    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise TransitionReceiptError("transition receipt attempt must be a positive integer")
    contract.validate()
    _validate_slug(transition_id, "transition_id")
    _validate_slug(obligation_id, "obligation_id")
    evidence_categories: dict[str, tuple[Evidence, ...]] = {
        "input_refs": tuple(input_refs),
        "operator_decisions": tuple(operator_decisions),
        "execution_receipts": tuple(execution_receipts),
        "canonical_outputs": tuple(canonical_outputs),
        "check_results": tuple(check_results),
        "review_findings": tuple(review_findings),
        "lifecycle_evidence": tuple(lifecycle_evidence),
        "external_facts": tuple(external_facts),
    }
    _validate_evidence_categories(evidence_categories)
    proof = tuple(
        item
        for name, category in evidence_categories.items()
        if name != "input_refs"
        for item in category
    )
    identity_result = _repository_identity_result(
        obligation_id,
        tuple(item for category in evidence_categories.values() for item in category),
        repo_root=repo_root,
    )
    computed = identity_result or evaluate_obligation(
        contract,
        obligation_id,
        proof,
        repo_root=repo_root,
    )
    claim = (
        SettlementState(claimed_settlement) if claimed_settlement is not None else computed.state
    )
    final_state = computed.state if claim is computed.state else SettlementState.CONFLICTING
    reasons = list(computed.reasons)
    if final_state is SettlementState.CONFLICTING and claim is not computed.state:
        reasons.append(
            f"claimed settlement {claim.value!r} disagrees with computed "
            f"settlement {computed.state.value!r}"
        )
    identity_payload: dict[str, Any] = {
        "contract_id": contract.contract_id,
        "workstream_id": contract.workstream_id,
        "transition_id": transition_id,
        "obligation_id": obligation_id,
        "attempt": attempt,
        **{
            name: [item.to_dict() for item in category]
            for name, category in evidence_categories.items()
        },
        "claimed_settlement": claim.value,
    }
    receipt_id = _derive_receipt_id(identity_payload)
    receipt = TransitionReceipt(
        receipt_id=receipt_id,
        contract_id=contract.contract_id,
        workstream_id=contract.workstream_id,
        transition_id=transition_id,
        obligation_id=obligation_id,
        attempt=attempt,
        input_refs=evidence_categories["input_refs"],
        operator_decisions=evidence_categories["operator_decisions"],
        execution_receipts=evidence_categories["execution_receipts"],
        canonical_outputs=evidence_categories["canonical_outputs"],
        check_results=evidence_categories["check_results"],
        review_findings=evidence_categories["review_findings"],
        lifecycle_evidence=evidence_categories["lifecycle_evidence"],
        external_facts=evidence_categories["external_facts"],
        claimed_settlement=claim,
        settlement_state=final_state,
        settlement_reasons=tuple(reasons),
    )
    receipt.validate_shape()
    return receipt


def evaluate_transition_receipt(
    receipt: TransitionReceipt,
    contract: ObligationContract,
    *,
    repo_root: Path | None = None,
) -> SettlementResult:
    """Recompute and verify a serialized receipt against its contract."""

    receipt.validate_shape()
    contract.validate()
    if receipt.contract_id != contract.contract_id:
        return SettlementResult(
            receipt.obligation_id,
            SettlementState.CONFLICTING,
            reasons=("receipt contract_id does not match the supplied contract",),
        )
    if receipt.workstream_id != contract.workstream_id:
        return SettlementResult(
            receipt.obligation_id,
            SettlementState.CONFLICTING,
            reasons=("receipt workstream_id does not match the supplied contract",),
        )
    identity_result = _repository_identity_result(
        receipt.obligation_id,
        receipt.all_evidence(include_inputs=True),
        repo_root=repo_root,
    )
    computed = identity_result or evaluate_obligation(
        contract,
        receipt.obligation_id,
        receipt.all_evidence(),
        repo_root=repo_root,
    )
    expected = (
        computed.state
        if receipt.claimed_settlement is computed.state
        else SettlementState.CONFLICTING
    )
    if receipt.settlement_state is not expected:
        return SettlementResult(
            receipt.obligation_id,
            SettlementState.CONFLICTING,
            evidence_ids=computed.evidence_ids,
            reasons=(
                f"receipt settlement_state {receipt.settlement_state.value!r} does not match "
                f"recomputed state {expected.value!r}",
            ),
        )
    if expected is SettlementState.CONFLICTING and receipt.claimed_settlement is not computed.state:
        return SettlementResult(
            receipt.obligation_id,
            expected,
            evidence_ids=computed.evidence_ids,
            reasons=(
                *computed.reasons,
                f"claimed settlement {receipt.claimed_settlement.value!r} disagrees with "
                f"computed settlement {computed.state.value!r}",
            ),
        )
    return computed


def deliberation_evidence(
    *,
    repo_root: Path,
    receipt_path: Path,
    evidence_id: str,
    subject: str,
    producer: str,
) -> Evidence:
    """Bind one complete deliberation receipt as verified transition evidence."""

    _validate_slug(evidence_id, "deliberation evidence_id")
    if not isinstance(subject, str) or not subject.strip():
        raise TransitionReceiptError("deliberation evidence subject must be non-empty")
    if not isinstance(producer, str) or not producer.strip():
        raise TransitionReceiptError("deliberation evidence producer must be non-empty")
    root = repo_root.resolve()
    target = receipt_path if receipt_path.is_absolute() else root / receipt_path
    try:
        resolved = target.resolve(strict=True)
        reference = resolved.relative_to(root).as_posix()
        raw = resolved.read_bytes()
        data = json.loads(raw)
    except ValueError as exc:
        raise TransitionReceiptError(
            "deliberation receipt must resolve inside the repository"
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransitionReceiptError("deliberation receipt is not readable JSON") from exc
    expected = {
        "schema",
        "receipt_id",
        "manifest_id",
        "phase",
        "complete",
        "coverage",
        "requested",
        "observed",
        "host_capability_receipt",
        "accepted_results",
        "issues",
        "recovery_requests",
        "convergence",
        "escalation",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise TransitionReceiptError("deliberation receipt has an invalid closed shape")
    if data.get("schema") != DELIBERATION_RECEIPT_SCHEMA:
        raise TransitionReceiptError("deliberation receipt schema is unsupported")
    if data.get("complete") is not True:
        raise TransitionReceiptError("incomplete deliberation cannot become transition evidence")
    claimed_id = data.get("receipt_id")
    body = {key: value for key, value in data.items() if key != "receipt_id"}
    actual_id = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    if claimed_id != actual_id:
        raise TransitionReceiptError("deliberation receipt identity does not match its content")
    return Evidence(
        evidence_id=evidence_id,
        kind=EvidenceKind.DELIBERATION_RECEIPT,
        subject=subject,
        producer=producer,
        reference=reference,
        digest="sha256:" + hashlib.sha256(raw).hexdigest(),
        verification_state=VerificationState.VERIFIED,
        assertion="complete",
    )


def receipt_path(repo_root: Path, outcome_id: str, receipt_id: str) -> Path:
    """Return the canonical repository path for a transition receipt."""

    if outcome_id in {".", ".."} or not _SLUG.fullmatch(outcome_id):
        raise TransitionReceiptError("outcome_id must be a slug")
    if receipt_id in {".", ".."} or not _SLUG.fullmatch(receipt_id):
        raise TransitionReceiptError("receipt_id must be a slug")
    return repo_root / "docs" / "outcomes" / outcome_id / "receipts" / f"{receipt_id}.json"


def write_transition_receipt(
    repo_root: Path,
    outcome_id: str,
    receipt: TransitionReceipt,
) -> Path:
    """Atomically create a receipt, or return the identical existing receipt."""

    receipt.validate_shape()
    identity_result = _repository_identity_result(
        receipt.obligation_id,
        receipt.all_evidence(include_inputs=True),
        repo_root=repo_root,
    )
    if identity_result is not None and receipt.settlement_state in {
        SettlementState.SATISFIED,
        SettlementState.DEGRADED,
    }:
        raise TransitionReceiptError(
            f"cannot persist {receipt.settlement_state.value} receipt with "
            f"{identity_result.state.value} repository evidence: "
            f"{'; '.join(identity_result.reasons)}"
        )
    path = receipt_path(repo_root, outcome_id, receipt.receipt_id)
    content = receipt.to_json()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(
        f"{path.name}.{os.getpid()}.{threading.get_ident()}.{time.monotonic_ns()}.tmp"
    )
    tmp.write_text(content, encoding="utf-8")
    try:
        try:
            os.link(tmp, path)
        except FileExistsError:
            try:
                existing = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise TransitionReceiptConflictError(
                    f"receipt {receipt.receipt_id} exists but cannot be compared: {exc}"
                ) from exc
            if existing != content:
                raise TransitionReceiptConflictError(
                    f"receipt {receipt.receipt_id} already exists with different content"
                ) from None
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()
    return path


def _evidence_list(data: Mapping[str, Any], field_name: str) -> tuple[Evidence, ...]:
    if field_name not in data:
        raise TransitionReceiptError(f"transition receipt requires {field_name}")
    value = data[field_name]
    if not isinstance(value, list):
        raise TransitionReceiptError(f"transition receipt {field_name} must be a list")
    return tuple(
        Evidence.from_dict(_mapping(item, f"transition receipt {field_name}")) for item in value
    )


def _validate_evidence_categories(
    categories: Mapping[str, tuple[Evidence, ...]],
) -> None:
    seen: set[str] = set()
    for category, allowed in _CATEGORY_KINDS.items():
        for item in categories[category]:
            if not isinstance(item, Evidence):
                raise TransitionReceiptError(f"{category} must contain Evidence values")
            item.validate()
            if item.kind not in allowed:
                expected = ", ".join(sorted(kind.value for kind in allowed))
                raise TransitionReceiptError(
                    f"{category} cannot contain {item.kind.value}; expected {expected}"
                )
            if item.evidence_id in seen:
                raise TransitionReceiptError(
                    "transition receipt contains duplicate evidence_id values across categories"
                )
            seen.add(item.evidence_id)


def _repository_identity_result(
    obligation_id: str,
    evidence: tuple[Evidence, ...],
    *,
    repo_root: Path | None,
) -> SettlementResult | None:
    """Fail closed when receipt evidence identities cannot be reproduced."""

    unavailable: list[str] = []
    unsatisfied: list[str] = []
    conflicting: list[str] = []
    for item in evidence:
        if item.kind is EvidenceKind.INPUT:
            if item.verification_state in {
                VerificationState.UNKNOWN,
                VerificationState.UNAVAILABLE,
            }:
                unavailable.append(
                    f"input evidence {item.evidence_id} is {item.verification_state.value}"
                )
                continue
            if item.verification_state is VerificationState.UNVERIFIED:
                unsatisfied.append(f"input evidence {item.evidence_id} is unverified")
                continue
            if item.verification_state is VerificationState.CONFLICTING:
                conflicting.append(f"input evidence {item.evidence_id} is conflicting")
                continue
        if (
            item.kind in REPOSITORY_EVIDENCE_KINDS
            and item.verification_state is VerificationState.VERIFIED
        ):
            ok, reason = verify_repository_evidence(item, repo_root=repo_root)
            if not ok:
                if repo_root is None:
                    unavailable.append(reason)
                else:
                    conflicting.append(reason)
    if conflicting:
        return SettlementResult(
            obligation_id,
            SettlementState.CONFLICTING,
            reasons=tuple(conflicting),
        )
    if unavailable:
        return SettlementResult(
            obligation_id,
            SettlementState.UNAVAILABLE,
            reasons=tuple(unavailable),
        )
    if unsatisfied:
        return SettlementResult(
            obligation_id,
            SettlementState.UNSATISFIED,
            reasons=tuple(unsatisfied),
        )
    return None


def _derive_receipt_id(identity_payload: Mapping[str, Any]) -> str:
    return "tr-" + hashlib.sha256(_canonical_bytes(identity_payload)).hexdigest()[:24]


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TransitionReceiptError(f"{where} item must be an object")
    return value


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise TransitionReceiptError(f"{where} has unknown keys: {', '.join(unknown)}")


def _required_str(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise TransitionReceiptError(f"{where} requires non-empty string {field_name}")
    return value


def _slug_value(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = _required_str(data, field_name, where)
    _validate_slug(value, f"{where}.{field_name}")
    return value


def _validate_slug(value: Any, where: str) -> str:
    if not isinstance(value, str) or value in {".", ".."} or not _SLUG.fullmatch(value):
        raise TransitionReceiptError(f"{where} must be a slug")
    return value
