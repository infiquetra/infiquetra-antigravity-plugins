"""Semantic contract tests for the native application-security audit skill."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, cast

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = PLUGIN_ROOT / "skills" / "appsec-audit" / "SKILL.md"
CONTRACT_MARKER = "<!-- appsec-audit-contract-v1 -->"
DIGEST = "a" * 64


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _contract() -> dict[str, Any]:
    text = _skill_text()
    block = text.split(CONTRACT_MARKER, maxsplit=1)[1]
    payload = block.split("```json", maxsplit=1)[1].split("```", maxsplit=1)[0]
    contract = json.loads(payload)
    if not isinstance(contract, dict):
        raise TypeError("application-security audit contract must be a JSON object")
    return cast(dict[str, Any], contract)


def _valid_documents(
    *,
    mode: str = "consume-external-evidence",
) -> tuple[dict[str, Any], dict[str, Any]]:
    identity_source = "external" if mode == "consume-external-evidence" else "antigravity-host"
    request = {
        "schema": "antigravity.appsec-audit-request.v1",
        "request_id": "audit-1",
        "subject_producer_id": "implementation-worker",
        "scope_paths": ["src/http_client.py"],
        "focus_categories": ["ssrf"],
        "execution_mode": mode,
        "reviewer": {
            "reviewer_id": "security-reviewer",
            "identity_source": identity_source,
        },
    }
    packet = {
        "schema": "antigravity.appsec-audit-evidence.v1",
        "request_id": "audit-1",
        "reviewer": {
            "reviewer_id": "security-reviewer",
            "identity_source": identity_source,
            "host_independence_performed": mode == "originate-independent-reviewer",
        },
        "verdict": "findings-present",
        "findings": [
            {
                "finding_id": "finding-1",
                "severity": "high",
                "category": "ssrf",
                "location": "src/http_client.py:12",
                "evidence_ids": ["evidence-1"],
                "impact": "A caller can reach a private address.",
                "fix": "Reject private and link-local destinations before connecting.",
                "validation_check_ids": ["check-1"],
            }
        ],
        "checks": [
            {
                "check_id": "check-1",
                "status": "failed",
                "detail": "The private-address rejection check failed.",
                "evidence_ids": ["evidence-1"],
            }
        ],
        "evidence": [
            {
                "evidence_id": "evidence-1",
                "path": "src/http_client.py",
                "line_start": 12,
                "line_end": 15,
                "observation": "The parsed host is connected without an address-class check.",
            }
        ],
        "capability": (
            None
            if mode == "consume-external-evidence"
            else {"receipt_sha256": DIGEST, "agy.agent.execution": "passed"}
        ),
    }
    return request, packet


def _is_normal_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "://" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not any(token in value for token in ("*", "?", "["))
    )


def _inside_scope(path: str, scopes: list[str]) -> bool:
    candidate = PurePosixPath(path)
    return any(
        candidate == PurePosixPath(scope) or PurePosixPath(scope) in candidate.parents
        for scope in scopes
    )


def _validate(request: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    contract = _contract()
    request_contract = contract["request"]
    packet_contract = contract["evidence_packet"]
    errors: list[str] = []

    if set(request) != set(request_contract["required_fields"]):
        errors.append("request fields are not closed")
    if request.get("schema") != request_contract["schema"]:
        errors.append("request schema is invalid")
    reviewer = request.get("reviewer", {})
    if not isinstance(reviewer, dict):
        return errors + ["request reviewer must be an object"]
    if set(reviewer) != set(request_contract["reviewer_required_fields"]):
        errors.append("request reviewer fields are not closed")
    for field in ("request_id", "subject_producer_id"):
        if not isinstance(request.get(field), str) or not request[field].strip():
            errors.append(f"{field} is blank")
    if not isinstance(reviewer.get("reviewer_id"), str) or not reviewer["reviewer_id"].strip():
        errors.append("request reviewer_id is blank")
    if request.get("execution_mode") not in request_contract["execution_modes"]:
        errors.append("execution mode is invalid")
    if reviewer.get("identity_source") not in request_contract["identity_sources"]:
        errors.append("identity source is invalid")
    if reviewer.get("reviewer_id") == request.get("subject_producer_id"):
        errors.append("self-certified review")

    scopes = request.get("scope_paths", [])
    focuses = request.get("focus_categories", [])
    if (
        not isinstance(scopes, list)
        or not scopes
        or not all(isinstance(path, str) for path in scopes)
        or len(scopes) != len(set(scopes))
        or not all(_is_normal_relative_path(path) for path in scopes)
    ):
        errors.append("scope paths are not bounded")
    if (
        not isinstance(focuses, list)
        or not focuses
        or not all(isinstance(category, str) for category in focuses)
        or len(focuses) != len(set(focuses))
        or not set(focuses) <= set(request_contract["categories"])
    ):
        errors.append("focus categories are invalid")

    if set(packet) != set(packet_contract["required_fields"]):
        errors.append("packet fields are not closed")
    if packet.get("schema") != packet_contract["schema"]:
        errors.append("packet schema is invalid")
    if packet.get("request_id") != request.get("request_id"):
        errors.append("request identity does not match")

    packet_reviewer = packet.get("reviewer", {})
    if not isinstance(packet_reviewer, dict):
        return errors + ["packet reviewer must be an object"]
    if set(packet_reviewer) != set(packet_contract["reviewer_required_fields"]):
        errors.append("packet reviewer fields are not closed")
    for field in ("reviewer_id", "identity_source"):
        if packet_reviewer.get(field) != reviewer.get(field):
            errors.append(f"reviewer {field} does not match")

    findings = packet.get("findings", [])
    checks = packet.get("checks", [])
    evidence = packet.get("evidence", [])
    if (
        not isinstance(findings, list)
        or not isinstance(checks, list)
        or not isinstance(evidence, list)
    ):
        return errors + ["findings, checks, and evidence must be lists"]
    if not checks or not evidence:
        errors.append("evidence-free completion")

    collections = (
        (findings, "finding_id", packet_contract["finding_required_fields"]),
        (checks, "check_id", packet_contract["check_required_fields"]),
        (evidence, "evidence_id", packet_contract["evidence_required_fields"]),
    )
    for rows, identifier, fields in collections:
        ids = [row.get(identifier) for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or any(
            not isinstance(row, dict) or set(row) != set(fields) for row in rows
        ):
            errors.append(f"{identifier} fields are not closed")
        if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(
            set(ids)
        ):
            errors.append(f"{identifier} values are invalid")
    if any(not isinstance(row, dict) for rows, _, _ in collections for row in rows):
        return errors

    evidence_ids = {row.get("evidence_id") for row in evidence}
    check_ids = {row.get("check_id") for row in checks}
    for row in evidence:
        line_start = row.get("line_start")
        line_end = row.get("line_end")
        if not _is_normal_relative_path(row.get("path")) or not _inside_scope(
            row.get("path", ""), scopes
        ):
            errors.append("evidence path is outside scope")
        if (
            not isinstance(line_start, int)
            or isinstance(line_start, bool)
            or not isinstance(line_end, int)
            or isinstance(line_end, bool)
            or line_start < 1
            or line_end < line_start
        ):
            errors.append("evidence line range is invalid")
        if not isinstance(row.get("observation"), str) or not row["observation"].strip():
            errors.append("evidence observation is blank")

    for row in checks:
        if row.get("status") not in packet_contract["check_statuses"]:
            errors.append("check status is invalid")
        if not row.get("evidence_ids") or not set(row["evidence_ids"]) <= evidence_ids:
            errors.append("check evidence reference is invalid")
        if not isinstance(row.get("detail"), str) or not row["detail"].strip():
            errors.append("check detail is blank")

    for row in findings:
        if row.get("severity") not in packet_contract["severities"]:
            errors.append("finding severity is invalid")
        if row.get("category") not in focuses:
            errors.append("finding category is outside the request")
        if not row.get("evidence_ids") or not set(row["evidence_ids"]) <= evidence_ids:
            errors.append("finding evidence reference is invalid")
        if not row.get("validation_check_ids") or not set(row["validation_check_ids"]) <= check_ids:
            errors.append("finding validation reference is invalid")
        for field in ("location", "impact", "fix"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"finding {field} is blank")

    verdict = packet.get("verdict")
    if verdict not in packet_contract["verdicts"]:
        errors.append("verdict is invalid")
    if verdict == "no-findings" and (
        findings or any(check.get("status") != "pass" for check in checks)
    ):
        errors.append("no-findings verdict is not supported")
    if verdict == "findings-present" and not findings:
        errors.append("findings-present verdict has no findings")

    mode = request.get("execution_mode")
    capability = packet.get("capability")
    independence = packet_reviewer.get("host_independence_performed")
    if mode == "consume-external-evidence":
        if reviewer.get("identity_source") != "external" or capability is not None or independence:
            errors.append("external evidence makes an independence claim")
    elif mode == "originate-independent-reviewer":
        expected_fields = set(packet_contract["capability_required_fields"])
        if reviewer.get("identity_source") != "antigravity-host" or not independence:
            errors.append("originated reviewer identity is invalid")
        if not isinstance(capability, dict) or set(capability) != expected_fields:
            errors.append("capability evidence is not closed")
        elif (
            not re.fullmatch(r"[0-9a-f]{64}", capability["receipt_sha256"])
            or capability["agy.agent.execution"] != "passed"
        ):
            errors.append("agy.agent.execution is not passed")

    return errors


def test_appsec_audit_preserves_bounded_findings_and_validation() -> None:
    external_request, external_packet = _valid_documents()
    originated_request, originated_packet = _valid_documents(mode="originate-independent-reviewer")

    assert _validate(external_request, external_packet) == []
    assert _validate(originated_request, originated_packet) == []

    skill = _skill_text()
    assert "plugins/fleet-core/scripts/fleet_commons/models.json" in skill
    assert "plugins/fleet-core/scripts/fleet_commons/tier_resolver.py" in skill
    assert "plugins/fleet-core/scripts/fleet_commons/effort_rider.py" in skill
    assert "`agy.agent.execution` as `passed`" in skill


def test_appsec_audit_preserves_bounded_findings_and_validation_rejects_negative_cases() -> None:
    request, packet = _valid_documents()
    negative_cases: list[tuple[dict[str, Any], dict[str, Any]]] = []

    self_certified_request = copy.deepcopy(request)
    self_certified_request["reviewer"]["reviewer_id"] = "implementation-worker"
    self_certified_packet = copy.deepcopy(packet)
    self_certified_packet["reviewer"]["reviewer_id"] = "implementation-worker"
    negative_cases.append((self_certified_request, self_certified_packet))

    unbounded_request = copy.deepcopy(request)
    unbounded_request["scope_paths"] = ["../outside.py"]
    negative_cases.append((unbounded_request, copy.deepcopy(packet)))

    evidence_free = copy.deepcopy(packet)
    evidence_free["findings"] = []
    evidence_free["checks"] = []
    evidence_free["evidence"] = []
    evidence_free["verdict"] = "no-findings"
    negative_cases.append((copy.deepcopy(request), evidence_free))

    unbound_finding = copy.deepcopy(packet)
    unbound_finding["findings"][0]["evidence_ids"] = ["missing"]
    negative_cases.append((copy.deepcopy(request), unbound_finding))

    unknown_field = copy.deepcopy(packet)
    unknown_field["narrated_independence"] = True
    negative_cases.append((copy.deepcopy(request), unknown_field))

    false_independence = copy.deepcopy(packet)
    false_independence["reviewer"]["host_independence_performed"] = True
    negative_cases.append((copy.deepcopy(request), false_independence))

    origin_request, unavailable_capability = _valid_documents(mode="originate-independent-reviewer")
    unavailable_capability["capability"]["agy.agent.execution"] = "unavailable"
    negative_cases.append((origin_request, unavailable_capability))

    unsafe_verdict = copy.deepcopy(packet)
    unsafe_verdict["verdict"] = "no-findings"
    negative_cases.append((copy.deepcopy(request), unsafe_verdict))

    for invalid_request, invalid_packet in negative_cases:
        assert _validate(invalid_request, invalid_packet)
