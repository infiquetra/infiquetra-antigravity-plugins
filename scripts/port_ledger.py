#!/usr/bin/env python3
"""Strict semantic-port ledger and read-only discovery commands."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess  # nosec B404
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, cast

import yaml
from yaml.nodes import MappingNode

SCHEMA_V1 = "antigravity.semantic-port-ledger.v1"
SCHEMA_V2 = "antigravity.semantic-port-ledger.v2"
SCHEMA = SCHEMA_V1
MIGRATION_PLAN_SCHEMA = "antigravity.semantic-port-migration-plan.v1"
MIGRATION_EVIDENCE_SCHEMA = "antigravity.semantic-port-migration-evidence.v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_LEDGER_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_BYTES = 8 * 1024 * 1024
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
CAMPAIGN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
HOSTS = frozenset({"claude", "codex", "antigravity"})
CHANGES = frozenset({"added", "modified", "deleted", "renamed", "tree"})
PACKET_SOURCES = frozenset({"history", "tree"})
ANTIGRAVITY_STATES = frozenset(
    {"absent", "partial", "present", "intentional-divergence", "blocked-by-host"}
)
DISPOSITIONS = frozenset(
    {"direct-port", "antigravity-adapt", "metadata-only", "reject", "superseded", "blocked"}
)
DECISION_STATES = frozenset(
    {"pending", "approved-survivor", "rejected", "superseded", "metadata-only", "blocked"}
)
RAW_CAPABILITY_STATES = frozenset({"passed", "failed", "unknown", "unavailable"})
ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS = frozenset(
    {
        "plugins/saga/tests/fixtures/port-ledger/complete.yaml",
        "plugins/saga/tests/fixtures/port-ledger/duplicate-source-edits.yaml",
        "plugins/saga/tests/fixtures/port-ledger/release-drift.yaml",
        "plugins/saga/tests/fixtures/port-ledger/unapproved-survivors.yaml",
        "plugins/saga/tests/fixtures/port-ledger/unclassified.yaml",
        "plugins/saga/tests/test_port_ledger.py",
        "scripts/port_ledger.py",
    }
)

TOP_KEYS = frozenset({"schema", "campaign", "candidates"})
CAMPAIGN_KEYS = frozenset(
    {
        "id",
        "snapshots",
        "selected_surfaces",
        "historical_seeds",
        "host_receipt",
        "edit_packets",
        "unmatched_edit_packet_ids",
        "release_drift",
    }
)
SNAPSHOT_KEYS = frozenset(
    {
        "host",
        "repository",
        "planning_commit",
        "inventory_commit",
        "head_commit",
        "origin_main_commit",
    }
)
SURFACE_KEYS = frozenset({"host", "repository", "paths"})
SEED_KEYS = frozenset({"host", "commit"})
HOST_RECEIPT_KEYS = frozenset({"schema", "catalog_digest", "receipt_sha256", "states"})
CAPABILITY_STATE_KEYS = frozenset({"capability", "state"})
PACKET_KEYS = frozenset({"id", "host", "commit", "path", "change", "content_sha256", "source"})
RELEASE_DRIFT_KEYS = frozenset({"checked_at", "status", "snapshots", "unmatched_edit_packet_ids"})
DRIFT_SNAPSHOT_KEYS = frozenset({"host", "inventory_commit", "current_commit"})
CANDIDATE_KEYS_V1 = frozenset(
    {
        "id",
        "title",
        "edit_packet_ids",
        "provenance",
        "semantic_contract",
        "adjacent_dependencies",
        "required_host_capabilities",
        "antigravity_state",
        "proposed_disposition",
        "ranking",
        "evidence_expectation",
        "decision",
    }
)
CANDIDATE_KEYS_V2 = CANDIDATE_KEYS_V1 | {"migration"}
PROVENANCE_KEYS = frozenset({"host", "commit", "path"})
RANKING_KEYS = frozenset(
    {"operator_value", "antigravity_fit", "proof_feasibility", "maintenance_cost"}
)
DECISION_KEYS = frozenset({"state", "rationale", "revisit_trigger", "operator", "decided_at"})
DECISION_INPUT_KEYS = frozenset({"state", "rationale", "revisit_trigger"})
MIGRATION_KEYS = frozenset(
    {
        "state",
        "target_paths",
        "test_node_ids",
        "negative_test_node_ids",
        "intentional_differences",
        "packet_set_sha256",
        "host_receipt_sha256",
        "evidence_manifest_sha256",
        "blocking_capabilities",
        "validated_at",
    }
)
MIGRATION_STATES = frozenset({"planned", "migrated", "blocked"})
MIGRATION_FINAL_STATES = frozenset({"present", "intentional-divergence"})
MIGRATION_PLAN_KEYS = frozenset({"schema", "campaign_id", "ledger_schema", "candidates"})
MIGRATION_PLAN_ROW_KEYS = frozenset(
    {
        "semantic_contract",
        "final_antigravity_state",
        "target_paths",
        "test_node_ids",
        "negative_test_node_ids",
        "intentional_differences",
    }
)
EVIDENCE_KEYS = frozenset(
    {
        "schema",
        "campaign_id",
        "ledger_schema",
        "candidate_ids",
        "source_binding",
        "host_binding",
        "results",
        "candidate_evidence",
        "manifest_sha256",
    }
)
SOURCE_BINDING_KEYS = frozenset(
    {
        "snapshot_commits",
        "selected_surfaces_sha256",
        "packet_content_sha256",
        "decision_sha256",
        "operator_gate_state",
        "refresh_assignment_id",
    }
)
HOST_BINDING_KEYS = frozenset({"schema", "catalog_digest", "receipt_sha256", "states"})
RESULT_KEYS = frozenset(
    {
        "result_schema",
        "assignment_id",
        "terminal_status",
        "summary",
        "changed_paths",
        "no_change",
        "checks",
        "findings",
        "residual_risks",
    }
)
REVIEWER_RESULT_KEYS = RESULT_KEYS | {
    "verdict",
    "hard_stop",
}
CHECK_KEYS = frozenset({"check_id", "status", "detail"})
FINDING_KEYS = frozenset(
    {
        "finding_id",
        "severity",
        "category",
        "location",
        "impact",
        "fix",
        "validation",
        "resolved",
        "hard_stop",
    }
)
CANDIDATE_EVIDENCE_KEYS = frozenset(
    {
        "target_paths",
        "test_node_ids",
        "negative_test_node_ids",
        "owning_result_ids",
        "reviewed_unchanged_paths",
        "pytest_outcomes",
    }
)
PYTEST_OUTCOME_KEYS = frozenset({"node_id", "status"})
ALLOWED_TARGET_ROOTS = (
    PurePosixPath("plugins/fleet-core"),
    PurePosixPath("plugins/mission-control"),
    PurePosixPath("plugins/multi-agent-consensus"),
    PurePosixPath("plugins/saga"),
    PurePosixPath("scripts"),
)

GIT_BEARING_NODES = frozenset(
    {
        "plugins/saga/tests/test_port_ledger.py::"
        "test_release_refresh_uses_controlled_temporary_repositories",
        "plugins/saga/tests/test_port_ledger.py::"
        "test_release_refresh_rejects_drift_byte_identically",
        "plugins/saga/tests/test_promote_scan.py::"
        "test_promotion_requires_canonical_target_provenance_and_no_conflict",
        "plugins/saga/tests/test_promote_scan.py::"
        "test_promotion_requires_canonical_target_provenance_and_no_conflict_rejects_negative_cases",
        "plugins/saga/tests/test_outcome_merge_queue.py::"
        "test_outcome_merge_settles_only_from_verified_integration_receipt",
        "plugins/saga/tests/test_outcome_merge_queue.py::"
        "test_outcome_merge_settles_only_from_verified_integration_receipt_rejects_negative_cases",
        "plugins/saga/tests/test_ship_ceremony.py::"
        "test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation",
        "plugins/saga/tests/test_ship_ceremony.py::"
        "test_ship_ceremony_requires_hazards_reversibility_receipt_and_confirmation_rejects_negative_cases",
    }
)

DEFAULT_SURFACES: dict[str, tuple[str, ...]] = {
    "claude": (
        "plugins/saga",
        "plugins/fleet-core",
        "plugins/mission-control",
        "plugins/team-execution",
        "scripts",
        "tools",
    ),
    "codex": (
        "plugins/saga",
        "plugins/fleet-core",
        "plugins/mission-control",
        "plugins/verified-workflows",
        "scripts",
        "docs/portability",
    ),
    "antigravity": (
        "plugins/saga",
        "plugins/fleet-core",
        "plugins/mission-control",
        "plugins/multi-agent-consensus",
        "scripts",
        "tools",
    ),
}


class LedgerError(ValueError):
    """The ledger or requested operation violates the closed contract."""


class StrictSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_strict_mapping(
    loader: StrictSafeLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    seen: dict[Any, Any] = {}
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in seen
        except TypeError as exc:
            raise LedgerError(
                f"YAML mapping key at line {key_node.start_mark.line + 1}, "
                f"column {key_node.start_mark.column + 1} is not hashable"
            ) from exc
        if duplicate:
            raise LedgerError(
                f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}, "
                f"column {key_node.start_mark.column + 1}"
            )
        seen[key] = key_node.start_mark
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_strict_mapping,
)


def _strict_yaml_load(text: str) -> object:
    # StrictSafeLoader inherits SafeLoader and adds duplicate-key rejection.
    return yaml.load(text, Loader=StrictSafeLoader)  # nosec B506


class GitRunner(Protocol):
    """Injected boundary used by discovery."""

    def run(self, repository: Path, arguments: Sequence[str]) -> bytes: ...


class ReadOnlyGitRunner:
    """Run only the closed, no-shell Git plumbing forms needed by discovery."""

    _ALLOWED = frozenset({"rev-parse", "diff", "ls-tree", "show"})

    def run(self, repository: Path, arguments: Sequence[str]) -> bytes:
        args = tuple(arguments)
        _validate_git_arguments(args)
        command = ["git", "-C", str(repository), *args]
        try:
            # The executable and all permitted argument forms are fixed above.
            completed = subprocess.run(  # nosec B603
                command,
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise LedgerError(f"read-only Git command failed in {repository}: {args[0]}") from exc
        return completed.stdout


def _validate_git_arguments(arguments: Sequence[str]) -> None:
    if not arguments or arguments[0] not in ReadOnlyGitRunner._ALLOWED:
        raise LedgerError("discovery permits only rev-parse, diff, ls-tree, and show")
    if any("\x00" in item or item.startswith("-C") for item in arguments):
        raise LedgerError("unsafe Git argument")
    command = arguments[0]
    if command == "rev-parse":
        if (
            len(arguments) != 2
            or arguments[1]
            not in {
                "HEAD",
                "refs/remotes/origin/main",
            }
            and not arguments[1].endswith("^{commit}")
        ):
            raise LedgerError("rev-parse form is not permitted")
    elif command == "diff":
        if len(arguments) < 5 or arguments[1:3] != ("--name-status", "-z"):
            raise LedgerError("diff form is not permitted")
        if arguments[4] != "--":
            raise LedgerError("diff must separate revisions from selected paths")
    elif command == "ls-tree":
        if len(arguments) < 7 or arguments[1:5] != (
            "-r",
            "-z",
            "--full-tree",
            "--name-only",
        ):
            raise LedgerError("ls-tree form is not permitted")
        if arguments[6] != "--":
            raise LedgerError("ls-tree must separate the commit from selected paths")
    elif command == "show":
        if len(arguments) != 3 or arguments[1] != "--no-ext-diff":
            raise LedgerError("show form is not permitted")
        object_name = arguments[2]
        if ":" not in object_name or object_name.startswith("-"):
            raise LedgerError("show must name a commit-bound repository path")


def _mapping(value: object, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path}: expected an object")
        return None
    if not all(isinstance(key, str) for key in value):
        errors.append(f"{path}: keys must be strings")
        return None
    return cast(Mapping[str, Any], value)


def _sequence(value: object, path: str, errors: list[str]) -> Sequence[Any] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        errors.append(f"{path}: expected a list")
        return None
    return cast(Sequence[Any], value)


def _closed(
    value: Mapping[str, Any], allowed: frozenset[str], path: str, errors: list[str]
) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")
    for key in sorted(allowed - set(value)):
        errors.append(f"{path}: missing required field {key!r}")


def _required_string(
    value: object, path: str, errors: list[str], *, allow_empty: bool = False
) -> str | None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        suffix = "a string" if allow_empty else "a non-empty string"
        errors.append(f"{path}: expected {suffix}")
        return None
    return value


def _identifier(value: object, path: str, errors: list[str]) -> str | None:
    item = _required_string(value, path, errors)
    if item is not None and not ID_RE.fullmatch(item):
        errors.append(f"{path}: expected a stable lowercase identifier")
        return None
    return item


def _sha(value: object, path: str, errors: list[str], pattern: re.Pattern[str]) -> str | None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        errors.append(f"{path}: expected a lowercase hexadecimal digest")
        return None
    return value


def _repository_path(value: object, path: str, errors: list[str]) -> str | None:
    item = _required_string(value, path, errors)
    if item is None:
        return None
    parsed = PurePosixPath(item)
    if (
        parsed.is_absolute()
        or item != parsed.as_posix()
        or any(part in {"", ".", "..", ".git"} for part in parsed.parts)
        or "\\" in item
    ):
        errors.append(f"{path}: expected a safe repository-relative POSIX path")
        return None
    return item


def _string_list(
    value: object,
    path: str,
    errors: list[str],
    *,
    identifiers: bool = False,
    paths: bool = False,
    nonempty: bool = False,
) -> list[str]:
    items = _sequence(value, path, errors)
    if items is None:
        return []
    result: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        parsed = (
            _identifier(item, item_path, errors)
            if identifiers
            else _repository_path(item, item_path, errors)
            if paths
            else _required_string(item, item_path, errors)
        )
        if parsed is not None:
            result.append(parsed)
    if len(result) != len(set(result)):
        errors.append(f"{path}: duplicate values are not allowed")
    if nonempty and not result:
        errors.append(f"{path}: expected at least one value")
    return result


def load_ledger(path: Path | str) -> dict[str, Any]:
    """Load one bounded YAML ledger without accepting arbitrary objects."""

    source = Path(path)
    try:
        size = source.stat().st_size
        if size > MAX_LEDGER_BYTES:
            raise LedgerError("ledger exceeds the size limit")
        parsed = _strict_yaml_load(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise LedgerError(f"could not load ledger: {source}") from exc
    errors = validate_ledger(parsed, inventory_only=True)
    structural = [error for error in errors if not error.startswith("decision gate:")]
    if structural:
        raise LedgerError("invalid ledger:\n- " + "\n- ".join(structural))
    return cast(dict[str, Any], parsed)


def validate_ledger(
    ledger: object,
    *,
    inventory_only: bool = False,
    require_migrated: bool = False,
) -> list[str]:
    """Return every actionable contract violation in deterministic order."""

    errors: list[str] = []
    root = _mapping(ledger, "ledger", errors)
    if root is None:
        return errors
    _closed(root, TOP_KEYS, "ledger", errors)
    schema = root.get("schema")
    if schema not in {SCHEMA_V1, SCHEMA_V2}:
        errors.append(
            f"ledger.schema: expected {SCHEMA_V1!r} or {SCHEMA_V2!r}; unknown versions fail closed"
        )
    if require_migrated and schema != SCHEMA_V2:
        errors.append(f"ledger.schema: --require-migrated requires {SCHEMA_V2!r}")

    campaign = _mapping(root.get("campaign"), "ledger.campaign", errors)
    packets_by_id: dict[str, Mapping[str, Any]] = {}
    unmatched: list[str] = []
    host_states: dict[str, str] = {}
    snapshots: dict[str, Mapping[str, Any]] = {}
    if campaign is not None:
        _closed(campaign, CAMPAIGN_KEYS, "ledger.campaign", errors)
        campaign_id = campaign.get("id")
        if not isinstance(campaign_id, str) or CAMPAIGN_RE.fullmatch(campaign_id) is None:
            errors.append("ledger.campaign.id: expected YYYY-MM-DD-lowercase-slug")
        snapshots = _validate_snapshots(campaign.get("snapshots"), errors)
        surfaces = _validate_surfaces(campaign.get("selected_surfaces"), errors)
        _validate_snapshot_surface_repositories(snapshots, surfaces, errors)
        _validate_seeds(campaign.get("historical_seeds"), errors)
        host_states = _validate_host_receipt(campaign.get("host_receipt"), errors)
        packets_by_id = _validate_packets(
            campaign.get("edit_packets"),
            snapshots,
            surfaces,
            errors,
        )
        unmatched = _string_list(
            campaign.get("unmatched_edit_packet_ids"),
            "ledger.campaign.unmatched_edit_packet_ids",
            errors,
            identifiers=True,
        )
        unknown_unmatched = sorted(set(unmatched) - set(packets_by_id))
        if unknown_unmatched:
            errors.append(
                "ledger.campaign.unmatched_edit_packet_ids: unknown packet IDs "
                + ", ".join(unknown_unmatched)
            )
        _validate_release_drift(
            campaign.get("release_drift"),
            unmatched,
            snapshots,
            errors,
        )

    candidates = _validate_candidates(
        root.get("candidates"),
        packets_by_id,
        host_states,
        errors,
        schema=cast(str, schema),
        require_migrated=require_migrated,
    )
    ownership: dict[str, list[str]] = {}
    for candidate in candidates:
        candidate_id = cast(str, candidate.get("id"))
        for packet_id in cast(list[str], candidate.get("edit_packet_ids", [])):
            ownership.setdefault(packet_id, []).append(candidate_id)
    duplicated = {key: owners for key, owners in ownership.items() if len(owners) > 1}
    for packet_id, owners in sorted(duplicated.items()):
        errors.append(
            f"edit packet {packet_id!r}: duplicate candidate ownership by {', '.join(owners)}"
        )
    unowned = sorted(set(packets_by_id) - set(ownership))
    if unowned:
        errors.append("inventory coverage: unowned edit packets " + ", ".join(unowned))
    if sorted(unmatched) != unowned:
        errors.append(
            "ledger.campaign.unmatched_edit_packet_ids: must equal the exact unowned packet set"
        )
    if unmatched:
        errors.append("inventory coverage: unmatched edit packets remain")

    if not inventory_only:
        pending = sorted(
            cast(str, candidate["id"])
            for candidate in candidates
            if cast(Mapping[str, Any], candidate.get("decision", {})).get("state") == "pending"
        )
        if pending:
            errors.append("decision gate: pending candidates " + ", ".join(pending))
    return errors


def _validate_snapshots(value: object, errors: list[str]) -> dict[str, Mapping[str, Any]]:
    rows = _sequence(value, "ledger.campaign.snapshots", errors)
    if rows is None:
        return {}
    seen: set[str] = set()
    snapshots: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(rows):
        path = f"ledger.campaign.snapshots[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        _closed(row, SNAPSHOT_KEYS, path, errors)
        host = row.get("host")
        if host not in HOSTS:
            errors.append(f"{path}.host: expected one of {sorted(HOSTS)}")
        elif host in seen:
            errors.append(f"{path}.host: duplicate host snapshot")
        else:
            seen.add(cast(str, host))
            snapshots[cast(str, host)] = row
        _repository_path(row.get("repository"), f"{path}.repository", errors)
        for field in (
            "planning_commit",
            "inventory_commit",
            "head_commit",
            "origin_main_commit",
        ):
            _sha(row.get(field), f"{path}.{field}", errors, SHA40_RE)
        if host == "antigravity":
            if row.get("inventory_commit") != row.get("origin_main_commit"):
                errors.append(f"{path}: Antigravity inventory_commit must equal local origin/main")
        else:
            if row.get("inventory_commit") != row.get("head_commit"):
                errors.append(f"{path}: inventory_commit must equal head_commit")
            if row.get("head_commit") != row.get("origin_main_commit"):
                errors.append(f"{path}: HEAD and local origin/main differ; discovery must stop")
    if seen != HOSTS:
        errors.append("ledger.campaign.snapshots: must contain Claude, Codex, and Antigravity")
    return snapshots


def _validate_surfaces(value: object, errors: list[str]) -> dict[str, Mapping[str, Any]]:
    rows = _sequence(value, "ledger.campaign.selected_surfaces", errors)
    if rows is None:
        return {}
    seen: set[str] = set()
    surfaces: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(rows):
        path = f"ledger.campaign.selected_surfaces[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        _closed(row, SURFACE_KEYS, path, errors)
        host = row.get("host")
        if host not in HOSTS:
            errors.append(f"{path}.host: expected one of {sorted(HOSTS)}")
        elif host in seen:
            errors.append(f"{path}.host: duplicate host surface")
        else:
            seen.add(cast(str, host))
            surfaces[cast(str, host)] = row
        _repository_path(row.get("repository"), f"{path}.repository", errors)
        _string_list(row.get("paths"), f"{path}.paths", errors, paths=True, nonempty=True)
    if seen != HOSTS:
        errors.append(
            "ledger.campaign.selected_surfaces: must contain Claude, Codex, and Antigravity"
        )
    return surfaces


def _validate_snapshot_surface_repositories(
    snapshots: Mapping[str, Mapping[str, Any]],
    surfaces: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    for host in sorted(HOSTS):
        snapshot = snapshots.get(host)
        surface = surfaces.get(host)
        if (
            snapshot is not None
            and surface is not None
            and snapshot.get("repository") != surface.get("repository")
        ):
            errors.append(
                f"ledger.campaign.selected_surfaces[{host}].repository: "
                "must match the host snapshot repository identity"
            )


def _validate_seeds(value: object, errors: list[str]) -> None:
    rows = _sequence(value, "ledger.campaign.historical_seeds", errors)
    if rows is None:
        return
    seen: set[str] = set()
    for index, item in enumerate(rows):
        path = f"ledger.campaign.historical_seeds[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        _closed(row, SEED_KEYS, path, errors)
        host = row.get("host")
        if host not in HOSTS:
            errors.append(f"{path}.host: expected one of {sorted(HOSTS)}")
        elif host in seen:
            errors.append(f"{path}.host: duplicate history seed")
        else:
            seen.add(cast(str, host))
        _sha(row.get("commit"), f"{path}.commit", errors, SHA40_RE)
    if "claude" not in seen:
        errors.append("ledger.campaign.historical_seeds: Claude discovery seed is required")


def _validate_host_receipt(value: object, errors: list[str]) -> dict[str, str]:
    path = "ledger.campaign.host_receipt"
    receipt = _mapping(value, path, errors)
    if receipt is None:
        return {}
    _closed(receipt, HOST_RECEIPT_KEYS, path, errors)
    if receipt.get("schema") != "antigravity.capabilities.v1":
        errors.append(f"{path}.schema: expected 'antigravity.capabilities.v1'")
    _sha(receipt.get("catalog_digest"), f"{path}.catalog_digest", errors, SHA256_RE)
    receipt_sha256 = _sha(
        receipt.get("receipt_sha256"), f"{path}.receipt_sha256", errors, SHA256_RE
    )
    rows = _sequence(receipt.get("states"), f"{path}.states", errors)
    states: dict[str, str] = {}
    if rows is None:
        return states
    for index, item in enumerate(rows):
        row_path = f"{path}.states[{index}]"
        row = _mapping(item, row_path, errors)
        if row is None:
            continue
        _closed(row, CAPABILITY_STATE_KEYS, row_path, errors)
        capability = _identifier(row.get("capability"), f"{row_path}.capability", errors)
        state = row.get("state")
        if state not in RAW_CAPABILITY_STATES:
            errors.append(f"{row_path}.state: expected one of {sorted(RAW_CAPABILITY_STATES)}")
        if capability is not None:
            if capability in states:
                errors.append(f"{row_path}.capability: duplicate capability")
            elif isinstance(state, str):
                states[capability] = state
    if not states:
        errors.append(f"{path}.states: expected at least one sanitized capability state")
    if receipt_sha256 is not None:
        states["__receipt_sha256__"] = receipt_sha256
    return states


def _validate_packets(
    value: object,
    snapshots: Mapping[str, Mapping[str, Any]],
    surfaces: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> dict[str, Mapping[str, Any]]:
    rows = _sequence(value, "ledger.campaign.edit_packets", errors)
    if rows is None:
        return {}
    packets: dict[str, Mapping[str, Any]] = {}
    identities: set[tuple[object, ...]] = set()
    history_hosts: set[str] = set()
    tree_hosts: set[str] = set()
    for index, item in enumerate(rows):
        path = f"ledger.campaign.edit_packets[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        _closed(row, PACKET_KEYS, path, errors)
        packet_id = _identifier(row.get("id"), f"{path}.id", errors)
        host = row.get("host")
        if host not in HOSTS:
            errors.append(f"{path}.host: expected one of {sorted(HOSTS)}")
        commit = _sha(row.get("commit"), f"{path}.commit", errors, SHA40_RE)
        packet_path = _repository_path(row.get("path"), f"{path}.path", errors)
        change = row.get("change")
        if change not in CHANGES:
            errors.append(f"{path}.change: expected one of {sorted(CHANGES)}")
        _sha(row.get("content_sha256"), f"{path}.content_sha256", errors, SHA256_RE)
        source = row.get("source")
        if source not in PACKET_SOURCES:
            errors.append(f"{path}.source: expected one of {sorted(PACKET_SOURCES)}")
        elif isinstance(host, str):
            (history_hosts if source == "history" else tree_hosts).add(host)
        if source == "tree" and row.get("change") != "tree":
            errors.append(f"{path}.change: tree packets must use 'tree'")
        if source == "history" and row.get("change") == "tree":
            errors.append(f"{path}.change: history packets may not use 'tree'")
        if isinstance(host, str) and host in HOSTS:
            snapshot = snapshots.get(host)
            if (
                snapshot is not None
                and commit is not None
                and commit != snapshot.get("inventory_commit")
            ):
                errors.append(f"{path}.commit: must match the {host} inventory snapshot")
            surface = surfaces.get(host)
            surface_paths = (
                cast(Sequence[Any], surface.get("paths", [])) if surface is not None else ()
            )
            if packet_path is not None and not any(
                isinstance(surface_path, str) and _path_is_within_surface(packet_path, surface_path)
                for surface_path in surface_paths
            ):
                errors.append(
                    f"{path}.path: must remain inside the declared {host} selected surface"
                )
        if (
            packet_id is not None
            and isinstance(host, str)
            and host in HOSTS
            and source in PACKET_SOURCES
            and packet_path is not None
            and change in CHANGES
        ):
            expected_id = _packet_id(host, cast(str, source), packet_path, cast(str, change))
            if packet_id != expected_id:
                errors.append(f"{path}.id: must equal deterministic packet ID {expected_id!r}")
        identity = (
            row.get("host"),
            row.get("commit"),
            row.get("path"),
            row.get("change"),
            row.get("source"),
        )
        if identity in identities:
            errors.append(f"{path}: duplicate normalized source edit")
        identities.add(identity)
        if packet_id is not None:
            if packet_id in packets:
                errors.append(f"{path}.id: duplicate edit-packet ID")
            else:
                packets[packet_id] = row
    if tree_hosts != HOSTS:
        errors.append(
            "ledger.campaign.edit_packets: complete current-tree packets require all hosts"
        )
    if "claude" not in history_hosts:
        errors.append("ledger.campaign.edit_packets: Claude history-delta packets are required")
    return packets


def _path_is_within_surface(path: str, surface: str) -> bool:
    parsed_path = PurePosixPath(path)
    parsed_surface = PurePosixPath(surface)
    return parsed_path == parsed_surface or parsed_surface in parsed_path.parents


def _validate_release_drift(
    value: object,
    unmatched: list[str],
    snapshots: Mapping[str, Mapping[str, Any]],
    errors: list[str],
) -> None:
    path = "ledger.campaign.release_drift"
    drift = _mapping(value, path, errors)
    if drift is None:
        return
    _closed(drift, RELEASE_DRIFT_KEYS, path, errors)
    checked_at = _required_string(drift.get("checked_at"), f"{path}.checked_at", errors)
    if checked_at is not None:
        try:
            datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{path}.checked_at: expected an ISO-8601 timestamp")
    status = drift.get("status")
    if status not in {"clean", "unmatched"}:
        errors.append(f"{path}.status: expected 'clean' or 'unmatched'")
    rows = _sequence(drift.get("snapshots"), f"{path}.snapshots", errors)
    seen: set[str] = set()
    if rows is not None:
        for index, item in enumerate(rows):
            row_path = f"{path}.snapshots[{index}]"
            row = _mapping(item, row_path, errors)
            if row is None:
                continue
            _closed(row, DRIFT_SNAPSHOT_KEYS, row_path, errors)
            host = row.get("host")
            if host not in HOSTS:
                errors.append(f"{row_path}.host: expected one of {sorted(HOSTS)}")
            elif host in seen:
                errors.append(f"{row_path}.host: duplicate drift snapshot")
            else:
                seen.add(cast(str, host))
            _sha(row.get("inventory_commit"), f"{row_path}.inventory_commit", errors, SHA40_RE)
            _sha(row.get("current_commit"), f"{row_path}.current_commit", errors, SHA40_RE)
            snapshot = snapshots.get(cast(str, host))
            if snapshot is not None:
                if row.get("inventory_commit") != snapshot.get("inventory_commit"):
                    errors.append(f"{row_path}.inventory_commit: must match the campaign inventory")
                if row.get("current_commit") != snapshot.get("origin_main_commit"):
                    errors.append(f"{row_path}.current_commit: must match local origin/main")
    if seen != HOSTS:
        errors.append(f"{path}.snapshots: must disclose every host")
    drift_unmatched = _string_list(
        drift.get("unmatched_edit_packet_ids"),
        f"{path}.unmatched_edit_packet_ids",
        errors,
        identifiers=True,
    )
    if sorted(drift_unmatched) != sorted(unmatched):
        errors.append(f"{path}.unmatched_edit_packet_ids: must match campaign unmatched packets")
    expected_status = "unmatched" if unmatched else "clean"
    if status != expected_status:
        errors.append(f"{path}.status: must be {expected_status!r} for current unmatched packets")


def _validate_candidates(
    value: object,
    packets_by_id: Mapping[str, Mapping[str, Any]],
    host_states: Mapping[str, str],
    errors: list[str],
    *,
    schema: str,
    require_migrated: bool,
) -> list[Mapping[str, Any]]:
    rows = _sequence(value, "ledger.candidates", errors)
    if rows is None:
        return []
    result: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(rows):
        path = f"ledger.candidates[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        if schema == SCHEMA_V2:
            for key in sorted(set(row) - CANDIDATE_KEYS_V2):
                errors.append(f"{path}: unknown field {key!r}")
            for key in sorted(CANDIDATE_KEYS_V1 - set(row)):
                errors.append(f"{path}: missing required field {key!r}")
        else:
            _closed(row, CANDIDATE_KEYS_V1, path, errors)
        candidate_id = _identifier(row.get("id"), f"{path}.id", errors)
        if candidate_id is not None:
            if candidate_id in seen:
                errors.append(f"{path}.id: duplicate candidate ID")
            seen.add(candidate_id)
        _required_string(row.get("title"), f"{path}.title", errors)
        packet_ids = _string_list(
            row.get("edit_packet_ids"),
            f"{path}.edit_packet_ids",
            errors,
            identifiers=True,
            nonempty=True,
        )
        unknown = sorted(set(packet_ids) - set(packets_by_id))
        if unknown:
            errors.append(f"{path}.edit_packet_ids: unknown packet IDs {', '.join(unknown)}")
        provenance = _validate_provenance(row.get("provenance"), path, errors)
        expected_provenance = {
            (packet["host"], packet["commit"], packet["path"])
            for packet_id in packet_ids
            if (packet := packets_by_id.get(packet_id)) is not None
        }
        if provenance != expected_provenance:
            errors.append(f"{path}.provenance: must exactly bind every owned edit packet")
        _required_string(row.get("semantic_contract"), f"{path}.semantic_contract", errors)
        _string_list(row.get("adjacent_dependencies"), f"{path}.adjacent_dependencies", errors)
        required_capabilities = _string_list(
            row.get("required_host_capabilities"),
            f"{path}.required_host_capabilities",
            errors,
            identifiers=True,
        )
        unknown_capabilities = sorted(set(required_capabilities) - set(host_states))
        if unknown_capabilities:
            errors.append(
                f"{path}.required_host_capabilities: absent from sanitized receipt "
                + ", ".join(unknown_capabilities)
            )
        antigravity_state = row.get("antigravity_state")
        if antigravity_state not in ANTIGRAVITY_STATES:
            errors.append(f"{path}.antigravity_state: expected one of {sorted(ANTIGRAVITY_STATES)}")
        proposed = row.get("proposed_disposition")
        if proposed not in DISPOSITIONS:
            errors.append(f"{path}.proposed_disposition: expected one of {sorted(DISPOSITIONS)}")
        blocked_caps = [
            capability
            for capability in required_capabilities
            if host_states.get(capability) in {"failed", "unknown", "unavailable"}
        ]
        if blocked_caps and (antigravity_state != "blocked-by-host" or proposed != "blocked"):
            errors.append(
                f"{path}: required non-passing host capabilities require "
                "blocked-by-host and blocked disposition"
            )
        _validate_ranking(row.get("ranking"), path, errors)
        _string_list(
            row.get("evidence_expectation"),
            f"{path}.evidence_expectation",
            errors,
            nonempty=True,
        )
        decision = _validate_decision(row.get("decision"), path, errors)
        _validate_migration(
            row.get("migration"),
            candidate_path=path,
            schema=schema,
            decision_state=decision,
            packet_ids=packet_ids,
            host_receipt_sha256=cast(str | None, host_states.get("__receipt_sha256__")),
            antigravity_state=antigravity_state,
            proposed_disposition=proposed,
            require_migrated=require_migrated,
            errors=errors,
        )
        result.append(row)
    return result


def _validate_provenance(
    value: object, candidate_path: str, errors: list[str]
) -> set[tuple[str, str, str]]:
    rows = _sequence(value, f"{candidate_path}.provenance", errors)
    result: set[tuple[str, str, str]] = set()
    if rows is None:
        return result
    for index, item in enumerate(rows):
        path = f"{candidate_path}.provenance[{index}]"
        row = _mapping(item, path, errors)
        if row is None:
            continue
        _closed(row, PROVENANCE_KEYS, path, errors)
        host = row.get("host")
        if host not in HOSTS:
            errors.append(f"{path}.host: expected one of {sorted(HOSTS)}")
        commit = _sha(row.get("commit"), f"{path}.commit", errors, SHA40_RE)
        source_path = _repository_path(row.get("path"), f"{path}.path", errors)
        if isinstance(host, str) and commit is not None and source_path is not None:
            identity = (host, commit, source_path)
            if identity in result:
                errors.append(f"{path}: duplicate provenance entry")
            result.add(identity)
    return result


def _validate_ranking(value: object, candidate_path: str, errors: list[str]) -> None:
    path = f"{candidate_path}.ranking"
    ranking = _mapping(value, path, errors)
    if ranking is None:
        return
    _closed(ranking, RANKING_KEYS, path, errors)
    for field in sorted(RANKING_KEYS):
        score = ranking.get(field)
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
            errors.append(f"{path}.{field}: expected an integer from 1 through 5")


def _validate_decision(value: object, candidate_path: str, errors: list[str]) -> str | None:
    path = f"{candidate_path}.decision"
    decision = _mapping(value, path, errors)
    if decision is None:
        return None
    _closed(decision, DECISION_KEYS, path, errors)
    state = decision.get("state")
    if state not in DECISION_STATES:
        errors.append(f"{path}.state: expected one of {sorted(DECISION_STATES)}")
    rationale = _required_string(decision.get("rationale"), f"{path}.rationale", errors)
    revisit = _required_string(
        decision.get("revisit_trigger"),
        f"{path}.revisit_trigger",
        errors,
    )
    if state == "pending":
        if decision.get("operator") is not None or decision.get("decided_at") is not None:
            errors.append(f"{path}: pending decisions may not record operator or decision time")
    else:
        _required_string(decision.get("operator"), f"{path}.operator", errors)
        decided_at = _required_string(decision.get("decided_at"), f"{path}.decided_at", errors)
        if decided_at is not None:
            try:
                datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}.decided_at: expected an ISO-8601 timestamp")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{path}.rationale: non-pending decisions require a rationale")
        if not isinstance(revisit, str) or not revisit.strip():
            errors.append(f"{path}.revisit_trigger: non-pending decisions require a trigger")
    return cast(str | None, state)


def packet_set_sha256(packet_ids: Sequence[str]) -> str:
    """Hash the closed sorted packet-ID set using the published newline framing."""

    if len(packet_ids) != len(set(packet_ids)):
        raise LedgerError("packet IDs must be unique")
    encoded: list[bytes] = []
    for packet_id in packet_ids:
        if not isinstance(packet_id, str):
            raise LedgerError("packet IDs must be Unicode strings")
        if "\r" in packet_id or "\n" in packet_id:
            raise LedgerError("packet IDs may not contain carriage returns or line feeds")
        try:
            encoded.append(packet_id.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise LedgerError("packet IDs must contain valid Unicode") from exc
    payload = b"\n".join(sorted(encoded))
    if encoded:
        payload += b"\n"
    return hashlib.sha256(payload).hexdigest()


def _target_path(value: object, path: str, errors: list[str]) -> str | None:
    target = _repository_path(value, path, errors)
    if target is None:
        return None
    parsed = PurePosixPath(target)
    if not any(root == parsed or root in parsed.parents for root in ALLOWED_TARGET_ROOTS):
        errors.append(f"{path}: must remain beneath an allowed Antigravity repository root")
    if (
        PurePosixPath("plugins/team-execution") == parsed
        or PurePosixPath("plugins/team-execution") in parsed.parents
    ):
        errors.append(f"{path}: source team-execution targets are forbidden")
    return target


def _target_path_list(
    value: object,
    path: str,
    errors: list[str],
    *,
    nonempty: bool = True,
) -> list[str]:
    rows = _sequence(value, path, errors)
    if rows is None:
        return []
    result: list[str] = []
    for index, item in enumerate(rows):
        target = _target_path(item, f"{path}[{index}]", errors)
        if target is not None:
            result.append(target)
    if len(result) != len(set(result)):
        errors.append(f"{path}: duplicate values are not allowed")
    if nonempty and not result:
        errors.append(f"{path}: expected at least one value")
    return result


def _test_node_list(value: object, path: str, errors: list[str]) -> list[str]:
    rows = _sequence(value, path, errors)
    if rows is None:
        return []
    result: list[str] = []
    for index, item in enumerate(rows):
        item_path = f"{path}[{index}]"
        node = _required_string(item, item_path, errors)
        if node is None:
            continue
        if node.count("::") < 1:
            errors.append(f"{item_path}: expected a Pytest node ID")
            continue
        file_path = node.split("::", 1)[0]
        parsed = _target_path(file_path, f"{item_path}.path", errors)
        if parsed is not None and not parsed.endswith(".py"):
            errors.append(f"{item_path}: Pytest node path must end in .py")
        result.append(node)
    if len(result) != len(set(result)):
        errors.append(f"{path}: duplicate values are not allowed")
    if not result:
        errors.append(f"{path}: expected at least one value")
    return result


def _validate_migration(
    value: object,
    *,
    candidate_path: str,
    schema: str,
    decision_state: str | None,
    packet_ids: Sequence[str],
    host_receipt_sha256: str | None,
    antigravity_state: object,
    proposed_disposition: object,
    require_migrated: bool,
    errors: list[str],
) -> None:
    path = f"{candidate_path}.migration"
    if schema == SCHEMA_V1:
        return
    if decision_state != "approved-survivor":
        if value is not None:
            errors.append(f"{path}: non-survivors may not carry migration data")
        return
    migration = _mapping(value, path, errors)
    if migration is None:
        errors.append(f"{path}: approved survivors require the closed migration object in v2")
        return
    _closed(migration, MIGRATION_KEYS, path, errors)
    state = migration.get("state")
    if state not in MIGRATION_STATES:
        errors.append(f"{path}.state: expected one of {sorted(MIGRATION_STATES)}")
    _target_path_list(migration.get("target_paths"), f"{path}.target_paths", errors)
    test_nodes = _test_node_list(migration.get("test_node_ids"), f"{path}.test_node_ids", errors)
    negative_nodes = _test_node_list(
        migration.get("negative_test_node_ids"),
        f"{path}.negative_test_node_ids",
        errors,
    )
    overlap = sorted(set(test_nodes) & set(negative_nodes))
    if overlap:
        errors.append(f"{path}: positive and negative node IDs overlap: {', '.join(overlap)}")
    _string_list(
        migration.get("intentional_differences"),
        f"{path}.intentional_differences",
        errors,
        nonempty=True,
    )
    packet_digest = _sha(
        migration.get("packet_set_sha256"),
        f"{path}.packet_set_sha256",
        errors,
        SHA256_RE,
    )
    try:
        expected_packet_digest = packet_set_sha256(packet_ids)
    except LedgerError as exc:
        errors.append(f"{path}.packet_set_sha256: {exc}")
    else:
        if packet_digest is not None and packet_digest != expected_packet_digest:
            errors.append(f"{path}.packet_set_sha256: must bind the exact owned packet set")
    receipt_digest = _sha(
        migration.get("host_receipt_sha256"),
        f"{path}.host_receipt_sha256",
        errors,
        SHA256_RE,
    )
    if (
        receipt_digest is not None
        and host_receipt_sha256 is not None
        and receipt_digest != host_receipt_sha256
    ):
        errors.append(f"{path}.host_receipt_sha256: must match the current campaign receipt")
    blocking = _string_list(
        migration.get("blocking_capabilities"),
        f"{path}.blocking_capabilities",
        errors,
        identifiers=True,
    )
    evidence_digest = migration.get("evidence_manifest_sha256")
    if evidence_digest is not None:
        _sha(evidence_digest, f"{path}.evidence_manifest_sha256", errors, SHA256_RE)
    validated_at = migration.get("validated_at")
    if validated_at is not None:
        timestamp = _required_string(validated_at, f"{path}.validated_at", errors)
        if timestamp is not None:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}.validated_at: expected an ISO-8601 timestamp")
    if state == "planned":
        if evidence_digest is not None or blocking or validated_at is not None:
            errors.append(
                f"{path}: planned migrations may not carry evidence, blockers, or validation time"
            )
        if antigravity_state not in {"partial", "absent"}:
            errors.append(f"{path}: planned migrations must remain partial or absent")
    elif state == "migrated":
        if evidence_digest is None or blocking or validated_at is None:
            errors.append(
                f"{path}: migrated rows require evidence and validation time with no blockers"
            )
        if antigravity_state not in MIGRATION_FINAL_STATES:
            errors.append(f"{path}: migrated rows require a final Antigravity state")
        if proposed_disposition == "blocked":
            errors.append(f"{path}: migrated rows may not retain a blocked disposition")
    elif state == "blocked":
        if not blocking or evidence_digest is not None or validated_at is not None:
            errors.append(
                f"{path}: blocked rows require capabilities and forbid evidence or validation time"
            )
        if antigravity_state != "blocked-by-host" or proposed_disposition != "blocked":
            errors.append(f"{path}: blocked rows require blocked-by-host and blocked disposition")
    if require_migrated and state != "migrated":
        errors.append(f"{path}.state: --require-migrated requires every survivor to be migrated")


def _packet_id(host: str, source: str, path: str, change: str) -> str:
    digest = hashlib.sha256(f"{host}\0{source}\0{path}\0{change}".encode()).hexdigest()[:20]
    return f"edit-{host}-{digest}"


def _content_at(runner: GitRunner, repository: Path, commit: str, path: str) -> bytes:
    return runner.run(repository, ("show", "--no-ext-diff", f"{commit}:{path}"))


def _tree_packets(
    runner: GitRunner,
    repository: Path,
    host: str,
    commit: str,
    paths: Sequence[str],
) -> list[dict[str, str]]:
    output = runner.run(
        repository,
        ("ls-tree", "-r", "-z", "--full-tree", "--name-only", commit, "--", *paths),
    )
    packets: list[dict[str, str]] = []
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        try:
            path = raw_path.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LedgerError(f"{host} tree contains a non-UTF-8 path") from exc
        path_errors: list[str] = []
        if _repository_path(path, f"{host} tree path", path_errors) is None:
            raise LedgerError(path_errors[0])
        content = _content_at(runner, repository, commit, path)
        packets.append(
            {
                "id": _packet_id(host, "tree", path, "tree"),
                "host": host,
                "commit": commit,
                "path": path,
                "change": "tree",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "source": "tree",
            }
        )
    return packets


def _history_packets(
    runner: GitRunner,
    repository: Path,
    host: str,
    seed: str,
    commit: str,
    paths: Sequence[str],
) -> list[dict[str, str]]:
    output = runner.run(
        repository,
        ("diff", "--name-status", "-z", f"{seed}..{commit}", "--", *paths),
    )
    tokens = output.split(b"\0")
    packets: list[dict[str, str]] = []
    index = 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index].decode("ascii", errors="strict")
        index += 1
        if index >= len(tokens):
            raise LedgerError(f"{host} history emitted an incomplete name-status row")
        old_path: str | None = None
        if status.startswith(("R", "C")):
            old_path = tokens[index].decode("utf-8")
            index += 1
            if index >= len(tokens):
                raise LedgerError(f"{host} history emitted an incomplete rename row")
        path = tokens[index].decode("utf-8")
        index += 1
        change = {
            "A": "added",
            "M": "modified",
            "D": "deleted",
            "R": "renamed",
            "C": "added",
            "T": "modified",
        }.get(status[0])
        if change is None:
            raise LedgerError(f"{host} history emitted unsupported change kind {status!r}")
        content_commit = seed if change == "deleted" else commit
        content_path = old_path if change == "deleted" and old_path is not None else path
        content = _content_at(runner, repository, content_commit, content_path)
        packets.append(
            {
                "id": _packet_id(host, "history", path, change),
                "host": host,
                "commit": commit,
                "path": path,
                "change": change,
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "source": "history",
            }
        )
    return packets


def _resolve_commit(runner: GitRunner, repository: Path, ref: str) -> str:
    output = runner.run(repository, ("rev-parse", ref)).decode("ascii").strip()
    if SHA40_RE.fullmatch(output) is None:
        raise LedgerError(f"repository {repository} returned an invalid commit for {ref}")
    return output


def _absolute_path(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _reject_existing_symlink_components(base: Path, destination: Path) -> None:
    relative = destination.relative_to(base)
    current = base
    for part in (".", *relative.parts):
        if part != ".":
            current /= part
        if current.is_symlink():
            raise LedgerError(
                f"discovery output path component may not be a symbolic link: {current}"
            )


def _safe_output(target_repository: Path, campaign_id: str, output: Path) -> Path:
    if CAMPAIGN_RE.fullmatch(campaign_id) is None:
        raise LedgerError("campaign ID must use YYYY-MM-DD-lowercase-slug")
    lexical_target = _absolute_path(target_repository)
    if not lexical_target.is_dir():
        raise LedgerError(f"antigravity repository does not exist: {lexical_target}")
    lexical_campaign = lexical_target / "docs" / "ports" / campaign_id
    lexical_output = _absolute_path(output)
    if lexical_output != lexical_campaign and lexical_campaign not in lexical_output.parents:
        raise LedgerError(f"discovery output must remain beneath docs/ports/{campaign_id}/")
    _reject_existing_symlink_components(lexical_target, lexical_output.parent)
    if lexical_output.is_symlink():
        raise LedgerError("discovery output may not be a symbolic link")

    physical_target = lexical_target.resolve()
    physical_campaign = (physical_target / "docs" / "ports" / campaign_id).resolve()
    physical_output = lexical_output.resolve()
    if physical_output != physical_campaign and physical_campaign not in physical_output.parents:
        raise LedgerError(
            f"physical discovery output must remain beneath docs/ports/{campaign_id}/"
        )
    return lexical_output


def discover(
    *,
    campaign_id: str,
    output: Path,
    repositories: Mapping[str, Path],
    planning_snapshots: Mapping[str, str],
    claude_seed: str,
    host_receipt: Mapping[str, Any],
    runner: GitRunner | None = None,
    checked_at: str,
    persist: bool = True,
) -> dict[str, Any]:
    """Read all pinned source inputs and atomically write one campaign ledger."""

    target_repository_path = repositories["antigravity"]
    safe_output = _safe_output(target_repository_path, campaign_id, output)
    target_repository = target_repository_path.resolve()
    effective_runner = runner or ReadOnlyGitRunner()
    resolved_repositories = {host: repositories[host].resolve() for host in sorted(HOSTS)}
    for host, repository in resolved_repositories.items():
        if not repository.is_dir():
            raise LedgerError(f"{host} repository does not exist: {repository}")

    snapshots: list[dict[str, str]] = []
    packets: list[dict[str, str]] = []
    for host in sorted(HOSTS):
        repository = resolved_repositories[host]
        head = _resolve_commit(effective_runner, repository, "HEAD")
        origin_main = _resolve_commit(effective_runner, repository, "refs/remotes/origin/main")
        if host != "antigravity" and head != origin_main:
            raise LedgerError(f"{host} HEAD differs from local origin/main; discovery stopped")
        inventory_commit = origin_main if host == "antigravity" else head
        planning = planning_snapshots[host]
        if SHA40_RE.fullmatch(planning) is None:
            raise LedgerError(f"{host} planning snapshot is not a full commit")
        surface_paths = DEFAULT_SURFACES[host]
        packets.extend(
            _tree_packets(
                effective_runner,
                repository,
                host,
                inventory_commit,
                surface_paths,
            )
        )
        if host == "claude":
            seed = _resolve_commit(effective_runner, repository, f"{claude_seed}^{{commit}}")
            packets.extend(
                _history_packets(
                    effective_runner,
                    repository,
                    host,
                    seed,
                    inventory_commit,
                    surface_paths,
                )
            )
        snapshots.append(
            {
                "host": host,
                "repository": _display_repository(target_repository, repository),
                "planning_commit": planning,
                "inventory_commit": inventory_commit,
                "head_commit": head,
                "origin_main_commit": origin_main,
            }
        )

    packets = [
        packet
        for packet in packets
        if not (
            packet["host"] == "antigravity"
            and packet["path"] in ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS
        )
    ]
    packets.sort(key=lambda item: item["id"])
    existing = _load_existing_for_refresh(safe_output, campaign_id)
    candidates = cast(list[dict[str, Any]], existing.get("candidates", [])) if existing else []
    packet_by_id = {packet["id"]: packet for packet in packets}
    old_campaign = cast(Mapping[str, Any], existing["campaign"]) if existing is not None else None
    new_surfaces = [
        {
            "host": host,
            "repository": _display_repository(target_repository, resolved_repositories[host]),
            "paths": list(DEFAULT_SURFACES[host]),
        }
        for host in sorted(HOSTS)
    ]
    binding = _sanitize_receipt_binding(host_receipt)
    for candidate in candidates:
        original_packet_ids = list(cast(list[str], candidate["edit_packet_ids"]))
        retained = [packet_id for packet_id in original_packet_ids if packet_id in packet_by_id]
        evidence_changed = old_campaign is not None and _candidate_refresh_inputs_changed(
            candidate,
            old_campaign=old_campaign,
            new_packets=packet_by_id,
            new_receipt=binding,
            retained_packet_ids=retained,
        )
        candidate["edit_packet_ids"] = retained
        candidate["provenance"] = _provenance_for(retained, packet_by_id)
        if evidence_changed:
            _invalidate_decision_authority(candidate)
    owned = {
        packet_id
        for candidate in candidates
        for packet_id in cast(list[str], candidate["edit_packet_ids"])
    }
    unmatched = sorted(set(packet_by_id) - owned)
    ledger: dict[str, Any] = {
        "schema": existing["schema"] if existing is not None else SCHEMA,
        "campaign": {
            "id": campaign_id,
            "snapshots": snapshots,
            "selected_surfaces": new_surfaces,
            "historical_seeds": [{"host": "claude", "commit": claude_seed}],
            "host_receipt": binding,
            "edit_packets": packets,
            "unmatched_edit_packet_ids": unmatched,
            "release_drift": {
                "checked_at": checked_at,
                "status": "unmatched" if unmatched else "clean",
                "snapshots": [
                    {
                        "host": snapshot["host"],
                        "inventory_commit": snapshot["inventory_commit"],
                        "current_commit": snapshot["origin_main_commit"],
                    }
                    for snapshot in snapshots
                ],
                "unmatched_edit_packet_ids": unmatched,
            },
        },
        "candidates": candidates,
    }
    if persist:
        write_ledger(
            safe_output,
            ledger,
            discovery_guard=(target_repository_path, campaign_id),
        )
    return ledger


def release_refresh(
    *,
    ledger_path: Path,
    repositories: Mapping[str, Path],
    planning_snapshots: Mapping[str, str],
    claude_seed: str,
    host_receipt: Mapping[str, Any],
    checked_at: str,
    runner: GitRunner | None = None,
) -> dict[str, Any]:
    """Prove a release refresh is byte-identical without writing the ledger."""

    try:
        before = ledger_path.read_bytes()
    except OSError as exc:
        raise LedgerError(f"could not read release ledger: {ledger_path}") from exc
    refreshed = discover(
        campaign_id=cast(str, load_ledger(ledger_path)["campaign"]["id"]),
        output=ledger_path,
        repositories=repositories,
        planning_snapshots=planning_snapshots,
        claude_seed=claude_seed,
        host_receipt=host_receipt,
        runner=runner,
        checked_at=checked_at,
        persist=False,
    )
    if _serialize_ledger(refreshed).encode("utf-8") != before:
        raise LedgerError("release refresh detected drift; ledger bytes were not changed")
    return refreshed


def _candidate_refresh_inputs_changed(
    candidate: Mapping[str, Any],
    *,
    old_campaign: Mapping[str, Any],
    new_packets: Mapping[str, Mapping[str, Any]],
    new_receipt: Mapping[str, Any],
    retained_packet_ids: Sequence[str],
) -> bool:
    old_packet_ids = cast(Sequence[str], candidate["edit_packet_ids"])
    if list(old_packet_ids) != list(retained_packet_ids):
        return True

    old_packets = {
        cast(str, packet["id"]): cast(Mapping[str, Any], packet)
        for packet in cast(Sequence[Mapping[str, Any]], old_campaign["edit_packets"])
    }
    semantic_packet_fields = ("id", "host", "path", "change", "content_sha256", "source")
    for packet_id in retained_packet_ids:
        old_packet = old_packets.get(packet_id)
        new_packet = new_packets.get(packet_id)
        if old_packet is None or new_packet is None:
            return True
        if any(old_packet.get(field) != new_packet.get(field) for field in semantic_packet_fields):
            return True

    required_capabilities = cast(Sequence[str], candidate.get("required_host_capabilities", []))
    if required_capabilities:
        old_receipt = cast(Mapping[str, Any], old_campaign.get("host_receipt", {}))
        old_states = {
            cast(str, item["capability"]): item.get("state")
            for item in cast(Sequence[Mapping[str, Any]], old_receipt.get("states", []))
            if isinstance(item.get("capability"), str)
        }
        new_states = {
            cast(str, item["capability"]): item.get("state")
            for item in cast(Sequence[Mapping[str, Any]], new_receipt.get("states", []))
            if isinstance(item.get("capability"), str)
        }
        if any(
            old_states.get(capability) != new_states.get(capability)
            for capability in required_capabilities
        ):
            return True
    return False


def _invalidate_decision_authority(candidate: dict[str, Any]) -> None:
    decision = cast(Mapping[str, Any], candidate.get("decision", {}))
    if decision.get("state") == "pending":
        return
    candidate["decision"] = {
        "state": "pending",
        "rationale": (
            "Source evidence changed during refresh; renewed operator review is required."
        ),
        "revisit_trigger": (
            "Reassess after the refreshed snapshots and semantic inputs are reviewed."
        ),
        "operator": None,
        "decided_at": None,
    }


def _display_repository(target_repository: Path, repository: Path) -> str:
    del target_repository
    name = repository.name
    errors: list[str] = []
    if _repository_path(name, "repository", errors) is None:
        raise LedgerError(errors[0])
    return name


def _sanitize_receipt_binding(receipt: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema",
        "catalog_digest",
        "agy_cli_version",
        "antigravity_host_version",
        "supported_flags",
        "runtime_roots",
        "requested_facts",
        "observed_facts",
        "results",
    }
    if set(receipt) != expected:
        raise LedgerError("host receipt does not match the promotable v1 contract")
    if receipt.get("schema") != "antigravity.capabilities.v1":
        raise LedgerError("host receipt schema is not antigravity.capabilities.v1")
    catalog_digest = receipt.get("catalog_digest")
    if not isinstance(catalog_digest, str) or SHA256_RE.fullmatch(catalog_digest) is None:
        raise LedgerError("host receipt catalog digest is invalid")
    results = receipt.get("results")
    if not isinstance(results, list):
        raise LedgerError("host receipt results must be a list")
    states: list[dict[str, str]] = []
    for item in results:
        if not isinstance(item, Mapping):
            raise LedgerError("host receipt result must be an object")
        capability = item.get("id")
        state = item.get("state")
        if (
            not isinstance(capability, str)
            or ID_RE.fullmatch(capability) is None
            or state not in RAW_CAPABILITY_STATES
        ):
            raise LedgerError("host receipt contains an invalid capability state")
        states.append({"capability": capability, "state": cast(str, state)})
    canonical = yaml.safe_dump(
        _plain_data(receipt), sort_keys=True, default_flow_style=False
    ).encode()
    return {
        "schema": "antigravity.capabilities.v1",
        "catalog_digest": catalog_digest,
        "receipt_sha256": hashlib.sha256(canonical).hexdigest(),
        "states": sorted(states, key=lambda item: item["capability"]),
    }


def _load_existing_for_refresh(path: Path, campaign_id: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    existing = load_ledger(path)
    if existing["campaign"]["id"] != campaign_id:
        raise LedgerError("existing ledger campaign ID does not match requested campaign")
    return existing


def _provenance_for(
    packet_ids: Sequence[str], packets: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, str]]:
    unique = {
        (
            cast(str, packets[packet_id]["host"]),
            cast(str, packets[packet_id]["commit"]),
            cast(str, packets[packet_id]["path"]),
        )
        for packet_id in packet_ids
    }
    return [{"host": host, "commit": commit, "path": path} for host, commit, path in sorted(unique)]


def _plain_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_data(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain_data(item) for item in value]
    return value


def write_ledger(
    path: Path | str,
    ledger: Mapping[str, Any],
    *,
    discovery_guard: tuple[Path, str] | None = None,
    compare_inputs: Mapping[Path, bytes] | None = None,
    before_replace: Callable[[], None] | None = None,
) -> None:
    """Serialize deterministically and replace the destination atomically."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if discovery_guard is not None:
        target_repository, campaign_id = discovery_guard
        target = _safe_output(target_repository, campaign_id, target)
    encoded = _serialize_ledger(ledger)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if discovery_guard is not None:
            target_repository, campaign_id = discovery_guard
            rechecked = _safe_output(target_repository, campaign_id, target)
            if rechecked != target:
                raise LedgerError("discovery output changed during atomic write")
        if before_replace is not None:
            before_replace()
        if compare_inputs is not None:
            for guarded_path, expected_bytes in compare_inputs.items():
                try:
                    current_bytes = guarded_path.read_bytes()
                except OSError as exc:
                    raise LedgerError(
                        f"atomic input changed or disappeared: {guarded_path}"
                    ) from exc
                if current_bytes != expected_bytes:
                    raise LedgerError(f"atomic input changed during validation: {guarded_path}")
        os.replace(temporary_name, target)
        temporary_name = None
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_fd = os.open(target.parent, directory_flags)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except LedgerError:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise
    except OSError as exc:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise LedgerError(f"could not write ledger atomically: {target}") from exc


