"""Focused tests for the typed Mission Control runtime and board census."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import sdlc_manager  # noqa: E402


def _page(
    *item_ids: str,
    total_count: int,
    has_next_page: bool,
    end_cursor: str | None,
) -> dict:
    return {
        "organization": {
            "projectV2": {
                "id": "PVT_board",
                "items": {
                    "totalCount": total_count,
                    "nodes": [{"id": item_id} for item_id in item_ids],
                    "pageInfo": {
                        "hasNextPage": has_next_page,
                        "endCursor": end_cursor,
                    },
                },
            }
        }
    }


def test_board_census_requires_every_page_before_complete() -> None:
    responses = [
        _page("PVTI_1", total_count=2, has_next_page=True, end_cursor="cursor-1"),
        _page("PVTI_2", total_count=2, has_next_page=False, end_cursor=None),
    ]
    with patch.object(sdlc_manager, "_graphql", side_effect=responses) as graphql:
        census = sdlc_manager.get_project_census(2)

    assert census.complete is True
    assert census.project_id == "PVT_board"
    assert census.total_count == 2
    assert census.page_count == 2
    assert [item["id"] for item in census.items] == ["PVTI_1", "PVTI_2"]
    assert graphql.call_args_list[0].args[1]["cursor"] is None
    assert graphql.call_args_list[1].args[1]["cursor"] == "cursor-1"


def test_board_census_requires_every_page_before_complete_rejects_negative_cases() -> None:
    cases = [
        [
            _page("PVTI_1", total_count=2, has_next_page=True, end_cursor=None),
        ],
        [
            _page("PVTI_1", total_count=3, has_next_page=True, end_cursor="cursor-1"),
            _page("PVTI_2", total_count=3, has_next_page=True, end_cursor="cursor-1"),
        ],
        [
            _page("PVTI_1", total_count=2, has_next_page=False, end_cursor=None),
        ],
    ]

    for responses in cases:
        with (
            patch.object(sdlc_manager, "_graphql", side_effect=responses),
            pytest.raises(sdlc_manager.ProjectCensusError),
        ):
            sdlc_manager.get_project_census(2)


def test_runtime_normalizes_repository_inputs_and_typed_failures() -> None:
    assert sdlc_manager._normalize_repo_arg("infiquetra/mission-control") == "mission-control"
    assert sdlc_manager._normalize_repo_arg(" mission-control ") == "mission-control"

    with pytest.raises(sdlc_manager.ApiResponseError, match="malformed JSON"):
        sdlc_manager._decode_json_response("not-json", operation="GraphQL")
    with pytest.raises(sdlc_manager.ApiResponseError, match="non-object"):
        sdlc_manager._decode_json_response("[]", operation="GraphQL")

    item = {
        "id": "PVTI_1",
        "content": {"number": 15, "repository": {"name": "mission-control"}},
    }
    assert sdlc_manager._resolve_project_item([item], "mission-control", 15) == item


def test_runtime_normalizes_repository_inputs_and_typed_failures_rejects_negative_cases() -> None:
    for repo in ("other/mission-control", "infiquetra/too/many", " "):
        with pytest.raises(argparse.ArgumentTypeError):
            sdlc_manager._normalize_repo_arg(repo)

    with pytest.raises(sdlc_manager.ProjectItemResolutionError, match="not found"):
        sdlc_manager._resolve_project_item([], "mission-control", 15)

    duplicate = {
        "id": "PVTI_1",
        "content": {"number": 15, "repository": {"name": "mission-control"}},
    }
    with pytest.raises(sdlc_manager.ProjectItemResolutionError, match="ambiguous"):
        sdlc_manager._resolve_project_item(
            [duplicate, {**duplicate, "id": "PVTI_2"}], "mission-control", 15
        )
