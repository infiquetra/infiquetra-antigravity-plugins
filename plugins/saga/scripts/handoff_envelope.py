#!/usr/bin/env python3
"""Build a thin Infiquetra loop handoff envelope for mission-control."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

STATE_DIR = Path(".gemini/saga")
SOURCE_DIRS = (
    Path("docs/plans"),
    Path("docs/brainstorms"),
    Path("docs/specs"),
    Path("docs/ideation"),
    Path("docs/reviews"),
    Path("docs/work-sessions"),
)


def infer_maturity(source: str) -> str:
    normalized = source.replace("\\", "/")
    if "docs/ideation/" in normalized:
        return "idea-ready"
    if "docs/brainstorms/" in normalized:
        return "requirements-ready"
    if "docs/specs/" in normalized:
        # A spec is a sharp WHAT, NOT plan-ready. This equals the final default below and
        # is set for consistency with the other SOURCE_DIRS entries, not a behavior change.
        return "requirements-ready"
    if "docs/plans/" in normalized or "docs/reviews/" in normalized:
        return "plan-ready"
    if "docs/work-sessions/" in normalized or normalized.startswith("branch:"):
        return "resume-ready"
    return "requirements-ready"


def infer_lifecycle_phase(source: str) -> str:
    normalized = source.replace("\\", "/")
    if "docs/ideation/" in normalized:
        return "ideation"
    if "docs/brainstorms/" in normalized:
        return "brainstorm"
    if "docs/plans/" in normalized:
        return "plan"
    if "docs/reviews/" in normalized:
        return "review"
    if "docs/work-sessions/" in normalized or normalized.startswith("branch:"):
        return "work"
    # docs/specs/ is off-chain (/spec) — no lifecycle phase; maturity is set in infer_maturity.
    return "unknown"


def read_state(root: Path) -> dict[str, object]:
    state_path = root / STATE_DIR / "state.json"
    if not state_path.exists():
        return {}
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def discover_active_source(root: Path) -> str | None:
    state = read_state(root)
    current = state.get("current_work")
    if isinstance(current, dict):
        for key in ("plan_path", "work_session_path"):
            value = current.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    candidates: list[Path] = []
    for rel_dir in SOURCE_DIRS:
        directory = root / rel_dir
        if directory.exists():
            candidates.extend(path for path in directory.rglob("*.md") if path.is_file())
    if not candidates:
        return None
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return latest.relative_to(root).as_posix()


def _repository_reference(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not value.strip():
        raise ValueError("handoff artifact references must be non-empty repository-relative paths")
    return path.as_posix()


def validate_handoff_envelope(value: object) -> list[str]:
    """Validate the closed local handoff packet; this function performs no external action."""

    if not isinstance(value, dict):
        return ["handoff envelope must be an object"]
    required = {
        "schema",
        "created_at",
        "source",
        "artifacts",
        "evidence",
        "risks",
        "still_unauthorized",
        "lifecycle_phase",
        "handoff_maturity",
        "handoff_reason",
        "target_team",
        "target_repo",
        "issue_type",
        "blockers",
        "open_questions",
        "suggested_command",
        "lifecycle_owner",
        "issue_artifact_owner",
        "body_template_owner",
    }
    errors: list[str] = []
    if set(value) != required:
        errors.append("handoff envelope has unknown or missing fields")
    if value.get("schema") != "saga.handoff-envelope.v1":
        errors.append("handoff envelope schema is invalid")
    for name in ("artifacts", "evidence", "risks", "still_unauthorized"):
        rows = value.get(name)
        if not isinstance(rows, list) or not rows or any(
            not isinstance(item, str) or not item.strip() for item in rows
        ):
            errors.append(f"handoff envelope {name} must be a non-empty string list")
    artifacts = value.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, str):
                try:
                    _repository_reference(artifact)
                except ValueError as exc:
                    errors.append(str(exc))
    unauthorized = value.get("still_unauthorized")
    if isinstance(unauthorized, list) and any(
        action not in {"issue-create", "board-update", "pr-create", "merge", "deploy"}
        for action in unauthorized
    ):
        errors.append("handoff envelope still_unauthorized contains an unsupported action")
    if value.get("issue_artifact_owner") != "mission-control":
        errors.append("mission-control must own the issue artifact")
    return errors


def build_handoff_envelope(
    source: str | None = None,
    *,
    target_team: str = "",
    target_repo: str = "",
    issue_type: str = "",
    reason: str = "",
    blockers: str = "",
    open_questions: str = "",
    root: Path | None = None,
    artifacts: Sequence[str] | None = None,
    evidence: Sequence[str] | None = None,
    risks: Sequence[str] | None = None,
    still_unauthorized: Sequence[str] | None = None,
    now: Callable[[], datetime] | None = None,
) -> dict[str, object]:
    root = root or Path.cwd()
    selected_source = source or discover_active_source(root)
    if not selected_source:
        raise RuntimeError("No handoff source found; provide --source or create a durable artifact")

    maturity = infer_maturity(selected_source)
    suggested_command = f"/issue --prepare --from {selected_source} --maturity {maturity}"
    if target_team:
        suggested_command += f" for {target_team}"
    if target_repo:
        suggested_command += f" in {target_repo}"

    source_ref = _repository_reference(selected_source)
    artifact_refs = [_repository_reference(item) for item in (artifacts or [source_ref])]
    packet: dict[str, Any] = {
        "schema": "saga.handoff-envelope.v1",
        "created_at": (now or (lambda: datetime.now(UTC)))().isoformat(),
        "source": source_ref,
        "artifacts": artifact_refs,
        "evidence": list(evidence or [f"durable-source:{source_ref}"]),
        "risks": list(risks or ["recipient must validate current repository state"]),
        "still_unauthorized": list(
            still_unauthorized
            or ["issue-create", "board-update", "pr-create", "merge", "deploy"]
        ),
        "lifecycle_phase": infer_lifecycle_phase(selected_source),
        "handoff_maturity": maturity,
        "handoff_reason": reason,
        "target_team": target_team,
        "target_repo": target_repo,
        "issue_type": issue_type,
        "blockers": blockers,
        "open_questions": open_questions,
        "suggested_command": suggested_command,
        "lifecycle_owner": "saga",
        "issue_artifact_owner": "mission-control",
        "body_template_owner": "mission-control",
    }
    errors = validate_handoff_envelope(packet)
    if errors:
        raise ValueError("invalid handoff envelope: " + "; ".join(errors))
    return packet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=None)
    parser.add_argument("--target-team", default="")
    parser.add_argument("--target-repo", default="")
    parser.add_argument("--issue-type", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--blockers", default="")
    parser.add_argument("--open-questions", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    envelope = build_handoff_envelope(
        args.source,
        target_team=args.target_team,
        target_repo=args.target_repo,
        issue_type=args.issue_type,
        reason=args.reason,
        blockers=args.blockers,
        open_questions=args.open_questions,
    )
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
