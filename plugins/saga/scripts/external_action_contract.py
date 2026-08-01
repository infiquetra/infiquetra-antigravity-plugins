#!/usr/bin/env python3
"""Closed, local contracts for an externally mutating Saga action.

This module describes authority; it never obtains authority and never performs
an action.  The four receipts deliberately keep requested intent, workspace
containment, operator authority, and observed adapter outcome separate.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

INTENT_SCHEMA = "antigravity.external-action-intent.v1"
AUTHORITY_SCHEMA = "antigravity.external-action-authority.v1"
RESULT_SCHEMA = "antigravity.external-action-result.v1"
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

INTENT_FIELDS = frozenset(
    {
        "schema",
        "action_id",
        "workspace_id",
        "adapter",
        "operation",
        "target",
        "payload_sha256",
        "requested_by",
    }
)
AUTHORITY_FIELDS = frozenset(
    {
        "schema",
        "receipt_id",
        "action_id",
        "intent_sha256",
        "authority",
        "decision",
    }
)
RESULT_FIELDS = frozenset(
    {
        "schema",
        "result_id",
        "action_id",
        "adapter",
        "status",
        "observed_target",
        "evidence_sha256",
        "authority_receipt_id",
    }
)


class ExternalActionContractError(ValueError):
    """An external-action receipt is malformed or does not bind its input."""


def canonical_sha256(value: Mapping[str, Any]) -> str:
    """Return the digest of a strict canonical JSON object."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_intent(
    *,
    action_id: str,
    workspace_id: str,
    adapter: str,
    operation: str,
    target: str,
    payload_sha256: str,
    requested_by: str,
) -> dict[str, str]:
    intent = {
        "schema": INTENT_SCHEMA,
        "action_id": action_id,
        "workspace_id": workspace_id,
        "adapter": adapter,
        "operation": operation,
        "target": target,
        "payload_sha256": payload_sha256,
        "requested_by": requested_by,
    }
    validate_intent(intent)
    return intent


def build_authority(
    *,
    receipt_id: str,
    intent: Mapping[str, Any],
    authority: str,
    decision: str = "authorized",
) -> dict[str, str]:
    validate_intent(intent)
    receipt = {
        "schema": AUTHORITY_SCHEMA,
        "receipt_id": receipt_id,
        "action_id": str(intent["action_id"]),
        "intent_sha256": canonical_sha256(intent),
        "authority": authority,
        "decision": decision,
    }
    validate_authority(receipt, intent=intent)
    return receipt


def build_result(
    *,
    result_id: str,
    intent: Mapping[str, Any],
    authority: Mapping[str, Any],
    status: str,
    observed_target: str,
    evidence_sha256: str,
) -> dict[str, str]:
    validate_authority(authority, intent=intent)
    result = {
        "schema": RESULT_SCHEMA,
        "result_id": result_id,
        "action_id": str(intent["action_id"]),
        "adapter": str(intent["adapter"]),
        "status": status,
        "observed_target": observed_target,
        "evidence_sha256": evidence_sha256,
        "authority_receipt_id": str(authority["receipt_id"]),
    }
    validate_result(result, intent=intent, authority=authority)
    return result


def validate_intent(value: object) -> None:
    row = _strict_mapping(value, INTENT_FIELDS, "external action intent")
    if row.get("schema") != INTENT_SCHEMA:
        raise ExternalActionContractError("external action intent schema is invalid")
    for field in (
        "action_id",
        "workspace_id",
        "adapter",
        "operation",
        "requested_by",
    ):
        _identifier(row.get(field), f"external action intent {field}")
    target = row.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ExternalActionContractError("external action intent target must be non-empty")
    _digest(row.get("payload_sha256"), "external action intent payload_sha256")


def validate_authority(value: object, *, intent: Mapping[str, Any]) -> None:
    validate_intent(intent)
    row = _strict_mapping(value, AUTHORITY_FIELDS, "external action authority")
    if row.get("schema") != AUTHORITY_SCHEMA:
        raise ExternalActionContractError("external action authority schema is invalid")
    for field in ("receipt_id", "action_id", "authority"):
        _identifier(row.get(field), f"external action authority {field}")
    if row.get("decision") != "authorized":
        raise ExternalActionContractError("external action authority is not authorized")
    if row.get("action_id") != intent.get("action_id"):
        raise ExternalActionContractError("external action authority action_id does not match")
    if row.get("intent_sha256") != canonical_sha256(intent):
        raise ExternalActionContractError("external action authority does not bind exact intent")


def validate_result(
    value: object,
    *,
    intent: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> None:
    validate_authority(authority, intent=intent)
    row = _strict_mapping(value, RESULT_FIELDS, "external action result")
    if row.get("schema") != RESULT_SCHEMA:
        raise ExternalActionContractError("external action result schema is invalid")
    for field in ("result_id", "action_id", "adapter", "authority_receipt_id"):
        _identifier(row.get(field), f"external action result {field}")
    if row.get("status") not in {"ok", "failed", "refused"}:
        raise ExternalActionContractError("external action result status is invalid")
    if row.get("action_id") != intent.get("action_id"):
        raise ExternalActionContractError("external action result action_id does not match")
    if row.get("adapter") != intent.get("adapter"):
        raise ExternalActionContractError("external action result adapter does not match")
    if row.get("authority_receipt_id") != authority.get("receipt_id"):
        raise ExternalActionContractError("external action result authority receipt does not match")
    if row.get("observed_target") != intent.get("target"):
        raise ExternalActionContractError("external action result observed target does not match")
    _digest(row.get("evidence_sha256"), "external action result evidence_sha256")


def _strict_mapping(
    value: object, expected: frozenset[str], name: str
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExternalActionContractError(f"{name} must be an object")
    if set(value) != expected:
        raise ExternalActionContractError(f"{name} has unknown or missing fields")
    return value


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ExternalActionContractError(f"{name} must be a logical identifier")
    return value


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ExternalActionContractError(f"{name} must be a SHA-256 digest")
    return value
