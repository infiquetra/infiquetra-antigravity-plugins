"""Antigravity capability catalog, promotable receipt, and consumer evaluation.

The catalog is stored as the JSON-compatible subset of YAML so installed
``fleet-core`` remains standard-library only. Catalog rows may select a
registered probe method and revision, but cannot provide executable commands.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

CATALOG_SCHEMA = "antigravity.capability-catalog.v1"
RECEIPT_SCHEMA = "antigravity.capabilities.v1"
EVALUATION_SCHEMA = "antigravity.capability-evaluation.v1"
MAX_RECEIPT_BYTES = 256 * 1024
MAX_PROMOTABLE_VALUE_LENGTH = 128

RAW_STATES = frozenset({"passed", "failed", "unknown", "unavailable"})
EVALUATION_STATES = frozenset({"passed", "blocked", "degraded"})
FALLBACK_STATES = frozenset({"unknown", "unavailable"})

PROBE_METHOD_REVISIONS: dict[str, int] = {
    "agy-version": 1,
    "agy-help-flags": 1,
    "antigravity-host-version": 1,
    "plugin-links": 1,
    "plugin-load": 1,
    "plugin-validation": 1,
    "controlled-model-selection": 1,
    "controlled-effort-selection": 1,
    "controlled-agent-execution": 1,
    "controlled-resume": 1,
    "controlled-plan-mode": 1,
    "controlled-sandbox": 1,
    "controlled-sequential-isolation": 1,
    "runtime-root-discovery": 1,
}

RUNTIME_ROOT_ROLES = frozenset(
    {
        "repository",
        "plugin-install",
        "saga-state",
        "conversation-artifacts",
        "brain-artifacts",
    }
)

FACT_IDS = frozenset(
    {
        "model-selection",
        "effort-selection",
        "agent-execution",
        "conversation-resume",
        "plan-mode",
        "plugin-links",
        "plugin-load",
        "plugin-validation",
        "sandbox-isolation",
        "sequential-isolation",
    }
)

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(
    r"^[0-9]+(?:[.][0-9]+){1,3}"
    r"(?:-(?:alpha|beta|rc|dev)(?:[.-]?[0-9]+)?)?$"
)
_FLAG_RE = re.compile(r"^--[a-z0-9]+(?:-[a-z0-9]+)*$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MODEL_RE = re.compile(
    r"^(?:"
    r"gemini-[0-9]+(?:[.][0-9]+)*-(?:pro|flash)(?:-[a-z0-9]+)*"
    r"|gpt-[0-9]+(?:[.][0-9]+)*(?:-[a-z0-9]+)*"
    r"|claude-(?:haiku|sonnet|opus)-[0-9]+(?:[.][0-9]+)*"
    r"|codex-[0-9]+(?:[.][0-9]+)*(?:-[a-z0-9]+)*"
    r"|o[0-9]+(?:-[a-z0-9]+)*"
    r")$"
)
_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
_HOSTNAME_SUFFIXES = (".local", ".lan", ".home", ".internal")
_CREDENTIAL_SHAPE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|authorization|bearer[ _-]|"
    r"password|secret|ghp_|github_pat_|glpat-|xox[baprs]-|npm_|pypi-AgEI|ya29[.]|"
    r"sk-[A-Za-z0-9]|A(?:KI|SI)A[0-9A-Z]{8,}|"
    r"eyJ[A-Za-z0-9_-]{8,}[.][A-Za-z0-9_-]{8,}[.][A-Za-z0-9_-]{8,})"
)
CAPABILITY_FACT_IDS = {
    "agy.model.selection": "model-selection",
    "agy.effort.selection": "effort-selection",
    "agy.agent.execution": "agent-execution",
    "agy.conversation.resume": "conversation-resume",
    "agy.plan.mode": "plan-mode",
    "antigravity.plugin.links": "plugin-links",
    "antigravity.plugin.load": "plugin-load",
    "antigravity.plugin.validation": "plugin-validation",
    "agy.sandbox.isolation": "sandbox-isolation",
    "agy.sequential.isolation": "sequential-isolation",
}
FACT_CAPABILITY_IDS = {
    fact_id: capability_id for capability_id, fact_id in CAPABILITY_FACT_IDS.items()
}
BOOLEAN_FACT_IDS = frozenset(
    {
        "agent-execution",
        "conversation-resume",
        "plan-mode",
        "plugin-links",
        "plugin-load",
        "plugin-validation",
        "sandbox-isolation",
        "sequential-isolation",
    }
)

_CATALOG_KEYS = frozenset({"catalog_schema", "receipt_schema", "catalog_revision", "capabilities"})
_CAPABILITY_KEYS = frozenset(
    {
        "id",
        "revision",
        "description",
        "allowed_values",
        "probe_method",
        "probe_revision",
        "expected_evidence",
        "required_for",
        "outcome_rules",
        "fallback",
    }
)
_FALLBACK_KEYS = frozenset({"capability", "for_consumers", "when_states"})
_RECEIPT_KEYS = frozenset(
    {
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
)
_RESULT_KEYS = frozenset({"id", "probe_revision", "state", "evidence"})


class CapabilityContractError(ValueError):
    """Raised when invalid evidence is passed to consumer evaluation."""


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _extra_keys(value: Mapping[str, Any], allowed: frozenset[str], path: str) -> list[str]:
    return [f"{path}: unknown field" for _key in sorted(set(value) - allowed)]


def _validate_id(value: object, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        errors.append(f"{path}: expected a lowercase dotted identifier")
        return None
    return value


def _validate_id_list(value: object, path: str, errors: list[str]) -> list[str]:
    if not _is_sequence(value):
        errors.append(f"{path}: expected a list of identifiers")
        return []
    result: list[str] = []
    for index, item in enumerate(cast(Sequence[object], value)):
        valid = _validate_id(item, f"{path}[{index}]", errors)
        if valid is not None:
            result.append(valid)
    if len(result) != len(set(result)):
        errors.append(f"{path}: duplicate identifiers are not allowed")
    return result


def canonical_catalog_digest(catalog: Mapping[str, Any]) -> str:
    """Return the stable SHA-256 digest for a parsed catalog."""

    encoded = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_catalog(path: Path | str) -> dict[str, Any]:
    """Load and validate a JSON-compatible YAML catalog."""

    source = Path(path)
    try:
        parsed = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityContractError("could not load capability catalog") from exc
    errors = validate_catalog(parsed)
    if errors:
        raise CapabilityContractError("invalid capability catalog: " + "; ".join(errors))
    return cast(dict[str, Any], parsed)


def load_receipt(
    path: Path | str,
    catalog: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load one bounded JSON receipt and validate it before returning it."""

    source = Path(path)
    try:
        if source.stat().st_size > MAX_RECEIPT_BYTES:
            raise CapabilityContractError("capability receipt exceeds the size limit")
        raw = source.read_bytes()
    except OSError as exc:
        raise CapabilityContractError("capability receipt could not be read") from exc
    if len(raw) > MAX_RECEIPT_BYTES:
        raise CapabilityContractError("capability receipt exceeds the size limit")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityContractError("capability receipt is not valid UTF-8 JSON") from exc
    errors = validate_receipt(parsed, catalog)
    if errors:
        raise CapabilityContractError("capability receipt failed strict validation")
    return cast(dict[str, Any], parsed)


