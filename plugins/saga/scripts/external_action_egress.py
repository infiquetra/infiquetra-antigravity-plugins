#!/usr/bin/env python3
"""Fail-closed authorization check immediately before an adapter boundary."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from external_action_contract import validate_authority
from external_action_workspace import WorkspaceBoundary, validate_intent_workspace


class EgressAuthorizationError(ValueError):
    """The proposed egress lacks fresh, exact, workspace-bound authority."""


@dataclass(frozen=True)
class EgressDecision:
    action_id: str
    authority_receipt_id: str
    target: Path


def authorize_egress(
    intent: Mapping[str, Any],
    authority: Mapping[str, Any],
    boundary: WorkspaceBoundary,
    *,
    consumed_receipt_ids: Collection[str] = (),
) -> EgressDecision:
    """Authorize one exact intent without executing it."""

    validate_authority(authority, intent=intent)
    target = validate_intent_workspace(dict(intent), boundary)
    receipt_id = str(authority["receipt_id"])
    if receipt_id in consumed_receipt_ids:
        raise EgressAuthorizationError("external action authority receipt was already consumed")
    return EgressDecision(
        action_id=str(intent["action_id"]),
        authority_receipt_id=receipt_id,
        target=target,
    )
