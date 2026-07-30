#!/usr/bin/env python3
"""Versioned lifecycle-obligation contracts and settlement evaluation.

The evaluator is deliberately independent of command routing.  It answers one
question: does the supplied, independently verifiable evidence settle a named
obligation?  Callers such as outcome, loop, and resume decide what to do with
that answer in later integration work.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "saga.lifecycle-obligation.v1"

# The forward workstream contract follows plugins/saga/docs/lifecycle.md.  The
# generic legacy saga envelope still parses "retro"; this module does not
# reinterpret or migrate those stored envelopes.
STORED_LIFECYCLE_PHASES = ("ideation", "brainstorm", "plan", "review", "work", "qa")
OFF_CHAIN_OBLIGATIONS = ("impl-spec", "retro")

_SLUG = re.compile(r"[A-Za-z0-9._-]+")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class ObligationError(ValueError):
    """A lifecycle contract or evidence record is malformed."""


class SettlementState(StrEnum):
    """Closed settlement vocabulary shared by lifecycle consumers."""

    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


class RequirementLevel(StrEnum):
    """Whether an obligation is mandatory for settlement."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class ObligationKind(StrEnum):
    """Closed workstream obligation taxonomy."""

    STORED_PHASE = "stored-phase"
    OFF_CHAIN_CEREMONY = "off-chain-ceremony"
    GATE = "gate"
    ARTIFACT = "artifact"
    CHECK = "check"
    QUALITY_ASSURANCE = "quality-assurance"
    REVIEW = "review"
    DELIBERATION = "deliberation"
    HANDOFF = "handoff"
    EXTERNAL_GITHUB = "external-github"


class EvidenceKind(StrEnum):
    """Closed evidence roles that can appear in a transition receipt."""

    INPUT = "input"
    LIFECYCLE_STATE = "lifecycle-state"
    CEREMONY_ARTIFACT = "ceremony-artifact"
    OPERATOR_DECISION = "operator-decision"
    EXECUTION_RECEIPT = "execution-receipt"
    CANONICAL_OUTPUT = "canonical-output"
    CHECK_RESULT = "check-result"
    QA_RESULT = "qa-result"
    REVIEW_FINDING = "review-finding"
    DELIBERATION_RECEIPT = "deliberation-receipt"
    FALLBACK_RECEIPT = "fallback-receipt"
    HANDOFF_RECEIPT = "handoff-receipt"
    GITHUB_FACT = "github-fact"