def validate_catalog(catalog: object) -> list[str]:
    """Validate the closed capability-catalog schema. Empty means valid."""

    if not isinstance(catalog, dict):
        return [f"catalog: expected an object, got {type(catalog).__name__}"]

    errors = _extra_keys(catalog, _CATALOG_KEYS, "catalog")
    if catalog.get("catalog_schema") != CATALOG_SCHEMA:
        errors.append(f"catalog.catalog_schema: expected {CATALOG_SCHEMA!r}")
    if catalog.get("receipt_schema") != RECEIPT_SCHEMA:
        errors.append(f"catalog.receipt_schema: expected {RECEIPT_SCHEMA!r}")
    revision = catalog.get("catalog_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append("catalog.catalog_revision: expected a positive integer")

    capabilities = catalog.get("capabilities")
    if not _is_sequence(capabilities) or not capabilities:
        errors.append("catalog.capabilities: expected a non-empty list")
        return errors

    seen_ids: set[str] = set()
    rows: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(capabilities):
        path = f"catalog.capabilities[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path}: expected an object")
            continue
        errors.extend(_extra_keys(row, _CAPABILITY_KEYS, path))
        capability_id = _validate_id(row.get("id"), f"{path}.id", errors)
        if capability_id is not None:
            if capability_id in seen_ids:
                errors.append(f"{path}.id: duplicate capability")
            seen_ids.add(capability_id)
            rows[capability_id] = row

        row_revision = row.get("revision")
        if not isinstance(row_revision, int) or isinstance(row_revision, bool) or row_revision < 1:
            errors.append(f"{path}.revision: expected a positive integer")
        description = row.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{path}.description: expected non-empty text")

        method = row.get("probe_method")
        if method not in PROBE_METHOD_REVISIONS:
            errors.append(f"{path}.probe_method: unknown registered method")
        expected_revision = PROBE_METHOD_REVISIONS.get(method) if isinstance(method, str) else None
        if row.get("probe_revision") != expected_revision:
            errors.append(
                f"{path}.probe_revision: expected registered revision {expected_revision!r}"
            )

        evidence = _validate_id_list(
            row.get("expected_evidence"), f"{path}.expected_evidence", errors
        )
        if not evidence:
            errors.append(f"{path}.expected_evidence: expected at least one evidence identifier")
        required_for = _validate_id_list(row.get("required_for"), f"{path}.required_for", errors)
        allowed_values = row.get("allowed_values")
        if capability_id == "agy.model.selection":
            if not _is_sequence(allowed_values) or not allowed_values:
                errors.append(f"{path}.allowed_values: expected a non-empty model allowlist")
            else:
                model_values = cast(Sequence[object], allowed_values)
                string_models = [value for value in model_values if isinstance(value, str)]
                if len(string_models) != len(model_values):
                    errors.append(f"{path}.allowed_values: invalid canonical model identifier")
                if len(string_models) != len(set(string_models)):
                    errors.append(f"{path}.allowed_values: duplicate values are not allowed")
                for value in model_values:
                    if (
                        not isinstance(value, str)
                        or len(value) > MAX_PROMOTABLE_VALUE_LENGTH
                        or _CREDENTIAL_SHAPE_RE.search(value) is not None
                        or not _MODEL_RE.fullmatch(value)
                    ):
                        errors.append(f"{path}.allowed_values: invalid canonical model identifier")
        elif "allowed_values" in row:
            errors.append(f"{path}.allowed_values: unexpected for this capability")

        outcome_rules = row.get("outcome_rules")
        if not isinstance(outcome_rules, dict):
            errors.append(f"{path}.outcome_rules: expected an object")
        else:
            expected_rule_keys = set(RAW_STATES)
            if set(outcome_rules) != expected_rule_keys:
                errors.append(
                    f"{path}.outcome_rules: expected exactly {sorted(expected_rule_keys)}"
                )
            for state, rule in outcome_rules.items():
                if state in RAW_STATES and (
                    not isinstance(rule, str) or not _ID_RE.fullmatch(rule)
                ):
                    errors.append(
                        f"{path}.outcome_rules.{state}: expected a stable rule identifier"
                    )

        fallback = row.get("fallback")
        if fallback is not None:
            if not isinstance(fallback, dict):
                errors.append(f"{path}.fallback: expected an object or null")
            else:
                errors.extend(_extra_keys(fallback, _FALLBACK_KEYS, f"{path}.fallback"))
                _validate_id(fallback.get("capability"), f"{path}.fallback.capability", errors)
                consumers = _validate_id_list(
                    fallback.get("for_consumers"),
                    f"{path}.fallback.for_consumers",
                    errors,
                )
                overlap = sorted(set(consumers) & set(required_for))
                if overlap:
                    errors.append(
                        f"{path}.fallback.for_consumers: required consumers cannot degrade"
                    )
                when_states = fallback.get("when_states")
                if not _is_sequence(when_states) or not when_states:
                    errors.append(f"{path}.fallback.when_states: expected a non-empty list")
                else:
                    invalid_states = sorted(set(when_states) - FALLBACK_STATES)
                    if invalid_states:
                        errors.append(f"{path}.fallback.when_states: unsupported state")

    for capability_id, row in rows.items():
        fallback = row.get("fallback")
        if not isinstance(fallback, dict):
            continue
        fallback_id = fallback.get("capability")
        if fallback_id == capability_id:
            errors.append("catalog capability fallback cannot reference itself")
        elif fallback_id not in rows:
            errors.append("catalog capability references an unknown fallback")
    return errors


