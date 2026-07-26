"""Static Antigravity host-contract linter with narrow adjacent annotations."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

SELECTOR_SCHEMA = "antigravity.host-contract-surfaces.v1"
LINT_RECEIPT_SCHEMA = "antigravity.host-contract-lint.v1"
ANNOTATION_RULE = "AGHC000"

_SELECTOR_KEYS = frozenset(
    {"schema", "active_globs", "exact_paths", "comparison_roots", "digest_inputs"}
)
_SELECTOR_DIGEST_INPUTS = ["schema", "active_globs", "exact_paths", "comparison_roots"]
_ANNOTATION_KEYS = frozenset(
    {"class", "rule", "reason", "revisit", "capability", "access"}
)
_ANNOTATION_CLASSES = frozenset(
    {"historical", "foreign-runtime-input", "capability-gated"}
)
_FINDING_KEYS = frozenset(
    {
        "path",
        "line",
        "rule",
        "classification",
        "capability",
        "reason",
        "remediation",
        "excerpt_sha256",
        "unresolved",
    }
)
_RECEIPT_KEYS = frozenset({"schema", "selector_digest", "findings", "unresolved_count"})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MD_ANNOTATION_RE = re.compile(
    r"^\s*<!--\s*antigravity-host-contract:\s*(\{.*\})\s*-->\s*$"
)
_PY_ANNOTATION_RE = re.compile(r"^\s*#\s*antigravity-host-contract:\s*(\{.*\})\s*$")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern[str]
    capability: str | None
    remediation: str


RULES = (
    Rule("AGHC001", re.compile(r"(?:^|[^A-Za-z0-9_])[.~]?\.claude/"), None, "use-gemini-state"),
    Rule(
        "AGHC002",
        re.compile(r"\b(?:AskUserQuestion|ToolSearch)\b"),
        None,
        "use-session-blocking-question",
    ),
    Rule(
        "AGHC003",
        re.compile(r"\bWorkflow\s*\(|\bcc-workflows-ultracode\b|\bWorkflow tool\b"),
        None,
        "remove-claude-workflow-routing",
    ),
    Rule(
        "AGHC004",
        re.compile(r"\.gemini/antigravity-cli/brain|antigravity-cli[\"']?\s*/\s*[\"']brain"),
        None,
        "discover-brain-root",
    ),
    Rule(
        "AGHC005",
        re.compile(
            r"(?:\b(?:automatically|guarantees?|will|must)\b.{0,60}"
            r"\b(?:schedule[ds]?|scheduled|cron|timer)\b)"
            r"|(?:\b(?:scheduled routine|cron-driven|cron tick)\b|/loop/cron)",
            re.IGNORECASE,
        ),
        None,
        "state-external-trigger-or-gate",
    ),
    Rule(
        "AGHC006",
        re.compile(
            r"\b(?:guarantee(?:s|d)?|ensure(?:s|d)?|provide(?:s|d)?|always)\b.{0,80}"
            r"\b(?:isolation|isolated|sandbox|worktree|clone)\b",
            re.IGNORECASE,
        ),
        "agy.sandbox.isolation",
        "separate-requested-observed-proof",
    ),
)
RULE_BY_ID = {rule.rule_id: rule for rule in RULES}


class HostContractError(ValueError):
    """Selector, annotation, or lint receipt validation failed."""


def _safe_relative(value: object, *, allow_glob: bool) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    if not allow_glob and any(char in value for char in "*?[]"):
        return False
    return not (allow_glob and value.strip("*/") == "")


def validate_selector(selector: object, repo_root: Path | str) -> list[str]:
    """Validate a closed selector and all declared exact paths."""

    if not isinstance(selector, dict):
        return ["selector: expected an object"]
    errors = [
        f"selector: unknown field {key!r}"
        for key in sorted(set(selector) - _SELECTOR_KEYS)
    ]
    if selector.get("schema") != SELECTOR_SCHEMA:
        errors.append(f"selector.schema: expected {SELECTOR_SCHEMA!r}")
    for field, allow_glob in (
        ("active_globs", True),
        ("exact_paths", False),
        ("comparison_roots", False),
    ):
        values = selector.get(field)
        if not isinstance(values, list) or not values:
            errors.append(f"selector.{field}: expected a non-empty list")
            continue
        string_values = [value for value in values if isinstance(value, str)]
        if len(string_values) != len(set(string_values)):
            errors.append(f"selector.{field}: duplicate values are not allowed")
        for index, value in enumerate(values):
            if not _safe_relative(value, allow_glob=allow_glob):
                errors.append(f"selector.{field}[{index}]: unsafe repository-relative path")

    if selector.get("digest_inputs") != _SELECTOR_DIGEST_INPUTS:
        errors.append(f"selector.digest_inputs: expected exactly {_SELECTOR_DIGEST_INPUTS}")

    root = Path(repo_root).resolve()
    exact_paths = selector.get("exact_paths")
    if isinstance(exact_paths, list):
        for value in exact_paths:
            if _safe_relative(value, allow_glob=False) and not (root / value).is_file():
                errors.append(f"selector.exact_paths: declared file is missing: {value}")
    comparison_roots = selector.get("comparison_roots")
    if isinstance(comparison_roots, list):
        for value in comparison_roots:
            if _safe_relative(value, allow_glob=False) and not (root / value).is_dir():
                errors.append(f"selector.comparison_roots: declared directory is missing: {value}")
    return errors


def load_selector(path: Path | str, repo_root: Path | str) -> dict[str, Any]:
    try:
        selector = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostContractError(f"could not load host-contract selector: {exc}") from exc
    errors = validate_selector(selector, repo_root)
    if errors:
        raise HostContractError("invalid host-contract selector: " + "; ".join(errors))
    return cast(dict[str, Any], selector)


def selector_digest(selector: Mapping[str, Any]) -> str:
    digest_input = {key: selector[key] for key in _SELECTOR_DIGEST_INPUTS}
    encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def selected_active_paths(
    repo_root: Path | str, selector: Mapping[str, Any]
) -> list[Path]:
    root = Path(repo_root).resolve()
    paths: set[Path] = set()
    for pattern in selector["active_globs"]:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    paths.update(root / value for value in selector["exact_paths"])
    return sorted(paths)


def _annotation_payload(line: str) -> tuple[dict[str, Any] | None, str | None]:
    match = _MD_ANNOTATION_RE.fullmatch(line) or _PY_ANNOTATION_RE.fullmatch(line)
    if match is None:
        return None, None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None, "annotation-invalid-json"
    if not isinstance(payload, dict):
        return None, "annotation-not-object"
    return payload, None


def _validate_annotation(
    payload: Mapping[str, Any],
    rule: Rule,
    known_capabilities: set[str],
) -> str | None:
    if set(payload) - _ANNOTATION_KEYS:
        return "annotation-unknown-field"
    if payload.get("class") not in _ANNOTATION_CLASSES:
        return "annotation-invalid-class"
    if payload.get("rule") != rule.rule_id:
        return "annotation-stale-rule"
    for field in ("reason", "revisit"):
        value = payload.get(field)
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 240
            or "*" in value
        ):
            return f"annotation-invalid-{field}"
    classification = payload["class"]
    if classification == "foreign-runtime-input":
        if payload.get("access") != "read-only":
            return "annotation-foreign-not-read-only"
        if "capability" in payload:
            return "annotation-unexpected-capability"
    elif classification == "capability-gated":
        capability = payload.get("capability")
        if capability not in known_capabilities:
            return "annotation-unknown-capability"
        if "access" in payload:
            return "annotation-unexpected-access"
    elif "capability" in payload or "access" in payload:
        return "annotation-unexpected-field"
    return None


def _finding(
    *,
    path: str,
    line: int,
    rule: str,
    classification: str,
    capability: str | None,
    reason: str,
    remediation: str,
    excerpt: str,
    unresolved: bool,
) -> dict[str, Any]:
    return {
        "path": path,
        "line": line,
        "rule": rule,
        "classification": classification,
        "capability": capability,
        "reason": reason,
        "remediation": remediation,
        "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
        "unresolved": unresolved,
    }


def scan_text(
    path: str,
    text: str,
    *,
    known_capabilities: set[str] | None = None,
    capability_states: Mapping[str, str] | None = None,
    default_classification: str = "active",
) -> list[dict[str, Any]]:
    """Scan one injected file and return structured findings without excerpts."""

    capabilities = known_capabilities or set()
    states = capability_states or {}
    lines = text.splitlines()
    findings: list[dict[str, Any]] = []
    consumed_annotations: set[int] = set()

    for index, line in enumerate(lines):
        matched_rules = [rule for rule in RULES if rule.pattern.search(line)]
        if not matched_rules:
            continue
        annotation: dict[str, Any] | None = None
        parse_error: str | None = None
        annotation_index = index - 1
        if annotation_index >= 0:
            annotation, parse_error = _annotation_payload(lines[annotation_index])
            if annotation is not None or parse_error is not None:
                consumed_annotations.add(annotation_index)

        for rule in matched_rules:
            if default_classification != "active":
                findings.append(
                    _finding(
                        path=path,
                        line=index + 1,
                        rule=rule.rule_id,
                        classification=default_classification,
                        capability=None,
                        reason="comparison-corpus",
                        remediation=rule.remediation,
                        excerpt=line,
                        unresolved=False,
                    )
                )
                continue
            annotation_error = parse_error
            if annotation is not None:
                annotation_error = _validate_annotation(annotation, rule, capabilities)
            if annotation is None or annotation_error is not None:
                findings.append(
                    _finding(
                        path=path,
                        line=index + 1,
                        rule=rule.rule_id,
                        classification="active",
                        capability=rule.capability,
                        reason=annotation_error or "unannotated-active-match",
                        remediation=rule.remediation,
                        excerpt=line,
                        unresolved=True,
                    )
                )
                continue

            classification = annotation["class"]
            capability = annotation.get("capability")
            unresolved = False
            reason = f"annotated-{classification}"
            if classification == "capability-gated":
                unresolved = (
                    not isinstance(capability, str) or states.get(capability) != "passed"
                )
                reason = (
                    "capability-proven"
                    if not unresolved
                    else "capability-missing-or-nonpassing"
                )
            findings.append(
                _finding(
                    path=path,
                    line=index + 1,
                    rule=rule.rule_id,
                    classification=classification,
                    capability=capability,
                    reason=reason,
                    remediation=rule.remediation,
                    excerpt=line,
                    unresolved=unresolved,
                )
            )

    for index, line in enumerate(lines):
        payload, parse_error = _annotation_payload(line)
        if (payload is not None or parse_error is not None) and index not in consumed_annotations:
            findings.append(
                _finding(
                    path=path,
                    line=index + 1,
                    rule=ANNOTATION_RULE,
                    classification="active",
                    capability=None,
                    reason=parse_error or "annotation-not-adjacent-to-match",
                    remediation="remove-or-adjoin-annotation",
                    excerpt=line,
                    unresolved=True,
                )
            )
    return findings


def _is_comparison_path(path: str, selector: Mapping[str, Any]) -> bool:
    pure = PurePosixPath(path)
    return any(
        pure == PurePosixPath(root) or PurePosixPath(root) in pure.parents
        for root in selector["comparison_roots"]
    )


def scan_repository(
    repo_root: Path | str,
    selector: Mapping[str, Any],
    *,
    known_capabilities: set[str] | None = None,
    capability_states: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Scan the selected repository surface and build a strict lint receipt."""

    root = Path(repo_root).resolve()
    findings: list[dict[str, Any]] = []
    for path in selected_active_paths(root, selector):
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise HostContractError(f"could not read selected path {relative}") from exc
        default = "historical" if _is_comparison_path(relative, selector) else "active"
        findings.extend(
            scan_text(
                relative,
                text,
                known_capabilities=known_capabilities,
                capability_states=capability_states,
                default_classification=default,
            )
        )
    return build_lint_receipt(selector, findings)