class VerificationState(StrEnum):
    """Whether the evidence source was actually verified."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    CONFLICTING = "conflicting"


REPOSITORY_EVIDENCE_KINDS = frozenset(
    {
        EvidenceKind.INPUT,
        EvidenceKind.LIFECYCLE_STATE,
        EvidenceKind.CEREMONY_ARTIFACT,
        EvidenceKind.OPERATOR_DECISION,
        EvidenceKind.EXECUTION_RECEIPT,
        EvidenceKind.CANONICAL_OUTPUT,
        EvidenceKind.CHECK_RESULT,
        EvidenceKind.QA_RESULT,
        EvidenceKind.REVIEW_FINDING,
        EvidenceKind.DELIBERATION_RECEIPT,
        EvidenceKind.FALLBACK_RECEIPT,
        EvidenceKind.HANDOFF_RECEIPT,
    }
)

INDEPENDENT_EVIDENCE_KINDS = frozenset(
    {
        EvidenceKind.EXECUTION_RECEIPT,
        EvidenceKind.REVIEW_FINDING,
        EvidenceKind.QA_RESULT,
    }
)


@dataclass(frozen=True)
class EvidenceRule:
    """One evidence role required by an obligation."""

    kind: EvidenceKind
    minimum_count: int = 1
    independent: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceRule:
        _reject_unknown(data, {"kind", "minimum_count", "independent"}, "evidence rule")
        try:
            kind = EvidenceKind(_required_str(data, "kind", "evidence rule"))
        except ValueError as exc:
            raise ObligationError(f"evidence rule has unsupported kind: {exc}") from exc
        count = data.get("minimum_count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ObligationError("evidence rule minimum_count must be a positive integer")
        independent = data.get("independent", False)
        if not isinstance(independent, bool):
            raise ObligationError("evidence rule independent must be a boolean")
        if kind in INDEPENDENT_EVIDENCE_KINDS and not independent:
            raise ObligationError(f"{kind.value} evidence must be declared independent")
        return cls(kind=kind, minimum_count=count, independent=independent)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "minimum_count": self.minimum_count,
            "independent": self.independent,
        }


@dataclass(frozen=True)
class DegradedFallback:
    """A fallback declared before an optional obligation executes."""

    evidence: tuple[EvidenceRule, ...]
    state: SettlementState = SettlementState.DEGRADED

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DegradedFallback:
        _reject_unknown(data, {"state", "evidence"}, "fallback")
        try:
            state = SettlementState(_required_str(data, "state", "fallback"))
        except ValueError as exc:
            raise ObligationError(f"fallback has unsupported state: {exc}") from exc
        if state is not SettlementState.DEGRADED:
            raise ObligationError("an optional fallback state must be 'degraded'")
        evidence = _rules(data.get("evidence"), "fallback.evidence")
        if not evidence:
            raise ObligationError("fallback.evidence must declare at least one evidence rule")
        return cls(evidence=evidence, state=state)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "evidence": [rule.to_dict() for rule in self.evidence],
        }


@dataclass(frozen=True)
class Obligation:
    """One named settlement obligation in a workstream contract."""

    obligation_id: str
    kind: ObligationKind
    subject: str
    requirement: RequirementLevel
    producer: str
    required_evidence: tuple[EvidenceRule, ...]
    phase: str = ""
    command: str = ""
    fallback: DegradedFallback | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Obligation:
        _reject_unknown(
            data,
            {
                "obligation_id",
                "kind",
                "subject",
                "requirement",
                "producer",
                "required_evidence",
                "phase",
                "command",
                "fallback",
            },
            "obligation",
        )
        obligation_id = _slug_value(data, "obligation_id", "obligation")
        try:
            kind = ObligationKind(_required_str(data, "kind", f"obligation {obligation_id}"))
            requirement = RequirementLevel(
                _required_str(data, "requirement", f"obligation {obligation_id}")
            )
        except ValueError as exc:
            raise ObligationError(f"obligation {obligation_id} has unsupported enum: {exc}") from exc
        fallback_raw = data.get("fallback")
        if fallback_raw is not None and not isinstance(fallback_raw, Mapping):
            raise ObligationError(f"obligation {obligation_id} fallback must be an object or null")
        obligation = cls(
            obligation_id=obligation_id,
            kind=kind,
            subject=_required_str(data, "subject", f"obligation {obligation_id}"),
            requirement=requirement,
            producer=_required_str(data, "producer", f"obligation {obligation_id}"),
            required_evidence=_rules(
                data.get("required_evidence"), f"obligation {obligation_id}.required_evidence"
            ),
            phase=_optional_str(data, "phase", f"obligation {obligation_id}"),
            command=_optional_str(data, "command", f"obligation {obligation_id}"),
            fallback=DegradedFallback.from_dict(fallback_raw) if fallback_raw else None,
        )
        obligation.validate()
        return obligation

    def validate(self) -> None:
        if not self.required_evidence:
            raise ObligationError(
                f"obligation {self.obligation_id} must declare required_evidence"
            )
        if self.requirement is RequirementLevel.REQUIRED and self.fallback is not None:
            raise ObligationError(
                f"required obligation {self.obligation_id} cannot declare a degraded fallback"
            )
        if self.kind is ObligationKind.STORED_PHASE:
            if self.phase not in STORED_LIFECYCLE_PHASES or self.command:
                raise ObligationError(
                    f"stored-phase obligation {self.obligation_id} needs a supported phase "
                    "and no off-chain command"
                )
        elif self.kind is ObligationKind.OFF_CHAIN_CEREMONY:
            if self.command not in OFF_CHAIN_OBLIGATIONS or self.phase:
                raise ObligationError(
                    f"off-chain obligation {self.obligation_id} needs impl-spec or retro "
                    "and no stored phase"
                )
        elif self.phase or self.command:
            raise ObligationError(
                f"obligation {self.obligation_id} may use phase/command only for lifecycle kinds"
            )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "obligation_id": self.obligation_id,
            "kind": self.kind.value,
            "subject": self.subject,
            "requirement": self.requirement.value,
            "producer": self.producer,
            "required_evidence": [rule.to_dict() for rule in self.required_evidence],
        }
        if self.phase:
            out["phase"] = self.phase
        if self.command:
            out["command"] = self.command
        if self.fallback is not None:
            out["fallback"] = self.fallback.to_dict()
        return out


@dataclass(frozen=True)
class ObligationContract:
    """A complete workstream settlement contract."""

    contract_id: str
    workstream_id: str
    stored_lifecycle_phases: tuple[str, ...]
    off_chain_obligations: tuple[str, ...]
    obligations: tuple[Obligation, ...]
    schema: str = field(default=SCHEMA_VERSION)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ObligationContract:
        _reject_unknown(
            data,
            {
                "schema",
                "contract_id",
                "workstream_id",
                "stored_lifecycle_phases",
                "off_chain_obligations",
                "obligations",
            },
            "obligation contract",
        )
        schema = data.get("schema")
        if schema != SCHEMA_VERSION:
            raise ObligationError(
                f"unsupported lifecycle obligation schema {schema!r}; expected {SCHEMA_VERSION!r}"
            )
        phases = _unique_str_tuple(
            data.get("stored_lifecycle_phases"), "stored_lifecycle_phases"
        )
        off_chain = _unique_str_tuple(
            data.get("off_chain_obligations"), "off_chain_obligations"
        )
        invalid_phases = sorted(set(phases) - set(STORED_LIFECYCLE_PHASES))
        if invalid_phases:
            raise ObligationError(
                f"stored_lifecycle_phases contains unsupported values: {', '.join(invalid_phases)}"
            )
        invalid_off_chain = sorted(set(off_chain) - set(OFF_CHAIN_OBLIGATIONS))
        if invalid_off_chain:
            raise ObligationError(
                f"off_chain_obligations contains unsupported values: "
                f"{', '.join(invalid_off_chain)}"
            )
        obligations_raw = data.get("obligations")
        if not isinstance(obligations_raw, list) or not obligations_raw:
            raise ObligationError("obligation contract requires a non-empty obligations list")
        obligations = tuple(
            Obligation.from_dict(_mapping(item, "obligation")) for item in obligations_raw
        )
        ids = [item.obligation_id for item in obligations]
        if len(ids) != len(set(ids)):
            raise ObligationError("obligation contract contains duplicate obligation_id values")
        contract = cls(
            contract_id=_slug_value(data, "contract_id", "obligation contract"),
            workstream_id=_slug_value(data, "workstream_id", "obligation contract"),
            stored_lifecycle_phases=phases,
            off_chain_obligations=off_chain,
            obligations=obligations,
        )
        contract.validate()
        return contract

    def validate(self) -> None:
        for obligation in self.obligations:
            obligation.validate()
            if obligation.phase and obligation.phase not in self.stored_lifecycle_phases:
                raise ObligationError(
                    f"obligation {obligation.obligation_id} uses undeclared stored phase "
                    f"{obligation.phase!r}"
                )
            if obligation.command and obligation.command not in self.off_chain_obligations:
                raise ObligationError(
                    f"obligation {obligation.obligation_id} uses undeclared off-chain command "
                    f"{obligation.command!r}"
                )

    def obligation(self, obligation_id: str) -> Obligation:
        for obligation in self.obligations:
            if obligation.obligation_id == obligation_id:
                return obligation
        raise ObligationError(
            f"contract {self.contract_id} has no obligation {obligation_id!r}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "contract_id": self.contract_id,
            "workstream_id": self.workstream_id,
            "stored_lifecycle_phases": list(self.stored_lifecycle_phases),
            "off_chain_obligations": list(self.off_chain_obligations),
            "obligations": [obligation.to_dict() for obligation in self.obligations],
        }


@dataclass(frozen=True)
class Evidence:
    """One typed evidence identity carried by a transition receipt."""

    evidence_id: str
    kind: EvidenceKind
    subject: str
    producer: str
    reference: str
    digest: str
    verification_state: VerificationState
    assertion: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Evidence:
        _reject_unknown(
            data,
            {
                "evidence_id",
                "kind",
                "subject",
                "producer",
                "reference",
                "digest",
                "verification_state",
                "assertion",
            },
            "evidence",
        )
        evidence_id = _slug_value(data, "evidence_id", "evidence")
        try:
            kind = EvidenceKind(_required_str(data, "kind", f"evidence {evidence_id}"))
            state = VerificationState(
                _required_str(data, "verification_state", f"evidence {evidence_id}")
            )
        except ValueError as exc:
            raise ObligationError(f"evidence {evidence_id} has unsupported enum: {exc}") from exc
        digest = _required_str(data, "digest", f"evidence {evidence_id}")
        if not _DIGEST.fullmatch(digest):
            raise ObligationError(
                f"evidence {evidence_id} digest must be 'sha256:' plus 64 lowercase hex characters"
            )
        reference = _required_str(data, "reference", f"evidence {evidence_id}")
        if kind in REPOSITORY_EVIDENCE_KINDS:
            _repository_reference(reference, f"evidence {evidence_id}.reference")
        return cls(
            evidence_id=evidence_id,
            kind=kind,
            subject=_required_str(data, "subject", f"evidence {evidence_id}"),
            producer=_required_str(data, "producer", f"evidence {evidence_id}"),
            reference=reference,
            digest=digest,
            verification_state=state,
            assertion=_optional_str(data, "assertion", f"evidence {evidence_id}"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "subject": self.subject,
            "producer": self.producer,
            "reference": self.reference,
            "digest": self.digest,
            "verification_state": self.verification_state.value,
            "assertion": self.assertion,
        }


@dataclass(frozen=True)
class SettlementResult:
    """The evaluator's reproducible decision for one obligation."""

    obligation_id: str
    state: SettlementState
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def evaluate_obligation(
    contract: ObligationContract,
    obligation_id: str,
    evidence: Iterable[Evidence],
    *,
    repo_root: Path | None = None,
) -> SettlementResult:
    """Evaluate one obligation without trusting a producer-authored verdict."""

    contract.validate()
    obligation = contract.obligation(obligation_id)
    records = tuple(evidence)
    duplicate_ids = _duplicates(record.evidence_id for record in records)
    if duplicate_ids:
        return SettlementResult(
            obligation_id,
            SettlementState.CONFLICTING,
            reasons=(f"duplicate evidence identities: {', '.join(duplicate_ids)}",),
        )
    conflict = _authority_conflict(records, subject=obligation.subject)
    if conflict:
        return SettlementResult(
            obligation_id,
            SettlementState.CONFLICTING,
            reasons=(conflict,),
        )

    primary = _evaluate_rules(
        obligation,
        obligation.required_evidence,
        records,
        repo_root=repo_root,
    )
    if primary.state is SettlementState.SATISFIED:
        return primary
    if primary.state is SettlementState.CONFLICTING:
        return primary
    if obligation.requirement is RequirementLevel.REQUIRED or obligation.fallback is None:
        return primary

    fallback = _evaluate_rules(
        obligation,
        obligation.fallback.evidence,
        records,
        repo_root=repo_root,
    )
    if fallback.state is SettlementState.SATISFIED:
        return SettlementResult(
            obligation_id,
            SettlementState.DEGRADED,
            evidence_ids=fallback.evidence_ids,
            reasons=("optional obligation used its predeclared fallback",),
        )
    return fallback