def _validate_version(value: object, path: str, errors: list[str]) -> None:
    is_ip_address = False
    if isinstance(value, str):
        try:
            ipaddress.ip_address(value)
        except ValueError:
            pass
        else:
            is_ip_address = True
    if value is not None and (
        not isinstance(value, str)
        or len(value) > MAX_PROMOTABLE_VALUE_LENGTH
        or _CREDENTIAL_SHAPE_RE.search(value) is not None
        or value.lower().endswith(_HOSTNAME_SUFFIXES)
        or is_ip_address
        or not _VERSION_RE.fullmatch(value)
    ):
        errors.append(f"{path}: expected a normalized version string or null")


def _validate_facts(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return
    for key, fact in value.items():
        if key not in FACT_IDS:
            errors.append(f"{path}: unknown fact")
            continue
        if fact is None:
            continue
        if key == "model-selection":
            if (
                not isinstance(fact, str)
                or len(fact) > MAX_PROMOTABLE_VALUE_LENGTH
                or _CREDENTIAL_SHAPE_RE.search(fact) is not None
                or not _MODEL_RE.fullmatch(fact)
                or fact.lower().endswith(_HOSTNAME_SUFFIXES)
            ):
                errors.append(f"{path}.{key}: expected a normalized model identifier or null")
        elif key == "effort-selection":
            if fact not in _EFFORTS:
                errors.append(f"{path}.{key}: expected a normalized effort or null")
        elif not isinstance(fact, bool):
            errors.append(f"{path}.{key}: expected bool or null")


def validate_receipt(receipt: object, catalog: Mapping[str, Any] | None = None) -> list[str]:
    """Validate a strict promotable capability receipt. Empty means valid."""

    if not isinstance(receipt, dict):
        return [f"receipt: expected an object, got {type(receipt).__name__}"]
    errors = _extra_keys(receipt, _RECEIPT_KEYS, "receipt")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append(f"receipt.schema: expected {RECEIPT_SCHEMA!r}")

    digest = receipt.get("catalog_digest")
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
        errors.append("receipt.catalog_digest: expected a lowercase SHA-256 digest")
    if catalog is not None:
        catalog_errors = validate_catalog(catalog)
        if catalog_errors:
            errors.append("receipt.catalog: supplied catalog is invalid")
        elif digest != canonical_catalog_digest(catalog):
            errors.append("receipt.catalog_digest: does not match the supplied catalog")

    _validate_version(receipt.get("agy_cli_version"), "receipt.agy_cli_version", errors)
    _validate_version(
        receipt.get("antigravity_host_version"),
        "receipt.antigravity_host_version",
        errors,
    )

    flags = receipt.get("supported_flags")
    if not _is_sequence(flags):
        errors.append("receipt.supported_flags: expected a list")
    else:
        flag_values = cast(Sequence[object], flags)
        if len(flag_values) != len(set(flag_values)):
            errors.append("receipt.supported_flags: duplicate flags are not allowed")
        for index, flag in enumerate(flag_values):
            if (
                not isinstance(flag, str)
                or len(flag) > MAX_PROMOTABLE_VALUE_LENGTH
                or _CREDENTIAL_SHAPE_RE.search(flag) is not None
                or not _FLAG_RE.fullmatch(flag)
            ):
                errors.append(f"receipt.supported_flags[{index}]: invalid normalized flag")

    runtime_roots = receipt.get("runtime_roots")
    if not _is_sequence(runtime_roots):
        errors.append("receipt.runtime_roots: expected a list of logical roles")
    else:
        root_values = cast(Sequence[object], runtime_roots)
        if len(root_values) != len(set(root_values)):
            errors.append("receipt.runtime_roots: duplicate roles are not allowed")
        for index, role in enumerate(root_values):
            if role not in RUNTIME_ROOT_ROLES:
                errors.append(f"receipt.runtime_roots[{index}]: unknown logical role")

    _validate_facts(receipt.get("requested_facts"), "receipt.requested_facts", errors)
    _validate_facts(receipt.get("observed_facts"), "receipt.observed_facts", errors)

    catalog_rows: dict[str, Mapping[str, Any]] = {}
    if catalog is not None and not validate_catalog(catalog):
        catalog_rows = {
            row["id"]: row
            for row in catalog["capabilities"]
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }

    results = receipt.get("results")
    if not _is_sequence(results):
        errors.append("receipt.results: expected a list")
        return errors
    seen: set[str] = set()
    for index, result in enumerate(cast(Sequence[object], results)):
        path = f"receipt.results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{path}: expected an object")
            continue
        errors.extend(_extra_keys(result, _RESULT_KEYS, path))
        result_id = _validate_id(result.get("id"), f"{path}.id", errors)
        if result_id is not None:
            if result_id in seen:
                errors.append(f"{path}.id: duplicate result")
            seen.add(result_id)
            if catalog_rows and result_id not in catalog_rows:
                errors.append(f"{path}.id: capability is not present in the supplied catalog")

        probe_revision = result.get("probe_revision")
        if not isinstance(probe_revision, int) or isinstance(probe_revision, bool):
            errors.append(f"{path}.probe_revision: expected an integer")
        elif result_id in catalog_rows:
            expected = catalog_rows[result_id]["probe_revision"]
            if probe_revision != expected:
                errors.append(f"{path}.probe_revision: expected {expected!r}")

        if result.get("state") not in RAW_STATES:
            errors.append(f"{path}.state: expected one of {sorted(RAW_STATES)}")
        state = result.get("state")
        evidence = _validate_id_list(result.get("evidence"), f"{path}.evidence", errors)
        if result_id in catalog_rows:
            allowed_evidence = set(catalog_rows[result_id]["expected_evidence"])
            unexpected = sorted(set(evidence) - allowed_evidence)
            if unexpected:
                errors.append(f"{path}.evidence: contains identifiers not declared by catalog")
            if result.get("state") == "passed" and set(evidence) != allowed_evidence:
                errors.append(f"{path}.evidence: passed result must contain all declared evidence")

        fact_id = CAPABILITY_FACT_IDS.get(result_id or "")
        if fact_id is not None:
            requested_facts = receipt.get("requested_facts")
            observed_facts = receipt.get("observed_facts")
            requested = requested_facts.get(fact_id) if isinstance(requested_facts, dict) else None
            observed = observed_facts.get(fact_id) if isinstance(observed_facts, dict) else None
            if fact_id == "model-selection" and (requested is not None or observed is not None):
                model_row = catalog_rows.get(result_id or "")
                if model_row is None:
                    errors.append(
                        f"{path}.state: model facts require the supplied capability catalog"
                    )
                else:
                    allowed_models = set(model_row.get("allowed_values", []))
                    if requested not in allowed_models or (
                        observed is not None and observed not in allowed_models
                    ):
                        errors.append(f"{path}.state: model fact is not in the catalog allowlist")
            if fact_id in BOOLEAN_FACT_IDS and requested is not None and requested is not True:
                errors.append(f"{path}.state: boolean capability requests must be true")
            if state == "passed" and (
                requested is None
                or requested != observed
                or (fact_id in BOOLEAN_FACT_IDS and observed is not True)
            ):
                errors.append(
                    f"{path}.state: passed result requires matching requested and observed facts"
                )
            elif state == "failed" and (
                requested is None or observed is None or requested == observed
            ):
                errors.append(
                    f"{path}.state: failed result requires differing requested and observed facts"
                )
            elif state in FALLBACK_STATES:
                if evidence:
                    errors.append(f"{path}.evidence: non-observed result must not claim evidence")
                if observed is not None:
                    errors.append(
                        f"{path}.state: non-observed result must not retain an observed fact"
                    )

        if result_id == "agy.cli.version" and state == "passed":
            if receipt.get("agy_cli_version") is None:
                errors.append(f"{path}.state: passed result requires the observed CLI version")
        elif result_id == "antigravity.host.version" and state == "passed":
            if receipt.get("antigravity_host_version") is None:
                errors.append(f"{path}.state: passed result requires the observed host version")
        elif result_id == "antigravity.runtime.roots" and state == "passed":
            observed_roots = (
                set(cast(Sequence[object], runtime_roots)) if _is_sequence(runtime_roots) else set()
            )
            if observed_roots != RUNTIME_ROOT_ROLES:
                errors.append(f"{path}.state: passed result requires every logical runtime root")

    requested_facts = receipt.get("requested_facts")
    observed_facts = receipt.get("observed_facts")
    if isinstance(requested_facts, dict) and isinstance(observed_facts, dict):
        if set(requested_facts) != set(observed_facts):
            errors.append("receipt requested and observed fact identifiers must match")
        result_capabilities = {
            result.get("id")
            for result in cast(Sequence[object], results)
            if isinstance(result, dict)
        }
        for fact_id in set(requested_facts) | set(observed_facts):
            capability_id = FACT_CAPABILITY_IDS.get(fact_id)
            if capability_id is not None and capability_id not in result_capabilities:
                errors.append("receipt facts must correspond to a present controlled result")
    return errors


