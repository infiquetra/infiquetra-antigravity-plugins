#!/usr/bin/env python3
"""Repository-relative containment for an external-action intent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from external_action_contract import validate_intent


class WorkspaceBoundaryError(ValueError):
    """An intent targets a path outside its declared workspace boundary."""


@dataclass(frozen=True)
class WorkspaceBoundary:
    """A logical workspace and its exact allowed repository-relative targets."""

    workspace_id: str
    root: Path
    allowed_targets: tuple[str, ...]

    def validate(self) -> None:
        if not self.workspace_id:
            raise WorkspaceBoundaryError("workspace_id must be non-empty")
        if not self.root.is_absolute():
            raise WorkspaceBoundaryError("workspace root must be absolute")
        if not self.allowed_targets:
            raise WorkspaceBoundaryError("workspace must declare at least one allowed target")
        for target in self.allowed_targets:
            _relative_target(target)
        if len(self.allowed_targets) != len(set(self.allowed_targets)):
            raise WorkspaceBoundaryError("workspace contains duplicate allowed targets")

    def resolve(self, target: str) -> Path:
        self.validate()
        _relative_target(target)
        if target not in self.allowed_targets:
            raise WorkspaceBoundaryError("target is outside the declared workspace write set")
        resolved = self.root.joinpath(*PurePosixPath(target).parts).resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError as exc:
            raise WorkspaceBoundaryError("target resolves outside the workspace") from exc
        return resolved


def validate_intent_workspace(intent: dict[str, Any], boundary: WorkspaceBoundary) -> Path:
    """Validate the intent and return its contained target path."""

    validate_intent(intent)
    boundary.validate()
    if intent["workspace_id"] != boundary.workspace_id:
        raise WorkspaceBoundaryError("intent workspace_id does not match boundary")
    return boundary.resolve(intent["target"])


def _relative_target(target: object) -> str:
    if not isinstance(target, str) or not target:
        raise WorkspaceBoundaryError("target must be a non-empty repository-relative path")
    path = PurePosixPath(target)
    if path.is_absolute() or "\\" in target or any(part in {"", ".", ".."} for part in path.parts):
        raise WorkspaceBoundaryError("target must be a safe repository-relative path")
    return target
