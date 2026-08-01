#!/usr/bin/env python3
"""Validate and run the deterministic Saga conformance laboratory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
SAGA_SCRIPTS = REPO_ROOT / "plugins" / "saga" / "scripts"
sys.path.insert(0, str(SAGA_SCRIPTS))

import artifact_promotion  # noqa: E402

FIXTURE_SCHEMA = "saga.conformance-fixture.v1"
SCENARIO_SET_SCHEMA = "saga.conformance-scenario-set.v1"
BASELINE_SCHEMA = "saga.conformance-baseline.v1"
BASELINE_ARTIFACT_SCHEMA = "saga.conformance-baseline-artifact.v1"
FIXTURE_ROOT = Path("plugins/saga/tests/fixtures/conformance")
BASELINE_ROOT = Path("docs/conformance/baselines")
FIXTURES = {
    "reference-lifecycle": FIXTURE_ROOT / "reference-lifecycle" / "fixture.json",
}

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_REQUIREMENT = re.compile(r"^(?:R\d+|F\d+|AE\d+)$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_APPROVAL_REFERENCE = re.compile(
    r"^https://github\.com/infiquetra/infiquetra-antigravity-plugins/issues/\d+"
    r"(?:#issuecomment-\d+)?$"
)
_PYTEST_NODE = re.compile(
    r"^plugins/(?:saga|fleet-core|multi-agent-consensus)/tests/"
    r"test_[a-z0-9_]+\.py::test_[a-zA-Z0-9_]+$"
)
_FORBIDDEN_KEYS = {
    "brain",
    "credential",
    "environment",
    "history",
    "home",
    "hostname",
    "operator_name",
    "password",
    "prompt",
    "raw_prompt",
    "secret",
    "stderr",
    "stdout",
    "token",
    "transcript",
    "transcript_path",
    "user_name",
    "username",
}
_FIXTURE_KEYS = {
    "schema",
    "fixture_id",
    "revision",
    "semantic_contract_version",
    "scenario_sets",
    "validator_sources",
    "reference_inputs",
}
_SCENARIO_SET_KEYS = {"schema", "fixture_id", "fixture_revision", "scenarios"}
_SCENARIO_KEYS = {
    "scenario_id",
    "scenario_class",
    "requirement_ids",
    "input_contract",
    "validator",
    "expected",
    "sanitization",
}
_BASELINE_KEYS = {
    "schema",
    "fixture",
    "semantic_contract",
    "source_snapshots",
    "artifacts",
    "operator_approval",
}
_ARTIFACT_KEYS = {
    "schema",
    "artifact_id",
    "fixture_id",
    "fixture_revision",
    "provider",
    "source_snapshot",
    "quality_dimensions",
    "sanitization",
}
QUALITY_DIMENSIONS = {
    "adjudication",
    "depth",
    "evidence_use",
    "lifecycle_completeness",
    "seed_retention",
}
REQUIRED_FAILURE_SCENARIOS = {
    "claude-only-api",
    "conflicting-canonical-docs",
    "false-completion-narration",
    "mismatched-receipt",
    "missing-strategies",
    "stale-brain-state",
    "unauthorized-external-mutation",
    "unavailable-required-capability",
}
REQUIRED_COVERAGE = {
    "capability-catalog-valid",
    "deliberation-complete",
    "external-authority-valid",
    "host-contract-clean",
    "impl-spec-profile-valid",
    "optional-capability-fallback",
    "promoted-content-sanitized",
    "promotion-idempotent",
    "resume-retry-idempotent",
    "transition-settlement",
} | REQUIRED_FAILURE_SCENARIOS


class ConformanceError(ValueError):
    """A conformance fixture or baseline violates its closed contract."""


Runner = Callable[..., Any]


def _closed(mapping: Mapping[str, Any], keys: set[str], label: str) -> None:
    unknown = sorted(set(mapping) - keys)
    missing = sorted(keys - set(mapping))
    if unknown or missing:
        raise ConformanceError(f"{label} fields do not match the closed contract")


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ConformanceError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ConformanceError(f"{label} must be a list")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConformanceError(f"{label} must be a non-empty string")
    return value


def _identifier(value: Any, label: str) -> str:
    identifier = _string(value, label)
    if not _IDENTIFIER.fullmatch(identifier):
        raise ConformanceError(f"{label} must be a lowercase identifier")
    return identifier


def _repo_path(repo_root: Path, reference: Any) -> Path:
    value = _string(reference, "repository reference")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or value != relative.as_posix():
        raise ConformanceError("repository reference must be canonical and relative")
    root = repo_root.resolve()
    try:
        target = (root / relative).resolve(strict=True)
    except OSError as exc:
        raise ConformanceError("repository reference is missing") from exc
    if root not in target.parents:
        raise ConformanceError("repository reference escapes the repository")
    if not target.is_file():
        raise ConformanceError("repository reference must identify a file")
    return target


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_bytes(content: bytes, label: str) -> None:
    try:
        artifact_promotion.sanitize_promoted_content(content)
    except ValueError as exc:
        raise ConformanceError(f"{label} failed promoted-content sanitization") from exc


def _reject_private_keys(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ConformanceError(f"{label} contains a forbidden private field")
            _reject_private_keys(item, label)
    elif isinstance(value, list):
        for item in value:
            _reject_private_keys(item, label)


def _load_json(repo_root: Path, reference: Any, label: str) -> tuple[Path, dict[str, Any]]:
    path = _repo_path(repo_root, reference)
    content = path.read_bytes()
    _sanitize_bytes(content, label)
    try:
        loaded = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConformanceError(f"{label} must contain one JSON object") from exc
    mapping = _mapping(loaded, label)
    _reject_private_keys(mapping, label)
    return path, mapping


def _expect_digest(path: Path, value: Any, label: str) -> None:
    expected = _string(value, f"{label} digest")
    if not _DIGEST.fullmatch(expected) or _digest(path) != expected:
        raise ConformanceError(f"{label} digest does not match repository bytes")


def _validate_sanitization(value: Any, label: str) -> None:
    row = _mapping(value, f"{label} sanitization")
    _closed(row, {"state", "raw_source_committed"}, f"{label} sanitization")
    if row["state"] != "sanitized" or row["raw_source_committed"] is not False:
        raise ConformanceError(f"{label} is not explicitly sanitized")


def _validate_scenario(
    value: Any,
    *,
    repo_root: Path,
) -> tuple[str, str, str]:
    row = _mapping(value, "scenario")
    _closed(row, _SCENARIO_KEYS, "scenario")
    scenario_id = _identifier(row["scenario_id"], "scenario_id")
    if row["scenario_class"] not in {"success", "failure"}:
        raise ConformanceError("scenario_class must be success or failure")
    requirements = _list(row["requirement_ids"], "requirement_ids")
    if not requirements or not all(
        isinstance(item, str) and _REQUIREMENT.fullmatch(item) for item in requirements
    ):
        raise ConformanceError("requirement_ids must contain canonical requirement identifiers")
    if len(requirements) != len(set(requirements)):
        raise ConformanceError("requirement_ids contains duplicates")

    input_contract = _mapping(row["input_contract"], "input_contract")
    _closed(input_contract, {"kind", "reference"}, "input_contract")
    if input_contract["kind"] not in {"repository-fixture", "synthetic-test-builder"}:
        raise ConformanceError("input_contract kind is unsupported")
    _repo_path(repo_root, input_contract["reference"])

    validator = _mapping(row["validator"], "validator")
    _closed(validator, {"kind", "node_id"}, "validator")
    node_id = _string(validator["node_id"], "validator node_id")
    if validator["kind"] != "pytest-node" or not _PYTEST_NODE.fullmatch(node_id):
        raise ConformanceError("validator must be one exact plugin pytest node")
    _repo_path(repo_root, node_id.split("::", maxsplit=1)[0])

    expected = _mapping(row["expected"], "expected")
    _closed(expected, {"exit_code", "observable"}, "expected")
    if expected["exit_code"] != 0:
        raise ConformanceError("deterministic scenario expected exit_code must be zero")
    _string(expected["observable"], "expected observable")
    _validate_sanitization(row["sanitization"], scenario_id)
    return scenario_id, node_id, str(input_contract["reference"])


def load_fixture(
    fixture_id: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], list[str]]:
    """Validate a named fixture and return its manifest plus exact test nodes."""

    if fixture_id not in FIXTURES:
        raise ConformanceError("unknown conformance fixture")
    fixture_ref = FIXTURES[fixture_id]
    _fixture_path, fixture = _load_json(repo_root, fixture_ref.as_posix(), "fixture")
    _closed(fixture, _FIXTURE_KEYS, "fixture")
    if fixture["schema"] != FIXTURE_SCHEMA:
        raise ConformanceError("fixture schema is unsupported")
    if _identifier(fixture["fixture_id"], "fixture_id") != fixture_id:
        raise ConformanceError("fixture_id does not match the selected fixture")
    revision = fixture["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ConformanceError("fixture revision must be a positive integer")
    _string(fixture["semantic_contract_version"], "semantic_contract_version")

    nodes: list[str] = []
    input_refs: list[str] = []
    scenario_ids: list[str] = []
    for index, value in enumerate(_list(fixture["scenario_sets"], "scenario_sets")):
        row = _mapping(value, f"scenario_sets[{index}]")
        _closed(row, {"path", "sha256"}, f"scenario_sets[{index}]")
        path, scenario_set = _load_json(repo_root, row["path"], "scenario set")
        _expect_digest(path, row["sha256"], "scenario set")
        _closed(scenario_set, _SCENARIO_SET_KEYS, "scenario set")
        if scenario_set["schema"] != SCENARIO_SET_SCHEMA:
            raise ConformanceError("scenario set schema is unsupported")
        if scenario_set["fixture_id"] != fixture_id or scenario_set["fixture_revision"] != revision:
            raise ConformanceError("scenario set fixture binding does not match")
        for scenario in _list(scenario_set["scenarios"], "scenarios"):
            scenario_id, node_id, input_ref = _validate_scenario(
                scenario,
                repo_root=repo_root,
            )
            scenario_ids.append(scenario_id)
            nodes.append(node_id)
            input_refs.append(input_ref)

    if len(scenario_ids) != len(set(scenario_ids)):
        raise ConformanceError("scenario identifiers must be unique")
    if set(scenario_ids) != REQUIRED_COVERAGE:
        raise ConformanceError("reference fixture does not match required conformance coverage")

    validator_refs: set[str] = set()
    for index, value in enumerate(_list(fixture["validator_sources"], "validator_sources")):
        row = _mapping(value, f"validator_sources[{index}]")
        _closed(row, {"path", "sha256"}, f"validator_sources[{index}]")
        path = _repo_path(repo_root, row["path"])
        _expect_digest(path, row["sha256"], "validator source")
        validator_refs.add(str(row["path"]))
    if len(validator_refs) != len(fixture["validator_sources"]):
        raise ConformanceError("validator_sources contains duplicate paths")
    if {node.split("::", maxsplit=1)[0] for node in nodes} != validator_refs:
        raise ConformanceError("scenario validators do not match the bound validator sources")

    reference_refs: set[str] = set()
    for index, value in enumerate(_list(fixture["reference_inputs"], "reference_inputs")):
        row = _mapping(value, f"reference_inputs[{index}]")
        _closed(row, {"role", "path", "sha256"}, f"reference_inputs[{index}]")
        _identifier(row["role"], "reference input role")
        path = _repo_path(repo_root, row["path"])
        _expect_digest(path, row["sha256"], "reference input")
        reference_refs.add(str(row["path"]))
    if len(reference_refs) != len(fixture["reference_inputs"]):
        raise ConformanceError("reference_inputs contains duplicate paths")
    if not set(input_refs) <= validator_refs | reference_refs:
        raise ConformanceError("scenario input is not bound by the fixture")
    return fixture, nodes


def verify_fixture(
    fixture_id: str,
    *,
    repo_root: Path = REPO_ROOT,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Validate and execute one named fixture without a model or network call."""

    fixture, nodes = load_fixture(fixture_id, repo_root=repo_root)
    completed = runner(
        ["uv", "run", "--frozen", "python", "-m", "pytest", *nodes, "-q"],
        cwd=repo_root,
        check=False,
    )
    returncode = int(completed.returncode)
    if returncode != 0:
        raise ConformanceError("one or more deterministic scenario validators failed")
    return {
        "fixture_id": fixture_id,
        "fixture_revision": fixture["revision"],
        "scenario_count": len(nodes),
        "passed": True,
    }


