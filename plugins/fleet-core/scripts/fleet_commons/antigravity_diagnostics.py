"""Ignored local diagnostics and the one-way promotable sanitization boundary."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

LOCAL_DIAGNOSTIC_SCHEMA = "antigravity.capability-diagnostic.local.v1"
DEFAULT_DIAGNOSTIC_ROOT = Path(".gemini/saga/capability-doctor")
MAX_DIAGNOSTIC_BYTES = 256 * 1024
DEFAULT_RETENTION_SECONDS = 7 * 24 * 60 * 60
MAX_RETENTION_SECONDS = 30 * 24 * 60 * 60
DEFAULT_MAX_DIAGNOSTIC_FILES = 20
MAX_DIAGNOSTIC_FILES = 100
_SAFE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


class DiagnosticError(ValueError):
    """A local diagnostic write or promotion request was rejected."""


@lru_cache(maxsize=1)
def _capabilities_module() -> ModuleType:
    path = Path(__file__).with_name("antigravity_capabilities.py")
    spec = importlib.util.spec_from_file_location("_antigravity_capabilities_contract", path)
    if spec is None or spec.loader is None:
        raise DiagnosticError("capability contract module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _safe_name(name: str) -> str:
    if not _SAFE_NAME_RE.fullmatch(name):
        raise DiagnosticError("diagnostic name must be a bounded lowercase filename stem")
    return name


def _diagnostic_files(target_root: Path) -> list[Path]:
    try:
        return [
            path for path in target_root.glob("*.json") if path.is_file() and not path.is_symlink()
        ]
    except OSError as exc:
        raise DiagnosticError("could not inspect local diagnostic retention") from exc


def purge_local_diagnostics(repo_root: Path | str) -> int:
    """Delete all bounded local diagnostic JSON files and return the count."""

    repository = Path(repo_root).resolve()
    target_root = (repository / DEFAULT_DIAGNOSTIC_ROOT).resolve()
    if not target_root.is_relative_to(repository):
        raise DiagnosticError("diagnostic state root escapes the repository")
    removed = 0
    for path in _diagnostic_files(target_root):
        try:
            path.unlink()
        except OSError as exc:
            raise DiagnosticError("could not purge local diagnostics") from exc
        removed += 1
    return removed


def _prune_local_diagnostics(
    target_root: Path,
    *,
    now: float,
    retention_seconds: int,
    max_files: int,
) -> None:
    cutoff = now - retention_seconds
    retained: list[tuple[float, Path]] = []
    for path in _diagnostic_files(target_root):
        try:
            modified = path.stat().st_mtime
            if modified < cutoff:
                path.unlink()
            else:
                retained.append((modified, path))
        except OSError as exc:
            raise DiagnosticError("could not enforce local diagnostic retention") from exc
    retained.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    for _modified, path in retained[max(max_files - 1, 0) :]:
        try:
            path.unlink()
        except OSError as exc:
            raise DiagnosticError("could not enforce local diagnostic retention") from exc


def write_local_diagnostic(
    repo_root: Path | str,
    name: str,
    payload: Mapping[str, Any],
    *,
    max_bytes: int = MAX_DIAGNOSTIC_BYTES,
    retention_seconds: int = DEFAULT_RETENTION_SECONDS,
    max_files: int = DEFAULT_MAX_DIAGNOSTIC_FILES,
    now: Callable[[], float] = time.time,
) -> Path:
    """Atomically write rich local evidence with bounded local retention."""

    safe_name = _safe_name(name)
    if max_bytes < 1 or max_bytes > MAX_DIAGNOSTIC_BYTES:
        raise DiagnosticError("diagnostic byte limit is outside the allowed bound")
    if retention_seconds < 1 or retention_seconds > MAX_RETENTION_SECONDS:
        raise DiagnosticError("diagnostic retention is outside the allowed bound")
    if max_files < 1 or max_files > MAX_DIAGNOSTIC_FILES:
        raise DiagnosticError("diagnostic file limit is outside the allowed bound")
    repository = Path(repo_root).resolve()
    target_root = (repository / DEFAULT_DIAGNOSTIC_ROOT).resolve()
    if not target_root.is_relative_to(repository):
        raise DiagnosticError("diagnostic state root escapes the repository")
    document = dict(payload)
    document["schema"] = LOCAL_DIAGNOSTIC_SCHEMA
    try:
        encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DiagnosticError("diagnostic payload is not JSON serializable") from exc
    if len(encoded) > max_bytes:
        raise DiagnosticError("diagnostic payload exceeds the configured byte limit")

    target_root.mkdir(parents=True, exist_ok=True)
    _prune_local_diagnostics(
        target_root,
        now=now(),
        retention_seconds=retention_seconds,
        max_files=max_files,
    )
    target = target_root / f"{safe_name}.json"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target_root,
            prefix=f".{safe_name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except OSError as exc:
        if temporary_name is not None:
            with suppress(OSError):
                Path(temporary_name).unlink(missing_ok=True)
        raise DiagnosticError("could not write the local diagnostic atomically") from exc
    return target


def sanitize_for_promotion(
    diagnostic: Mapping[str, Any],
    catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a promotable receipt without copying any rich diagnostic fields."""

    capabilities = _capabilities_module()
    if diagnostic.get("schema") != LOCAL_DIAGNOSTIC_SCHEMA:
        raise DiagnosticError("input is not a local capability diagnostic")

    roots = diagnostic.get("runtime_roots", {})
    if not isinstance(roots, dict):
        raise DiagnosticError("diagnostic runtime_roots must map logical roles to local paths")
    invalid_roles = sorted(set(roots) - capabilities.RUNTIME_ROOT_ROLES)
    if invalid_roles:
        raise DiagnosticError("diagnostic runtime_roots contains an unknown role")

    receipt = {
        "schema": capabilities.RECEIPT_SCHEMA,
        "catalog_digest": capabilities.canonical_catalog_digest(catalog),
        "agy_cli_version": diagnostic.get("agy_cli_version"),
        "antigravity_host_version": diagnostic.get("antigravity_host_version"),
        "supported_flags": list(diagnostic.get("supported_flags", [])),
        "runtime_roots": sorted(roots),
        "requested_facts": dict(diagnostic.get("requested_facts", {})),
        "observed_facts": dict(diagnostic.get("observed_facts", {})),
        "results": [dict(result) for result in diagnostic.get("results", [])],
    }
    errors = capabilities.validate_receipt(receipt, catalog)
    if errors:
        raise DiagnosticError("sanitized capability receipt is invalid: " + "; ".join(errors))
    return receipt
