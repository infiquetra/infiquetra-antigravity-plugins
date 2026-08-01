#!/usr/bin/env python3
"""Deterministic contracts for the profile-backed `/impl-spec` pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE_SCHEMA = "saga.impl-spec-profile.v1"
SPEC_SET_SCHEMA = "saga.impl-spec-set.v1"
PROBE_SCHEMA = "saga.buildability-probe.v1"
QUESTION_CATEGORIES = ("product", "architecture", "data", "api", "operations")
BREAKDOWN_CATEGORIES = (
    "repositories",
    "modules",
    "endpoints",
    "entities",
    "events_published",
    "events_consumed",
    "tests",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SEPARATOR = re.compile(r"^:?-{3,}:?$")


class ImplSpecError(ValueError):
    """A profile, folder contract, spec set, or probe result is invalid."""


@dataclass(frozen=True)
class Profile:
    """Closed repository-relative profile for one multi-document spec set."""

    profile_id: str
    spec_root: str
    folder_contract_readme: str
    schema: str = PROFILE_SCHEMA

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Profile:
        _closed(data, {"schema", "profile_id", "spec_root", "folder_contract_readme"}, "profile")
        if data.get("schema") != PROFILE_SCHEMA:
            raise ImplSpecError("unsupported impl-spec profile schema")
        profile_id = _string(data, "profile_id", "profile")
        if not _SAFE_ID.fullmatch(profile_id):
            raise ImplSpecError("profile_id must be a bounded identifier")
        spec_root = _relative_ref(_string(data, "spec_root", "profile"), "profile spec_root")
        if not _is_within(spec_root, "docs/specs"):
            raise ImplSpecError("profile spec_root must be inside canonical docs/specs")
        readme = _relative_ref(
            _string(data, "folder_contract_readme", "profile"),
            "profile folder_contract_readme",
        )
        if not _is_within(readme, spec_root):
            raise ImplSpecError("folder contract README must be inside the declared spec_root")
        return cls(profile_id, spec_root, readme)

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": self.schema,
            "profile_id": self.profile_id,
            "spec_root": self.spec_root,
            "folder_contract_readme": self.folder_contract_readme,
        }


@dataclass(frozen=True)
class FolderRule:
    """One folder row parsed from the README contract table."""

    folder: str
    required_files: tuple[str, ...]
    completeness: str
    depends_on: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "folder": self.folder,
            "required_files": list(self.required_files),
            "completeness": self.completeness,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True)
class FolderContract:
    """Parsed folder contract and deterministic dependency waves."""

    readme_ref: str
    readme_sha256: str
    folders: tuple[FolderRule, ...]
    waves: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "readme_ref": self.readme_ref,
            "readme_sha256": self.readme_sha256,
            "folders": [folder.to_dict() for folder in self.folders],
            "waves": [list(wave) for wave in self.waves],
        }


@dataclass(frozen=True)
class ValidationResult:
    """Completeness result for a profile-backed spec set."""

    complete: bool
    missing: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"complete": self.complete, "missing": list(self.missing)}


@dataclass(frozen=True)
class ProbeResult:
    """Closed buildability result whose verdict is derived from question classifications."""

    subject: str
    round: int
    implementation_breakdown: dict[str, tuple[str, ...]]
    questions: dict[str, tuple[dict[str, str], ...]]
    verdict: str
    schema: str = PROBE_SCHEMA

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProbeResult:
        _closed(
            data,
            {"schema", "subject", "round", "implementation_breakdown", "questions", "verdict"},
            "buildability probe",
        )
        if data.get("schema") != PROBE_SCHEMA:
            raise ImplSpecError("unsupported buildability probe schema")
        subject = _string(data, "subject", "buildability probe")
        round_number = data.get("round")
        if (
            isinstance(round_number, bool)
            or not isinstance(round_number, int)
            or not 1 <= round_number <= 3
        ):
            raise ImplSpecError("buildability probe round must be between 1 and 3")
        breakdown_raw = data.get("implementation_breakdown")
        if not isinstance(breakdown_raw, Mapping) or set(breakdown_raw) != set(
            BREAKDOWN_CATEGORIES
        ):
            raise ImplSpecError("buildability probe implementation breakdown is incomplete")
        breakdown = {
            category: _string_list(breakdown_raw[category], f"breakdown {category}")
            for category in BREAKDOWN_CATEGORIES
        }
        questions_raw = data.get("questions")
        if not isinstance(questions_raw, Mapping) or set(questions_raw) != set(QUESTION_CATEGORIES):
            raise ImplSpecError("buildability probe must enumerate every question category")
        questions = {
            category: _questions(questions_raw[category], category)
            for category in QUESTION_CATEGORIES
        }
        defects = sum(
            question["classification"] == "spec-defect"
            for category in QUESTION_CATEGORIES
            for question in questions[category]
        )
        expected = "FAIL" if defects else "PASS"
        verdict = data.get("verdict")
        if verdict != expected:
            raise ImplSpecError(
                f"buildability probe verdict must be {expected} for {defects} boundary-test defect(s)"
            )
        return cls(subject, round_number, breakdown, questions, expected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "subject": self.subject,
            "round": self.round,
            "implementation_breakdown": {
                category: list(self.implementation_breakdown[category])
                for category in BREAKDOWN_CATEGORIES
            },
            "questions": {
                category: [dict(question) for question in self.questions[category]]
                for category in QUESTION_CATEGORIES
            },
            "verdict": self.verdict,
        }


def load_profile(repo_root: Path, profile_ref: str) -> Profile:
    """Load a strict profile from an ordinary repository file."""

    path = _repo_path(repo_root, profile_ref, must_exist=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImplSpecError("impl-spec profile is not readable JSON") from exc
    if not isinstance(data, Mapping):
        raise ImplSpecError("impl-spec profile must be a JSON object")
    return Profile.from_dict(data)


def discover(repo_root: Path, profile_ref: str) -> tuple[Profile, FolderContract]:
    """Resolve a profile and parse its README folder contract."""

    profile = load_profile(repo_root, profile_ref)
    spec_root = _repo_path(repo_root, profile.spec_root, must_exist=True)
    if not spec_root.is_dir():
        raise ImplSpecError("profile spec_root is unavailable")
    readme = _repo_path(repo_root, profile.folder_contract_readme, must_exist=True)
    try:
        raw = readme.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ImplSpecError("folder contract README is unavailable") from exc
    folders = parse_folder_contract(text)
    waves = dependency_waves(folders)
    return profile, FolderContract(
        readme_ref=profile.folder_contract_readme,
        readme_sha256=_sha256(raw),
        folders=folders,
        waves=waves,
    )


def parse_folder_contract(text: str) -> tuple[FolderRule, ...]:
    """Parse the one strict Markdown folder-contract table from README text."""

    lines = text.splitlines()
    matches: list[tuple[list[str], list[list[str]]]] = []
    for index in range(len(lines) - 1):
        headers = [_normalize_header(cell) for cell in _table_row(lines[index])]
        if not headers or headers[:3] != ["folder", "required files", "completeness"]:
            continue
        if len(headers) not in {3, 4} or (len(headers) == 4 and headers[3] != "depends on"):
            continue
        separators = _table_row(lines[index + 1])
        if len(separators) != len(headers) or not all(
            _SEPARATOR.fullmatch(cell.strip()) for cell in separators
        ):
            continue
        rows: list[list[str]] = []
        for line in lines[index + 2 :]:
            cells = _table_row(line)
            if len(cells) != len(headers):
                break
            rows.append(cells)
        matches.append((headers, rows))
    if len(matches) != 1:
        raise ImplSpecError("README must contain exactly one parseable folder contract table")
    headers, rows = matches[0]
    if not rows:
        raise ImplSpecError("folder contract table must contain at least one folder")
    rules: list[FolderRule] = []
    for row in rows:
        folder = _relative_ref(_clean_cell(row[0]), "folder contract folder")
        if len(PurePosixPath(folder).parts) != 1:
            raise ImplSpecError("folder contract folders must be direct children of spec_root")
        files = tuple(
            _relative_ref(item, f"required file in {folder}")
            for item in _cell_list(row[1], allow_none=False)
        )
        if any(len(PurePosixPath(item).parts) != 1 for item in files):
            raise ImplSpecError("required files must be direct children of their folder")
        if len(files) != len(set(files)):
            raise ImplSpecError(f"folder {folder} contains duplicate required files")
        completeness = _clean_cell(row[2])
        if not completeness:
            raise ImplSpecError(f"folder {folder} requires a completeness rule")
        depends = (
            tuple(
                _relative_ref(item, f"dependency in {folder}")
                for item in _cell_list(row[3], allow_none=True)
            )
            if len(headers) == 4
            else ()
        )
        rules.append(FolderRule(folder, files, completeness, depends))
    names = [rule.folder for rule in rules]
    if len(names) != len(set(names)):
        raise ImplSpecError("folder contract contains duplicate folders")
    for rule in rules:
        unknown = set(rule.depends_on) - set(names)
        if unknown or rule.folder in rule.depends_on:
            raise ImplSpecError("folder contract has an unknown or self dependency")
    return tuple(rules)


def dependency_waves(folders: Sequence[FolderRule]) -> tuple[tuple[str, ...], ...]:
    """Return stable topological waves or reject a dependency cycle."""

    remaining = {folder.folder: set(folder.depends_on) for folder in folders}
    order = [folder.folder for folder in folders]
    completed: set[str] = set()
    waves: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(name for name in order if name in remaining and remaining[name] <= completed)
        if not ready:
            raise ImplSpecError("folder contract dependency graph contains a cycle")
        waves.append(ready)
        completed.update(ready)
        for name in ready:
            remaining.pop(name)
    return tuple(waves)


def validate_spec_set(
    repo_root: Path,
    profile: Profile,
    contract: FolderContract,
) -> ValidationResult:
    """Verify that every required folder and file exists as ordinary repository content."""

    missing: list[str] = []
    for folder in contract.folders:
        folder_ref = f"{profile.spec_root}/{folder.folder}"
        try:
            folder_path = _repo_path(repo_root, folder_ref, must_exist=True)
        except ImplSpecError:
            missing.extend(f"{folder_ref}/{name}" for name in folder.required_files)
            continue
        if not folder_path.is_dir():
            missing.extend(f"{folder_ref}/{name}" for name in folder.required_files)
            continue
        for name in folder.required_files:
            reference = f"{folder_ref}/{name}"
            try:
                path = _repo_path(repo_root, reference, must_exist=True)
            except ImplSpecError:
                missing.append(reference)
                continue
            if not path.is_file():
                missing.append(reference)
    normalized = tuple(sorted(set(missing)))
    return ValidationResult(not normalized, normalized)


def build_spec_set_manifest(
    repo_root: Path,
    profile: Profile,
    contract: FolderContract,
) -> dict[str, Any]:
    """Build a deterministic content manifest only for a complete spec set."""

    validation = validate_spec_set(repo_root, profile, contract)
    if not validation.complete:
        raise ImplSpecError("spec set is incomplete: " + ", ".join(validation.missing))
    refs = [profile.folder_contract_readme]
    refs.extend(
        f"{profile.spec_root}/{folder.folder}/{name}"
        for folder in contract.folders
        for name in folder.required_files
    )
    files = [
        {
            "reference": reference,
            "sha256": _sha256(_repo_path(repo_root, reference, must_exist=True).read_bytes()),
        }
        for reference in refs
    ]
    body = {
        "schema": SPEC_SET_SCHEMA,
        "profile_id": profile.profile_id,
        "spec_root": profile.spec_root,
        "folder_contract_sha256": contract.readme_sha256,
        "files": files,
    }
    return {**body, "spec_set_id": _identity(body)}


def load_probe_result(path: Path) -> ProbeResult:
    """Load and validate one machine-readable buildability result."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImplSpecError("buildability probe result is not readable JSON") from exc
    if not isinstance(data, Mapping):
        raise ImplSpecError("buildability probe result must be a JSON object")
    return ProbeResult.from_dict(data)


