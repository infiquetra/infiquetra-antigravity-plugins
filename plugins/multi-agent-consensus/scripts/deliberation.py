#!/usr/bin/env python3
"""Validate independent deliberation coverage and produce deterministic receipts."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

MANIFEST_SCHEMA = "multi-agent-consensus.deliberation-manifest.v1"
RECEIPT_SCHEMA = "multi-agent-consensus.deliberation-receipt.v1"
UNKNOWN = "unknown"

_SLUG = re.compile(r"[A-Za-z0-9._-]+")
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
_CAPABILITY_STATES = frozenset({"passed", "failed", "unknown", "unavailable"})


class DeliberationError(ValueError):
    """A deliberation contract or result is malformed."""


class ExecutionMode(StrEnum):
    NATIVE_AGENT = "native-agent"
    ISOLATED_SEQUENTIAL = "isolated-sequential"


class ResultStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class Strategy:
    strategy_id: str
    role: str
    applicable: bool = True
    applicability_reason: str = ""
    applicability_rule: str = ""
    operator_decision_ref: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Strategy:
        _closed(
            data,
            {
                "strategy_id",
                "role",
                "applicable",
                "applicability_reason",
                "applicability_rule",
                "operator_decision_ref",
            },
            "strategy",
        )
        strategy = cls(
            strategy_id=_slug(data, "strategy_id", "strategy"),
            role=_text(data, "role", "strategy"),
            applicable=_bool(data, "applicable", "strategy"),
            applicability_reason=_optional_text(data, "applicability_reason", "strategy"),
            applicability_rule=_optional_text(data, "applicability_rule", "strategy"),
            operator_decision_ref=_optional_text(data, "operator_decision_ref", "strategy"),
        )
        if not strategy.applicable and not (
            strategy.applicability_rule or strategy.operator_decision_ref
        ):
            raise DeliberationError(
                f"strategy {strategy.strategy_id} needs an applicability rule or operator decision"
            )
        if not strategy.applicable and not strategy.applicability_reason:
            raise DeliberationError(
                f"strategy {strategy.strategy_id} needs an applicability reason"
            )
        return strategy

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "role": self.role,
            "applicable": self.applicable,
            "applicability_reason": self.applicability_reason,
            "applicability_rule": self.applicability_rule,
            "operator_decision_ref": self.operator_decision_ref,
        }


@dataclass(frozen=True)
class HostReceiptBinding:
    reference: str
    sha256: str
    states: tuple[tuple[str, str], ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HostReceiptBinding:
        _closed(data, {"reference", "sha256", "states"}, "host capability receipt")
        raw_states = data.get("states")
        if not isinstance(raw_states, Mapping) or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or value not in _CAPABILITY_STATES
            for key, value in raw_states.items()
        ):
            raise DeliberationError(
                "host capability receipt states must map capability IDs to supported states"
            )
        binding = cls(
            reference=_text(data, "reference", "host capability receipt"),
            sha256=_text(data, "sha256", "host capability receipt"),
            states=tuple(sorted(raw_states.items())),
        )
        if _SHA256.fullmatch(binding.sha256) is None:
            raise DeliberationError("host capability receipt sha256 must be a SHA-256 digest")
        return binding

    def state(self, capability: str) -> str:
        return dict(self.states).get(capability, "unknown")

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "sha256": self.sha256,
            "states": dict(self.states),
        }


@dataclass(frozen=True)
class DeliberationManifest:
    manifest_id: str
    phase: str
    strategies: tuple[Strategy, ...]
    minimum_coverage: int
    requested_model: str
    requested_effort: str
    allowed_tools: tuple[str, ...]
    max_workers: int
    max_turns_per_strategy: int
    expected_result_fields: tuple[str, ...]
    convergence_rule: str
    max_attempts_per_strategy: int
    escalation_mode: str
    escalated_model: str
    escalation_triggers: tuple[str, ...]
    host_receipt: HostReceiptBinding

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DeliberationManifest:
        _closed(
            data,
            {
                "schema",
                "manifest_id",
                "phase",
                "strategies",
                "minimum_coverage",
                "requested",
                "allowed_tools",
                "execution_bounds",
                "expected_result_fields",
                "convergence",
                "recovery",
                "escalation",
                "host_capability_receipt",
            },
            "deliberation manifest",
        )
        if data.get("schema") != MANIFEST_SCHEMA:
            raise DeliberationError(f"manifest schema must be {MANIFEST_SCHEMA!r}")
        requested = _mapping(data.get("requested"), "requested")
        _closed(requested, {"model", "effort"}, "requested")
        bounds = _mapping(data.get("execution_bounds"), "execution_bounds")
        _closed(bounds, {"max_workers", "max_turns_per_strategy"}, "execution_bounds")
        convergence = _mapping(data.get("convergence"), "convergence")
        _closed(convergence, {"rule", "preserve_disagreement"}, "convergence")
        if convergence.get("preserve_disagreement") is not True:
            raise DeliberationError("convergence must preserve disagreement")
        recovery = _mapping(data.get("recovery"), "recovery")
        _closed(recovery, {"max_attempts_per_strategy"}, "recovery")
        escalation = _mapping(data.get("escalation"), "escalation")
        _closed(escalation, {"mode", "escalated_model", "triggers"}, "escalation")
        strategies_raw = data.get("strategies")
        if not isinstance(strategies_raw, list) or not strategies_raw:
            raise DeliberationError("manifest strategies must be a non-empty list")
        strategies = tuple(Strategy.from_dict(_mapping(row, "strategy")) for row in strategies_raw)
        strategy_ids = [strategy.strategy_id for strategy in strategies]
        if len(strategy_ids) != len(set(strategy_ids)):
            raise DeliberationError("manifest contains duplicate strategy IDs")
        allowed_tools = _unique_strings(data.get("allowed_tools"), "allowed_tools")
        expected_fields = _unique_strings(
            data.get("expected_result_fields"), "expected_result_fields", required=True
        )
        triggers = _unique_strings(escalation.get("triggers"), "escalation.triggers")
        mode = _text(escalation, "mode", "escalation")
        escalated_model = _optional_text(escalation, "escalated_model", "escalation")
        if mode not in {"fixed", "cheap-first"}:
            raise DeliberationError("escalation mode must be 'fixed' or 'cheap-first'")
        if mode == "fixed" and (escalated_model or triggers):
            raise DeliberationError("fixed escalation cannot declare a model or triggers")
        if mode == "cheap-first" and (not escalated_model or not triggers):
            raise DeliberationError("cheap-first escalation needs a model and triggers")
        minimum = _positive_int(data.get("minimum_coverage"), "minimum_coverage")
        applicable_count = sum(strategy.applicable for strategy in strategies)
        if minimum != applicable_count:
            raise DeliberationError(
                "minimum_coverage must equal the number of applicable strategies"
            )
        manifest = cls(
            manifest_id=_slug(data, "manifest_id", "deliberation manifest"),
            phase=_slug(data, "phase", "deliberation manifest"),
            strategies=strategies,
            minimum_coverage=minimum,
            requested_model=_text(requested, "model", "requested"),
            requested_effort=_text(requested, "effort", "requested"),
            allowed_tools=allowed_tools,
            max_workers=_positive_int(bounds.get("max_workers"), "execution_bounds.max_workers"),
            max_turns_per_strategy=_positive_int(
                bounds.get("max_turns_per_strategy"),
                "execution_bounds.max_turns_per_strategy",
            ),
            expected_result_fields=expected_fields,
            convergence_rule=_text(convergence, "rule", "convergence"),
            max_attempts_per_strategy=_positive_int(
                recovery.get("max_attempts_per_strategy"),
                "recovery.max_attempts_per_strategy",
                maximum=5,
            ),
            escalation_mode=mode,
            escalated_model=escalated_model,
            escalation_triggers=triggers,
            host_receipt=HostReceiptBinding.from_dict(
                _mapping(data.get("host_capability_receipt"), "host_capability_receipt")
            ),
        )
        return manifest

    @property
    def applicable_strategy_ids(self) -> tuple[str, ...]:
        return tuple(row.strategy_id for row in self.strategies if row.applicable)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": MANIFEST_SCHEMA,
            "manifest_id": self.manifest_id,
            "phase": self.phase,
            "strategies": [row.to_dict() for row in self.strategies],
            "minimum_coverage": self.minimum_coverage,
            "requested": {"model": self.requested_model, "effort": self.requested_effort},
            "allowed_tools": list(self.allowed_tools),
            "execution_bounds": {
                "max_workers": self.max_workers,
                "max_turns_per_strategy": self.max_turns_per_strategy,
            },
            "expected_result_fields": list(self.expected_result_fields),
            "convergence": {
                "rule": self.convergence_rule,
                "preserve_disagreement": True,
            },
            "recovery": {"max_attempts_per_strategy": self.max_attempts_per_strategy},
            "escalation": {
                "mode": self.escalation_mode,
                "escalated_model": self.escalated_model,
                "triggers": list(self.escalation_triggers),
            },
            "host_capability_receipt": self.host_receipt.to_dict(),
        }


@dataclass(frozen=True)
class StrategyResult:
    execution_id: str
    strategy_id: str
    attempt: int
    mode: ExecutionMode
    status: ResultStatus
    requested_model: str
    requested_effort: str
    requested_tools: tuple[str, ...]
    observed_model: str
    observed_effort: str
    observed_tools: tuple[str, ...] | None
    observed_isolation: str
    observed_worker_count: int | None
    output: dict[str, Any] | None
    evidence_refs: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StrategyResult:
        _closed(
            data,
            {
                "execution_id",
                "strategy_id",
                "attempt",
                "mode",
                "status",
                "requested",
                "observed",
                "output",
                "evidence_refs",
            },
            "strategy result",
        )
        requested = _mapping(data.get("requested"), "result.requested")
        _closed(requested, {"model", "effort", "tools"}, "result.requested")
        observed = _mapping(data.get("observed"), "result.observed")
        _closed(
            observed,
            {"model", "effort", "tools", "isolation", "worker_count"},
            "result.observed",
        )
        try:
            mode = ExecutionMode(_text(data, "mode", "strategy result"))
            status = ResultStatus(_text(data, "status", "strategy result"))
        except ValueError as exc:
            raise DeliberationError(f"strategy result has unsupported state: {exc}") from exc
        output_raw = data.get("output")
        if output_raw is not None and not isinstance(output_raw, Mapping):
            raise DeliberationError("strategy result output must be an object or null")
        if status is ResultStatus.SUCCEEDED and output_raw is None:
            raise DeliberationError("successful strategy result needs an output object")
        tools_raw = observed.get("tools")
        if tools_raw == UNKNOWN:
            observed_tools = None
        else:
            observed_tools = _unique_strings(tools_raw, "result.observed.tools")
        workers_raw = observed.get("worker_count")
        if workers_raw == UNKNOWN:
            observed_workers = None
        else:
            observed_workers = _positive_int(workers_raw, "result.observed.worker_count")
        return cls(
            execution_id=_slug(data, "execution_id", "strategy result"),
            strategy_id=_slug(data, "strategy_id", "strategy result"),
            attempt=_positive_int(data.get("attempt"), "strategy result.attempt"),
            mode=mode,
            status=status,
            requested_model=_text(requested, "model", "result.requested"),
            requested_effort=_text(requested, "effort", "result.requested"),
            requested_tools=_unique_strings(requested.get("tools"), "result.requested.tools"),
            observed_model=_observed_text(observed, "model"),
            observed_effort=_observed_text(observed, "effort"),
            observed_tools=observed_tools,
            observed_isolation=_observed_text(observed, "isolation"),
            observed_worker_count=observed_workers,
            output=dict(output_raw) if output_raw is not None else None,
            evidence_refs=_unique_strings(data.get("evidence_refs"), "result.evidence_refs"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "strategy_id": self.strategy_id,
            "attempt": self.attempt,
            "mode": self.mode.value,
            "status": self.status.value,
            "requested": {
                "model": self.requested_model,
                "effort": self.requested_effort,
                "tools": list(self.requested_tools),
            },
            "observed": {
                "model": self.observed_model,
                "effort": self.observed_effort,
                "tools": list(self.observed_tools) if self.observed_tools is not None else UNKNOWN,
                "isolation": self.observed_isolation,
                "worker_count": (
                    self.observed_worker_count
                    if self.observed_worker_count is not None
                    else UNKNOWN
                ),
            },
            "output": self.output,
            "evidence_refs": list(self.evidence_refs),
        }


def evaluate_deliberation(
    manifest: DeliberationManifest | Mapping[str, Any],
    raw_results: Sequence[Mapping[str, Any]],
    *,
    convergence: Mapping[str, Any],
    escalation: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate supplied execution receipts without invoking the Antigravity host."""

    contract = (
        manifest
        if isinstance(manifest, DeliberationManifest)
        else DeliberationManifest.from_dict(manifest)
    )
    parsed: list[StrategyResult] = []
    malformed: list[str] = []
    malformed_attempts: dict[str, int] = {}
    for index, raw in enumerate(raw_results):
        try:
            parsed.append(StrategyResult.from_dict(raw))
        except DeliberationError as exc:
            malformed.append(f"result[{index}]: {exc}")
            strategy_id = raw.get("strategy_id")
            attempt = raw.get("attempt")
            if (
                isinstance(strategy_id, str)
                and strategy_id in contract.applicable_strategy_ids
                and isinstance(attempt, int)
                and not isinstance(attempt, bool)
                and attempt > 0
            ):
                malformed_attempts[strategy_id] = max(
                    malformed_attempts.get(strategy_id, 0), attempt
                )
    duplicate_executions = {
        execution_id
        for execution_id, count in Counter(row.execution_id for row in parsed).items()
        if count > 1
    }
    known_strategies = {row.strategy_id for row in contract.strategies}
    applicable = set(contract.applicable_strategy_ids)
    issues = list(malformed)
    if duplicate_executions:
        issues.append("duplicate execution IDs: " + ", ".join(sorted(duplicate_executions)))
    unexpected = sorted({row.strategy_id for row in parsed} - known_strategies)
    if unexpected:
        issues.append("undeclared strategy IDs: " + ", ".join(unexpected))

    selected_model, escalation_record = _validate_escalation(contract, escalation)
    accepted: list[StrategyResult] = []
    missing: list[str] = []
    recovery_requests: list[dict[str, Any]] = []
    exhausted: list[str] = []
    duplicate_strategies: list[str] = []
    for strategy_id in contract.applicable_strategy_ids:
        attempts = sorted(
            (row for row in parsed if row.strategy_id == strategy_id),
            key=lambda row: (row.attempt, row.execution_id),
        )
        candidates: list[StrategyResult] = []
        for row in attempts:
            reason = _result_rejection(contract, row, selected_model, duplicate_executions)
            if reason:
                issues.append(f"{row.execution_id}: {reason}")
            else:
                candidates.append(row)
        if len(candidates) > 1:
            duplicate_strategies.append(strategy_id)
            issues.append(f"strategy {strategy_id} has duplicate successful executions")
        if candidates:
            accepted.append(candidates[0])
            continue
        missing.append(strategy_id)
        attempts_seen = max(
            max((row.attempt for row in attempts), default=0),
            malformed_attempts.get(strategy_id, 0),
        )
        next_attempt = attempts_seen + 1
        if next_attempt <= contract.max_attempts_per_strategy:
            recovery_requests.append(
                {
                    "strategy_id": strategy_id,
                    "next_attempt": next_attempt,
                    "remaining_attempts": contract.max_attempts_per_strategy - attempts_seen,
                }
            )
        else:
            exhausted.append(strategy_id)
    if duplicate_strategies:
        issues.append("duplicate strategy coverage: " + ", ".join(duplicate_strategies))

    complete = len(accepted) >= contract.minimum_coverage and not missing
    convergence_record = _validate_convergence(convergence, applicable, complete=complete)
    body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "manifest_id": contract.manifest_id,
        "phase": contract.phase,
        "complete": complete,
        "coverage": {
            "required": contract.minimum_coverage,
            "accepted": len(accepted),
            "missing_strategy_ids": missing,
            "exhausted_strategy_ids": exhausted,
        },
        "requested": {
            "model": contract.requested_model,
            "effort": contract.requested_effort,
            "tools": list(contract.allowed_tools),
            "max_workers": contract.max_workers,
        },
        "observed": _observed_summary(accepted),
        "host_capability_receipt": contract.host_receipt.to_dict(),
        "accepted_results": [row.to_dict() for row in accepted],
        "issues": issues,
        "recovery_requests": recovery_requests,
        "convergence": convergence_record,
        "escalation": escalation_record,
    }
    body["receipt_id"] = hashlib.sha256(_canonical(body)).hexdigest()
    return body


