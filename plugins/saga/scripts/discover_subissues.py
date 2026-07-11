#!/usr/bin/env python3
"""Discover GitHub sub-issues for an Infiquetra issue."""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys
from collections.abc import Callable
from typing import Any

# ``stateReason`` seeds a closed sub-issue's terminal node state (#375 KTD2); ``trackedIssues`` is the
# stable relationship signal for edge inference (#375 KTD1 — a tracker depends on what it tracks). We
# deliberately avoid a speculative ``blockedBy``/dependency field: an unknown field 400s the whole
# query, which would break ingestion rather than degrade it.
GRAPHQL_QUERY = """
query SubIssues($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      number
      title
      state
      subIssues(first: 50, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        totalCount
        nodes {
          number
          title
          state
          stateReason
          url
          repository { nameWithOwner }
          labels(first: 10) { nodes { name } }
          assignees(first: 5) { nodes { login } }
          trackedIssues(first: 50) {
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
            nodes {
              number
              repository { nameWithOwner }
            }
          }
        }
      }
    }
  }
}
""".strip()

TRACKED_ISSUES_QUERY = """
query TrackedIssues($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      trackedIssues(first: 50, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        totalCount
        nodes {
          number
          repository { nameWithOwner }
        }
      }
    }
  }
}
""".strip()


def parse_repo(value: str) -> tuple[str, str]:
    if "/" in value:
        owner, repo = value.split("/", 1)
        return owner, repo
    return "infiquetra", value


def fetch_subissues(
    owner: str, repo: str, number: int, *, runner: Callable[..., Any] | None = None
) -> dict[str, object]:
    """Fetch the parent issue + its sub-issues via ``gh api graphql`` with pagination."""
    run = runner if runner is not None else subprocess.run

    nodes: list[dict[str, Any]] = []
    has_next = True
    cursor = None
    total_count = 0
    parent_issue: dict[str, Any] = {}

    while has_next:
        cmd = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"owner={owner}",
            "-f",
            f"repo={repo}",
            "-F",
            f"number={number}",
            "-f",
            f"query={GRAPHQL_QUERY}",
        ]
        if cursor is not None:
            cmd.extend(["-f", f"cursor={cursor}"])

        result = run(cmd, capture_output=True, text=True, check=False)  # nosec B603
        if getattr(result, "returncode", 0) != 0:
            print(f"gh api graphql failed: {getattr(result, 'stderr', '')}", file=sys.stderr)
            raise SystemExit(2)

        payload = json.loads(result.stdout)
        data = payload.get("data") or {}
        repository = data.get("repository") or {}
        issue = repository.get("issue") or {}
        if issue:
            parent_issue = issue

        subissues = issue.get("subIssues") or {}
        total_count = subissues.get("totalCount", 0)
        page_nodes = subissues.get("nodes") or []
        nodes.extend(page_nodes)

        page_info = subissues.get("pageInfo") or {}
        has_next = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

        if not page_nodes:
            break

    for node in nodes:
        tracked = node.get("trackedIssues") or {}
        tracked_nodes = tracked.get("nodes") or []
        tracked_page_info = tracked.get("pageInfo") or {}
        tracked_has_next = tracked_page_info.get("hasNextPage", False)
        tracked_cursor = tracked_page_info.get("endCursor")

        node_repo_name = node.get("repository", {}).get("nameWithOwner", "")
        if "/" in node_repo_name:
            node_owner, node_repo = node_repo_name.split("/", 1)
        else:
            node_owner, node_repo = owner, repo

        while tracked_has_next:
            t_cmd = [
                "gh",
                "api",
                "graphql",
                "-f",
                f"owner={node_owner}",
                "-f",
                f"repo={node_repo}",
                "-F",
                f"number={node['number']}",
                "-f",
                f"cursor={tracked_cursor}",
                "-f",
                f"query={TRACKED_ISSUES_QUERY}",
            ]
            t_result = run(t_cmd, capture_output=True, text=True, check=False)  # nosec B603
            if getattr(t_result, "returncode", 0) != 0:
                print(f"gh api graphql failed: {getattr(t_result, 'stderr', '')}", file=sys.stderr)
                raise SystemExit(2)

            t_payload = json.loads(t_result.stdout)
            t_data = t_payload.get("data") or {}
            t_repository = t_data.get("repository") or {}
            t_issue = t_repository.get("issue") or {}
            t_tracked = t_issue.get("trackedIssues") or {}

            t_nodes = t_tracked.get("nodes") or []
            tracked_nodes.extend(t_nodes)

            t_page_info = t_tracked.get("pageInfo") or {}
            tracked_has_next = t_page_info.get("hasNextPage", False)
            tracked_cursor = t_page_info.get("endCursor")

            if not t_nodes:
                break

        if "trackedIssues" in node and isinstance(node["trackedIssues"], dict):
            node["trackedIssues"]["nodes"] = tracked_nodes

    return {
        "data": {
            "repository": {
                "issue": {
                    "number": parent_issue.get("number"),
                    "title": parent_issue.get("title"),
                    "state": parent_issue.get("state"),
                    "subIssues": {"totalCount": total_count, "nodes": nodes},
                }
            }
        }
    }


