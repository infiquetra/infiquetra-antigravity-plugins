#!/usr/bin/env python3
"""Strict semantic-port ledger and read-only discovery commands."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, cast

import yaml
from yaml.nodes import MappingNode

SCHEMA = "antigravity.semantic-port-ledger.v1"
REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_LEDGER_BYTES = 8 * 1024 * 1024
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
PACKET_KEYS = frozenset(
    {"id", "host", "commit", "path", "change", "content_sha256", "source"}
)
RELEASE_DRIFT_KEYS = frozenset(
    {"checked_at", "status", "snapshots", "unmatched_edit_packet_ids"}
)
DRIFT_SNAPSHOT_KEYS = frozenset({"host", "inventory_commit", "current_commit"})
CANDIDATE_KEYS = frozenset(
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
PROVENANCE_KEYS = frozenset({"host", "commit", "path"})
RANKING_KEYS = frozenset(
    {"operator_value", "antigravity_fit", "proof_feasibility", "maintenance_cost"}
)
DECISION_KEYS = frozenset(
    {"state", "rationale", "revisit_trigger", "operator", "decided_at"}
)
DECISION_INPUT_KEYS = frozenset({"state", "rationale", "revisit_trigger"})

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
        if len(arguments) != 2 or arguments[1] not in {
            "HEAD",
            "refs/remotes/origin/main",
        } and not arguments[1].endswith("^{commit}"):
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


def _closed(value: Mapping[str, Any], allowed: frozenset[str], path: str, errors: list[str]) -> None:
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


def validate_ledger(ledger: object, *, inventory_only: bool = False) -> list[str]:
    """Return every actionable contract violation in deterministic order."""

    errors: list[str] = []
    root = _mapping(ledger, "ledger", errors)
    if root is None:
        return errors
    _closed(root, TOP_KEYS, "ledger", errors)
    if root.get("schema") != SCHEMA:
        errors.append(f"ledger.schema: expected {SCHEMA!r}")

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

    candidates = _validate_candidates(root.get("candidates"), packets_by_id, host_states, errors)
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


def _validate_snapshots(
    value: object, errors: list[str]
) -> dict[str, Mapping[str, Any]]:
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
                errors.append(
                    f"{path}: Antigravity inventory_commit must equal local origin/main"
                )
        else:
            if row.get("inventory_commit") != row.get("head_commit"):
                errors.append(f"{path}: inventory_commit must equal head_commit")
            if row.get("head_commit") != row.get("origin_main_commit"):
                errors.append(f"{path}: HEAD and local origin/main differ; discovery must stop")
    if seen != HOSTS:
        errors.append("ledger.campaign.snapshots: must contain Claude, Codex, and Antigravity")
    return snapshots


def _validate_surfaces(
    value: object, errors: list[str]
) -> dict[str, Mapping[str, Any]]:
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
    _sha(receipt.get("receipt_sha256"), f"{path}.receipt_sha256", errors, SHA256_RE)
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
                errors.append(
                    f"{path}.commit: must match the {host} inventory snapshot"
                )
            surface = surfaces.get(host)
            surface_paths = (
                cast(Sequence[Any], surface.get("paths", []))
                if surface is not None
                else ()
            )
            if packet_path is not None and not any(
                isinstance(surface_path, str)
                and _path_is_within_surface(packet_path, surface_path)
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
                errors.append(
                    f"{path}.id: must equal deterministic packet ID {expected_id!r}"
                )
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
        errors.append("ledger.campaign.edit_packets: complete current-tree packets require all hosts")
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
                    errors.append(
                        f"{row_path}.inventory_commit: must match the campaign inventory"
                    )
                if row.get("current_commit") != snapshot.get("origin_main_commit"):
                    errors.append(
                        f"{row_path}.current_commit: must match local origin/main"
                    )
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
        _closed(row, CANDIDATE_KEYS, path, errors)
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
        _string_list(
            row.get("adjacent_dependencies"), f"{path}.adjacent_dependencies", errors
        )
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
        if blocked_caps and (
            antigravity_state != "blocked-by-host" or proposed != "blocked"
        ):
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
        _validate_decision(row.get("decision"), path, errors)
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


def _validate_decision(value: object, candidate_path: str, errors: list[str]) -> None:
    path = f"{candidate_path}.decision"
    decision = _mapping(value, path, errors)
    if decision is None:
        return
    _closed(decision, DECISION_KEYS, path, errors)
    state = decision.get("state")
    if state not in DECISION_STATES:
        errors.append(f"{path}.state: expected one of {sorted(DECISION_STATES)}")
    rationale = _required_string(
        decision.get("rationale"), f"{path}.rationale", errors
    )
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


def _packet_id(host: str, source: str, path: str, change: str) -> str:
    digest = hashlib.sha256(f"{host}\0{source}\0{path}\0{change}".encode()).hexdigest()[:20]
    return f"edit-{host}-{digest}"


def _content_at(
    runner: GitRunner, repository: Path, commit: str, path: str
) -> bytes:
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
    if (
        lexical_output != lexical_campaign
        and lexical_campaign not in lexical_output.parents
    ):
        raise LedgerError(
            f"discovery output must remain beneath docs/ports/{campaign_id}/"
        )
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
        origin_main = _resolve_commit(
            effective_runner, repository, "refs/remotes/origin/main"
        )
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

    packets.sort(key=lambda item: item["id"])
    existing = _load_existing_for_refresh(safe_output, campaign_id)
    candidates = cast(list[dict[str, Any]], existing.get("candidates", [])) if existing else []
    packet_by_id = {packet["id"]: packet for packet in packets}
    old_campaign = (
        cast(Mapping[str, Any], existing["campaign"]) if existing is not None else None
    )
    new_surfaces = [
        {
            "host": host,
            "repository": _display_repository(
                target_repository, resolved_repositories[host]
            ),
            "paths": list(DEFAULT_SURFACES[host]),
        }
        for host in sorted(HOSTS)
    ]
    binding = _sanitize_receipt_binding(host_receipt)
    for candidate in candidates:
        original_packet_ids = list(cast(list[str], candidate["edit_packet_ids"]))
        retained = [
            packet_id
            for packet_id in original_packet_ids
            if packet_id in packet_by_id
        ]
        evidence_changed = (
            old_campaign is not None
            and _candidate_refresh_inputs_changed(
                candidate,
                old_campaign=old_campaign,
                new_snapshots=snapshots,
                new_surfaces=new_surfaces,
                new_packets=packet_by_id,
                new_receipt=binding,
                retained_packet_ids=retained,
            )
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
        "schema": SCHEMA,
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
    write_ledger(
        safe_output,
        ledger,
        discovery_guard=(target_repository_path, campaign_id),
    )
    return ledger


def _rows_by_host(value: object) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return {}
    return {
        cast(str, row["host"]): cast(Mapping[str, Any], row)
        for row in value
        if isinstance(row, Mapping) and isinstance(row.get("host"), str)
    }


def _candidate_refresh_inputs_changed(
    candidate: Mapping[str, Any],
    *,
    old_campaign: Mapping[str, Any],
    new_snapshots: Sequence[Mapping[str, Any]],
    new_surfaces: Sequence[Mapping[str, Any]],
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
    if any(
        old_packets.get(packet_id) != new_packets.get(packet_id)
        for packet_id in retained_packet_ids
    ):
        return True

    affected_hosts = {
        cast(str, packet["host"])
        for packet_id in retained_packet_ids
        if (packet := old_packets.get(packet_id)) is not None
    }
    old_snapshot_by_host = _rows_by_host(old_campaign.get("snapshots"))
    new_snapshot_by_host = _rows_by_host(new_snapshots)
    old_surface_by_host = _rows_by_host(old_campaign.get("selected_surfaces"))
    new_surface_by_host = _rows_by_host(new_surfaces)
    if any(
        old_snapshot_by_host.get(host) != new_snapshot_by_host.get(host)
        or old_surface_by_host.get(host) != new_surface_by_host.get(host)
        for host in affected_hosts
    ):
        return True

    required_capabilities = cast(
        Sequence[str], candidate.get("required_host_capabilities", [])
    )
    if required_capabilities:
        old_receipt = cast(Mapping[str, Any], old_campaign.get("host_receipt", {}))
        if old_receipt != new_receipt:
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
    return [
        {"host": host, "commit": commit, "path": path}
        for host, commit, path in sorted(unique)
    ]


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
) -> None:
    """Serialize deterministically and replace the destination atomically."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if discovery_guard is not None:
        target_repository, campaign_id = discovery_guard
        target = _safe_output(target_repository, campaign_id, target)
    encoded = yaml.safe_dump(
        _plain_data(ledger),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
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
        os.replace(temporary_name, target)
    except LedgerError:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise
    except OSError as exc:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
        raise LedgerError(f"could not write ledger atomically: {target}") from exc


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
                + (
                    ", ".join(
                        cast(list[str], candidate["required_host_capabilities"])
                    )
                    or "none"
                ),
                f"  actual decision: {decision['state']}",
                f"  rationale: {decision['rationale']}",
                f"  revisit trigger: {decision['revisit_trigger']}",
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
    expected_ids = {candidate["id"] for candidate in cast(list[dict[str, Any]], ledger["candidates"])}
    provided_ids = set(root)
    if provided_ids != expected_ids:
        missing = sorted(expected_ids - provided_ids)
        extra = sorted(provided_ids - expected_ids)
        details = []
        if missing:
            details.append("missing " + ", ".join(cast(list[str], missing)))
        if extra:
            details.append("extra/stale " + ", ".join(extra))
        raise LedgerError("decision mapping must exactly match candidate IDs: " + "; ".join(details))
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
            by_id[candidate_id]["decision"] = {
                "state": state,
                "rationale": rationale,
                "revisit_trigger": trigger,
                "operator": operator,
                "decided_at": decided_at,
            }
    if input_errors:
        raise LedgerError("invalid decision mapping:\n- " + "\n- ".join(input_errors))
    errors = validate_ledger(updated, inventory_only=False)
    if errors:
        raise LedgerError("decided ledger is invalid:\n- " + "\n- ".join(errors))
    return updated


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
            errors = validate_ledger(parsed, inventory_only=args.inventory_only)
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