def validate_receipt(data: Mapping[str, Any]) -> None:
    """Validate the closed receipt shape and its content-derived identity."""

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
    _closed(data, expected, "deliberation receipt")
    if data.get("schema") != RECEIPT_SCHEMA:
        raise DeliberationError(f"receipt schema must be {RECEIPT_SCHEMA!r}")
    receipt_id = data.get("receipt_id")
    if not isinstance(receipt_id, str) or re.fullmatch(r"[0-9a-f]{64}", receipt_id) is None:
        raise DeliberationError("receipt_id must be a SHA-256 digest")
    body = {key: value for key, value in data.items() if key != "receipt_id"}
    if hashlib.sha256(_canonical(body)).hexdigest() != receipt_id:
        raise DeliberationError("receipt_id does not match receipt content")


def _result_rejection(
    manifest: DeliberationManifest,
    result: StrategyResult,
    selected_model: str,
    duplicate_executions: set[str],
) -> str:
    if result.execution_id in duplicate_executions:
        return "execution ID is duplicated"
    if result.attempt > manifest.max_attempts_per_strategy:
        return "attempt exceeds the recovery bound"
    if result.status is not ResultStatus.SUCCEEDED:
        return f"result status is {result.status.value}"
    allowed_models = {manifest.requested_model, selected_model}
    if manifest.escalated_model:
        allowed_models.add(manifest.escalated_model)
    if result.requested_model not in allowed_models:
        return "requested model is not authorized by the manifest"
    if result.requested_effort != manifest.requested_effort:
        return "requested effort does not match the manifest"
    if not set(result.requested_tools) <= set(manifest.allowed_tools):
        return "requested tools exceed the manifest allowlist"
    if result.output is None or not set(manifest.expected_result_fields) <= set(result.output):
        return "result output is missing required fields"
    if manifest.host_receipt.state("agy.model.selection") != "passed":
        return "requested model control is not proven by the host receipt"
    if result.observed_model != UNKNOWN and result.observed_model != result.requested_model:
        return "observed model does not match the requested model"
    if result.observed_effort != UNKNOWN and result.observed_effort != result.requested_effort:
        return "observed effort does not match the requested effort"
    if result.observed_tools is not None and not set(result.observed_tools) <= set(
        manifest.allowed_tools
    ):
        return "observed tools exceed the manifest allowlist"
    expected_isolation = result.mode.value
    if result.observed_isolation not in {UNKNOWN, expected_isolation}:
        return "observed isolation does not match the execution mode"
    if result.observed_worker_count not in {None, 1}:
        return "one strategy result must represent exactly one observed worker"
    if result.mode is ExecutionMode.NATIVE_AGENT:
        if manifest.host_receipt.state("agy.agent.execution") != "passed":
            return "native agent execution is not proven by the host receipt"
    elif manifest.host_receipt.state("agy.sequential.isolation") != "passed":
        return "isolated sequential execution is not proven by the host receipt"
    return ""


