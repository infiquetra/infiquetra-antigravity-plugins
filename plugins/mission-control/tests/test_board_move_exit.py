"""Acceptance contract for resolving board moves before remote mutation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sdlc_manager  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _item(item_id: str = "PVTI_1") -> dict:
    return {
        "id": item_id,
        "content": {"number": 15, "repository": {"name": "mission-control"}},
    }


def _config() -> dict:
    return {
        "project_mappings": {
            "projects": {
                "asgard": {
                    "id": "PVT_asgard",
                    "number": 2,
                    "name": "Asgard",
                    "repositories": [],
                }
            }
        }
    }


def _field_response() -> dict:
    return {
        "organization": {
            "projectV2": {
                "fields": {
                    "nodes": [
                        {
                            "id": "PVTF_status",
                            "name": "Status",
                            "options": [{"id": "opt-active", "name": "Active"}],
                        }
                    ]
                }
            }
        }
    }


def test_board_move_requires_resolved_item_field_and_status() -> None:
    with (
        patch.object(sdlc_manager, "load_config", return_value=_config()),
        patch.object(sdlc_manager, "get_project_items", return_value=("PVT_asgard", [_item()])),
        patch.object(
            sdlc_manager,
            "_graphql",
            side_effect=[_field_response(), {"updateProjectV2ItemFieldValue": {}}],
        ) as graphql,
    ):
        sdlc_manager.board_move(
            "mission-control",
            15,
            "Active",
            fmt="text",
            project_name="asgard",
        )

    mutation = graphql.call_args_list[-1]
    assert mutation.args[0] == sdlc_manager.QUERY_SET_FIELD_VALUE
    assert mutation.args[1] == {
        "projectId": "PVT_asgard",
        "itemId": "PVTI_1",
        "fieldId": "PVTF_status",
        "optionId": "opt-active",
    }

    board_skill = (PLUGIN_ROOT / "skills/board/SKILL.md").read_text(encoding="utf-8")
    normalized_skill = " ".join(board_skill.split())
    assert "obtain explicit operator approval before applying it" in normalized_skill
    assert "applicable exit criteria" in board_skill


def test_board_move_requires_resolved_item_field_and_status_rejects_negative_cases() -> None:
    duplicate = [_item("PVTI_1"), _item("PVTI_2")]
    with pytest.raises(sdlc_manager.ProjectItemResolutionError, match="ambiguous"):
        sdlc_manager._resolve_project_item(duplicate, "mission-control", 15)

    incomplete = {
        "organization": {
            "projectV2": {
                "id": "PVT_asgard",
                "items": {
                    "totalCount": 2,
                    "nodes": [{"id": "PVTI_1"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                },
            }
        }
    }
    with (
        patch.object(sdlc_manager, "_graphql", return_value=incomplete),
        pytest.raises(sdlc_manager.ProjectCensusError, match="partial"),
    ):
        sdlc_manager.get_project_census(2)

    workflow = (PLUGIN_ROOT / "skills/board/references/kanban-workflow.md").read_text(
        encoding="utf-8"
    )
    assert "If the exit criteria are absent or unresolved, stop" in workflow
