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
    Evidence,
    EvidenceKind,
    ObligationContract,
    ObligationError,
    SettlementResult,
    SettlementState,
    evaluate_obligation,
)

SCHEMA_VERSION = "saga.transition-receipt.v1"
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
            settled = SettlementState(
                _required_str(data, "settlement_state", "transition receipt")
            )
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
        for category, allowed in _CATEGORY_KINDS.items():
            for item in getattr(self, category):
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
    if not _SLUG.fullmatch(transition_id):
        raise TransitionReceiptError("transition_id must be a slug")
    evidence_categories = {
        "input_refs": tuple(input_refs),
        "operator_decisions": tuple(operator_decisions),
        "execution_receipts": tuple(execution_receipts),
        "canonical_outputs": tuple(canonical_outputs),
        "check_results": tuple(check_results),
        "review_findings": tuple(review_findings),
        "lifecycle_evidence": tuple(lifecycle_evidence),
        "external_facts": tuple(external_facts),
    }
    proof = tuple(
        item
        for name, category in evidence_categories.items()
        if name != "input_refs"
        for item in category
    )
    computed = evaluate_obligation(
        contract,
        obligation_id,
        proof,
        repo_root=repo_root,
    )
    claim = (
        SettlementState(claimed_settlement)
        if claimed_settlement is not None
        else computed.state
    )
    final_state = (
        computed.state
        if claim is computed.state
        else SettlementState.CONFLICTING
    )
    reasons = list(computed.reasons)
    if final_state is SettlementState.CONFLICTING and claim is not computed.state:
        reasons.append(
            f"claimed settlement {claim.value!r} disagrees with computed "
            f"settlement {computed.state.value!r}"
        )
    identity_payload = {
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
    receipt_id = "tr-" + hashlib.sha256(_canonical_bytes(identity_payload)).hexdigest()[:24]
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
    computed = evaluate_obligation(
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
        Evidence.from_dict(_mapping(item, f"transition receipt {field_name}"))
        for item in value
    )


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
    if value in {".", ".."} or not _SLUG.fullmatch(value):
        raise TransitionReceiptError(f"{where}.{field_name} must be a slug")
    return value