def _validate_convergence(
    data: Mapping[str, Any], applicable: set[str], *, complete: bool
) -> dict[str, Any]:
    _closed(data, {"summary", "disagreements", "adjudication"}, "convergence result")
    disagreements = data.get("disagreements")
    if not isinstance(disagreements, list):
        raise DeliberationError("convergence disagreements must be a list")
    normalized: list[dict[str, Any]] = []
    for row in disagreements:
        item = _mapping(row, "convergence disagreement")
        _closed(item, {"topic", "strategy_ids", "evidence_refs"}, "convergence disagreement")
        strategies = _unique_strings(item.get("strategy_ids"), "disagreement.strategy_ids", True)
        evidence = _unique_strings(item.get("evidence_refs"), "disagreement.evidence_refs", True)
        if not set(strategies) <= applicable:
            raise DeliberationError("disagreement names a non-applicable strategy")
        normalized.append(
            {
                "topic": _text(item, "topic", "convergence disagreement"),
                "strategy_ids": list(strategies),
                "evidence_refs": list(evidence),
            }
        )
    adjudication = _optional_text(data, "adjudication", "convergence result")
    if normalized and not adjudication:
        raise DeliberationError("material disagreement requires an adjudication")
    summary = _optional_text(data, "summary", "convergence result")
    if not complete and (summary or normalized or adjudication):
        raise DeliberationError("incomplete coverage cannot carry convergence output")
    return {
        "summary": summary,
        "disagreements": normalized,
        "adjudication": adjudication,
    }


