#!/usr/bin/env python3
"""Thin Antigravity transport for producer-owned profile-evolution contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, cast

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE_ROOT = PLUGIN_ROOT / "conformance"
CLASSIFIER_FIXTURE = CONFORMANCE_ROOT / "profile-change-classifier.v1.json"
HERMES_FIXTURE = CONFORMANCE_ROOT / "profile-request-cli.v1.json"
PROVENANCE_FIXTURE = CONFORMANCE_ROOT / "provenance.json"
MAX_INPUT_BYTES = 65_536
MAX_OUTPUT_BYTES = 65_536
SUBPROCESS_TIMEOUT_SECONDS = 20
PROFILE_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
SECRET_RE = re.compile(
    r"(?i)(?:gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(?:api[_-]?key|password|secret|token|credential)\s*[:=]\s*[^\s]+)"
)
PROHIBITED_KEYS = {
    "host",
    "url",
    "endpoint",
    "api_key",
    "model",
    "provider",
    "system_prompt",
    "tools",
}
PROHIBITED_REFERENCE_PARTS = {
    ".auth",
    "auth",
    "credentials",
    "logs",
    "runtime-db",
    "runtime_dbs",
    "sessions",
    "transcripts",
}
PROHIBITED_REFERENCE_NAMES = {
    ".env",
    "auth.json",
    "credentials.json",
    "secrets.yml",
    "state.db",
}
PROHIBITED_REFERENCE_SUFFIXES = {".db", ".key", ".log", ".pem", ".sqlite", ".sqlite3"}
ACTOR_FIELDS = {"actor_kind", "actor_id", "verification"}
ACTOR_KINDS = {"operator", "harness", "profile", "external_agent"}
ENVELOPE_FIELDS = {
    "schema_version",
    "record_type",
    "proposal_id",
    "revision_digest",
    "target",
    "requester",
    "delegation_chain",
    "intent",
    "evidence_references",
    "created_at",
}


class RequestError(ValueError):
    """The request cannot safely cross the harness boundary."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RequestError("producer conformance artifacts are unavailable or malformed") from exc