def fetch_objective(
    owner: str, repo: str, number: int, *, runner: Callable[..., Any] | None = None
) -> dict[str, object]:
    """Library entry point (#375): fetch + normalize a parent Objective's sub-issues in one call."""
    return normalize(fetch_subissues(owner, repo, number, runner=runner))


def normalize(payload: dict[str, object]) -> dict[str, object]:
    data = payload.get("data")
    repository = data.get("repository", {}) if isinstance(data, dict) else {}
    issue = repository.get("issue", {}) if isinstance(repository, dict) else {}
    subissues = issue.get("subIssues", {}) if isinstance(issue, dict) else {}
    total_subissues = subissues.get("totalCount", 0) if isinstance(subissues, dict) else 0
    raw_nodes = subissues.get("nodes", []) if isinstance(subissues, dict) else []
    nodes = (
        [node for node in raw_nodes if isinstance(node, dict)]
        if isinstance(raw_nodes, list)
        else []
    )
    if total_subissues > len(nodes):
        print(
            f"[saga/discover-subissues] Warning: Objective #{issue.get('number')} has {total_subissues} "
            f"sub-issues, but only {len(nodes)} were fetched. Truncation occurred!",
            file=sys.stderr,
        )

    for node in nodes:
        tracked = node.get("trackedIssues", {})
        tracked_total = tracked.get("totalCount", 0) if isinstance(tracked, dict) else 0
        tracked_nodes = tracked.get("nodes", []) if isinstance(tracked, dict) else []
        if tracked_total > len(tracked_nodes):
            print(
                f"[saga/discover-subissues] Warning: Sub-issue #{node.get('number')} tracks {tracked_total} "
                f"issues, but only {len(tracked_nodes)} were fetched. Truncation occurred!",
                file=sys.stderr,
            )

    def _repo_name(node: dict[str, Any]) -> str:
        repo_data = node.get("repository")
        if isinstance(repo_data, dict):
            name = repo_data.get("nameWithOwner")
            if isinstance(name, str):
                return name
        return ""

    def _tracked_ref(node: dict[str, Any]) -> object:
        repo_name = _repo_name(node)
        if not repo_name:
            return node.get("number")
        return {"number": node.get("number"), "repo": repo_name}

    return {
        "parent": {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
        },
        "totalCount": total_subissues,
        "subissues": [
            {
                "number": node.get("number"),
                "title": node.get("title"),
                "state": node.get("state"),
                "state_reason": node.get("stateReason"),
                "url": node.get("url"),
                "repo": _repo_name(node),
                "labels": [
                    label.get("name") for label in (node.get("labels", {}).get("nodes") or [])
                ],
                "assignees": [
                    assignee.get("login")
                    for assignee in (node.get("assignees", {}).get("nodes") or [])
                ],
                # #375 KTD1: a tracker depends on what it tracks; empty when absent (degrade-to-no-edges).
                "blocked_by": [
                    _tracked_ref(t)
                    for t in (node.get("trackedIssues", {}).get("nodes") or [])
                    if t.get("number") is not None
                ],
            }
            for node in nodes
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="<owner>/<repo> or repo name")
    parser.add_argument("--issue", type=int, required=True, help="Parent issue number")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    owner, repo = parse_repo(args.repo)
    print(json.dumps(normalize(fetch_subissues(owner, repo, args.issue)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