def _evaluate_rules(
    obligation: Obligation,
    rules: tuple[EvidenceRule, ...],
    evidence: tuple[Evidence, ...],
    *,
    repo_root: Path | None,
) -> SettlementResult:
    accepted: list[str] = []
    reasons: list[str] = []
    saw_unavailable = False
    for rule in rules:
        candidates = [
            item
            for item in evidence
            if item.kind is rule.kind and item.subject == obligation.subject
        ]
        if any(item.verification_state is VerificationState.CONFLICTING for item in candidates):
            return SettlementResult(
                obligation.obligation_id,
                SettlementState.CONFLICTING,
                reasons=(f"{rule.kind.value} evidence reports conflicting authorities",),
            )
        if candidates and all(
            item.verification_state in {VerificationState.UNKNOWN, VerificationState.UNAVAILABLE}
            for item in candidates
        ):
            saw_unavailable = True
        verified: list[Evidence] = []
        for item in candidates:
            if item.verification_state is not VerificationState.VERIFIED:
                continue
            if rule.independent and item.producer == obligation.producer:
                continue
            if item.kind in REPOSITORY_EVIDENCE_KINDS:
                ok, reason = verify_repository_evidence(item, repo_root=repo_root)
                if not ok:
                    reasons.append(reason)
                    continue
            verified.append(item)
        distinct_producers = {item.producer for item in verified}
        count = len(distinct_producers) if rule.independent else len(verified)
        if count < rule.minimum_count:
            independence = " independent" if rule.independent else ""
            reasons.append(
                f"{rule.kind.value} needs {rule.minimum_count}{independence} verified evidence "
                f"item(s); found {count}"
            )
            continue
        accepted.extend(item.evidence_id for item in verified[: rule.minimum_count])
    if reasons:
        state = SettlementState.UNAVAILABLE if saw_unavailable else SettlementState.UNSATISFIED
        return SettlementResult(
            obligation.obligation_id,
            state,
            evidence_ids=tuple(dict.fromkeys(accepted)),
            reasons=tuple(reasons),
        )
    return SettlementResult(
        obligation.obligation_id,
        SettlementState.SATISFIED,
        evidence_ids=tuple(dict.fromkeys(accepted)),
    )