@lru_cache(maxsize=1)
def load_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify imported bytes and return the pinned producer contracts."""
    provenance = _load_json(PROVENANCE_FIXTURE)
    classifier = _load_json(CLASSIFIER_FIXTURE)
    hermes = _load_json(HERMES_FIXTURE)
    if (
        not isinstance(provenance, dict)
        or provenance.get("schema") != "hermes-profile-evolution.conformance-provenance.v1"
        or not isinstance(provenance.get("artifacts"), list)
        or len(provenance["artifacts"]) != 2
    ):
        raise RequestError("producer conformance provenance is incompatible")
    expected = {
        "profile-change-classifier.v1.json": (
            CLASSIFIER_FIXTURE,
            "infiquetra/team-mimir",
            "profile-governance/conformance/profile-change-classifier.v1.json",
        ),
        "profile-request-cli.v1.json": (
            HERMES_FIXTURE,
            "infiquetra/infiquetra-hermes-plugins",
            "plugins/profile_evolution/conformance/profile-request-cli.v1.json",
        ),
    }
    for row in provenance["artifacts"]:
        if not isinstance(row, dict) or row.get("artifact") not in expected:
            raise RequestError("producer conformance provenance is incompatible")
        path, repository, producer_path = expected[row["artifact"]]
        if (
            row.get("producer_repository") != repository
            or row.get("producer_artifact_path") != producer_path
            or not isinstance(row.get("source_commit"), str)
            or not re.fullmatch(r"[a-f0-9]{40}", row["source_commit"])
            or not isinstance(row.get("merge_commit"), str)
            or not re.fullmatch(r"[a-f0-9]{40}", row["merge_commit"])
            or row.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest()
        ):
            raise RequestError("producer conformance provenance or fixture digest drifted")
    if (
        not isinstance(classifier, dict)
        or classifier.get("classifier_schema_version") != 1
        or classifier.get("fixture_version") != 1
        or not isinstance(classifier.get("cases"), list)
        or not classifier["cases"]
    ):
        raise RequestError("Team Mimir classifier conformance is incompatible")
    contracts = hermes.get("contracts") if isinstance(hermes, dict) else None
    if (
        not isinstance(hermes, dict)
        or hermes.get("artifact") != "profile-request-cli-conformance"
        or hermes.get("schema_version") != 1
        or not isinstance(contracts, dict)
        or contracts.get("proposal_fields") != sorted(ENVELOPE_FIELDS)
        or contracts.get("doctor_fields")
        != ["credential_available", "route_registered", "service_available", "target"]
    ):
        raise RequestError("Hermes profile-request conformance is incompatible")
    return classifier, hermes


def _contains_secret(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in PROHIBITED_KEYS or _contains_secret(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return isinstance(value, str) and bool(SECRET_RE.search(value))


def _read_input(stream: Any = None) -> bytes:
    source = stream if stream is not None else sys.stdin.buffer
    payload = source.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise RequestError("input exceeds the supported size")
    return payload


def _parse_one_json(payload: bytes) -> Any:
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RequestError("standard input must contain one valid JSON value") from exc


def _validate_target(value: object) -> str:
    if not isinstance(value, str) or not PROFILE_RE.fullmatch(value):
        raise RequestError("target must be a named Hermes profile")
    return value


def _validate_actor(value: object) -> dict[str, str]:
    limits = load_contracts()[1]["contracts"]["limits"]["delegation_actor_id"]
    if (
        not isinstance(value, dict)
        or set(value) != ACTOR_FIELDS
        or value.get("actor_kind") not in ACTOR_KINDS
        or value.get("verification") != "claimed"
        or not isinstance(value.get("actor_id"), str)
        or not limits["min_characters"] <= len(value["actor_id"]) <= limits["max_characters"]
    ):
        raise RequestError("delegation identity is invalid")
    return dict(value)


def _validate_references(value: object) -> list[str]:
    limits = load_contracts()[1]["contracts"]["limits"]
    if not isinstance(value, list) or len(value) > limits["evidence_references"]["max_items"]:
        raise RequestError("evidence references are invalid")
    result: list[str] = []
    for reference in value:
        if not isinstance(reference, str):
            raise RequestError("evidence references are invalid")
        parts = PurePosixPath(reference).parts
        lowered = {part.lower() for part in parts}
        if (
            not limits["evidence_reference"]["min_characters"]
            <= len(reference)
            <= limits["evidence_reference"]["max_characters"]
            or reference.startswith("/")
            or ".." in parts
            or lowered & (PROHIBITED_REFERENCE_PARTS | PROHIBITED_REFERENCE_NAMES)
            or any(
                PurePosixPath(part).suffix.lower() in PROHIBITED_REFERENCE_SUFFIXES
                for part in parts
            )
            or SECRET_RE.search(reference)
        ):
            raise RequestError("evidence references are unsafe or out of bounds")
        result.append(reference)
    if len(result) != len(set(result)):
        raise RequestError("evidence references must be unique")
    return result


def _validate_envelope(value: object) -> dict[str, Any]:
    limits = load_contracts()[1]["contracts"]["limits"]
    if not isinstance(value, dict) or set(value) != ENVELOPE_FIELDS or _contains_secret(value):
        raise RequestError("proposal envelope is malformed or secret-bearing")
    target = _validate_target(value["target"])
    if (
        value["schema_version"] != 1
        or value["record_type"] != "proposal_envelope"
        or not isinstance(value["proposal_id"], str)
        or not OPAQUE_ID_RE.fullmatch(value["proposal_id"])
    ):
        raise RequestError("proposal envelope version or identifier is invalid")
    requester = _validate_actor(value["requester"])
    chain = value["delegation_chain"]
    if (
        not isinstance(chain, list)
        or not limits["delegation_chain"]["min_items"]
        <= len(chain)
        <= limits["delegation_chain"]["max_items"]
    ):
        raise RequestError("delegation chain is out of bounds")
    parsed_chain = [_validate_actor(actor) for actor in chain]
    intent = value["intent"]
    if (
        not isinstance(intent, str)
        or not intent.strip()
        or len(intent) > limits["intent"]["max_characters"]
    ):
        raise RequestError("proposal intent is empty or too large")
    references = _validate_references(value["evidence_references"])
    body = {
        key: value[key]
        for key in (
            "schema_version",
            "target",
            "requester",
            "delegation_chain",
            "intent",
            "evidence_references",
        )
    }
    if (
        not isinstance(value["revision_digest"], str)
        or value["revision_digest"] != hashlib.sha256(_canonical_json(body)).hexdigest()
    ):
        raise RequestError("proposal revision digest is invalid")
    if not isinstance(value["created_at"], str):
        raise RequestError("proposal timestamp is invalid")
    try:
        datetime.fromisoformat(value["created_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise RequestError("proposal timestamp is invalid") from exc
    return {
        **value,
        "target": target,
        "requester": requester,
        "delegation_chain": parsed_chain,
        "evidence_references": references,
    }


def _run(
    command: list[str],
    *,
    payload: bytes = b"",
    runner: Callable[..., Any] = subprocess.run,
) -> Any:
    try:
        result = runner(
            command,
            input=payload,
            capture_output=True,
            check=False,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RequestError("required producer command is unavailable or timed out") from exc
    stdout = result.stdout
    if not isinstance(stdout, bytes) or len(stdout) > MAX_OUTPUT_BYTES:
        raise RequestError("producer output is invalid or exceeds the supported size")
    return result


def classify_paths(
    paths: Sequence[str],
    *,
    team_mimir_root: Path,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Call the real Team Mimir classifier and validate its closed response."""
    classifier_fixture, _ = load_contracts()
    if not paths or not all(isinstance(path, str) and path for path in paths):
        raise RequestError("paths must be a non-empty list of repository-relative strings")
    active_root = team_mimir_root.resolve()
    classifier = active_root / "scripts" / "classify_profile_change.py"
    result = _run(
        [
            sys.executable,
            str(classifier),
            "--root",
            str(active_root),
            "--schema-version",
            "1",
            "--format",
            "json",
            *paths,
        ],
        runner=runner,
    )
    if result.returncode != 0:
        raise RequestError("Team Mimir classifier failed")
    output = _parse_one_json(result.stdout)
    required = {"schema_version", "disposition", "owner", "reason", "category", "paths"}
    if (
        not isinstance(output, dict)
        or set(output) != required
        or output.get("schema_version") != 1
        or not isinstance(output.get("paths"), list)
        or len(output["paths"]) != len(paths)
    ):
        raise RequestError("Team Mimir classifier output is incompatible")
    path_fields = {"path", "disposition", "owner", "reason", "category"}
    if any(not isinstance(row, dict) or set(row) != path_fields for row in output["paths"]):
        raise RequestError("Team Mimir classifier output is incompatible")
    matching = [case for case in classifier_fixture["cases"] if case.get("paths") == list(paths)]
    if matching and output != matching[0].get("expected"):
        raise RequestError("Team Mimir classifier output drifted from producer conformance")
    return output


