"""Bounded semantic comparison for Saga compatibility canaries."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

CONTRACT_SCHEMA = "antigravity.saga-acceptance-contract.v1"
RECEIPT_SCHEMA = "antigravity.saga-acceptance-receipt.v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SagaAcceptanceError(ValueError):
    """A canary contract or receipt is invalid."""


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_contract(path: Path | str) -> dict[str, Any]:
    try:
        contract = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SagaAcceptanceError("could not load Saga acceptance contract") from exc
    errors = validate_contract(contract)
    if errors:
        raise SagaAcceptanceError("invalid Saga acceptance contract: " + "; ".join(errors))
    return cast(dict[str, Any], contract)


def validate_contract(contract: object) -> list[str]:
    if not isinstance(contract, dict):
        return ["contract must be an object"]
    errors: list[str] = []
    if set(contract) != {"schema", "contract_id", "required_facts", "max_age_s"}:
        errors.append("contract has unknown or missing fields")
    if contract.get("schema") != CONTRACT_SCHEMA:
        errors.append("contract schema is invalid")
    if not isinstance(contract.get("contract_id"), str) or not contract["contract_id"]:
        errors.append("contract_id must be a non-empty string")
    facts = contract.get("required_facts")
    if (
        not isinstance(facts, list)
        or not facts
        or any(not isinstance(fact, str) or not fact for fact in facts)
        or len(facts) != len(set(facts))
    ):
        errors.append("required_facts must be a non-empty unique string list")
    max_age = contract.get("max_age_s")
    if (
        isinstance(max_age, bool)
        or not isinstance(max_age, (int, float))
        or not math.isfinite(max_age)
        or max_age <= 0
    ):
        errors.append("max_age_s must be positive")
    return errors


def emit_receipt(
    *,
    contract: Mapping[str, Any],
    canary_id: str,
    runtime_id: str,
    input_payload: Any,
    facts: Mapping[str, Any],
    observed_at: float,
) -> dict[str, Any]:
    errors = validate_contract(contract)
    if errors:
        raise SagaAcceptanceError("invalid Saga acceptance contract: " + "; ".join(errors))
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "contract_sha256": _digest(contract),
        "canary_id": canary_id,
        "runtime_id": runtime_id,
        "input_sha256": _digest(input_payload),
        "observed_at": observed_at,
        "facts": dict(facts),
    }
    receipt_errors = _validate_receipt(contract, receipt, "emitted", observed_at)
    if receipt_errors:
        raise SagaAcceptanceError("invalid Saga acceptance receipt: " + "; ".join(receipt_errors))
    return receipt


def _validate_receipt(
    contract: Mapping[str, Any], receipt: object, label: str, evaluated_at: float
) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return [f"{label} receipt must be an object"]
    expected_fields = {
        "schema", "contract_sha256", "canary_id", "runtime_id", "input_sha256",
        "observed_at", "facts",
    }
    if set(receipt) != expected_fields:
        return [f"{label} receipt has an invalid shape"]
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append(f"{label} receipt schema is invalid")
    if receipt.get("contract_sha256") != _digest(contract):
        errors.append(f"{label} receipt has a different contract binding")
    for field in ("canary_id", "runtime_id"):
        if not isinstance(receipt.get(field), str) or not receipt[field].strip():
            errors.append(f"{label} receipt {field} must be non-empty")
    if not isinstance(receipt.get("input_sha256"), str) or SHA256_RE.fullmatch(
        receipt["input_sha256"]
    ) is None:
        errors.append(f"{label} receipt input_sha256 is invalid")
    observed_at = receipt.get("observed_at")
    if (
        isinstance(observed_at, bool)
        or not isinstance(observed_at, (int, float))
        or not math.isfinite(observed_at)
        or not math.isfinite(evaluated_at)
        or observed_at > evaluated_at
        or evaluated_at - observed_at > contract.get("max_age_s", 0)
    ):
        errors.append(f"{label} receipt is stale or has an invalid observation time")
    facts = receipt.get("facts")
    required = contract.get("required_facts", [])
    if not isinstance(facts, dict) or set(facts) != set(required):
        errors.append(f"{label} receipt facts must exactly match required semantic facts")
    elif any(value is None for value in facts.values()):
        errors.append(f"{label} receipt required fact values may not be null")
    if isinstance(facts, dict) and "evidence_sha256" in required:
        digest = facts.get("evidence_sha256")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            errors.append(f"{label} receipt evidence_sha256 is invalid")
    return errors


def compare_receipts(
    contract: Mapping[str, Any],
    left: object,
    right: object,
    *,
    evaluated_at: float,
) -> dict[str, Any]:
    errors = validate_contract(contract)
    if isinstance(evaluated_at, bool) or not isinstance(evaluated_at, (int, float)) or not math.isfinite(evaluated_at):
        errors.append("evaluated_at must be a finite number")
    for label, receipt in (("left", left), ("right", right)):
        errors.extend(_validate_receipt(contract, receipt, label, evaluated_at))
    if not errors and isinstance(left, dict) and isinstance(right, dict):
        if left is right or left == right:
            errors.append("receipts must be distinct runtime attestations")
        if left["runtime_id"] == right["runtime_id"]:
            errors.append("receipts must bind distinct runtime identities")
        for field in ("canary_id", "input_sha256"):
            if left[field] != right[field]:
                errors.append(f"receipts have different {field} bindings")
        required = contract["required_facts"]
        if {key: left["facts"][key] for key in required} != {
            key: right["facts"][key] for key in required
        }:
            errors.append("receipts disagree on required semantic facts")
    return {
        "schema": "antigravity.saga-acceptance-result.v1",
        "compatible": not errors,
        "errors": errors,
    }