def verify_repository_evidence(
    evidence: Evidence,
    *,
    repo_root: Path | None,
) -> tuple[bool, str]:
    """Verify an evidence reference against repository bytes."""

    if evidence.kind not in REPOSITORY_EVIDENCE_KINDS:
        return True, ""
    if repo_root is None:
        return False, f"{evidence.evidence_id} cannot resolve repository evidence without repo_root"
    root = repo_root.resolve()
    target = root.joinpath(*PurePosixPath(evidence.reference).parts)
    try:
        resolved = target.resolve(strict=True)
    except OSError:
        return False, f"{evidence.evidence_id} references missing repository evidence"
    try:
        resolved.relative_to(root)
    except ValueError:
        return False, f"{evidence.evidence_id} resolves outside the repository"
    if not resolved.is_file():
        return False, f"{evidence.evidence_id} repository evidence is not a regular file"
    actual = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual != evidence.digest:
        return False, f"{evidence.evidence_id} repository evidence digest does not match"
    return True, ""


def _authority_conflict(evidence: tuple[Evidence, ...], *, subject: str) -> str:
    assertions: dict[tuple[EvidenceKind, str], set[str]] = {}
    for item in evidence:
        if (
            item.subject != subject
            or item.verification_state is not VerificationState.VERIFIED
            or not item.assertion
        ):
            continue
        assertions.setdefault((item.kind, item.reference), set()).add(item.assertion)
    for (kind, reference), values in assertions.items():
        if len(values) > 1:
            return (
                f"verified authorities conflict for {kind.value} at {reference}: "
                f"{', '.join(sorted(values))}"
            )
    return ""