def _binding_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in ("fixture", "semantic_contract", "source_snapshots", "artifacts")
    }


def binding_digest(manifest: Mapping[str, Any]) -> str:
    """Return the approval identity for every reusable baseline binding."""

    encoded = json.dumps(
        _binding_payload(manifest),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_baseline_artifact(
    value: Any,
    *,
    provider: str,
    fixture_id: str,
    fixture_revision: int,
    source_snapshot: str,
) -> None:
    artifact = _mapping(value, f"{provider} baseline artifact")
    _closed(artifact, _ARTIFACT_KEYS, f"{provider} baseline artifact")
    if artifact["schema"] != BASELINE_ARTIFACT_SCHEMA:
        raise ConformanceError("baseline artifact schema is unsupported")
    _identifier(artifact["artifact_id"], "artifact_id")
    if artifact["fixture_id"] != fixture_id or artifact["fixture_revision"] != fixture_revision:
        raise ConformanceError("baseline artifact fixture binding does not match")
    if artifact["provider"] != provider or artifact["source_snapshot"] != source_snapshot:
        raise ConformanceError("baseline artifact source binding does not match")
    dimensions = _mapping(artifact["quality_dimensions"], "quality_dimensions")
    _closed(dimensions, QUALITY_DIMENSIONS, "quality_dimensions")
    for dimension, summary in dimensions.items():
        _string(summary, f"quality dimension {dimension}")
    _validate_sanitization(artifact["sanitization"], f"{provider} baseline artifact")


def validate_baseline_manifest(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Validate already-loaded baseline bindings against repository bytes."""

    _reject_private_keys(manifest, "baseline manifest")
    _closed(manifest, _BASELINE_KEYS, "baseline manifest")
    if manifest["schema"] != BASELINE_SCHEMA:
        raise ConformanceError("baseline manifest schema is unsupported")

    fixture_binding = _mapping(manifest["fixture"], "fixture binding")
    _closed(fixture_binding, {"id", "revision", "path", "sha256"}, "fixture binding")
    fixture_id = _identifier(fixture_binding["id"], "fixture id")
    if fixture_id not in FIXTURES:
        raise ConformanceError("baseline fixture is unsupported")
    fixture_path = _repo_path(repo_root, fixture_binding["path"])
    _expect_digest(fixture_path, fixture_binding["sha256"], "fixture binding")
    fixture, _nodes = load_fixture(fixture_id, repo_root=repo_root)
    if fixture_binding["revision"] != fixture["revision"]:
        raise ConformanceError("baseline fixture revision does not match")

    contract = _mapping(manifest["semantic_contract"], "semantic contract binding")
    _closed(contract, {"version", "path", "sha256"}, "semantic contract binding")
    if contract["version"] != fixture["semantic_contract_version"]:
        raise ConformanceError("semantic contract version does not match the fixture")
    contract_path = _repo_path(repo_root, contract["path"])
    _expect_digest(contract_path, contract["sha256"], "semantic contract")

    snapshots = _mapping(manifest["source_snapshots"], "source snapshots")
    _closed(snapshots, {"claude", "codex"}, "source snapshots")
    for provider, commit in snapshots.items():
        if not isinstance(commit, str) or not _COMMIT.fullmatch(commit):
            raise ConformanceError(f"{provider} source snapshot must be a full commit identity")

    artifacts = _mapping(manifest["artifacts"], "artifacts")
    _closed(artifacts, {"claude", "codex"}, "artifacts")
    for provider in ("claude", "codex"):
        binding = _mapping(artifacts[provider], f"{provider} artifact binding")
        _closed(binding, {"path", "sha256"}, f"{provider} artifact binding")
        artifact_path, artifact = _load_json(
            repo_root, binding["path"], f"{provider} baseline artifact"
        )
        _expect_digest(artifact_path, binding["sha256"], f"{provider} artifact")
        _validate_baseline_artifact(
            artifact,
            provider=provider,
            fixture_id=fixture_id,
            fixture_revision=fixture["revision"],
            source_snapshot=snapshots[provider],
        )

    approval = _mapping(manifest["operator_approval"], "operator approval")
    _closed(
        approval,
        {"state", "approved_by", "approved_at", "reference", "binding_sha256"},
        "operator approval",
    )
    if approval["state"] != "approved":
        raise ConformanceError("baseline is not operator-approved")
    if approval["approved_by"] != "operator":
        raise ConformanceError("baseline approval must use the operator role")
    approved_at = _string(approval["approved_at"], "approval timestamp")
    if not _TIMESTAMP.fullmatch(approved_at):
        raise ConformanceError("approval timestamp must be UTC second precision")
    approval_reference = _string(approval["reference"], "approval reference")
    if not _APPROVAL_REFERENCE.fullmatch(approval_reference):
        raise ConformanceError("approval reference must identify the canonical issue or comment")
    expected_binding = _string(approval["binding_sha256"], "approval binding digest")
    if not _DIGEST.fullmatch(expected_binding) or expected_binding != binding_digest(manifest):
        raise ConformanceError("baseline approval does not bind the current manifest inputs")
    return {
        "fixture_id": fixture_id,
        "fixture_revision": fixture["revision"],
        "providers": ["claude", "codex"],
        "approved": True,
    }


def validate_baseline(
    manifest_ref: str | Path,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Load and validate a version-bound, operator-approved baseline manifest."""

    reference = Path(manifest_ref).as_posix()
    path = _repo_path(repo_root, reference)
    baseline_root = (repo_root / BASELINE_ROOT).resolve()
    if baseline_root not in path.parents:
        raise ConformanceError("baseline manifest must be under the canonical baseline root")
    _path, manifest = _load_json(repo_root, reference, "baseline manifest")
    return validate_baseline_manifest(manifest, repo_root=repo_root)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify", help="Validate and run a named fixture")
    verify.add_argument("--fixture", choices=sorted(FIXTURES), required=True)
    baseline = subparsers.add_parser(
        "validate-baseline", help="Validate one approved baseline manifest"
    )
    baseline.add_argument("manifest")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_fixture(args.fixture)
        else:
            result = validate_baseline(args.manifest)
    except (ConformanceError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