def build_lint_receipt(
    selector: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    receipt = {
        "schema": LINT_RECEIPT_SCHEMA,
        "selector_digest": selector_digest(selector),
        "findings": [dict(finding) for finding in findings],
        "unresolved_count": sum(bool(finding.get("unresolved")) for finding in findings),
    }
    errors = validate_lint_receipt(receipt)
    if errors:
        raise HostContractError("invalid host-contract lint receipt: " + "; ".join(errors))
    return receipt


def validate_lint_receipt(receipt: object) -> list[str]:
    """Validate the strict, excerpt-free promotable lint receipt."""

    if not isinstance(receipt, dict):
        return ["lint receipt: expected an object"]
    errors = [
        f"lint receipt: unknown field {key!r}"
        for key in sorted(set(receipt) - _RECEIPT_KEYS)
    ]
    if receipt.get("schema") != LINT_RECEIPT_SCHEMA:
        errors.append(f"lint receipt.schema: expected {LINT_RECEIPT_SCHEMA!r}")
    digest = receipt.get("selector_digest")
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
        errors.append("lint receipt.selector_digest: expected a SHA-256 digest")
    findings = receipt.get("findings")
    if not isinstance(findings, list):
        errors.append("lint receipt.findings: expected a list")
        return errors
    unresolved = 0
    for index, finding in enumerate(findings):
        path = f"lint receipt.findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{path}: expected an object")
            continue
        for key in sorted(set(finding) - _FINDING_KEYS):
            errors.append(f"{path}: unknown field {key!r}")
        relative = finding.get("path")
        if not _safe_relative(relative, allow_glob=False):
            errors.append(f"{path}.path: expected a safe repository-relative path")
        line = finding.get("line")
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            errors.append(f"{path}.line: expected a positive integer")
        rule = finding.get("rule")
        if rule not in {*RULE_BY_ID, ANNOTATION_RULE}:
            errors.append(f"{path}.rule: unknown rule")
        if finding.get("classification") not in {
            "active",
            "historical",
            "foreign-runtime-input",
            "capability-gated",
        }:
            errors.append(f"{path}.classification: unknown classification")
        capability = finding.get("capability")
        if capability is not None and (
            not isinstance(capability, str)
            or not re.fullmatch(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$", capability)
        ):
            errors.append(f"{path}.capability: invalid capability identifier")
        for field in ("reason", "remediation"):
            if not isinstance(finding.get(field), str) or not _CODE_RE.fullmatch(
                finding[field]
            ):
                errors.append(f"{path}.{field}: expected a bounded code")
        excerpt_digest = finding.get("excerpt_sha256")
        if not isinstance(excerpt_digest, str) or not _DIGEST_RE.fullmatch(excerpt_digest):
            errors.append(f"{path}.excerpt_sha256: expected a SHA-256 digest")
        if not isinstance(finding.get("unresolved"), bool):
            errors.append(f"{path}.unresolved: expected a boolean")
        elif finding["unresolved"]:
            unresolved += 1
    if receipt.get("unresolved_count") != unresolved:
        errors.append("lint receipt.unresolved_count: does not match findings")
    return errors