def _rules(value: Any, where: str) -> tuple[EvidenceRule, ...]:
    if not isinstance(value, list):
        raise ObligationError(f"{where} must be a list")
    rules = tuple(EvidenceRule.from_dict(_mapping(item, where)) for item in value)
    kinds = [rule.kind for rule in rules]
    if len(kinds) != len(set(kinds)):
        raise ObligationError(f"{where} contains duplicate evidence kinds")
    return rules


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ObligationError(f"{where} must be an object")
    return value


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ObligationError(f"{where} has unknown keys: {', '.join(unknown)}")


def _required_str(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ObligationError(f"{where} requires non-empty string {field_name}")
    return value


def _optional_str(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = data.get(field_name, "")
    if not isinstance(value, str):
        raise ObligationError(f"{where}.{field_name} must be a string")
    return value


def _slug_value(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = _required_str(data, field_name, where)
    if value in {".", ".."} or not _SLUG.fullmatch(value):
        raise ObligationError(f"{where}.{field_name} must be a slug")
    return value


def _unique_str_tuple(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ObligationError(f"{where} must be a list")
    if any(not isinstance(item, str) or not item for item in value):
        raise ObligationError(f"{where} must contain non-empty strings")
    values = tuple(value)
    if len(values) != len(set(values)):
        raise ObligationError(f"{where} contains duplicate values")
    return values


def _repository_reference(value: str, where: str) -> str:
    if "\\" in value or "\x00" in value:
        raise ObligationError(f"{where} must use a safe repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ObligationError(f"{where} must be a normalized repository-relative path")
    if path.as_posix() != value:
        raise ObligationError(f"{where} must be a normalized repository-relative path")
    return value


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)