def _route_target(classification: dict[str, Any], requested_target: str) -> bool:
    disposition = classification["disposition"]
    if disposition == "normal_merge" and classification["category"] == "ordinary_repository":
        return False
    if disposition == "prohibited" or classification["category"] == "prohibited_secret_material":
        raise RequestError("prohibited material cannot enter profile dialogue")
    target_owners = {
        row["owner"]
        for row in classification["paths"]
        if row["category"] == "profile_owned_behavior" and row["disposition"] == "target_request"
    }
    if target_owners == {requested_target} and classification["category"] in {
        "profile_owned_behavior",
        "mixed_custody",
    }:
        return True
    raise RequestError("classification does not permit one target-addressed profile request")


def build_envelope(request: object, classification: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical Hermes envelope after producer classification."""
    if not isinstance(request, dict) or _contains_secret(request):
        raise RequestError("request is malformed or secret-bearing")
    required = {
        "target",
        "requester",
        "delegation_chain",
        "intent",
        "evidence_references",
        "paths",
    }
    if not required <= set(request) or set(request) - (required | {"proposal_id", "created_at"}):
        raise RequestError("request fields do not match the supported schema")
    target = _validate_target(request["target"])
    if not _route_target(classification, target):
        raise RequestError("ordinary repository work must not be sent to Hermes")
    requester = _validate_actor(request["requester"])
    chain = request["delegation_chain"]
    if not isinstance(chain, list):
        raise RequestError("delegation chain is invalid")
    validated_chain = [_validate_actor(actor) for actor in chain]
    references = _validate_references(request["evidence_references"])
    body: dict[str, Any] = {
        "schema_version": 1,
        "record_type": "proposal_envelope",
        "proposal_id": request.get("proposal_id", f"proposal-{uuid.uuid4().hex}"),
        "target": target,
        "requester": requester,
        "delegation_chain": validated_chain,
        "intent": request["intent"],
        "evidence_references": references,
        "created_at": request.get(
            "created_at", datetime.now(UTC).isoformat().replace("+00:00", "Z")
        ),
    }
    revision_body = {
        key: body[key]
        for key in (
            "schema_version",
            "target",
            "requester",
            "delegation_chain",
            "intent",
            "evidence_references",
        )
    }
    return _validate_envelope(
        {**body, "revision_digest": hashlib.sha256(_canonical_json(revision_body)).hexdigest()}
    )


def _parse_json_stream(payload: bytes) -> list[Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RequestError("Hermes returned an invalid response") from exc
    decoder = json.JSONDecoder()
    values: list[Any] = []
    offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            break
        try:
            value, offset = decoder.raw_decode(text, offset)
        except json.JSONDecodeError as exc:
            raise RequestError("Hermes returned an invalid response") from exc
        values.append(value)
    return values


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _pinned_stdout(*case_ids: str) -> list[list[Any]]:
    """Return successful producer examples without moving policy into the adapter."""
    cases = load_contracts()[1]["cases"]
    outputs: list[list[Any]] = []
    for case_id in case_ids:
        matching = [
            case
            for case in cases
            if isinstance(case, dict)
            and case.get("case_id") == case_id
            and isinstance(case.get("expected"), dict)
            and case["expected"].get("outcome") == "success"
            and isinstance(case["expected"].get("stdout_json"), list)
        ]
        if len(matching) != 1:
            raise RequestError("Hermes profile-request conformance is incompatible")
        outputs.append(matching[0]["expected"]["stdout_json"])
    return outputs


def _validate_dialogue_output(payload: bytes, envelope: dict[str, Any]) -> None:
    values = _parse_json_stream(payload)
    samples = _pinned_stdout(
        "suggest",
        "reply",
        "resume",
        "reply-message-at-minimum",
        "reply-message-at-maximum",
    )
    if len(values) != 2 or not isinstance(values[0], dict) or not isinstance(values[1], dict):
        raise RequestError("Hermes returned an unexpected dialogue response")
    provider, continuity = values
    sample_provider, sample_continuity = samples[0]
    if (
        not isinstance(sample_provider, dict)
        or not isinstance(sample_continuity, dict)
        or any(
            len(sample) != 2
            or not isinstance(sample[0], dict)
            or not isinstance(sample[1], dict)
            or set(sample[0]) != set(sample_provider)
            or set(sample[1]) != set(sample_continuity)
            for sample in samples
        )
    ):
        raise RequestError("Hermes profile-request conformance is incompatible")
    choices = provider.get("choices")
    if (
        set(provider) != set(sample_provider)
        or set(continuity) != set(sample_continuity)
        or continuity.get("proposal_id") != envelope["proposal_id"]
        or continuity.get("proposal_revision_digest") != envelope["revision_digest"]
        or continuity.get("target") != envelope["target"]
        or not isinstance(choices, list)
        or not choices
        or not all(
            isinstance(choice, dict)
            and set(choice) == {"message"}
            and isinstance(choice.get("message"), dict)
            and set(choice["message"]) == {"content"}
            and isinstance(choice["message"].get("content"), str)
            and bool(choice["message"]["content"].strip())
            for choice in choices
        )
        or not isinstance(continuity.get("proposal_id"), str)
        or not OPAQUE_ID_RE.fullmatch(continuity["proposal_id"])
        or not isinstance(continuity.get("target"), str)
        or not PROFILE_RE.fullmatch(continuity["target"])
        or not isinstance(continuity.get("response_digests"), list)
        or not continuity["response_digests"]
        or not all(
            isinstance(item, str) and DIGEST_RE.fullmatch(item)
            for item in continuity["response_digests"]
        )
        or not isinstance(continuity.get("continuity_digest"), str)
        or not DIGEST_RE.fullmatch(continuity["continuity_digest"])
        or not _valid_timestamp(continuity.get("updated_at"))
        or _contains_secret(values)
    ):
        raise RequestError("Hermes returned an unexpected dialogue response")


def _validate_status_output(payload: bytes, target: str, revision: str) -> None:
    values = _parse_json_stream(payload)
    samples = _pinned_stdout("status")
    sample = samples[0][0] if len(samples[0]) == 1 else None
    if (
        len(values) != 1
        or not isinstance(values[0], dict)
        or not isinstance(sample, dict)
        or set(values[0]) != set(sample)
        or values[0].get("target") != target
        or values[0].get("proposal_revision_digest") != revision
        or values[0].get("result") not in {sample.get("result")}
        or values[0].get("evidence_verification") not in {sample.get("evidence_verification")}
        or not isinstance(values[0].get("target"), str)
        or not PROFILE_RE.fullmatch(values[0]["target"])
        or not isinstance(values[0].get("proposal_revision_digest"), str)
        or not DIGEST_RE.fullmatch(values[0]["proposal_revision_digest"])
        or not isinstance(values[0].get("public_evidence_digest"), str)
        or not DIGEST_RE.fullmatch(values[0]["public_evidence_digest"])
        or not _valid_timestamp(values[0].get("deadline"))
        or _contains_secret(values[0])
    ):
        raise RequestError("Hermes returned an unexpected status response")


def _validate_census_output(payload: bytes) -> None:
    values = _parse_json_stream(payload)
    samples = _pinned_stdout("census")
    sample_rows = samples[0][0] if len(samples[0]) == 1 else None
    sample = sample_rows[0] if isinstance(sample_rows, list) and sample_rows else None
    if (
        len(values) != 1
        or not isinstance(values[0], list)
        or not isinstance(sample, dict)
        or not values[0]
        or any(
            not isinstance(row, dict)
            or set(row) != set(sample)
            or row.get("schema_version") != sample.get("schema_version")
            or row.get("record_type") != sample.get("record_type")
            or row.get("result") not in {sample.get("result")}
            or row.get("evidence_verification") not in {sample.get("evidence_verification")}
            or row.get("commit_state") not in {sample.get("commit_state")}
            or row.get("drift_state") not in {sample.get("drift_state")}
            or row.get("recovery_state") not in {sample.get("recovery_state")}
            or not isinstance(row.get("census_id"), str)
            or not OPAQUE_ID_RE.fullmatch(row["census_id"])
            or not isinstance(row.get("target"), str)
            or not PROFILE_RE.fullmatch(row["target"])
            or not _valid_timestamp(row.get("observed_at"))
            or not isinstance(row.get("public_evidence_digest"), str)
            or not DIGEST_RE.fullmatch(row["public_evidence_digest"])
            or _contains_secret(row)
            for row in values[0]
        )
        or len({row["target"] for row in values[0]}) != len(values[0])
        or len({row["census_id"] for row in values[0]}) != 1
    ):
        raise RequestError("Hermes returned an unexpected census response")


def _hermes_run(
    arguments: list[str],
    payload: bytes = b"",
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> bytes:
    result = _run(["hermes", "profile-request", *arguments], payload=payload, runner=runner)
    if result.returncode != 0:
        raise RequestError("Hermes profile-request failed")
    return cast(bytes, result.stdout)


def doctor(target: str, *, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    """Require the exact producer-owned doctor response."""
    target = _validate_target(target)
    payload = _hermes_run(["doctor", "--target", target], runner=runner)
    values = _parse_json_stream(payload)
    fields = set(load_contracts()[1]["contracts"]["doctor_fields"])
    if (
        len(values) != 1
        or not isinstance(values[0], dict)
        or set(values[0]) != fields
        or values[0].get("target") != target
        or any(values[0].get(field) is not True for field in fields - {"target"})
    ):
        raise RequestError("Hermes profile-request is unavailable or incompatible")
    return values[0]


def dialogue(
    action: str,
    envelope: dict[str, Any],
    *,
    message: str | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> bytes:
    """Continue one live target-owned dialogue."""
    if action not in {"suggest", "reply", "resume"}:
        raise RequestError("unsupported dialogue action")
    envelope = _validate_envelope(envelope)
    arguments = [action]
    if action == "reply":
        limit = load_contracts()[1]["contracts"]["limits"]["reply_message"]
        if (
            not isinstance(message, str)
            or not message.strip()
            or len(message) > limit["max_characters"]
            or _contains_secret(message)
        ):
            raise RequestError("reply is empty, too large, or secret-bearing")
        arguments.extend(["--message", message])
    elif message is not None:
        raise RequestError("message is supported only for reply")
    doctor(envelope["target"], runner=runner)
    output = _hermes_run(arguments, _canonical_json(envelope), runner=runner)
    _validate_dialogue_output(output, envelope)
    return output


def route_request(
    request: object,
    *,
    team_mimir_root: Path,
    classifier_runner: Callable[..., Any] = subprocess.run,
    hermes_runner: Callable[..., Any] = subprocess.run,
) -> bytes:
    """Route ordinary work normally and profile influence through Hermes."""
    if not isinstance(request, dict) or _contains_secret(request):
        raise RequestError("request is malformed or secret-bearing")
    paths = request.get("paths")
    if not isinstance(paths, list):
        raise RequestError("paths must be a non-empty list of repository-relative strings")
    classification = classify_paths(
        paths, team_mimir_root=team_mimir_root, runner=classifier_runner
    )
    if (
        classification["disposition"] == "normal_merge"
        and classification["category"] == "ordinary_repository"
    ):
        return (
            _canonical_json(
                {
                    "classification": classification,
                    "hermes_contacted": False,
                    "outcome": "ordinary_repository",
                }
            )
            + b"\n"
        )
    _route_target(classification, _validate_target(request.get("target")))
    envelope = build_envelope(request, classification)
    return dialogue("suggest", envelope, runner=hermes_runner)


def status(
    request: object,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> bytes:
    if not isinstance(request, dict) or set(request) != {"proposal_id", "revision", "target"}:
        raise RequestError("status input is malformed")
    proposal_id = request["proposal_id"]
    revision = request["revision"]
    target = _validate_target(request["target"])
    if (
        not isinstance(proposal_id, str)
        or not OPAQUE_ID_RE.fullmatch(proposal_id)
        or not isinstance(revision, str)
        or not DIGEST_RE.fullmatch(revision)
    ):
        raise RequestError("status identifiers are invalid")
    doctor(target, runner=runner)
    output = _hermes_run(
        [
            "status",
            "--proposal-id",
            proposal_id,
            "--revision",
            revision,
            "--target",
            target,
        ],
        runner=runner,
    )
    _validate_status_output(output, target, revision)
    return output


def census(payload: bytes, *, runner: Callable[..., Any] = subprocess.run) -> bytes:
    value = _parse_one_json(payload)
    if _contains_secret(value):
        raise RequestError("census input is secret-bearing")
    output = _hermes_run(["census"], _canonical_json(value), runner=runner)
    _validate_census_output(output)
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--team-mimir-root",
        type=Path,
        help="Team Mimir repository root containing the producer-owned classifier",
    )
    parser.add_argument(
        "action", choices=("request", "reply", "resume", "status", "census", "doctor")
    )
    args = parser.parse_args(argv)
    try:
        payload = _read_input()
        value = _parse_one_json(payload)
        if args.action == "request":
            if args.team_mimir_root is None:
                raise RequestError("request requires an explicit Team Mimir repository root")
            output = route_request(value, team_mimir_root=args.team_mimir_root)
        elif args.team_mimir_root is not None:
            raise RequestError("Team Mimir repository root is supported only for request")
        elif args.action == "reply":
            if not isinstance(value, dict) or set(value) != {"envelope", "message"}:
                raise RequestError("reply input is malformed")
            output = dialogue("reply", value["envelope"], message=value["message"])
        elif args.action == "resume":
            output = dialogue("resume", value)
        elif args.action == "status":
            output = status(value)
        elif args.action == "census":
            output = census(payload)
        else:
            if not isinstance(value, dict) or set(value) != {"target"}:
                raise RequestError("doctor input is malformed")
            output = _canonical_json(doctor(value["target"])) + b"\n"
    except RequestError as exc:
        print(f"hermes-profile-evolution: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
