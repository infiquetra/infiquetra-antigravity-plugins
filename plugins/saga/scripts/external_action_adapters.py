#!/usr/bin/env python3
"""Injected adapter seam for authority-bounded external actions.

No network, subprocess, provider, or product adapter is registered here.
Production callers must supply a separately reviewed adapter implementation and
separate authority receipt.  Tests use a local callable to prove the contract.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from typing import Any

from external_action_contract import build_result, validate_result
from external_action_egress import authorize_egress
from external_action_workspace import WorkspaceBoundary


class AdapterExecutionError(RuntimeError):
    """An injected adapter failed or returned an invalid typed result."""


Adapter = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def dispatch(
    intent: Mapping[str, Any],
    authority: Mapping[str, Any],
    boundary: WorkspaceBoundary,
    *,
    adapter: Adapter | None,
    consumed_receipt_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Run one injected adapter only after exact egress authorization."""

    decision = authorize_egress(
        intent,
        authority,
        boundary,
        consumed_receipt_ids=consumed_receipt_ids,
    )
    if adapter is None:
        raise AdapterExecutionError("no external action adapter was explicitly supplied")
    try:
        observed = adapter(intent)
    except Exception as exc:
        raise AdapterExecutionError("external action adapter failed") from exc
    if not isinstance(observed, Mapping):
        raise AdapterExecutionError("external action adapter must return an object")
    try:
        result = build_result(
            result_id=str(observed.get("result_id", "")),
            intent=intent,
            authority=authority,
            status=str(observed.get("status", "")),
            observed_target=str(observed.get("observed_target", "")),
            evidence_sha256=str(observed.get("evidence_sha256", "")),
        )
        validate_result(result, intent=intent, authority=authority)
    except ValueError as exc:
        raise AdapterExecutionError("external action adapter returned an invalid result") from exc
    if result["authority_receipt_id"] != decision.authority_receipt_id:
        raise AdapterExecutionError("external action result lost the authority binding")
    return result
