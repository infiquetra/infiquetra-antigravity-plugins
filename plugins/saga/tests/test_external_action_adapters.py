"""Semantic acceptance for Saga's local external-action authority boundary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import external_action_adapters as adapters  # noqa: E402
import external_action_contract as contract  # noqa: E402
import external_action_egress as egress  # noqa: E402
import external_action_workspace as workspace  # noqa: E402

DIGEST = "a" * 64


def _intent() -> dict[str, str]:
    return contract.build_intent(
        action_id="action-1",
        workspace_id="repo-1",
        adapter="injected-test-adapter",
        operation="update",
        target="docs/result.md",
        payload_sha256=DIGEST,
        requested_by="saga",
    )


def _boundary(tmp_path: Path) -> workspace.WorkspaceBoundary:
    return workspace.WorkspaceBoundary(
        workspace_id="repo-1",
        root=tmp_path.resolve(),
        allowed_targets=("docs/result.md",),
    )


def test_external_action_requires_intent_workspace_adapter_and_authority(
    tmp_path: Path,
) -> None:
    intent = _intent()
    authority = contract.build_authority(
        receipt_id="authority-1",
        intent=intent,
        authority="operator",
    )

    result = adapters.dispatch(
        intent,
        authority,
        _boundary(tmp_path),
        adapter=lambda request: {
            "result_id": "result-1",
            "status": "ok",
            "observed_target": request["target"],
            "evidence_sha256": "b" * 64,
        },
    )

    assert result["action_id"] == intent["action_id"]
    assert result["authority_receipt_id"] == authority["receipt_id"]
    assert result["observed_target"] == "docs/result.md"


def test_external_action_requires_intent_workspace_adapter_and_authority_rejects_negative_cases(
    tmp_path: Path,
) -> None:
    intent = _intent()
    authority = contract.build_authority(
        receipt_id="authority-1",
        intent=intent,
        authority="operator",
    )

    tampered = dict(intent)
    tampered["target"] = "docs/other.md"
    with pytest.raises(ValueError, match="bind exact intent"):
        egress.authorize_egress(tampered, authority, _boundary(tmp_path))

    with pytest.raises(ValueError, match="outside the declared workspace"):
        egress.authorize_egress(
            intent,
            authority,
            workspace.WorkspaceBoundary(
                workspace_id="repo-1",
                root=tmp_path.resolve(),
                allowed_targets=("docs/elsewhere.md",),
            ),
        )

    with pytest.raises(ValueError, match="already consumed"):
        egress.authorize_egress(
            intent,
            authority,
            _boundary(tmp_path),
            consumed_receipt_ids={"authority-1"},
        )

    with pytest.raises(adapters.AdapterExecutionError, match="explicitly supplied"):
        adapters.dispatch(intent, authority, _boundary(tmp_path), adapter=None)

    with pytest.raises(adapters.AdapterExecutionError, match="invalid result"):
        adapters.dispatch(
            intent,
            authority,
            _boundary(tmp_path),
            adapter=lambda _request: {
                "result_id": "result-1",
                "status": "ok",
                "observed_target": "../escape",
                "evidence_sha256": "b" * 64,
            },
        )
