"""``bridge_receipt.v1`` — the one proof-of-execution contract every engine bridge emits (#383, U1).

Rationale (plan ``2026-07-06-external-engine-http-bridge-receipt-pair-plan.md``, KTD6/KTD7): three
consumers across two plugins today (saga's dispatch manifest gating, saga's HTTP bridge, agy's
delegate), a fourth coming (#476 ``plugins/codex/``). A saga-local module imported by agy would break
at install time (journal ``{#marketplace-install-layout-no-import-path}``), so the schema, the builder,
and the validator live once here in fleet-commons and are loaded by consumers through their vendored
``fleet_commons_shim`` (``fleet_commons_shim.load("bridge_receipt")``).

A receipt has a common core (present on every transport) plus a transport-discriminated ``runner``
section that proves what actually ran:

* ``transport: cli``  — ``runner`` carries ``pid``, ``argv``, ``exit_code``.
* ``transport: http`` — ``runner`` carries ``url``, ``status_code``, ``model``.

``emit_receipt(...)`` builds a schema-valid receipt from keyword data (dispatching the ``runner``
section shape off ``transport``). ``validate_receipt(receipt)`` returns a list of human-readable
error strings — empty means valid — so callers can gate on ``not validate_receipt(receipt)`` without
raising, and can surface *why* a receipt is rejected (missing field, wrong section for the declared
transport, unknown schema version) rather than a bare boolean.

No secrets ever belong in a receipt: callers must resolve credentials at call time and never pass
them through ``emit_receipt`` (see plan's "no receipts/telemetry ever carry a resolved API key").
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_NAME = "bridge_receipt.v1"
SCHEMA_VERSIONS = (SCHEMA_NAME,)

TRANSPORT_CLI = "cli"
TRANSPORT_HTTP = "http"
TRANSPORTS = (TRANSPORT_CLI, TRANSPORT_HTTP)

# Common core fields present on every receipt regardless of transport.
COMMON_FIELDS = (
    "schema",
    "engine_id",
    "variant",
    "transport",
    "wall_time_s",
    "bytes_produced",
)

# Transport-discriminated ``runner`` section field requirements.
RUNNER_FIELDS: dict[str, tuple[str, ...]] = {
    TRANSPORT_CLI: ("pid", "argv", "exit_code"),
    TRANSPORT_HTTP: ("url", "status_code", "model"),
}

PORTABLE_SCHEMA_NAME = "antigravity.bridge-receipt.v2"
OBSERVATION_STATES = frozenset({"passed", "failed", "unknown", "unavailable"})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def emit_receipt(
    *,
    engine_id: str,
    variant: str,
    transport: str,
    wall_time_s: float,
    bytes_produced: int,
    runner: dict[str, Any],
) -> dict[str, Any]:
    """Build a schema-valid ``bridge_receipt.v1`` dict.

    ``runner`` must carry exactly the fields required for ``transport`` (see ``RUNNER_FIELDS``); a
    ``cli`` receipt's runner section is ``{"pid": ..., "argv": ..., "exit_code": ...}`` and an
    ``http`` receipt's is ``{"url": ..., "status_code": ..., "model": ...}``. Extra keys in
    ``runner`` are passed through unchanged (forward-compatible), but the required keys for the
    declared transport must all be present or the built receipt will fail ``validate_receipt``.

    Raises ``ValueError`` for an unknown ``transport`` — callers can't accidentally mislabel a
    receipt with a transport this module doesn't know how to validate.
    """
    if transport not in TRANSPORTS:
        raise ValueError(f"unknown transport {transport!r}; expected one of {TRANSPORTS}")

    return {
        "schema": SCHEMA_NAME,
        "engine_id": engine_id,
        "variant": variant,
        "transport": transport,
        "wall_time_s": wall_time_s,
        "bytes_produced": bytes_produced,
        "runner": dict(runner),
    }


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
    """Validate a receipt dict against ``bridge_receipt.v1``. Empty list means valid.

    Checks, in order: receipt is a dict; ``schema`` is present and a known version; every common
    field is present; ``transport`` is a known transport; ``runner`` is present and is a dict
    carrying exactly the fields required for the declared transport (missing fields are named;
    fields belonging to the *other* transport's section are flagged as a transport/section
    mismatch rather than silently accepted).
    """
    errors: list[str] = []

    if not isinstance(receipt, dict):
        return [f"receipt must be a dict, got {type(receipt).__name__}"]

    schema = receipt.get("schema")
    if schema is None:
        errors.append("missing required field: schema")
    elif schema not in SCHEMA_VERSIONS:
        errors.append(f"unknown schema version: {schema!r} (expected one of {SCHEMA_VERSIONS})")

    for field in COMMON_FIELDS:
        if field == "schema":
            continue
        if field not in receipt:
            errors.append(f"missing required field: {field}")

    transport = receipt.get("transport")
    if transport is not None and transport not in TRANSPORTS:
        errors.append(f"unknown transport: {transport!r} (expected one of {TRANSPORTS})")

    runner = receipt.get("runner")
    if "runner" not in receipt:
        errors.append("missing required field: runner")
    elif not isinstance(runner, dict):
        errors.append(f"runner must be a dict, got {type(runner).__name__}")
    elif transport in RUNNER_FIELDS:
        required = RUNNER_FIELDS[transport]
        missing = [f for f in required if f not in runner]
        for field in missing:
            errors.append(
                f"runner section missing required field for transport {transport!r}: {field}"
            )

        other_transport = TRANSPORT_HTTP if transport == TRANSPORT_CLI else TRANSPORT_CLI
        other_only = set(RUNNER_FIELDS[other_transport]) - set(required)
        present_other_only = other_only & set(runner)
        if present_other_only and missing:
            errors.append(
                f"runner section looks like {other_transport!r} shape but transport is "
                f"{transport!r}: found {sorted(present_other_only)}, missing {missing}"
            )

    return errors


def emit_portable_receipt(
    *,
    request_id: str,
    producer: str,
    requested_facts: Mapping[str, Any],
    observed_facts: Mapping[str, Mapping[str, Any]],
    evidence: Sequence[str],
) -> dict[str, Any]:
    """Build a portable receipt without converting requests into observations.

    Observed rows are supplied by an evidence-producing boundary and retain an
    explicit state. ``unknown`` and ``unavailable`` rows intentionally carry no
    value. The builder does not infer an observed value from a requested value.
    """

    return {
        "schema": PORTABLE_SCHEMA_NAME,
        "request_id": request_id,
        "producer": producer,
        "requested_facts": dict(requested_facts),
        "observed_facts": {key: dict(value) for key, value in observed_facts.items()},
        "evidence": list(evidence),
    }


def validate_portable_receipt(receipt: object) -> list[str]:
    """Validate the strict requested-versus-observed portable receipt."""

    if not isinstance(receipt, dict):
        return ["portable receipt must be an object"]
    allowed = {
        "schema",
        "request_id",
        "producer",
        "requested_facts",
        "observed_facts",
        "evidence",
    }
    errors = [f"unknown field: {key}" for key in sorted(set(receipt) - allowed)]
    if receipt.get("schema") != PORTABLE_SCHEMA_NAME:
        errors.append(f"schema must be {PORTABLE_SCHEMA_NAME!r}")
    for field in ("request_id", "producer"):
        value = receipt.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    requested = receipt.get("requested_facts")
    if not isinstance(requested, dict) or not requested:
        errors.append("requested_facts must be a non-empty object")
        requested = {}
    elif any(not isinstance(key, str) or not key for key in requested):
        errors.append("requested_facts keys must be non-empty strings")

    evidence = receipt.get("evidence")
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(not isinstance(item, str) or not _DIGEST_RE.fullmatch(item) for item in evidence)
        or len(evidence) != len(set(evidence))
    ):
        errors.append("evidence must be a non-empty unique list of SHA-256 digests")
        evidence = []

    producer = receipt.get("producer")
    observed = receipt.get("observed_facts")
    if not isinstance(observed, dict) or not observed:
        errors.append("observed_facts must be a non-empty object")
        return errors
    for fact_id, row in observed.items():
        prefix = f"observed_facts[{fact_id!r}]"
        if not isinstance(fact_id, str) or not fact_id:
            errors.append("observed_facts keys must be non-empty strings")
            continue
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        allowed_row = {"state", "value", "observer", "evidence_sha256"}
        if set(row) - allowed_row:
            errors.append(f"{prefix} contains unknown fields")
        state = row.get("state")
        if state not in OBSERVATION_STATES:
            errors.append(f"{prefix}.state is invalid")
        observer = row.get("observer")
        if not isinstance(observer, str) or not observer:
            errors.append(f"{prefix}.observer must be a non-empty string")
        elif observer == producer:
            errors.append(f"{prefix} is self-attested by the receipt producer")
        digest = row.get("evidence_sha256")
        if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
            errors.append(f"{prefix}.evidence_sha256 must be a SHA-256 digest")
        elif digest not in evidence:
            errors.append(f"{prefix}.evidence_sha256 is not bound by evidence")
        if state in {"unknown", "unavailable"} and "value" in row:
            errors.append(f"{prefix} must not invent a value for state {state!r}")
        if state in {"passed", "failed"} and "value" not in row:
            errors.append(f"{prefix} requires an observed value")
    return errors