def _serialize_ledger(ledger: Mapping[str, Any]) -> str:
    return yaml.safe_dump(
        _plain_data(ledger),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )


def ranking_key(candidate: Mapping[str, Any]) -> tuple[int, int, int, int, str]:
    ranking = cast(Mapping[str, int], candidate["ranking"])
    return (
        -ranking["operator_value"],
        -ranking["antigravity_fit"],
        -ranking["proof_feasibility"],
        ranking["maintenance_cost"],
        cast(str, candidate["id"]),
    )


def render_report(ledger: Mapping[str, Any]) -> str:
    """Render every candidate and the exact validation state."""

    inventory_errors = validate_ledger(ledger, inventory_only=True)
    final_errors = validate_ledger(ledger, inventory_only=False)
    campaign = cast(Mapping[str, Any], ledger["campaign"])
    lines = [
        f"Semantic port campaign: {campaign['id']}",
        f"Inventory validation: {'valid' if not inventory_errors else 'invalid'}",
        f"Final validation: {'valid' if not final_errors else 'blocked'}",
        f"Unmatched drift: {len(campaign['unmatched_edit_packet_ids'])}",
        "",
        "Advisory order only; ranking never selects or hides a candidate.",
    ]
    for candidate in sorted(cast(list[Mapping[str, Any]], ledger["candidates"]), key=ranking_key):
        packet_ids = cast(list[str], candidate["edit_packet_ids"])
        packets = {
            packet["id"]: packet
            for packet in cast(list[Mapping[str, Any]], campaign["edit_packets"])
        }
        hosts = sorted({packets[packet_id]["host"] for packet_id in packet_ids})
        ranking = cast(Mapping[str, int], candidate["ranking"])
        decision = cast(Mapping[str, Any], candidate["decision"])
        lines.extend(
            [
                "",
                f"{candidate['id']}: {candidate['title']}",
                f"  source hosts: {', '.join(cast(list[str], hosts))}",
                "  ranking: "
                f"operator-value={ranking['operator_value']} "
                f"antigravity-fit={ranking['antigravity_fit']} "
                f"proof-feasibility={ranking['proof_feasibility']} "
                f"maintenance-cost={ranking['maintenance_cost']}",
                f"  proposed disposition: {candidate['proposed_disposition']}",
                f"  Antigravity state: {candidate['antigravity_state']}",
                f"  semantic contract: {candidate['semantic_contract']}",
                "  required host capabilities: "
                + (", ".join(cast(list[str], candidate["required_host_capabilities"])) or "none"),
                f"  actual decision: {decision['state']}",
                f"  rationale: {decision['rationale']}",
                f"  revisit trigger: {decision['revisit_trigger']}",
            ]
        )
        migration = candidate.get("migration")
        if isinstance(migration, Mapping):
            lines.extend(
                [
                    f"  migration state: {migration['state']}",
                    f"  target paths: {', '.join(cast(list[str], migration['target_paths']))}",
                    "  positive tests: " + ", ".join(cast(list[str], migration["test_node_ids"])),
                    "  negative tests: "
                    + ", ".join(cast(list[str], migration["negative_test_node_ids"])),
                ]
            )
    if inventory_errors:
        lines.extend(["", "Inventory errors:"])
        lines.extend(f"- {error}" for error in inventory_errors)
    final_only = [error for error in final_errors if error not in inventory_errors]
    if final_only:
        lines.extend(["", "Final gate:"])
        lines.extend(f"- {error}" for error in final_only)
    unmatched = cast(list[str], campaign["unmatched_edit_packet_ids"])
    if unmatched:
        lines.extend(["", "Unmatched edit packets:"])
        lines.extend(f"- {packet_id}" for packet_id in unmatched)
    return "\n".join(lines) + "\n"