def evaluate_for_consumer(
    receipt: Mapping[str, Any],
    catalog: Mapping[str, Any],
    consumer: str,
) -> dict[str, Any]:
    """Evaluate one consumer without translating the shared state vocabulary."""

    catalog_errors = validate_catalog(catalog)
    receipt_errors = validate_receipt(receipt, catalog)
    if catalog_errors or receipt_errors:
        raise CapabilityContractError(
            "invalid capability evidence: " + "; ".join(catalog_errors + receipt_errors)
        )
    if not _ID_RE.fullmatch(consumer):
        raise CapabilityContractError("consumer must be a lowercase dotted identifier")

    result_by_id = {result["id"]: result for result in receipt["results"]}
    blocking: list[str] = []
    degraded: list[str] = []
    fallbacks: dict[str, str] = {}

    for row in catalog["capabilities"]:
        capability_id = row["id"]
        result = result_by_id.get(capability_id)
        state = result["state"] if result is not None else "unknown"
        required = consumer in row["required_for"]
        if required and state != "passed":
            blocking.append(capability_id)
            continue
        if required or state == "passed":
            continue

        fallback = row["fallback"]
        if not isinstance(fallback, dict):
            continue
        if consumer not in fallback["for_consumers"]:
            continue
        fallback_id = fallback["capability"]
        fallback_result = result_by_id.get(fallback_id)
        if (
            state in fallback["when_states"]
            and fallback_result is not None
            and fallback_result["state"] == "passed"
        ):
            degraded.append(capability_id)
            fallbacks[capability_id] = fallback_id
        else:
            blocking.append(capability_id)

    evaluation_state = "blocked" if blocking else "degraded" if degraded else "passed"
    return {
        "schema": EVALUATION_SCHEMA,
        "consumer": consumer,
        "state": evaluation_state,
        "blocking_capabilities": sorted(blocking),
        "degraded_capabilities": sorted(degraded),
        "fallbacks": dict(sorted(fallbacks.items())),
    }