def _validate_escalation(
    manifest: DeliberationManifest, data: Mapping[str, Any]
) -> tuple[str, dict[str, Any]]:
    _closed(data, {"selected_model", "trigger_evidence"}, "escalation decision")
    selected = _text(data, "selected_model", "escalation decision")
    evidence = _unique_strings(data.get("trigger_evidence"), "escalation.trigger_evidence")
    if manifest.escalation_mode == "fixed":
        if selected != manifest.requested_model or evidence:
            raise DeliberationError(
                "fixed escalation must use the requested model without triggers"
            )
    elif selected == manifest.requested_model:
        if evidence:
            raise DeliberationError("cheap-first did not escalate but supplied trigger evidence")
    elif selected == manifest.escalated_model:
        if not evidence or not set(evidence) <= set(manifest.escalation_triggers):
            raise DeliberationError("cheap-first escalation needs declared trigger evidence")
    else:
        raise DeliberationError("selected model is not authorized by the escalation policy")
    return selected, {
        "mode": manifest.escalation_mode,
        "selected_model": selected,
        "trigger_evidence": list(evidence),
    }


def _observed_summary(results: Sequence[StrategyResult]) -> dict[str, Any]:
    def values(items: Sequence[str]) -> list[str]:
        return sorted(set(items)) or [UNKNOWN]

    observed_tools = sorted(
        {tool for row in results if row.observed_tools is not None for tool in row.observed_tools}
    )
    return {
        "models": values([row.observed_model for row in results]),
        "efforts": values([row.observed_effort for row in results]),
        "tools": observed_tools or UNKNOWN,
        "isolation": values([row.observed_isolation for row in results]),
        "worker_count": len(results),
    }