def record_decisions(
    ledger: Mapping[str, Any],
    decision_input: object,
    *,
    operator: str,
    decided_at: str,
) -> dict[str, Any]:
    """Apply only an exact complete operator mapping to a copied ledger."""

    root = _mapping(decision_input, "decisions", [])
    if root is None:
        raise LedgerError("decisions: expected an object keyed by every candidate ID")
    expected_ids = {
        candidate["id"] for candidate in cast(list[dict[str, Any]], ledger["candidates"])
    }
    provided_ids = set(root)
    if provided_ids != expected_ids:
        missing = sorted(expected_ids - provided_ids)
        extra = sorted(provided_ids - expected_ids)
        details = []
        if missing:
            details.append("missing " + ", ".join(cast(list[str], missing)))
        if extra:
            details.append("extra/stale " + ", ".join(extra))
        raise LedgerError(
            "decision mapping must exactly match candidate IDs: " + "; ".join(details)
        )
    if not operator.strip():
        raise LedgerError("operator identity must be non-empty")
    try:
        datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError("decision time must be ISO-8601") from exc

    updated = cast(dict[str, Any], _plain_data(ledger))
    by_id = {
        candidate["id"]: candidate
        for candidate in cast(list[dict[str, Any]], updated["candidates"])
    }
    input_errors: list[str] = []
    for candidate_id in sorted(cast(set[str], expected_ids)):
        path = f"decisions.{candidate_id}"
        value = _mapping(root[candidate_id], path, input_errors)
        if value is None:
            continue
        _closed(value, DECISION_INPUT_KEYS, path, input_errors)
        state = value.get("state")
        if state not in DECISION_STATES - {"pending"}:
            input_errors.append(f"{path}.state: expected a non-pending decision state")
        rationale = _required_string(value.get("rationale"), f"{path}.rationale", input_errors)
        trigger = _required_string(
            value.get("revisit_trigger"), f"{path}.revisit_trigger", input_errors
        )
        if state in DECISION_STATES - {"pending"} and rationale and trigger:
            semantic_decision = {
                "state": state,
                "rationale": rationale,
                "revisit_trigger": trigger,
            }
            current = cast(Mapping[str, Any], by_id[candidate_id].get("decision", {}))
            if all(current.get(key) == value for key, value in semantic_decision.items()):
                continue
            by_id[candidate_id]["decision"] = {
                **semantic_decision,
                "operator": operator,
                "decided_at": decided_at,
            }
    if input_errors:
        raise LedgerError("invalid decision mapping:\n- " + "\n- ".join(input_errors))
    errors = validate_ledger(updated, inventory_only=False)
    if errors:
        raise LedgerError("decided ledger is invalid:\n- " + "\n- ".join(errors))
    return updated


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                _plain_data(value),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LedgerError("value cannot be encoded as canonical JSON") from exc


