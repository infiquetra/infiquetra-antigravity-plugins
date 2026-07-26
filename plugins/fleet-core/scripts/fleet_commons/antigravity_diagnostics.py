"""Ignored local diagnostics and the one-way promotable sanitization boundary."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

LOCAL_DIAGNOSTIC_SCHEMA = "antigravity.capability-diagnostic.local.v1"
DEFAULT_DIAGNOSTIC_ROOT = Path(".gemini/saga/capability-doctor")
MAX_DIAGNOSTIC_BYTES = 256 * 1024
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


def write_local_diagnostic(
    root: Path | str,
    name: str,
    payload: Mapping[str, Any],
    *,
    max_bytes: int = MAX_DIAGNOSTIC_BYTES,
) -> Path:
    """Atomically write rich local evidence under an injected ignored state root."""

    safe_name = _safe_name(name)
    if max_bytes < 1 or max_bytes > MAX_DIAGNOSTIC_BYTES:
        raise DiagnosticError("diagnostic byte limit is outside the allowed bound")
    target_root = Path(root)
    document = dict(payload)
    document["schema"] = LOCAL_DIAGNOSTIC_SCHEMA
    try:
        encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DiagnosticError("diagnostic payload is not JSON serializable") from exc
    if len(encoded) > max_bytes:
        raise DiagnosticError("diagnostic payload exceeds the configured byte limit")

    target_root.mkdir(parents=True, exist_ok=True)
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
        raise DiagnosticError(f"diagnostic runtime_roots contains unknown roles: {invalid_roles}")

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
