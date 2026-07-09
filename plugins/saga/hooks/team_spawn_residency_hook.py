#!/usr/bin/env python3
"""
PreToolUse hook: warn-first team-spawn residency guard.

Fires when the orchestrator spawns a team-execution reviewer or tester
(``Agent`` in this harness, ``Task`` on stock Claude Code) without the
named-persistent-teammate shape S-1 (#275) mandates. Emits a single-line
``additionalContext`` advisory pointing at the fix; never blocks, denies, or
mutates the spawn. Advisory-only: it observes the residency protocol, it
does not enforce it (issue #289).

Properties:
  - SILENT ON PASS: named spawns, non-team-family spawns, and spawns outside
    the trigger set produce no output.
  - NEVER BLOCKING: always exits 0.
  - REGISTRY-DRIVEN: the trigger set is parsed fresh from
    reviewer-registry.md / validator-registry.md on every invocation — no
    materialized manifest to drift (R4).
  - CROSS-LAYOUT-SAFE: resolves the registries' directory across dev-repo,
    versioned-cache-install, and project-root layouts; degrades silently
    when none resolve (D5).

Exit codes:
  0 — always (warn-only; never blocks a spawn).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from pathlib import Path

_REVIEWER_REGISTRY = "reviewer-registry.md"
_VALIDATOR_REGISTRY = "validator-registry.md"
_TEAM_EXECUTION_REFERENCES = Path("skills") / "team-execution" / "references"
_INSTALLED_PLUGINS_FILENAME = "installed_plugins.json"

_TEAM_TOOL_NAMES = {"invoke_subagent"}
_INCLUDE_ENV = "TEAM_SPAWN_GUARD_INCLUDE"
_EXCLUDE_ENV = "TEAM_SPAWN_GUARD_EXCLUDE"
_MAX_ANCESTOR_LEVELS = 10

_BACKTICK_TOKEN_RE = re.compile(r"`([a-z0-9-]+)`")
_REVIEWER_TOKEN_RE = re.compile(r"^[a-z0-9-]+-reviewer$")


# ---------------------------------------------------------------------------
# Registry parsing (KTD4, R3, R4)
# ---------------------------------------------------------------------------


def _table_row_tokens(text: str) -> list[str]:
    """Backticked tokens on markdown table rows (lines starting with '|')."""
    tokens: list[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        tokens.extend(_BACKTICK_TOKEN_RE.findall(line))
    return tokens


def _reviewer_names(text: str) -> set[str]:
    """Reviewer agent names: backticked `<name>-reviewer` tokens on any table row.

    The whole-token match naturally excludes the "Agent File" column's
    ``agents/<name>-reviewer.md`` values (extra `/` and `.md` break the
    `[a-z0-9-]+` match) and the "Adding a New Reviewer" section's literal
    ``<name>-reviewer`` template (not a table row and not a bare token).
    """
    return {tok for tok in _table_row_tokens(text) if _REVIEWER_TOKEN_RE.match(tok)}


def _tester_names(text: str) -> set[str]:
    """Tester agent names: backticked tokens on table rows within '## Testers' only.

    validator-registry.md also lists scanners/monitors/deploy-watcher/advisory
    roles under sibling sections — section-scoping (not a suffix filter) is
    what excludes them (R3).
    """
    names: set[str] = set()
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped == "## Testers"
            continue
        if not in_section or not line.lstrip().startswith("|"):
            continue
        names.update(_BACKTICK_TOKEN_RE.findall(line))
    return names


def load_trigger_set(references_dir: Path) -> frozenset[str]:
    """Parse the reviewer + tester registries into the team-spawn trigger set.

    A missing or unreadable registry file contributes nothing rather than
    raising (R10) — the hook degrades to a smaller (or empty) trigger set,
    never to an error.
    """
    names: set[str] = set()

    with contextlib.suppress(OSError, UnicodeDecodeError):
        names |= _reviewer_names((references_dir / _REVIEWER_REGISTRY).read_text(encoding="utf-8"))

    with contextlib.suppress(OSError, UnicodeDecodeError):
        names |= _tester_names((references_dir / _VALIDATOR_REGISTRY).read_text(encoding="utf-8"))

    return frozenset(names)


# ---------------------------------------------------------------------------
# Registry-directory resolution (KTD3 — four-step chain, first hit wins)
# ---------------------------------------------------------------------------


def _semver_key(path: Path) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in path.name.split("."))
    except ValueError:
        return (-1,)


def _versioned_cache_dir(plugin_root: Path, plugin_name: str, ref_path: Path) -> Path | None:
    """Resolve a plugin's references dir under a versioned-cache install (step 2).

    Only applies when ``plugin_root`` looks like
    ``.../cache/<marketplace>/<plugin>/<version>``. Reads the active
    ``installPath`` from ``installed_plugins.json`` (authoritative); falls
    back to a max-semver glob only when that registry is absent, unreadable,
    or has no ``<plugin>@*`` key (last-resort heuristic, D4).
    """
    parents = plugin_root.parents
    if len(parents) < 4 or parents[2].name != "cache":
        return None

    marketplace_dir = parents[1]
    marketplace = marketplace_dir.name
    installed_json = parents[3] / _INSTALLED_PLUGINS_FILENAME

    try:
        data = json.loads(installed_json.read_text(encoding="utf-8"))
        entries = data.get("plugins", {})
        candidates = entries.get(f"{plugin_name}@{marketplace}") or next(
            (v for k, v in entries.items() if k.startswith(f"{plugin_name}@") and v),
            None,
        )
        if candidates:
            install_path = Path(candidates[0]["installPath"])
            resolved = install_path / ref_path
            if resolved.is_dir():
                return resolved
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        pass

    team_execution_root = marketplace_dir / plugin_name
    try:
        version_dirs = [p for p in team_execution_root.iterdir() if p.is_dir()]
    except OSError:
        return None
    if not version_dirs:
        return None

    resolved = max(version_dirs, key=_semver_key) / ref_path
    return resolved if resolved.is_dir() else None


def _find_references_dir(cwd: str | None) -> Path | None:
    """Resolve team-execution / multi-agent-consensus references dir across dev-repo / installed / project layouts.

    First hit wins (KTD3): plugin-root sibling (dev repo) -> versioned-cache
    lookup -> CLAUDE_PROJECT_DIR -> bounded ancestor scan from cwd. Returns
    None when nothing resolves (R10/D5) — never raises.
    """
    plugin_roots = [
        os.environ.get(env)
        for env in ("CLAUDE_PLUGIN_ROOT", "GEMINI_PLUGIN_ROOT", "ANTIGRAVITY_PLUGIN_ROOT")
    ]
    for plugin_root_str in plugin_roots:
        if not plugin_root_str:
            continue
        plugin_root = Path(plugin_root_str)

        for name in ("multi-agent-consensus", "team-execution"):
            ref_path = Path("skills") / name / "references"
            dev_sibling = plugin_root.parent / name / ref_path
            if dev_sibling.is_dir():
                return dev_sibling

            cache_hit = _versioned_cache_dir(plugin_root, name, ref_path)
            if cache_hit is not None:
                return cache_hit

    project_dirs = [
        os.environ.get(env)
        for env in ("CLAUDE_PROJECT_DIR", "GEMINI_PROJECT_DIR", "ANTIGRAVITY_PROJECT_DIR")
    ]
    for project_dir in project_dirs:
        if not project_dir:
            continue
        for name in ("multi-agent-consensus", "team-execution"):
            ref_path = Path("skills") / name / "references"
            project_candidate = Path(project_dir) / "plugins" / name / ref_path
            if project_candidate.is_dir():
                return project_candidate

    current = Path(cwd) if isinstance(cwd, str) and cwd else Path.cwd()
    for _ in range(_MAX_ANCESTOR_LEVELS):
        for name in ("multi-agent-consensus", "team-execution"):
            ref_path = Path("skills") / name / "references"
            candidate = current / "plugins" / name / ref_path
            if candidate.is_dir():
                return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


# ---------------------------------------------------------------------------
# Decision (KTD1, KTD2, KTD5, R2, R5, R7, R8)
# ---------------------------------------------------------------------------


def _normalize_subagent_type(raw: str) -> str:
    """Strip an optional leading '<plugin>:' prefix (live spawns use the prefixed form)."""
    return raw.rsplit(":", 1)[-1]


def _effective_trigger_set(trigger_set: frozenset[str]) -> frozenset[str]:
    names = set(trigger_set)
    include = os.environ.get(_INCLUDE_ENV, "")
    exclude = os.environ.get(_EXCLUDE_ENV, "")
    if include:
        names |= {tok.strip() for tok in include.split(",") if tok.strip()}
    if exclude:
        names -= {tok.strip() for tok in exclude.split(",") if tok.strip()}
    return frozenset(names)


def decide(tool_input: dict, trigger_set: frozenset[str]) -> str | None:
    """Pure predicate: an advisory string on a nameless team-family spawn, else None.

    Warns iff the normalized name/type is in the (env-adjusted)
    trigger set AND ``name`` is missing, empty, or not a string.
    """
    subagents = tool_input.get("Subagents", [])
    if not isinstance(subagents, list):
        return None

    for subagent in subagents:
        if not isinstance(subagent, dict):
            continue
        subagent_type = subagent.get("TypeName")
        role = subagent.get("Role")

        matched_name = None

        if isinstance(subagent_type, str) and subagent_type:
            bare_name = _normalize_subagent_type(subagent_type)
            if bare_name in _effective_trigger_set(trigger_set):
                matched_name = subagent_type

        # Also check Role (e.g. for self-spawns where Role holds the persona)
        if matched_name is None and isinstance(role, str) and role:
            # Normalize Role to lower-hyphen to match registry (e.g., "Security Reviewer" -> "security-reviewer")
            normalized_role = role.strip().lower().replace(" ", "-").replace("_", "-")
            if normalized_role in _effective_trigger_set(trigger_set):
                matched_name = role

        if matched_name is None:
            continue

        # In Antigravity, subagents are stateless by default and do not carry a "name".
        # We can check for "name" just in case, but since there is no name field in Subagents,
        # it will warn when the trigger set matches.
        name = subagent.get("name")
        if isinstance(name, str) and name:
            continue

        return (
            f"[team-spawn-residency] '{matched_name}' spawned without a name — it will re-pay "
            "full context on every consensus/remediation cycle instead of staying resident. "
            "Spawn with `name` so it stays re-addressable via SendMessage (consensus-protocol.md)."
        )
    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    if not isinstance(payload, dict):
        sys.exit(0)

    if payload.get("tool_name") not in _TEAM_TOOL_NAMES:
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        sys.exit(0)

    references_dir = _find_references_dir(payload.get("cwd"))
    trigger_set = load_trigger_set(references_dir) if references_dir is not None else frozenset()

    advisory = decide(tool_input, trigger_set)
    if advisory is None:
        sys.exit(0)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": advisory,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