def _canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _approved_candidates(ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        cast(str, candidate["id"]): candidate
        for candidate in cast(Sequence[Mapping[str, Any]], ledger["candidates"])
        if cast(Mapping[str, Any], candidate["decision"])["state"] == "approved-survivor"
    }


def validate_migration_plan(
    plan: object,
    ledger: Mapping[str, Any],
    *,
    require_existing_paths: bool = False,
) -> list[str]:
    """Validate the closed plan against the authoritative approved-survivor set."""

    errors: list[str] = []
    root = _mapping(plan, "migration_plan", errors)
    if root is None:
        return errors
    _closed(root, MIGRATION_PLAN_KEYS, "migration_plan", errors)
    if root.get("schema") != MIGRATION_PLAN_SCHEMA:
        errors.append(f"migration_plan.schema: expected {MIGRATION_PLAN_SCHEMA!r}")
    campaign = cast(Mapping[str, Any], ledger.get("campaign", {}))
    if root.get("campaign_id") != campaign.get("id"):
        errors.append("migration_plan.campaign_id: must match the ledger campaign")
    if root.get("ledger_schema") != SCHEMA_V2:
        errors.append(f"migration_plan.ledger_schema: expected {SCHEMA_V2!r}")
    rows = _mapping(root.get("candidates"), "migration_plan.candidates", errors)
    if rows is None:
        return errors
    approved = _approved_candidates(ledger)
    expected_ids = set(approved)
    provided_ids = set(rows)
    if provided_ids != expected_ids:
        missing = sorted(expected_ids - provided_ids)
        extra = sorted(provided_ids - expected_ids)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra/non-survivor " + ", ".join(extra))
        errors.append(
            "migration_plan.candidates: must equal the exact approved-survivor ID set"
            + (": " + "; ".join(details) if details else "")
        )
    all_nodes: list[str] = []
    for candidate_id in sorted(provided_ids):
        path = f"migration_plan.candidates.{candidate_id}"
        candidate_id_errors: list[str] = []
        _identifier(candidate_id, f"{path}.key", candidate_id_errors)
        row = _mapping(rows[candidate_id], path, candidate_id_errors)
        if row is None:
            errors.extend(candidate_id_errors)
            continue
        _closed(row, MIGRATION_PLAN_ROW_KEYS, path, candidate_id_errors)
        candidate = approved.get(candidate_id)
        semantic_contract = _required_string(
            row.get("semantic_contract"), f"{path}.semantic_contract", candidate_id_errors
        )
        if candidate is not None and semantic_contract != candidate.get("semantic_contract"):
            candidate_id_errors.append(
                f"{path}.semantic_contract: must equal the ledger contract byte-for-byte"
            )
        final_state = row.get("final_antigravity_state")
        if final_state not in MIGRATION_FINAL_STATES:
            candidate_id_errors.append(
                f"{path}.final_antigravity_state: expected one of {sorted(MIGRATION_FINAL_STATES)}"
            )
        targets = _target_path_list(
            row.get("target_paths"), f"{path}.target_paths", candidate_id_errors
        )
        positive = _test_node_list(
            row.get("test_node_ids"), f"{path}.test_node_ids", candidate_id_errors
        )
        negative = _test_node_list(
            row.get("negative_test_node_ids"),
            f"{path}.negative_test_node_ids",
            candidate_id_errors,
        )
        if len(positive) != 1 or len(negative) != 1:
            candidate_id_errors.append(
                f"{path}: exactly one positive and one negative Pytest node ID are required"
            )
        if set(positive) & set(negative):
            candidate_id_errors.append(f"{path}: positive and negative node IDs must be distinct")
        for node in positive + negative:
            if node.split("::", 1)[0] not in targets:
                candidate_id_errors.append(
                    f"{path}: every Pytest node path must be included in target_paths"
                )
            all_nodes.append(node)
        _string_list(
            row.get("intentional_differences"),
            f"{path}.intentional_differences",
            candidate_id_errors,
            nonempty=True,
        )
        if require_existing_paths:
            for target in targets:
                absolute = (REPO_ROOT / target).resolve()
                try:
                    absolute.relative_to(REPO_ROOT.resolve())
                except ValueError:
                    candidate_id_errors.append(f"{path}.target_paths: escaped repository root")
                    continue
                if not absolute.is_file():
                    candidate_id_errors.append(
                        f"{path}.target_paths: target file does not exist: {target}"
                    )
        errors.extend(candidate_id_errors)
    duplicates = sorted(node for node, count in Counter(all_nodes).items() if count > 1)
    if duplicates:
        errors.append("migration_plan.candidates: duplicate node IDs " + ", ".join(duplicates))
    return errors