def _canonical(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DeliberationError(f"{path} must be an object")
    return value


def _closed(data: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(data) - allowed)
    missing = sorted(allowed - set(data))
    if unknown:
        raise DeliberationError(f"{path} has unknown fields: {', '.join(unknown)}")
    if missing:
        raise DeliberationError(f"{path} is missing fields: {', '.join(missing)}")


def _text(data: Mapping[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DeliberationError(f"{path}.{key} must be a non-empty string")
    return value


def _optional_text(data: Mapping[str, Any], key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise DeliberationError(f"{path}.{key} must be a string")
    return value


def _observed_text(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if value == UNKNOWN:
        return UNKNOWN
    if not isinstance(value, str) or not value.strip():
        raise DeliberationError(f"result.observed.{key} must be a string or 'unknown'")
    return value


def _bool(data: Mapping[str, Any], key: str, path: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise DeliberationError(f"{path}.{key} must be a boolean")
    return value


def _slug(data: Mapping[str, Any], key: str, path: str) -> str:
    value = _text(data, key, path)
    if _SLUG.fullmatch(value) is None:
        raise DeliberationError(f"{path}.{key} must be a slug")
    return value


def _positive_int(value: Any, path: str, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DeliberationError(f"{path} must be a positive integer")
    if maximum is not None and value > maximum:
        raise DeliberationError(f"{path} must be at most {maximum}")
    return int(value)


def _unique_strings(value: Any, path: str, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise DeliberationError(f"{path} must be a list of non-empty strings")
    if required and not value:
        raise DeliberationError(f"{path} must not be empty")
    if len(value) != len(set(value)):
        raise DeliberationError(f"{path} must not contain duplicates")
    return tuple(value)


def write_deliberation_receipt(
    repo_root: Path,
    outcome_id: str,
    receipt: Mapping[str, Any],
) -> Path:
    """Persist one validated deliberation receipt with deterministic write-once identity."""

    validate_receipt(receipt)
    if _SLUG.fullmatch(outcome_id) is None or outcome_id in {".", ".."}:
        raise DeliberationError("outcome_id must be a bounded identifier")
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or _SLUG.fullmatch(receipt_id) is None:
        raise DeliberationError("receipt_id must be a bounded identifier")
    root = repo_root.resolve(strict=True)
    target = (
        root / "docs" / "outcomes" / outcome_id / "deliberation-receipts" / f"{receipt_id}.json"
    )
    _assert_safe_output(root, target)
    payload = json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_text(encoding="utf-8") != payload:
                raise DeliberationError(
                    "deliberation receipt identity already contains different bytes"
                ) from None
    except OSError as exc:
        raise DeliberationError("could not persist deliberation receipt") from exc
    finally:
        if temporary is not None:
            with contextlib.suppress(FileNotFoundError):
                Path(temporary).unlink()
    return target


def _assert_safe_output(root: Path, target: Path) -> None:
    try:
        target.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise DeliberationError("deliberation receipt path escapes the repository") from exc
    current = root
    for part in target.relative_to(root).parts[:-1]:
        current /= part
        if current.is_symlink():
            raise DeliberationError("deliberation receipt path must not contain symlinks")


def _load_cli_json(repo_root: Path, reference: str, label: str) -> Any:
    path = Path(reference)
    if path.is_absolute() or ".." in path.parts:
        raise DeliberationError(f"{label} must be a repository-relative file")
    root = repo_root.resolve(strict=True)
    try:
        resolved = (root / path).resolve(strict=True)
        resolved.relative_to(root)
        return json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DeliberationError(f"{label} is unreadable or invalid JSON") from exc
    except ValueError as exc:
        raise DeliberationError(f"{label} must resolve inside the repository") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise DeliberationError(f"{label} is unreadable or invalid JSON") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate independent strategy results and persist a deliberation receipt."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser("evaluate", help="evaluate one declared deliberation")
    evaluate.add_argument("--repo-root", default=".")
    evaluate.add_argument("--outcome-id", required=True)
    evaluate.add_argument("--manifest", required=True)
    evaluate.add_argument("--results", required=True)
    evaluate.add_argument("--convergence", required=True)
    evaluate.add_argument("--escalation", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bounded deliberation command-line contract."""

    args = _build_parser().parse_args(argv)
    try:
        repo_root = Path(args.repo_root)
        manifest = _load_cli_json(repo_root, args.manifest, "manifest")
        results = _load_cli_json(repo_root, args.results, "results")
        convergence = _load_cli_json(repo_root, args.convergence, "convergence")
        escalation = _load_cli_json(repo_root, args.escalation, "escalation")
        if not isinstance(manifest, Mapping):
            raise DeliberationError("manifest must be an object")
        if not isinstance(results, list) or any(not isinstance(row, Mapping) for row in results):
            raise DeliberationError("results must be a list of objects")
        if not isinstance(convergence, Mapping):
            raise DeliberationError("convergence must be an object")
        if not isinstance(escalation, Mapping):
            raise DeliberationError("escalation must be an object")
        receipt = evaluate_deliberation(
            cast(Mapping[str, Any], manifest),
            cast(list[Mapping[str, Any]], results),
            convergence=cast(Mapping[str, Any], convergence),
            escalation=cast(Mapping[str, Any], escalation),
        )
        path = write_deliberation_receipt(repo_root, args.outcome_id, receipt)
        root = repo_root.resolve(strict=True)
        print(
            json.dumps(
                {
                    "schema": RECEIPT_SCHEMA,
                    "complete": receipt["complete"],
                    "receipt_id": receipt["receipt_id"],
                    "receipt_path": path.relative_to(root).as_posix(),
                },
                sort_keys=True,
            )
        )
        return 0 if receipt["complete"] is True else 2
    except DeliberationError as exc:
        print(f"deliberation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
