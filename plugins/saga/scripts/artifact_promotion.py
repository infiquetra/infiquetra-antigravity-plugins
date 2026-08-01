#!/usr/bin/env python3
"""Canonical, local-only promotion of staged Saga artifacts into repository evidence."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, cast

import transition_receipts
from lifecycle_obligations import (
    INDEPENDENT_EVIDENCE_KINDS,
    Evidence,
    EvidenceKind,
    SettlementState,
    verify_independent_receipt,
    verify_repository_evidence,
)

SCHEMA_VERSION = "saga.artifact-promotion-receipt.v1"
ABANDONMENT_SCHEMA = "saga.artifact-abandonment.v1"
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024

PHASE_TARGETS: dict[str, str] = {
    "ideate": "ideation",
    "brainstorm": "brainstorms",
    "impl-spec": "specs",
    "plan": "plans",
    "doc-review": "reviews",
    "work": "work-sessions",
    "code-review": "code-reviews",
    "qa": "qa",
    "retro": "retros",
    "handoff": "handoffs",
    "outcome": "outcomes",
    "conformance": "conformance",
}
SOURCE_ROLES = frozenset(
    {
        "antigravity-brain",
        "antigravity-runtime",
        "repository-staging",
        "historical-import",
        "inline",
    }
)
EVIDENCE_KINDS = frozenset({"execution", "review", "qa", "operator"})
_EVIDENCE_KIND_MAP = {
    "execution": EvidenceKind.EXECUTION_RECEIPT,
    "review": EvidenceKind.REVIEW_FINDING,
    "qa": EvidenceKind.QA_RESULT,
    "operator": EvidenceKind.OPERATOR_DECISION,
}
_SAFE_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_CONTENT = (
    ("absolute home path", re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[^\s<>'\"]+")),
    (
        "credential-shaped value",
        re.compile(
            r"(?:gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|"
            r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{16,}|"
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
            r"(?i:(?:password|secret|token|api[_ -]?key)\s*[:=]\s*[^\s]+))"
        ),
    ),
    (
        "private hostname",
        re.compile(r"(?i:\b[a-z0-9][a-z0-9-]{0,62}\.(?:local|lan|internal|home)\b)"),
    ),
    (
        "transcript payload",
        re.compile(r"(?i:(?:\"transcript\"|transcript_path)\s*[:=]|BEGIN[ _-]+TRANSCRIPT)"),
    ),
)


class ArtifactPromotionError(ValueError):
    """A promotion request is malformed or cannot be persisted safely."""


class ArtifactPromotionConflictError(ArtifactPromotionError):
    """A content-derived receipt identity already contains different bytes."""


@dataclass(frozen=True)
class PromotionReceipt:
    """Closed durable record of one canonical promotion attempt."""

    promotion_id: str
    outcome_id: str
    phase: str
    source_role: str
    source_ref: str
    historical_import: bool
    target_ref: str
    expected_predecessor_sha256: str | None
    staged_sha256: str
    canonical_sha256: str | None
    transition_receipt_ref: str
    transition_receipt_sha256: str
    transition_receipt_id: str
    transition_settlement: str
    evidence_refs: dict[str, dict[str, str]]
    state: SettlementState
    conflict_ref: str | None
    operator_adjudication_required: bool
    missing_required_evidence: tuple[str, ...] = ()
    schema: str = field(default=SCHEMA_VERSION)

    def body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "outcome_id": self.outcome_id,
            "phase": self.phase,
            "source": {
                "role": self.source_role,
                "reference": self.source_ref,
                "historical_import": self.historical_import,
            },
            "target_ref": self.target_ref,
            "expected_predecessor_sha256": self.expected_predecessor_sha256,
            "staged_sha256": self.staged_sha256,
            "canonical_sha256": self.canonical_sha256,
            "transition_receipt": {
                "reference": self.transition_receipt_ref,
                "sha256": self.transition_receipt_sha256,
                "receipt_id": self.transition_receipt_id,
                "settlement_state": self.transition_settlement,
            },
            "evidence_refs": self.evidence_refs,
            "state": self.state.value,
            "conflict_ref": self.conflict_ref,
            "operator_adjudication_required": self.operator_adjudication_required,
            "missing_required_evidence": list(self.missing_required_evidence),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "promotion_id": self.promotion_id}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def validate(self) -> None:
        if self.schema != SCHEMA_VERSION:
            raise ArtifactPromotionError("unsupported artifact promotion receipt schema")
        _slug(self.promotion_id, "promotion_id")
        _slug(self.outcome_id, "outcome_id")
        if self.phase not in PHASE_TARGETS:
            raise ArtifactPromotionError("promotion receipt phase is unsupported")
        if self.source_role not in SOURCE_ROLES:
            raise ArtifactPromotionError("promotion receipt source role is unsupported")
        _logical_reference(self.source_ref, "promotion receipt source reference")
        target = _logical_reference(self.target_ref, "promotion receipt target reference")
        if len(target.parts) < 3 or target.parts[:2] != ("docs", PHASE_TARGETS[self.phase]):
            raise ArtifactPromotionError("promotion receipt target does not match its phase")
        _logical_reference(self.transition_receipt_ref, "promotion receipt transition reference")
        if not isinstance(self.historical_import, bool):
            raise ArtifactPromotionError("historical_import must be a boolean")
        if self.historical_import != (self.source_role == "historical-import"):
            raise ArtifactPromotionError("historical import state must match its source role")
        _digest(self.staged_sha256, "staged_sha256")
        _optional_digest(self.expected_predecessor_sha256, "expected_predecessor_sha256")
        _optional_digest(self.canonical_sha256, "canonical_sha256")
        _digest(self.transition_receipt_sha256, "transition receipt sha256")
        if not isinstance(self.state, SettlementState):
            raise ArtifactPromotionError("promotion receipt state is unsupported")
        if self.state not in {
            SettlementState.SATISFIED,
            SettlementState.UNSATISFIED,
            SettlementState.CONFLICTING,
        }:
            raise ArtifactPromotionError("promotion receipt state is unsupported")
        if set(self.evidence_refs) - EVIDENCE_KINDS:
            raise ArtifactPromotionError("promotion receipt evidence kind is unsupported")
        for binding in self.evidence_refs.values():
            if not isinstance(binding, Mapping) or set(binding) != {
                "evidence_id",
                "producer",
                "reference",
                "sha256",
            }:
                raise ArtifactPromotionError("promotion receipt evidence binding is invalid")
            for field_name in ("evidence_id", "producer", "reference"):
                if not isinstance(binding[field_name], str) or not binding[field_name]:
                    raise ArtifactPromotionError("promotion receipt evidence identity is invalid")
            _logical_reference(binding["reference"], "promotion receipt evidence reference")
            _digest(binding["sha256"], "promotion receipt evidence sha256")
        if tuple(sorted(set(self.missing_required_evidence))) != tuple(
            self.missing_required_evidence
        ):
            raise ArtifactPromotionError("missing evidence kinds must be unique and sorted")
        if set(self.missing_required_evidence) - EVIDENCE_KINDS:
            raise ArtifactPromotionError("missing evidence kind is unsupported")
        _slug(self.transition_receipt_id, "transition_receipt_id")
        try:
            transition_state = SettlementState(self.transition_settlement)
        except ValueError as exc:
            raise ArtifactPromotionError("transition settlement state is unsupported") from exc
        if self.state is SettlementState.CONFLICTING:
            if not self.conflict_ref or not self.operator_adjudication_required:
                raise ArtifactPromotionError("conflicting promotion must preserve a candidate")
            conflict = _logical_reference(self.conflict_ref, "promotion receipt conflict reference")
            if conflict.parts[:4] != ("docs", "outcomes", self.outcome_id, "conflicts"):
                raise ArtifactPromotionError("promotion receipt conflict reference is invalid")
        elif self.conflict_ref is not None or self.operator_adjudication_required:
            raise ArtifactPromotionError("non-conflicting promotion cannot require adjudication")
        if self.state is SettlementState.SATISFIED and (
            self.missing_required_evidence or transition_state is not SettlementState.SATISFIED
        ):
            raise ArtifactPromotionError("satisfied promotion has unsettled required evidence")
        if (
            self.state is not SettlementState.CONFLICTING
            and self.canonical_sha256 != self.staged_sha256
        ):
            raise ArtifactPromotionError("non-conflicting promotion must bind the staged content")
        expected_id = _identity(self.body())
        if self.promotion_id != expected_id:
            raise ArtifactPromotionError("promotion receipt identity does not match its content")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PromotionReceipt:
        expected = {
            "schema",
            "promotion_id",
            "outcome_id",
            "phase",
            "source",
            "target_ref",
            "expected_predecessor_sha256",
            "staged_sha256",
            "canonical_sha256",
            "transition_receipt",
            "evidence_refs",
            "state",
            "conflict_ref",
            "operator_adjudication_required",
            "missing_required_evidence",
        }
        if set(data) != expected:
            raise ArtifactPromotionError("artifact promotion receipt has an invalid closed shape")
        source = _closed_mapping(data.get("source"), {"role", "reference", "historical_import"})
        transition = _closed_mapping(
            data.get("transition_receipt"),
            {"reference", "sha256", "receipt_id", "settlement_state"},
        )
        evidence_raw = data.get("evidence_refs")
        missing_raw = data.get("missing_required_evidence")
        if not isinstance(evidence_raw, dict):
            raise ArtifactPromotionError("promotion receipt evidence_refs must be an object")
        if not isinstance(missing_raw, list) or any(
            not isinstance(item, str) for item in missing_raw
        ):
            raise ArtifactPromotionError("promotion receipt missing evidence must be a list")
        if not isinstance(source.get("historical_import"), bool):
            raise ArtifactPromotionError("historical_import must be a boolean")
        if not isinstance(data.get("operator_adjudication_required"), bool):
            raise ArtifactPromotionError("operator_adjudication_required must be a boolean")
        try:
            receipt = cls(
                schema=str(data.get("schema", "")),
                promotion_id=str(data.get("promotion_id", "")),
                outcome_id=str(data.get("outcome_id", "")),
                phase=str(data.get("phase", "")),
                source_role=str(source.get("role", "")),
                source_ref=str(source.get("reference", "")),
                historical_import=source["historical_import"],
                target_ref=str(data.get("target_ref", "")),
                expected_predecessor_sha256=_nullable_string(
                    data.get("expected_predecessor_sha256")
                ),
                staged_sha256=str(data.get("staged_sha256", "")),
                canonical_sha256=_nullable_string(data.get("canonical_sha256")),
                transition_receipt_ref=str(transition.get("reference", "")),
                transition_receipt_sha256=str(transition.get("sha256", "")),
                transition_receipt_id=str(transition.get("receipt_id", "")),
                transition_settlement=str(transition.get("settlement_state", "")),
                evidence_refs={str(key): dict(value) for key, value in evidence_raw.items()},
                state=SettlementState(str(data.get("state", ""))),
                conflict_ref=_nullable_string(data.get("conflict_ref")),
                operator_adjudication_required=data["operator_adjudication_required"],
                missing_required_evidence=tuple(missing_raw),
            )
        except (TypeError, ValueError) as exc:
            raise ArtifactPromotionError("artifact promotion receipt has invalid values") from exc
        receipt.validate()
        return receipt


@dataclass(frozen=True)
class PromotionResult:
    """Paths and receipt returned by a promotion attempt."""

    receipt: PromotionReceipt
    artifact_path: Path
    receipt_path: Path
    projection_path: Path | None = None


def sanitize_promoted_content(content: bytes) -> None:
    """Reject unsafe promoted evidence without echoing the matched value."""

    if not content or len(content) > MAX_ARTIFACT_BYTES:
        raise ArtifactPromotionError("promoted content is empty or exceeds the byte limit")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArtifactPromotionError("promoted content must be UTF-8 text") from exc
    for label, pattern in _UNSAFE_CONTENT:
        if pattern.search(text):
            raise ArtifactPromotionError(f"promoted content contains a forbidden {label}")


def promote_artifact(
    *,
    repo_root: Path,
    outcome_id: str,
    phase: str,
    source_role: str,
    source_ref: str,
    staged_content: str | bytes,
    target_ref: str,
    expected_predecessor_sha256: str | None,
    transition_receipt_ref: str,
    historical_import: bool = False,
    evidence_refs: Mapping[str, str] | None = None,
    required_evidence: Sequence[str] | None = None,
    projection_path: Path | None = None,
) -> PromotionResult:
    """Promote staged content or preserve a conflict without performing remote mutations."""

    root = repo_root.resolve(strict=True)
    _slug(outcome_id, "outcome_id")
    if phase not in PHASE_TARGETS:
        raise ArtifactPromotionError("phase is not an artifact-producing Saga phase")
    if source_role not in SOURCE_ROLES:
        raise ArtifactPromotionError("source_role is unsupported")
    if historical_import != (source_role == "historical-import"):
        raise ArtifactPromotionError("historical_import must match source_role")
    if not source_ref or Path(source_ref).is_absolute():
        raise ArtifactPromotionError("source_ref must be a non-empty logical reference")
    _optional_digest(expected_predecessor_sha256, "expected_predecessor_sha256")
    content = staged_content.encode("utf-8") if isinstance(staged_content, str) else staged_content
    if not isinstance(content, bytes):
        raise ArtifactPromotionError("staged_content must be text or bytes")

    target, normalized_target = _target(root, phase, target_ref)
    transition, normalized_transition, transition_sha = _transition_receipt(
        root, transition_receipt_ref
    )
    bound_evidence = _evidence_bindings(root, evidence_refs or {}, transition)
    required = _required_evidence(historical_import, required_evidence)
    missing = tuple(sorted(required - set(bound_evidence)))
    sanitize_promoted_content(content)
    if projection_path is not None:
        _validate_projection_path(root, projection_path)
    _assert_no_symlinks(root, root / "docs" / "outcomes" / outcome_id / "promotion-receipts")
    _assert_no_symlinks(root, root / "docs" / "outcomes" / outcome_id / "conflicts")

    staged_sha = _sha256(content)
    conflict = False
    canonical_sha: str | None
    conflict_ref: str | None = None

    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlinks(root, target)
    with _directory_lock(target.parent):
        current = target.read_bytes() if target.exists() else None
        current_sha = _sha256(current) if current is not None else None
        if current_sha == staged_sha:
            canonical_sha = staged_sha
        elif current_sha != expected_predecessor_sha256:
            conflict = True
            canonical_sha = current_sha
        else:
            _replace_content(target, content)
            canonical_sha = staged_sha

        state = _promotion_state(
            conflict=conflict,
            transition_state=transition.settlement_state,
            missing_evidence=missing,
        )
        draft = PromotionReceipt(
            promotion_id="pending",
            outcome_id=outcome_id,
            phase=phase,
            source_role=source_role,
            source_ref=source_ref,
            historical_import=historical_import,
            target_ref=normalized_target,
            expected_predecessor_sha256=expected_predecessor_sha256,
            staged_sha256=staged_sha,
            canonical_sha256=canonical_sha,
            transition_receipt_ref=normalized_transition,
            transition_receipt_sha256=transition_sha,
            transition_receipt_id=transition.receipt_id,
            transition_settlement=transition.settlement_state.value,
            evidence_refs=bound_evidence,
            state=state,
            conflict_ref=None,
            operator_adjudication_required=conflict,
            missing_required_evidence=missing,
        )
        if conflict:
            candidate = (
                root
                / "docs"
                / "outcomes"
                / outcome_id
                / "conflicts"
                / f"{staged_sha}{target.suffix}"
            )
            _assert_no_symlinks(root, candidate)
            _write_once(candidate, content)
            conflict_ref = candidate.relative_to(root).as_posix()
            draft = PromotionReceipt(**{**draft.__dict__, "conflict_ref": conflict_ref})
        promotion_id = _identity(draft.body())
        receipt = PromotionReceipt(**{**draft.__dict__, "promotion_id": promotion_id})
        receipt.validate()
        receipt_path = _receipt_path(root, outcome_id, receipt.promotion_id)
        _assert_no_symlinks(root, receipt_path)
        _write_receipt(receipt_path, receipt.to_json())

    written_projection = _write_projection(projection_path, receipt) if projection_path else None
    artifact_path = root / conflict_ref if conflict_ref is not None else target
    return PromotionResult(receipt, artifact_path, receipt_path, written_projection)


def terminal_abandonment(
    *,
    outcome_id: str,
    phase: str,
    source_role: str,
    source_ref: str,
    reason: str,
    unfinished: bool,
    explicitly_abandoned: bool,
) -> dict[str, Any]:
    """Return a non-durable terminal no-save record for explicitly abandoned exploration."""

    _slug(outcome_id, "outcome_id")
    if phase not in {"ideate", "brainstorm"}:
        raise ArtifactPromotionError("terminal no-save is limited to unfinished exploration")
    if source_role not in SOURCE_ROLES or not source_ref or Path(source_ref).is_absolute():
        raise ArtifactPromotionError("abandonment source must be a logical staging reference")
    if not unfinished or not explicitly_abandoned or not reason.strip():
        raise ArtifactPromotionError(
            "terminal no-save requires unfinished work, explicit abandonment, and a reason"
        )
    body = {
        "schema": ABANDONMENT_SCHEMA,
        "outcome_id": outcome_id,
        "phase": phase,
        "source": {"role": source_role, "reference": source_ref},
        "reason": reason.strip(),
        "state": "abandoned",
        "phase_complete": False,
        "resumable": False,
        "handoffable": False,
        "outcome_settled": False,
    }
    return {**body, "abandonment_id": _identity(body)}


def _target(root: Path, phase: str, target_ref: str) -> tuple[Path, str]:
    path, normalized = _repository_path(root, target_ref, must_exist=False)
    relative = PurePosixPath(normalized)
    if len(relative.parts) < 3 or relative.parts[:2] != ("docs", PHASE_TARGETS[phase]):
        raise ArtifactPromotionError("target is outside the phase's canonical docs family")
    if path.suffix not in {".md", ".json", ".yaml", ".yml"}:
        raise ArtifactPromotionError("target must use an approved lifecycle document extension")
    return path, normalized


def _transition_receipt(
    root: Path, reference: str
) -> tuple[transition_receipts.TransitionReceipt, str, str]:
    try:
        path, normalized = _repository_path(root, reference, must_exist=True)
        raw = path.read_bytes()
        data = json.loads(raw)
        receipt = transition_receipts.TransitionReceipt.from_dict(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArtifactPromotionError("transition receipt is missing or invalid") from exc
    return receipt, normalized, _sha256(raw)


def _evidence_bindings(
    root: Path,
    evidence_refs: Mapping[str, str],
    transition: transition_receipts.TransitionReceipt,
) -> dict[str, dict[str, str]]:
    if set(evidence_refs) - EVIDENCE_KINDS:
        raise ArtifactPromotionError("historical evidence kind is unsupported")
    result: dict[str, dict[str, str]] = {}
    for kind in sorted(evidence_refs):
        path, normalized = _repository_path(root, evidence_refs[kind], must_exist=True)
        candidates = _transition_evidence(transition, _EVIDENCE_KIND_MAP[kind])
        matches = [evidence for evidence in candidates if evidence.reference == normalized]
        if len(matches) != 1:
            raise ArtifactPromotionError(
                "historical evidence is not uniquely bound by the transition receipt"
            )
        evidence = matches[0]
        valid, _reason = verify_repository_evidence(evidence, repo_root=root)
        if valid and evidence.kind in INDEPENDENT_EVIDENCE_KINDS:
            valid, _reason = verify_independent_receipt(
                evidence,
                obligation_producer=evidence.producer,
                repo_root=root,
            )
        if not valid:
            raise ArtifactPromotionError("historical evidence failed identity verification")
        result[kind] = {
            "evidence_id": evidence.evidence_id,
            "producer": evidence.producer,
            "reference": normalized,
            "sha256": _sha256(path.read_bytes()),
        }
    return result


def _transition_evidence(
    transition: transition_receipts.TransitionReceipt,
    kind: EvidenceKind,
) -> tuple[Evidence, ...]:
    if kind is EvidenceKind.EXECUTION_RECEIPT:
        return cast(tuple[Evidence, ...], transition.execution_receipts)
    if kind is EvidenceKind.REVIEW_FINDING:
        return cast(tuple[Evidence, ...], transition.review_findings)
    if kind is EvidenceKind.QA_RESULT:
        return tuple(item for item in transition.check_results if item.kind is kind)
    if kind is EvidenceKind.OPERATOR_DECISION:
        return cast(tuple[Evidence, ...], transition.operator_decisions)
    raise ArtifactPromotionError("historical evidence kind is unsupported")


def _required_evidence(historical_import: bool, supplied: Sequence[str] | None) -> set[str]:
    required = set(EVIDENCE_KINDS if historical_import and supplied is None else supplied or ())
    if required - EVIDENCE_KINDS:
        raise ArtifactPromotionError("required historical evidence kind is unsupported")
    return required


def _promotion_state(
    *, conflict: bool, transition_state: SettlementState, missing_evidence: Sequence[str]
) -> SettlementState:
    if conflict:
        return SettlementState.CONFLICTING
    if missing_evidence or transition_state is not SettlementState.SATISFIED:
        return SettlementState.UNSATISFIED
    return SettlementState.SATISFIED


def _repository_path(root: Path, reference: str, *, must_exist: bool) -> tuple[Path, str]:
    candidate = PurePosixPath(reference)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise ArtifactPromotionError("repository reference must be a normalized relative path")
    normalized = candidate.as_posix()
    path = root.joinpath(*candidate.parts)
    _assert_no_symlinks(root, path)
    try:
        path.resolve(strict=must_exist).relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ArtifactPromotionError(
            "repository reference is missing or escapes the repository"
        ) from exc
    if must_exist and (not path.is_file() or path.is_symlink()):
        raise ArtifactPromotionError("repository reference must identify an ordinary file")
    return path, normalized


def _assert_no_symlinks(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ArtifactPromotionError("path escapes the repository") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ArtifactPromotionError("promotion paths must not contain symlinks")


@contextmanager
def _directory_lock(directory: Path) -> Iterator[None]:
    import fcntl

    descriptor = os.open(directory, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _replace_content(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            with contextlib.suppress(OSError):
                Path(temporary).unlink()
        raise ArtifactPromotionError("could not persist canonical artifact") from exc


def _write_once(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink():
                raise ArtifactPromotionConflictError(
                    "write-once promotion path must not be a symlink"
                ) from None
            if path.read_bytes() != content:
                raise ArtifactPromotionConflictError(
                    "write-once promotion path has different content"
                ) from None
    finally:
        if temporary is not None:
            with contextlib.suppress(FileNotFoundError):
                Path(temporary).unlink()


def _write_receipt(path: Path, content: str) -> None:
    _write_once(path, content.encode("utf-8"))


def _write_projection(path: Path, receipt: PromotionReceipt) -> Path | None:
    payload = {
        "schema": "saga.artifact-projection.v1",
        "authoritative": False,
        "canonical_ref": receipt.target_ref,
        "canonical_sha256": receipt.canonical_sha256,
        "promotion_id": receipt.promotion_id,
    }
    try:
        _replace_content(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())
    except ArtifactPromotionError:
        return None
    return path


def _validate_projection_path(root: Path, path: Path) -> None:
    resolved = path.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return
    if not relative.parts or relative.parts[0] != ".gemini":
        raise ArtifactPromotionError(
            "repository-local projections must remain under the ignored .gemini runtime root"
        )
    _assert_no_symlinks(root, path)


def _receipt_path(root: Path, outcome_id: str, promotion_id: str) -> Path:
    return root / "docs" / "outcomes" / outcome_id / "promotion-receipts" / f"{promotion_id}.json"


def _closed_mapping(value: Any, expected: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ArtifactPromotionError("artifact promotion receipt has an invalid nested shape")
    return value


def _nullable_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ArtifactPromotionError("receipt digest or reference must be a string or null")
    return value


def _logical_reference(value: str, field_name: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ArtifactPromotionError(f"{field_name} must be a logical relative path")
    reference = PurePosixPath(value)
    if reference.is_absolute() or ".." in reference.parts or reference.as_posix() != value:
        raise ArtifactPromotionError(f"{field_name} must be a logical relative path")
    return reference


def _slug(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SAFE_SLUG.fullmatch(value) or value in {".", ".."}:
        raise ArtifactPromotionError(f"{field_name} must be a bounded slug")


def _digest(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ArtifactPromotionError(f"{field_name} must be a SHA-256 digest")


def _optional_digest(value: str | None, field_name: str) -> None:
    if value is not None:
        _digest(value, field_name)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _identity(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _contained_cli_file(repo_root: Path, reference: str, label: str) -> Path:
    path = Path(reference)
    if path.is_absolute() or ".." in path.parts:
        raise ArtifactPromotionError(f"{label} must be a repository-relative file")
    root = repo_root.resolve(strict=True)
    try:
        resolved = (root / path).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ArtifactPromotionError(f"{label} must resolve inside the repository") from exc
    if not resolved.is_file():
        raise ArtifactPromotionError(f"{label} must be a regular file")
    return resolved


def _cli_evidence_refs(repo_root: Path, reference: str | None) -> dict[str, str]:
    if reference is None:
        return {}
    path = _contained_cli_file(repo_root, reference, "evidence input")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactPromotionError("evidence input is invalid JSON") from exc
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()
    ):
        raise ArtifactPromotionError("evidence input must map evidence kinds to relative files")
    return {str(key): str(item) for key, item in value.items()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Promote one staged Saga artifact through the canonical local transaction."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    promote = subparsers.add_parser("promote", help="promote one staged artifact")
    promote.add_argument("--repo-root", default=".")
    promote.add_argument("--outcome-id", required=True)
    promote.add_argument("--phase", choices=sorted(PHASE_TARGETS), required=True)
    promote.add_argument("--source-role", choices=sorted(SOURCE_ROLES), required=True)
    promote.add_argument("--source-ref", required=True)
    promote.add_argument("--staged-file", required=True)
    promote.add_argument("--target-ref", required=True)
    promote.add_argument("--expected-predecessor-sha256")
    promote.add_argument("--transition-receipt", required=True)
    promote.add_argument("--historical-import", action="store_true")
    promote.add_argument("--evidence")
    promote.add_argument("--required-evidence", action="append", default=[])
    promote.add_argument("--projection")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bounded artifact-promotion command-line contract."""

    args = _build_parser().parse_args(argv)
    try:
        repo_root = Path(args.repo_root)
        root = repo_root.resolve(strict=True)
        staged_path = _contained_cli_file(root, args.staged_file, "staged file")
        evidence = _cli_evidence_refs(root, args.evidence)
        projection: Path | None = None
        if args.projection is not None:
            projection_ref = _logical_reference(args.projection, "projection")
            projection = root.joinpath(*projection_ref.parts)
        result = promote_artifact(
            repo_root=root,
            outcome_id=args.outcome_id,
            phase=args.phase,
            source_role=args.source_role,
            source_ref=args.source_ref,
            staged_content=staged_path.read_bytes(),
            target_ref=args.target_ref,
            expected_predecessor_sha256=args.expected_predecessor_sha256,
            transition_receipt_ref=args.transition_receipt,
            historical_import=args.historical_import,
            evidence_refs=evidence,
            required_evidence=args.required_evidence,
            projection_path=projection,
        )
        print(
            json.dumps(
                {
                    "schema": SCHEMA_VERSION,
                    "artifact_path": result.artifact_path.resolve().relative_to(root).as_posix(),
                    "promotion_id": result.receipt.promotion_id,
                    "receipt_path": result.receipt_path.resolve().relative_to(root).as_posix(),
                    "state": result.receipt.state.value,
                },
                sort_keys=True,
            )
        )
        return 0 if result.receipt.state is SettlementState.SATISFIED else 2
    except (ArtifactPromotionError, OSError) as exc:
        message = (
            str(exc) if isinstance(exc, ArtifactPromotionError) else "repository is unavailable"
        )
        print(f"artifact-promotion: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