def load_migration_plan(
    path: Path | str,
    ledger: Mapping[str, Any],
    *,
    require_existing_paths: bool = False,
) -> dict[str, Any]:
    parsed = _load_yaml(Path(path))
    errors = validate_migration_plan(
        parsed,
        ledger,
        require_existing_paths=require_existing_paths,
    )
    if errors:
        raise LedgerError("invalid migration plan:\n- " + "\n- ".join(errors))
    return cast(dict[str, Any], parsed)


def upgrade_v2(ledger: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    """Upgrade a fully decided v1 ledger without changing any existing field."""

    if ledger.get("schema") != SCHEMA_V1:
        raise LedgerError("upgrade-v2 accepts only a v1 ledger")
    ledger_errors = validate_ledger(ledger)
    if ledger_errors:
        raise LedgerError("v1 ledger is invalid:\n- " + "\n- ".join(ledger_errors))
    plan_errors = validate_migration_plan(plan, ledger)
    if plan_errors:
        raise LedgerError("invalid migration plan:\n- " + "\n- ".join(plan_errors))
    preserved_campaign = _canonical_json_bytes(ledger["campaign"])
    preserved_candidates = {
        cast(str, candidate["id"]): _canonical_json_bytes(candidate)
        for candidate in cast(Sequence[Mapping[str, Any]], ledger["candidates"])
    }
    updated = cast(dict[str, Any], _plain_data(ledger))
    updated["schema"] = SCHEMA_V2
    plan_rows = cast(Mapping[str, Mapping[str, Any]], plan["candidates"])
    receipt_sha256 = cast(str, updated["campaign"]["host_receipt"]["receipt_sha256"])
    host_states = {
        cast(str, row["capability"]): cast(str, row["state"])
        for row in cast(Sequence[Mapping[str, Any]], updated["campaign"]["host_receipt"]["states"])
    }
    for candidate in cast(list[dict[str, Any]], updated["candidates"]):
        candidate_id = cast(str, candidate["id"])
        if candidate_id not in plan_rows:
            continue
        row = plan_rows[candidate_id]
        blocking_capabilities = sorted(
            capability
            for capability in cast(Sequence[str], candidate["required_host_capabilities"])
            if host_states.get(capability) in {"failed", "unknown", "unavailable"}
        )
        candidate["migration"] = {
            "state": "blocked" if blocking_capabilities else "planned",
            "target_paths": list(row["target_paths"]),
            "test_node_ids": list(row["test_node_ids"]),
            "negative_test_node_ids": list(row["negative_test_node_ids"]),
            "intentional_differences": list(row["intentional_differences"]),
            "packet_set_sha256": packet_set_sha256(
                cast(Sequence[str], candidate["edit_packet_ids"])
            ),
            "host_receipt_sha256": receipt_sha256,
            "evidence_manifest_sha256": None,
            "blocking_capabilities": blocking_capabilities,
            "validated_at": None,
        }
    if _canonical_json_bytes(updated["campaign"]) != preserved_campaign:
        raise LedgerError("upgrade changed a preserved campaign subtree")
    for verified_candidate in cast(Sequence[Mapping[str, Any]], updated["candidates"]):
        preserved = {key: value for key, value in verified_candidate.items() if key != "migration"}
        if _canonical_json_bytes(preserved) != preserved_candidates[verified_candidate["id"]]:
            raise LedgerError(f"upgrade changed preserved candidate {verified_candidate['id']!r}")
    errors = validate_ledger(updated)
    if errors:
        raise LedgerError("upgraded ledger is invalid:\n- " + "\n- ".join(errors))
    return updated


def source_binding_for_ledger(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Build the deterministic source binding consumed by migration evidence."""

    campaign = cast(Mapping[str, Any], ledger["campaign"])
    snapshots = cast(Sequence[Mapping[str, Any]], campaign["snapshots"])
    snapshot_commits = {
        cast(str, row["host"]): cast(str, row["inventory_commit"])
        for row in sorted(snapshots, key=lambda item: cast(str, item["host"]))
    }
    surfaces = sorted(
        cast(Sequence[Mapping[str, Any]], campaign["selected_surfaces"]),
        key=lambda item: cast(str, item["host"]),
    )
    packets = sorted(
        (
            {
                "id": packet["id"],
                "content_sha256": packet["content_sha256"],
            }
            for packet in cast(Sequence[Mapping[str, Any]], campaign["edit_packets"])
        ),
        key=lambda item: cast(str, item["id"]),
    )
    decisions = {
        cast(str, candidate["id"]): candidate["decision"]
        for candidate in sorted(
            cast(Sequence[Mapping[str, Any]], ledger["candidates"]),
            key=lambda item: cast(str, item["id"]),
        )
    }
    decided = all(
        cast(Mapping[str, Any], decision)["state"] != "pending" for decision in decisions.values()
    )
    return {
        "snapshot_commits": snapshot_commits,
        "selected_surfaces_sha256": _canonical_json_sha256(surfaces),
        "packet_content_sha256": _canonical_json_sha256(packets),
        "decision_sha256": _canonical_json_sha256(decisions),
        "operator_gate_state": "decided" if decided else "reset",
    }


def _validate_check(value: object, path: str, errors: list[str]) -> bool:
    row = _mapping(value, path, errors)
    if row is None:
        return False
    _closed(row, CHECK_KEYS, path, errors)
    _identifier(row.get("check_id"), f"{path}.check_id", errors)
    status = row.get("status")
    if status not in {"pass", "warn", "failed", "blocked"}:
        errors.append(f"{path}.status: expected pass, warn, failed, or blocked")
    _required_string(row.get("detail"), f"{path}.detail", errors)
    return status == "pass"


def _validate_finding(value: object, path: str, errors: list[str]) -> bool:
    row = _mapping(value, path, errors)
    if row is None:
        return False
    _closed(row, FINDING_KEYS, path, errors)
    _identifier(row.get("finding_id"), f"{path}.finding_id", errors)
    if row.get("severity") not in {"P0", "P1", "P2", "P3"}:
        errors.append(f"{path}.severity: expected P0, P1, P2, or P3")
    for field in ("category", "location", "impact", "fix", "validation"):
        _required_string(row.get(field), f"{path}.{field}", errors)
    for field in ("resolved", "hard_stop"):
        if not isinstance(row.get(field), bool):
            errors.append(f"{path}.{field}: expected a boolean")
    return row.get("resolved") is True and row.get("hard_stop") is False


def _validate_result(
    value: object,
    path: str,
    assignment_id: str,
    errors: list[str],
) -> bool:
    initial_error_count = len(errors)
    row = _mapping(value, path, errors)
    if row is None:
        return False
    schema = row.get("result_schema")
    keys = REVIEWER_RESULT_KEYS if schema == "reviewer-result.v1" else RESULT_KEYS
    if "pytest_outcomes" in row:
        keys = keys | {"pytest_outcomes"}
    _closed(row, keys, path, errors)
    if schema not in {"assignment-result.v1", "reviewer-result.v1"}:
        errors.append(f"{path}.result_schema: expected assignment-result.v1 or reviewer-result.v1")
    if row.get("assignment_id") != assignment_id:
        errors.append(f"{path}.assignment_id: must match the results mapping key")
    for field in ("assignment_id", "summary"):
        _required_string(row.get(field), f"{path}.{field}", errors)
    terminal_status = row.get("terminal_status")
    if terminal_status not in {"completed", "failed", "interrupted", "blocked"}:
        errors.append(f"{path}.terminal_status: invalid terminal status")
    no_change = row.get("no_change")
    if not isinstance(no_change, bool):
        errors.append(f"{path}.no_change: expected a boolean")
    changed_paths = _string_list(
        row.get("changed_paths"),
        f"{path}.changed_paths",
        errors,
        paths=True,
    )
    if ".serena/project.yml" in changed_paths:
        errors.append(f"{path}.changed_paths: operator-owned .serena path is forbidden")
    if isinstance(no_change, bool) and no_change != (not changed_paths):
        errors.append(f"{path}: changed_paths must be empty exactly when no_change is true")
    checks_value = _sequence(row.get("checks"), f"{path}.checks", errors)
    checks_pass = checks_value is not None and bool(checks_value)
    if checks_value is not None:
        checks_pass = all(
            _validate_check(item, f"{path}.checks[{index}]", errors)
            for index, item in enumerate(checks_value)
        )
        check_ids = [
            item.get("check_id")
            for item in checks_value
            if isinstance(item, Mapping) and isinstance(item.get("check_id"), str)
        ]
        if len(check_ids) != len(set(check_ids)):
            errors.append(f"{path}.checks: duplicate check IDs")
    findings_value = _sequence(row.get("findings"), f"{path}.findings", errors)
    findings_clear = findings_value is not None
    if findings_value is not None:
        findings_clear = all(
            _validate_finding(item, f"{path}.findings[{index}]", errors)
            for index, item in enumerate(findings_value)
        )
    risks = _sequence(row.get("residual_risks"), f"{path}.residual_risks", errors)
    if risks is not None:
        for index, risk in enumerate(risks):
            _required_string(risk, f"{path}.residual_risks[{index}]", errors)
    if "pytest_outcomes" in row:
        outcomes = _sequence(row.get("pytest_outcomes"), f"{path}.pytest_outcomes", errors)
        node_ids: list[str] = []
        if outcomes is not None:
            for index, item in enumerate(outcomes):
                outcome_path = f"{path}.pytest_outcomes[{index}]"
                outcome = _mapping(item, outcome_path, errors)
                if outcome is None:
                    continue
                _closed(outcome, PYTEST_OUTCOME_KEYS, outcome_path, errors)
                node_id = _required_string(
                    outcome.get("node_id"), f"{outcome_path}.node_id", errors
                )
                if node_id is not None:
                    node_ids.append(node_id)
                if outcome.get("status") != "pass":
                    errors.append(f"{outcome_path}.status: tester evidence must pass")
        if not node_ids:
            errors.append(f"{path}.pytest_outcomes: must be non-empty")
        if len(node_ids) != len(set(node_ids)):
            errors.append(f"{path}.pytest_outcomes: duplicate node IDs")
    reviewer_pass = True
    if schema == "reviewer-result.v1":
        if row.get("verdict") not in {"accept", "needs-revision", "blocking"}:
            errors.append(f"{path}.verdict: invalid reviewer verdict")
        if not isinstance(row.get("hard_stop"), bool):
            errors.append(f"{path}.hard_stop: expected a boolean")
        reviewer_pass = row.get("verdict") == "accept" and row.get("hard_stop") is False
    return (
        terminal_status == "completed"
        and checks_pass
        and findings_clear
        and reviewer_pass
        and len(errors) == initial_error_count
    )


def _pytest_node_exists(node_id: str) -> bool:
    path_text, separator, function_name = node_id.partition("::")
    if not separator or "::" in function_name or "[" in function_name:
        return False
    source = (REPO_ROOT / path_text).resolve()
    try:
        source.relative_to(REPO_ROOT.resolve())
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, ValueError, SyntaxError, UnicodeDecodeError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
        for node in tree.body
    )


def validate_migration_evidence(
    evidence: object,
    ledger: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> list[str]:
    """Validate normalized migration evidence before any ledger transition."""

    errors: list[str] = []
    root = _mapping(evidence, "evidence", errors)
    if root is None:
        return errors
    _closed(root, EVIDENCE_KEYS, "evidence", errors)
    if root.get("schema") != MIGRATION_EVIDENCE_SCHEMA:
        errors.append(f"evidence.schema: expected {MIGRATION_EVIDENCE_SCHEMA!r}")
    campaign = cast(Mapping[str, Any], ledger["campaign"])
    if root.get("campaign_id") != campaign.get("id"):
        errors.append("evidence.campaign_id: must match the ledger campaign")
    if root.get("ledger_schema") != SCHEMA_V2:
        errors.append(f"evidence.ledger_schema: expected {SCHEMA_V2!r}")
    approved_ids = sorted(_approved_candidates(ledger))
    candidate_ids = _string_list(
        root.get("candidate_ids"), "evidence.candidate_ids", errors, identifiers=True
    )
    if candidate_ids != approved_ids:
        errors.append("evidence.candidate_ids: must be sorted and equal all approved survivors")
    source = _mapping(root.get("source_binding"), "evidence.source_binding", errors)
    if source is not None:
        _closed(source, SOURCE_BINDING_KEYS, "evidence.source_binding", errors)
        expected = source_binding_for_ledger(ledger)
        for field in (
            "snapshot_commits",
            "selected_surfaces_sha256",
            "packet_content_sha256",
            "decision_sha256",
            "operator_gate_state",
        ):
            if source.get(field) != expected[field]:
                errors.append(f"evidence.source_binding.{field}: stale or mismatched binding")
        refresh_id = _identifier(
            source.get("refresh_assignment_id"),
            "evidence.source_binding.refresh_assignment_id",
            errors,
        )
    else:
        refresh_id = None
    host = _mapping(root.get("host_binding"), "evidence.host_binding", errors)
    if host is not None:
        _closed(host, HOST_BINDING_KEYS, "evidence.host_binding", errors)
        if _plain_data(host) != _plain_data(campaign["host_receipt"]):
            errors.append("evidence.host_binding: must exactly match the sanitized host receipt")
    results = _mapping(root.get("results"), "evidence.results", errors)
    result_pass: dict[str, bool] = {}
    if results is not None:
        if not results:
            errors.append("evidence.results: at least one verification result is required")
        for assignment_id in sorted(results):
            _identifier(assignment_id, f"evidence.results.{assignment_id}.key", errors)
            result_pass[assignment_id] = _validate_result(
                results[assignment_id],
                f"evidence.results.{assignment_id}",
                assignment_id,
                errors,
            )
        for assignment_id, passed in sorted(result_pass.items()):
            if not passed:
                errors.append(f"evidence.results.{assignment_id}: verification result did not pass")
    if refresh_id is not None and (
        refresh_id not in result_pass or not result_pass.get(refresh_id, False)
    ):
        errors.append("evidence.source_binding.refresh_assignment_id: result must pass")
    candidate_evidence = _mapping(
        root.get("candidate_evidence"), "evidence.candidate_evidence", errors
    )
    if candidate_evidence is not None and set(candidate_evidence) != set(approved_ids):
        errors.append("evidence.candidate_evidence: must equal the exact approved-survivor ID set")
    plan_rows = cast(Mapping[str, Mapping[str, Any]], plan["candidates"])
    mapped_nodes = {
        node
        for row in plan_rows.values()
        for field in ("test_node_ids", "negative_test_node_ids")
        for node in cast(Sequence[str], row[field])
    }
    missing_nodes = sorted(node for node in mapped_nodes if not _pytest_node_exists(node))
    if missing_nodes:
        errors.append(
            "evidence.pytest_collection: uncollected node IDs: " + ", ".join(missing_nodes)
        )
    if candidate_evidence is not None:
        for candidate_id in sorted(candidate_evidence):
            path = f"evidence.candidate_evidence.{candidate_id}"
            row = _mapping(candidate_evidence[candidate_id], path, errors)
            if row is None:
                continue
            _closed(row, CANDIDATE_EVIDENCE_KEYS, path, errors)
            plan_row = plan_rows.get(candidate_id)
            for field in ("target_paths", "test_node_ids", "negative_test_node_ids"):
                values = (
                    _target_path_list(row.get(field), f"{path}.{field}", errors)
                    if field == "target_paths"
                    else _test_node_list(row.get(field), f"{path}.{field}", errors)
                )
                if plan_row is not None and values != list(plan_row[field]):
                    errors.append(f"{path}.{field}: must exactly match the migration plan")
            result_ids = _string_list(
                row.get("owning_result_ids"),
                f"{path}.owning_result_ids",
                errors,
                identifiers=True,
                nonempty=True,
            )
            for result_id in result_ids:
                if result_id not in result_pass or not result_pass[result_id]:
                    errors.append(f"{path}.owning_result_ids: result {result_id!r} did not pass")
            reviewed_value = row.get("reviewed_unchanged_paths")
            reviewed_unchanged = (
                []
                if reviewed_value == []
                else _target_path_list(
                    reviewed_value,
                    f"{path}.reviewed_unchanged_paths",
                    errors,
                )
            )
            target_paths = set(cast(Sequence[str], plan_row["target_paths"] if plan_row else ()))
            if set(reviewed_unchanged) - target_paths:
                errors.append(f"{path}.reviewed_unchanged_paths: contains a non-target path")
            outcomes = _sequence(row.get("pytest_outcomes"), f"{path}.pytest_outcomes", errors)
            observed: dict[str, str] = {}
            if outcomes is not None:
                for index, item in enumerate(outcomes):
                    outcome_path = f"{path}.pytest_outcomes[{index}]"
                    outcome = _mapping(item, outcome_path, errors)
                    if outcome is None:
                        continue
                    _closed(outcome, PYTEST_OUTCOME_KEYS, outcome_path, errors)
                    node_id = _required_string(
                        outcome.get("node_id"), f"{outcome_path}.node_id", errors
                    )
                    status = outcome.get("status")
                    if status not in {"pass", "failed", "skipped"}:
                        errors.append(f"{outcome_path}.status: expected pass, failed, or skipped")
                    if node_id is not None:
                        if node_id in observed:
                            errors.append(f"{outcome_path}.node_id: duplicate outcome")
                        elif isinstance(status, str):
                            observed[node_id] = status
            expected_nodes = (
                list(plan_row["test_node_ids"]) + list(plan_row["negative_test_node_ids"])
                if plan_row is not None
                else []
            )
            if set(observed) != set(expected_nodes):
                errors.append(f"{path}.pytest_outcomes: must cover the exact mapped node set")
            if any(status != "pass" for status in observed.values()):
                errors.append(f"{path}.pytest_outcomes: every mapped node must pass")
    manifest_digest = _sha(
        root.get("manifest_sha256"),
        "evidence.manifest_sha256",
        errors,
        SHA256_RE,
    )
    without_digest = {key: value for key, value in root.items() if key != "manifest_sha256"}
    expected_digest = _canonical_json_sha256(without_digest)
    if manifest_digest is not None and manifest_digest != expected_digest:
        errors.append("evidence.manifest_sha256: does not match canonical manifest content")
    return errors


def load_migration_evidence(
    path: Path | str,
    ledger: Mapping[str, Any],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise LedgerError(f"could not load migration evidence: {source}") from exc
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise LedgerError("migration evidence exceeds the size limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise LedgerError("migration evidence may not contain a byte-order mark")
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"could not parse migration evidence: {source}") from exc
    if raw != _canonical_json_bytes(parsed):
        raise LedgerError("migration evidence must use exact canonical JSON bytes")
    errors = validate_migration_evidence(parsed, ledger, plan)
    if errors:
        raise LedgerError("invalid migration evidence:\n- " + "\n- ".join(errors))
    return cast(dict[str, Any], parsed)


def _migration_preservation_errors(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    migrated_ids: set[str],
) -> list[str]:
    """Ensure recording changes migration state, not its source authority."""

    errors: list[str] = []
    before_root = {key: value for key, value in before.items() if key != "candidates"}
    after_root = {key: value for key, value in after.items() if key != "candidates"}
    if _plain_data(before_root) != _plain_data(after_root):
        errors.append("record-migrations changed top-level ledger authority")
    before_rows = cast(Sequence[Mapping[str, Any]], before["candidates"])
    after_rows = cast(Sequence[Mapping[str, Any]], after["candidates"])
    before_ids = [cast(str, row["id"]) for row in before_rows]
    after_ids = [cast(str, row["id"]) for row in after_rows]
    if before_ids != after_ids:
        errors.append("record-migrations changed candidate order")
    before_candidates = {cast(str, row["id"]): row for row in before_rows}
    after_candidates = {cast(str, row["id"]): row for row in after_rows}
    if set(before_candidates) != set(after_candidates):
        errors.append("record-migrations changed the candidate inventory")
        return errors
    for candidate_id in sorted(before_candidates):
        original = before_candidates[candidate_id]
        recorded = after_candidates[candidate_id]
        if candidate_id not in migrated_ids:
            if _plain_data(original) != _plain_data(recorded):
                errors.append(f"candidate {candidate_id!r}: non-migration candidate changed")
            continue
        protected_original = {
            key: value
            for key, value in original.items()
            if key not in {"migration", "antigravity_state"}
        }
        protected_recorded = {
            key: value
            for key, value in recorded.items()
            if key not in {"migration", "antigravity_state"}
        }
        if _plain_data(protected_original) != _plain_data(protected_recorded):
            errors.append(f"candidate {candidate_id!r}: source decision or packet authority changed")
    return errors


def record_migrations(
    ledger: Mapping[str, Any],
    plan: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    validated_at: str,
) -> dict[str, Any]:
    """Atomically prepare the all-survivor migration transition."""

    ledger_errors = validate_ledger(ledger)
    if ledger.get("schema") != SCHEMA_V2:
        ledger_errors.append("record-migrations requires a v2 ledger")
    if ledger_errors:
        raise LedgerError("migration ledger is invalid:\n- " + "\n- ".join(ledger_errors))
    try:
        datetime.fromisoformat(validated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError("migration validation time must be ISO-8601") from exc
    plan_errors = validate_migration_plan(plan, ledger, require_existing_paths=True)
    if plan_errors:
        raise LedgerError("invalid migration plan:\n- " + "\n- ".join(plan_errors))
    plan_rows = cast(Mapping[str, Mapping[str, Any]], plan["candidates"])
    migration_binding_errors: list[str] = []
    for candidate_id, candidate in sorted(_approved_candidates(ledger).items()):
        migration = cast(Mapping[str, Any], candidate["migration"])
        plan_row = plan_rows[candidate_id]
        if migration.get("state") != "planned":
            migration_binding_errors.append(
                f"candidate {candidate_id!r}: migration recording requires planned state"
            )
        for migration_field, plan_field in (
            ("target_paths", "target_paths"),
            ("test_node_ids", "test_node_ids"),
            ("negative_test_node_ids", "negative_test_node_ids"),
            ("intentional_differences", "intentional_differences"),
        ):
            if migration.get(migration_field) != plan_row.get(plan_field):
                migration_binding_errors.append(
                    f"candidate {candidate_id!r}: {migration_field} no longer matches the "
                    "upgraded ledger"
                )
    if migration_binding_errors:
        raise LedgerError(
            "migration plan changed after upgrade:\n- " + "\n- ".join(migration_binding_errors)
        )
    evidence_errors = validate_migration_evidence(evidence, ledger, plan)
    if evidence_errors:
        raise LedgerError("invalid migration evidence:\n- " + "\n- ".join(evidence_errors))
    updated = cast(dict[str, Any], _plain_data(ledger))
    manifest_digest = cast(str, evidence["manifest_sha256"])
    for candidate in cast(list[dict[str, Any]], updated["candidates"]):
        candidate_id = cast(str, candidate["id"])
        if candidate_id not in plan_rows:
            continue
        migration = cast(dict[str, Any], candidate["migration"])
        migration["state"] = "migrated"
        migration["evidence_manifest_sha256"] = manifest_digest
        migration["blocking_capabilities"] = []
        migration["validated_at"] = validated_at
        candidate["antigravity_state"] = plan_rows[candidate_id]["final_antigravity_state"]
    preservation_errors = _migration_preservation_errors(ledger, updated, set(plan_rows))
    if preservation_errors:
        raise LedgerError(
            "migration recording changed protected ledger data:\n- "
            + "\n- ".join(preservation_errors)
        )
    errors = validate_ledger(updated, require_migrated=True)
    if errors:
        raise LedgerError("recorded migration ledger is invalid:\n- " + "\n- ".join(errors))
    return updated


def migration_plan_nodes(plan: object, *, partition: str = "all") -> list[str]:
    """Return deterministic plan node arguments without reading a ledger."""

    errors: list[str] = []
    root = _mapping(plan, "migration_plan", errors)
    if root is None:
        raise LedgerError("invalid migration plan:\n- " + "\n- ".join(errors))
    _closed(root, MIGRATION_PLAN_KEYS, "migration_plan", errors)
    if root.get("schema") != MIGRATION_PLAN_SCHEMA:
        errors.append(f"migration_plan.schema: expected {MIGRATION_PLAN_SCHEMA!r}")
    if root.get("ledger_schema") != SCHEMA_V2:
        errors.append(f"migration_plan.ledger_schema: expected {SCHEMA_V2!r}")
    _required_string(root.get("campaign_id"), "migration_plan.campaign_id", errors)
    rows = _mapping(root.get("candidates"), "migration_plan.candidates", errors)
    nodes: list[str] = []
    if rows is not None:
        for candidate_id in sorted(rows):
            path = f"migration_plan.candidates.{candidate_id}"
            _identifier(candidate_id, f"{path}.key", errors)
            row = _mapping(rows[candidate_id], path, errors)
            if row is None:
                continue
            _closed(row, MIGRATION_PLAN_ROW_KEYS, path, errors)
            nodes.extend(_test_node_list(row.get("test_node_ids"), f"{path}.test_node_ids", errors))
            nodes.extend(
                _test_node_list(
                    row.get("negative_test_node_ids"),
                    f"{path}.negative_test_node_ids",
                    errors,
                )
            )
    duplicates = sorted(node for node, count in Counter(nodes).items() if count > 1)
    if duplicates:
        errors.append("migration_plan.candidates: duplicate node IDs " + ", ".join(duplicates))
    if errors:
        raise LedgerError("invalid migration plan:\n- " + "\n- ".join(errors))
    if partition == "git":
        return [node for node in nodes if node in GIT_BEARING_NODES]
    if partition == "non-git":
        return [node for node in nodes if node not in GIT_BEARING_NODES]
    return nodes


def _load_yaml(path: Path) -> object:
    try:
        return _strict_yaml_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise LedgerError(f"could not load YAML input: {path}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate the closed ledger contract")
    validate.add_argument("--inventory-only", action="store_true")
    validate.add_argument("--require-migrated", action="store_true")
    validate.add_argument("ledger", type=Path)

    report = commands.add_parser("report", help="render the complete advisory decision surface")
    report.add_argument("ledger", type=Path)

    decisions = commands.add_parser(
        "record-decisions", help="record one complete operator-provided mapping"
    )
    decisions.add_argument("ledger", type=Path)
    decisions.add_argument("mapping", type=Path)
    decisions.add_argument("--operator", required=True)
    decisions.add_argument("--decided-at", required=True)

    upgrade = commands.add_parser(
        "upgrade-v2", help="atomically upgrade one fully decided v1 ledger"
    )
    upgrade.add_argument("ledger", type=Path)
    upgrade.add_argument("migration_plan", type=Path)

    migrations = commands.add_parser(
        "record-migrations", help="atomically record exact typed migration evidence"
    )
    migrations.add_argument("ledger", type=Path)
    migrations.add_argument("migration_plan", type=Path)
    migrations.add_argument("evidence", type=Path)
    migrations.add_argument("--validated-at", required=True)

    test_nodes = commands.add_parser("test-nodes", help="print exact mapped Pytest node IDs")
    test_nodes.add_argument("migration_plan", type=Path)

    pytest_args = commands.add_parser(
        "pytest-args", help="print mapped Pytest nodes for a declared execution partition"
    )
    pytest_args.add_argument("migration_plan", type=Path)
    pytest_args.add_argument(
        "--partition",
        choices=("all", "git", "non-git"),
        default="all",
    )

    discover_command = commands.add_parser(
        "discover", help="read pinned repositories and refresh candidate inputs"
    )
    discover_command.add_argument("--campaign-id", required=True)
    discover_command.add_argument("--output", type=Path, required=True)
    discover_command.add_argument(
        "--claude-repo", type=Path, default=REPO_ROOT.parent / "infiquetra-claude-plugins"
    )
    discover_command.add_argument(
        "--codex-repo", type=Path, default=REPO_ROOT.parent / "infiquetra-codex-plugins"
    )
    discover_command.add_argument("--antigravity-repo", type=Path, default=REPO_ROOT)
    discover_command.add_argument("--claude-seed", required=True)
    discover_command.add_argument("--claude-planning-snapshot", required=True)
    discover_command.add_argument("--codex-planning-snapshot", required=True)
    discover_command.add_argument("--antigravity-planning-snapshot", required=True)
    discover_command.add_argument("--host-receipt", type=Path, required=True)
    discover_command.add_argument("--checked-at", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            parsed = _load_yaml(args.ledger)
            errors = validate_ledger(
                parsed,
                inventory_only=args.inventory_only,
                require_migrated=args.require_migrated,
            )
            if errors:
                print("Ledger validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            print(
                "Ledger inventory is complete; operator decisions remain permitted."
                if args.inventory_only
                else "Ledger is complete and fully decided."
            )
            return 0
        if args.command == "report":
            parsed = _load_yaml(args.ledger)
            print(render_report(cast(Mapping[str, Any], parsed)), end="")
            return 0
        if args.command == "record-decisions":
            ledger = load_ledger(args.ledger)
            mapping = _load_yaml(args.mapping)
            updated = record_decisions(
                ledger,
                mapping,
                operator=args.operator,
                decided_at=args.decided_at,
            )
            write_ledger(args.ledger, updated)
            print(f"Recorded complete decisions in {args.ledger}")
            return 0
        if args.command == "upgrade-v2":
            ledger = load_ledger(args.ledger)
            plan = load_migration_plan(args.migration_plan, ledger)
            updated = upgrade_v2(ledger, plan)
            write_ledger(args.ledger, updated)
            print(f"Upgraded semantic-port ledger to v2 at {args.ledger}")
            return 0
        if args.command == "record-migrations":
            guarded_inputs = {
                args.ledger: args.ledger.read_bytes(),
                args.migration_plan: args.migration_plan.read_bytes(),
                args.evidence: args.evidence.read_bytes(),
            }
            ledger = load_ledger(args.ledger)
            plan = load_migration_plan(
                args.migration_plan,
                ledger,
                require_existing_paths=True,
            )
            evidence = load_migration_evidence(args.evidence, ledger, plan)
            updated = record_migrations(
                ledger,
                plan,
                evidence,
                validated_at=args.validated_at,
            )
            write_ledger(args.ledger, updated, compare_inputs=guarded_inputs)
            print(f"Recorded complete migration evidence in {args.ledger}")
            return 0
        if args.command in {"test-nodes", "pytest-args"}:
            raw_plan = _load_yaml(args.migration_plan)
            partition = args.partition if args.command == "pytest-args" else "all"
            print("\n".join(migration_plan_nodes(raw_plan, partition=partition)))
            return 0
        if args.command == "discover":
            receipt = _load_yaml(args.host_receipt)
            if not isinstance(receipt, Mapping):
                raise LedgerError("host receipt must be an object")
            discover(
                campaign_id=args.campaign_id,
                output=args.output,
                repositories={
                    "claude": args.claude_repo,
                    "codex": args.codex_repo,
                    "antigravity": args.antigravity_repo,
                },
                planning_snapshots={
                    "claude": args.claude_planning_snapshot,
                    "codex": args.codex_planning_snapshot,
                    "antigravity": args.antigravity_planning_snapshot,
                },
                claude_seed=args.claude_seed,
                host_receipt=cast(Mapping[str, Any], receipt),
                checked_at=args.checked_at,
            )
            print(f"Refreshed discovery ledger at {args.output}")
            return 0
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    sys.exit(main())
