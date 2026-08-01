"""Acceptance contract for complete, descriptive flow metrics."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sdlc_manager  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _history_page(
    events: list[dict],
    *,
    total_count: int,
    has_next_page: bool,
    end_cursor: str | None,
) -> dict:
    return {
        "repository": {
            "issue": {
                "timelineItems": {
                    "totalCount": total_count,
                    "nodes": events,
                    "pageInfo": {
                        "hasNextPage": has_next_page,
                        "endCursor": end_cursor,
                    },
                }
            }
        }
    }


def test_metrics_contract_covers_throughput_cycle_age_and_state_time() -> None:
    pages = [
        _history_page(
            [
                {
                    "createdAt": "2026-07-01T00:00:00Z",
                    "previousProjectV2ItemFieldValue": {"name": "Ready"},
                    "projectV2ItemFieldValue": {"name": "Active"},
                }
            ],
            total_count=2,
            has_next_page=True,
            end_cursor="timeline-1",
        ),
        _history_page(
            [
                {
                    "createdAt": "2026-07-02T00:00:00Z",
                    "previousProjectV2ItemFieldValue": {"name": "Active"},
                    "projectV2ItemFieldValue": {"name": "Done"},
                }
            ],
            total_count=2,
            has_next_page=False,
            end_cursor=None,
        ),
    ]
    with patch.object(sdlc_manager, "_graphql", side_effect=pages):
        transitions = sdlc_manager._get_issue_column_times("infiquetra", "mission-control", 15)
    assert [(event["from"], event["to"]) for event in transitions] == [
        ("Ready", "Active"),
        ("Active", "Done"),
    ]

    command = (PLUGIN_ROOT / "commands/metrics.md").read_text(encoding="utf-8")
    skill = (PLUGIN_ROOT / "skills/metrics/SKILL.md").read_text(encoding="utf-8")
    for term in ("cycle time", "throughput", "WIP age"):
        assert term.lower() in command.lower()
    assert "Per-Status Time Breakdown" in skill
    assert "descriptive evidence, not routing, mutation, or completion authority" in skill


def test_metrics_contract_covers_throughput_cycle_age_and_state_time_rejects_negative_cases() -> (
    None
):
    incomplete = _history_page(
        [],
        total_count=1,
        has_next_page=False,
        end_cursor=None,
    )
    with (
        patch.object(sdlc_manager, "_graphql", return_value=incomplete),
        pytest.raises(sdlc_manager.ApiResponseError, match="incomplete"),
    ):
        sdlc_manager._get_issue_column_times("infiquetra", "mission-control", 15)

    command = (PLUGIN_ROOT / "commands/metrics.md").read_text(encoding="utf-8")
    normalized_command = " ".join(command.split()).lower()
    assert "do not calculate a complete metric" in normalized_command
    assert (
        "do not convert a target comparison into routing or mutation authority"
        in normalized_command
    )
