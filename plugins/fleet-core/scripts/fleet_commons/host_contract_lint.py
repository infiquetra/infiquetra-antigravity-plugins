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
_ANNOTATION_KEYS = frozenset({"class", "rule", "reason", "revisit", "capability", "access"})
_ANNOTATION_CLASSES = frozenset({"historical", "foreign-runtime-input", "capability-gated"})
_FINDING_KEYS = frozenset(
    {
        "path_sha256",
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
_COMPARISON_SUFFIXES = frozenset(
    {".conf", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
)
REQUIRED_ACTIVE_GLOBS: tuple[str, ...] = ()
REQUIRED_EXACT_PATHS: tuple[str, ...] = ()
REQUIRED_COMPARISON_ROOTS = ("docs", "tests")
_CANONICAL_SELECTOR_DIGEST = "08df27477f912819b88ff979e60416ec20ff124e9b3a5eda1cb2532fd6195629"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MD_ANNOTATION_RE = re.compile(r"^\s*<!--\s*antigravity-host-contract:\s*(\{.*\})\s*-->\s*$")
_PY_ANNOTATION_RE = re.compile(r"^\s*#\s*antigravity-host-contract:\s*(\{.*\})\s*$")
MAX_SELECTED_FILE_BYTES = 1024 * 1024
ALLOWED_COMPARISON_ROOTS = frozenset(REQUIRED_COMPARISON_ROOTS)
_FOREIGN_RUNTIME_READ_ALLOWLIST = frozenset(
    {
        (
            "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py",
            "55f7471f0d78c8ca8c837ebe29ffaa634b3c348855c0b05b617b2ee4c13bf013",
            "d11d3b3f76f345fda91fbc92e9741c11ca267d04b4d519140fc8da984c6bb73d",
        ),
        (
            "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py",
            "55f7471f0d78c8ca8c837ebe29ffaa634b3c348855c0b05b617b2ee4c13bf013",
            "af73c91789685f05c5410063e3da771b02c0550e5eeb08619999bdaca2e16345",
        ),
    }
)
_HISTORICAL_LINE_ALLOWLIST = frozenset(
    {
        (
            "plugins/saga/references/operator-choice.md",
            "bdd890bd5995d28273bbe69168fcca0663478ad66f7d3b657d04b586c1ba939f",
            "adee019867eb46e2a20c0550083a4e699d3ea866f0b69c10a7b675f00a29de07",
        ),
        (
            "plugins/saga/scripts/execution_spec.py",
            "a52d69f7c1a43a4835c8ef0fa9470fdb4911a3c0d157b7f8fb4a534fbe1cd4ba",
            "28daab9cce391b8a09b00a723a53dda525084bd7af1c3eeca76bb93c594e8eef",
        ),
        (
            "plugins/saga/scripts/outcome_dispatcher.py",
            "9cd0d71b9ab96e6944a8bcc5742ec288896a091da0cc29a8e8c70ebeb29b218e",
            "239546d9661611d5e9bfca46e34062416ba1478e864d0ff24a9eabddaf994a37",
        ),
        (
            "plugins/saga/scripts/outcome_spec.py",
            "2b1b74bec1c8b09be676d17b929f2a6ebc5f9a3a930177e5b60ea05a1be3451f",
            "947e287593feb5211391b3a0e630c4a5148089b7f6bbb8dd2dcd349d4eff016b",
        ),
        (
            "plugins/saga/skills/code-review/SKILL.md",
            "98ecad314a26a7b6f982e6c4ccd1f0b1f065b91c6821358cc69b51f964bf498a",
            "8f80c0c4421da48bcd3bc963685998fa4592419a6c8fdd9933a1036eb5c646b8",
        ),
        (
            "plugins/saga/skills/founder-review/SKILL.md",
            "a8838ce01ff51877a74c48634476c1f8ec2650ee6d534cbd96a3c3f006e40543",
            "50e81777770eccdf8e96cf1d4a59863eab54b9baabeda3b3e9398859cd874ec8",
        ),
        (
            "plugins/saga/skills/investigate/SKILL.md",
            "e13a7cea8adabef6d5da1af0200abb978036bbceff3db9f898259f7d9ac62f4c",
            "be02d074098701d374c677220cc31f3256f5bf48c230ad4676dd47bc804d7866",
        ),
        (
            "plugins/saga/skills/optimize/SKILL.md",
            "fbffa04a457d747d1877c9e2c22eb73f2e0cf1fac11a4d870cb84a46480c6542",
            "318c1ec102618e775ad240c4ad8a8305d3cb4c03bb2218a42024989b1acfd721",
        ),
        (
            "plugins/saga/skills/plan/SKILL.md",
            "aad1642cb458271a108d95169fd32d89b8be840eef415d0028da6e87aa40026c",
            "8f80c0c4421da48bcd3bc963685998fa4592419a6c8fdd9933a1036eb5c646b8",
        ),
        (
            "plugins/saga/skills/qa/SKILL.md",
            "5a6ea2f3fe89aac90d03bee2b72d201c337d1a4f872c948c4e0d8773c9ad216b",
            "be02d074098701d374c677220cc31f3256f5bf48c230ad4676dd47bc804d7866",
        ),
        (
            "plugins/saga/skills/retro/SKILL.md",
            "7f00a29fdafdaeb46742e89d98f9d099a711fae1007efc241ab4faac2c09bb62",
            "be02d074098701d374c677220cc31f3256f5bf48c230ad4676dd47bc804d7866",
        ),
    }
)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern[str]
    capability: str | None
    remediation: str


RULES = (
    Rule(
        "AGHC001",
        re.compile(r"(?:^|[^A-Za-z0-9_])[.~]?\.claude(?:/|[\"'])"),
        None,
        "use-gemini-state",
    ),
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
    errors = ["selector: unknown field" for _key in sorted(set(selector) - _SELECTOR_KEYS)]
    if selector.get("schema") != SELECTOR_SCHEMA:
        errors.append(f"selector.schema: expected {SELECTOR_SCHEMA!r}")
    for field, allow_glob, allow_empty in (
        ("active_globs", True, True),
        ("exact_paths", False, False),
        ("comparison_roots", False, False),
    ):
        values = selector.get(field)
        if not isinstance(values, list) or (not values and not allow_empty):
            qualifier = "a list" if allow_empty else "a non-empty list"
            errors.append(f"selector.{field}: expected {qualifier}")
            continue
        string_values = [value for value in values if isinstance(value, str)]
        if len(string_values) != len(set(string_values)):
            errors.append(f"selector.{field}: duplicate values are not allowed")
        for index, value in enumerate(values):
            if not _safe_relative(value, allow_glob=allow_glob):
                errors.append(f"selector.{field}[{index}]: unsafe repository-relative path")

    for field, expected in (
        ("active_globs", REQUIRED_ACTIVE_GLOBS),
        ("comparison_roots", REQUIRED_COMPARISON_ROOTS),
    ):
        if selector.get(field) != list(expected):
            errors.append(f"selector.{field}: does not match the canonical surface policy")

    if selector.get("digest_inputs") != _SELECTOR_DIGEST_INPUTS:
        errors.append(f"selector.digest_inputs: expected exactly {_SELECTOR_DIGEST_INPUTS}")
    elif (
        all(key in selector for key in _SELECTOR_DIGEST_INPUTS)
        and selector_digest(cast(Mapping[str, Any], selector)) != _CANONICAL_SELECTOR_DIGEST
    ):
        errors.append("selector: does not match the canonical surface policy")

    root = Path(repo_root).resolve()
    exact_paths = selector.get("exact_paths")
    if isinstance(exact_paths, list):
        for value in exact_paths:
            if not _safe_relative(value, allow_glob=False):
                continue
            candidate = root / value
            if not candidate.exists():
                continue
            if not candidate.is_file():
                errors.append("selector.exact_paths: declared path is not a file")
            elif candidate.is_symlink():
                errors.append("selector.exact_paths: symlinks are not allowed")
            else:
                try:
                    candidate.resolve(strict=True).relative_to(root)
                except (FileNotFoundError, OSError, ValueError):
                    errors.append("selector.exact_paths: declared file escapes repository")
    comparison_roots = selector.get("comparison_roots")
    if isinstance(comparison_roots, list):
        for value in comparison_roots:
            if not _safe_relative(value, allow_glob=False):
                continue
            if value not in ALLOWED_COMPARISON_ROOTS:
                errors.append("selector.comparison_roots: root is not in the controlled allowlist")
                continue
            candidate = root / value
            if candidate == root:
                errors.append("selector.comparison_roots: repository root is not allowed")
            elif not candidate.is_dir():
                errors.append("selector.comparison_roots: declared directory is missing")
            elif candidate.is_symlink():
                errors.append("selector.comparison_roots: symlinks are not allowed")
            else:
                try:
                    candidate.resolve(strict=True).relative_to(root)
                except (FileNotFoundError, OSError, ValueError):
                    errors.append(
                        "selector.comparison_roots: declared directory escapes repository"
                    )

        active_candidates: set[Path] = set()
        active_globs = selector.get("active_globs")
        if isinstance(active_globs, list):
            try:
                for pattern in active_globs:
                    if _safe_relative(pattern, allow_glob=True):
                        active_candidates.update(
                            path for path in root.glob(pattern) if path.is_file()
                        )
            except OSError:
                errors.append("selector.active_globs: could not enumerate repository paths")
        if isinstance(exact_paths, list):
            active_candidates.update(
                root / value
                for value in exact_paths
                if _safe_relative(value, allow_glob=False) and (root / value).is_file()
            )
        for value in comparison_roots:
            if value not in ALLOWED_COMPARISON_ROOTS:
                continue
            comparison = root / value
            if any(path == comparison or comparison in path.parents for path in active_candidates):
                errors.append(
                    "selector.comparison_roots: active selection overlaps comparison root"
                )
    return errors


def load_selector(path: Path | str, repo_root: Path | str) -> dict[str, Any]:
    try:
        selector = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostContractError("could not load host-contract selector") from exc
    errors = validate_selector(selector, repo_root)
    if errors:
        raise HostContractError("invalid host-contract selector: " + "; ".join(errors))
    return cast(dict[str, Any], selector)


def selector_digest(selector: Mapping[str, Any]) -> str:
    digest_input = {key: selector[key] for key in _SELECTOR_DIGEST_INPUTS}
    encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical_selector_digest() -> str:
    """Return the digest of the closed repository selector policy."""

    return _CANONICAL_SELECTOR_DIGEST


def selected_active_paths(repo_root: Path | str, selector: Mapping[str, Any]) -> list[Path]:
    root = Path(repo_root).resolve()
    paths: set[Path] = set()
    try:
        for pattern in selector["active_globs"]:
            paths.update(path for path in root.glob(pattern) if path.is_file())
    except OSError as exc:
        raise HostContractError("could not enumerate active host-contract paths") from exc
    paths.update(root / value for value in selector["exact_paths"] if (root / value).is_file())
    selected: list[Path] = []
    for path in sorted(paths):
        if path.is_symlink():
            raise HostContractError("selected host-contract path must not be a symlink")
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise HostContractError("selected host-contract path escapes the repository") from exc
        selected.append(resolved)
    return selected


def selected_comparison_paths(repo_root: Path | str, selector: Mapping[str, Any]) -> list[Path]:
    root = Path(repo_root).resolve()
    selected: list[Path] = []
    for value in selector["comparison_roots"]:
        try:
            candidates = sorted((root / value).rglob("*"))
        except OSError as exc:
            raise HostContractError("could not enumerate comparison host-contract paths") from exc
        for path in candidates:
            if path.is_symlink():
                raise HostContractError("comparison host-contract path must not be a symlink")
            if not path.is_file() or path.suffix.lower() not in _COMPARISON_SUFFIXES:
                continue
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
            except (FileNotFoundError, OSError, ValueError) as exc:
                raise HostContractError(
                    "comparison host-contract path escapes the repository"
                ) from exc
            selected.append(resolved)
    return selected


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
        if not isinstance(value, str) or not value.strip() or len(value) > 240 or "*" in value:
            return f"annotation-invalid-{field}"
    classification = payload["class"]
    if classification == "foreign-runtime-input":
        if payload.get("access") != "read-only":
            return "annotation-foreign-not-read-only"
        if "capability" in payload:
            return "annotation-unexpected-capability"
    elif classification == "capability-gated":
        capability = payload.get("capability")
        if capability not in known_capabilities or capability != rule.capability:
            return "annotation-unknown-capability"
        if "access" in payload:
            return "annotation-unexpected-access"
    elif "capability" in payload or "access" in payload:
        return "annotation-unexpected-field"
    return None


def _annotation_semantically_safe(
    payload: Mapping[str, Any],
    path: str,
    line: str,
    source_digest: str,
) -> bool:
    classification = payload.get("class")
    line_digest = hashlib.sha256(line.encode()).hexdigest()
    if classification == "foreign-runtime-input":
        return (path, source_digest, line_digest) in _FOREIGN_RUNTIME_READ_ALLOWLIST
    if classification == "historical":
        return (path, source_digest, line_digest) in _HISTORICAL_LINE_ALLOWLIST
    return True


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
        "path_sha256": hashlib.sha256(path.encode()).hexdigest(),
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
    source_digest = hashlib.sha256(text.encode()).hexdigest()
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
                if annotation_error is None and not _annotation_semantically_safe(
                    annotation,
                    path,
                    line,
                    source_digest,
                ):
                    annotation_error = "annotation-conflicts-with-executable-write"
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
                unresolved = not isinstance(capability, str) or states.get(capability) != "passed"
                reason = (
                    "capability-proven" if not unresolved else "capability-missing-or-nonpassing"
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
    selected_paths = [
        *selected_active_paths(root, selector),
        *selected_comparison_paths(root, selector),
    ]
    for path in selected_paths:
        relative = path.relative_to(root).as_posix()
        try:
            if path.stat().st_size > MAX_SELECTED_FILE_BYTES:
                raise HostContractError("selected host-contract path exceeds the size limit")
            raw = path.read_bytes()
            if len(raw) > MAX_SELECTED_FILE_BYTES:
                raise HostContractError("selected host-contract path exceeds the size limit")
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HostContractError("selected host-contract path is not valid UTF-8") from exc
        except OSError as exc:
            raise HostContractError("could not read selected host-contract path") from exc
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
    digest = selector_digest(selector)
    if digest != canonical_selector_digest():
        raise HostContractError("selector does not match the canonical surface policy")
    receipt = {
        "schema": LINT_RECEIPT_SCHEMA,
        "selector_digest": digest,
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
    errors = ["lint receipt: unknown field" for _key in sorted(set(receipt) - _RECEIPT_KEYS)]
    if receipt.get("schema") != LINT_RECEIPT_SCHEMA:
        errors.append(f"lint receipt.schema: expected {LINT_RECEIPT_SCHEMA!r}")
    digest = receipt.get("selector_digest")
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
        errors.append("lint receipt.selector_digest: expected a SHA-256 digest")
    elif digest != canonical_selector_digest():
        errors.append("lint receipt.selector_digest: does not match canonical policy")
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
        for _key in sorted(set(finding) - _FINDING_KEYS):
            errors.append(f"{path}: unknown field")
        path_digest = finding.get("path_sha256")
        if not isinstance(path_digest, str) or not _DIGEST_RE.fullmatch(path_digest):
            errors.append(f"{path}.path_sha256: expected a SHA-256 digest")
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
            if not isinstance(finding.get(field), str) or not _CODE_RE.fullmatch(finding[field]):
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
