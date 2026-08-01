#!/usr/bin/env python3
"""Repository-bound controller for the pure reconciliation contract."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import reconcile


def canonical_evidence(repo_root: Path, reference: str) -> reconcile.CanonicalEvidence:
    """Read one canonical repository file and bind its current bytes."""

    root = repo_root.resolve()
    relative = PurePosixPath(reference)
    if relative.is_absolute() or ".." in relative.parts or "\\" in reference:
        raise reconcile.ReconciliationError("canonical reference must be repository-relative")
    target = root.joinpath(*relative.parts).resolve(strict=True)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise reconcile.ReconciliationError("canonical reference escapes repository") from exc
    if not target.is_file():
        raise reconcile.ReconciliationError("canonical reference is not a regular file")
    return reconcile.CanonicalEvidence(
        reference=reference,
        sha256=reconcile.digest_bytes(target.read_bytes()),
    )


def run(
    repo_root: Path,
    reference: str,
    projections: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reconcile against one fresh read of canonical repository bytes."""

    return reconcile.reconcile_projections(
        canonical_evidence(repo_root, reference),
        projections,
    )


def canonical_json(receipt: Mapping[str, Any]) -> str:
    """Serialize a reconciliation receipt without writing it."""

    return json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