def _repo_path(repo_root: Path, reference: str, *, must_exist: bool) -> Path:
    root = repo_root.resolve(strict=True)
    normalized = _relative_ref(reference, "repository reference")
    path = root.joinpath(*PurePosixPath(normalized).parts)
    current = root
    for part in PurePosixPath(normalized).parts:
        current /= part
        if current.is_symlink():
            raise ImplSpecError("impl-spec paths must not contain symlinks")
    try:
        path.resolve(strict=must_exist).relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ImplSpecError("impl-spec repository reference is unavailable") from exc
    return path


def _questions(value: Any, category: str) -> tuple[dict[str, str], ...]:
    if not isinstance(value, list):
        raise ImplSpecError(f"buildability question category {category} must be a list")
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ImplSpecError(f"buildability question in {category} must be an object")
        _closed(item, {"question", "classification", "reasoning"}, f"question in {category}")
        classification = item.get("classification")
        if classification not in {"spec-defect", "execution-discovery"}:
            raise ImplSpecError("buildability question classification is unsupported")
        result.append(
            {
                "question": _string(item, "question", f"question in {category}"),
                "classification": classification,
                "reasoning": _string(item, "reasoning", f"question in {category}"),
            }
        )
    return tuple(result)


def _string_list(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ImplSpecError(f"{where} must be a list of non-empty strings")
    return tuple(item.strip() for item in value)


def _table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _normalize_header(value: str) -> str:
    return " ".join(_clean_cell(value).lower().replace("_", " ").replace("-", " ").split())


def _clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def _cell_list(value: str, *, allow_none: bool) -> list[str]:
    cleaned = _clean_cell(value)
    if allow_none and cleaned.lower() in {"", "-", "—", "none", "n/a"}:
        return []
    values = [_clean_cell(item) for item in re.split(r"\s*(?:,|<br\s*/?>)\s*", cleaned)]
    if not values or any(not item for item in values):
        raise ImplSpecError("folder contract list cell is empty or malformed")
    return values


def _relative_ref(value: str, where: str) -> str:
    path = PurePosixPath(value)
    normalized = path.as_posix()
    if not value or path.is_absolute() or ".." in path.parts or normalized != value:
        raise ImplSpecError(f"{where} must be a normalized repository-relative path")
    return normalized


def _is_within(reference: str, parent: str) -> bool:
    ref_parts = PurePosixPath(reference).parts
    parent_parts = PurePosixPath(parent).parts
    return ref_parts[: len(parent_parts)] == parent_parts


def _closed(data: Mapping[str, Any], fields: set[str], where: str) -> None:
    if set(data) != fields:
        raise ImplSpecError(f"{where} has unknown or missing fields")


def _string(data: Mapping[str, Any], field_name: str, where: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ImplSpecError(f"{where} requires non-empty {field_name}")
    return value.strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _identity(value: Mapping[str, Any]) -> str:
    return _sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    )


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("discover", "validate", "manifest"):
        command = subparsers.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=Path.cwd())
        command.add_argument("--profile", required=True)
    probe = subparsers.add_parser("probe-check")
    probe.add_argument("result", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "probe-check":
            _print(load_probe_result(args.result).to_dict())
            return 0
        profile, contract = discover(args.repo_root, args.profile)
        if args.command == "discover":
            _print({"profile": profile.to_dict(), "contract": contract.to_dict()})
            return 0
        if args.command == "validate":
            result = validate_spec_set(args.repo_root, profile, contract)
            _print(result.to_dict())
            return 0 if result.complete else 2
        _print(build_spec_set_manifest(args.repo_root, profile, contract))
        return 0
    except ImplSpecError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
