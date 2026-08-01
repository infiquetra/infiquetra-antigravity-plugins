#!/usr/bin/env python3
"""Receipt-driven provider telemetry with no live calls or routing authority."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import capability_elo  # noqa: E402
import provider_control_chart  # noqa: E402
import second_opinion  # noqa: E402

PULSE_SCHEMA = "pulse_snapshot.v1"
RUN_FACT_SCHEMA = "run_fact.v1"
SENSITIVE_KEYS = frozenset(
    {"api_key", "authorization", "credential", "password", "secret", "token"}
)


class PulseError(ValueError):
    """Supplied telemetry is malformed, stale, sparse, or requests authority."""


def _parse_time(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PulseError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PulseError(f"{field} must be an ISO-8601 string") from exc
    if parsed.tzinfo is None:
        raise PulseError(f"{field} must include a timezone")
    return parsed.astimezone(UTC)


def _validated_records(
    records: object, *, as_of: datetime, max_age: timedelta, min_samples: int
) -> list[dict[str, Any]]:
    if not isinstance(records, list) or not records:
        raise PulseError("receipts must be a non-empty list")
    if min_samples < 1:
        raise PulseError("min_samples must be positive")
    validated: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = defaultdict(int)
    subplot_ids: set[str] = set()
    evidence_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PulseError(f"receipt {index} must be an object")
        if SENSITIVE_KEYS & {str(key).lower() for key in record}:
            raise PulseError(f"receipt {index} contains a sensitive field")
        if record.get("schema") != RUN_FACT_SCHEMA or record.get("kind") != "engine":
            raise PulseError(f"receipt {index} must be an engine {RUN_FACT_SCHEMA} record")
        for field in ("subplot_id", "at", "provider", "capability", "evidence_sha256"):
            if not isinstance(record.get(field), str) or not record[field]:
                raise PulseError(f"receipt {index} has invalid {field}")
        digest = record["evidence_sha256"]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise PulseError(f"receipt {index} has invalid evidence_sha256")
        if record["subplot_id"] in subplot_ids:
            raise PulseError(f"receipt {index} replays subplot_id {record['subplot_id']!r}")
        if digest in evidence_ids:
            raise PulseError(f"receipt {index} replays evidence_sha256 {digest!r}")
        subplot_ids.add(record["subplot_id"])
        evidence_ids.add(digest)
        observed_at = _parse_time(record["at"], f"receipt {index} at")
        if observed_at > as_of or as_of - observed_at > max_age:
            raise PulseError(f"receipt {index} is stale or future-dated")
        for field in ("quality", "latency_seconds", "cost"):
            value = record.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or float(value) < 0
            ):
                raise PulseError(f"receipt {index} has invalid {field}")
        quality = float(record["quality"])
        if quality > 1.0:
            raise PulseError(f"receipt {index} quality must be between 0 and 1")
        counts[(record["provider"], record["capability"])] += 1
        validated.append(dict(record))
    sparse = sorted(
        f"{provider}::{capability}"
        for (provider, capability), count in counts.items()
        if count < min_samples
    )
    if sparse:
        raise PulseError(f"insufficient evidence for: {', '.join(sparse)}")
    return validated


def build_report(
    records: object,
    *,
    as_of: str,
    max_age_days: int = 30,
    min_samples: int = 3,
    auto_route: bool = False,
) -> dict[str, Any]:
    """Build an advisory snapshot from caller-supplied sanitized receipts only."""

    if auto_route:
        raise PulseError("provider telemetry has no automatic routing authority")
    if max_age_days < 1:
        raise PulseError("max_age_days must be positive")
    observed_as_of = _parse_time(as_of, "as_of")
    rows = _validated_records(
        records,
        as_of=observed_as_of,
        max_age=timedelta(days=max_age_days),
        min_samples=min_samples,
    )
    metric_series: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in sorted(rows, key=lambda item: (item["provider"], item["capability"], item["at"])):
        series_id = f"{row['provider']}::{row['capability']}"
        for metric in ("quality", "latency_seconds", "cost"):
            metric_series[series_id][metric].append(float(row[metric]))
    drift = {
        provider_capability: {
            metric: provider_control_chart.control_chart(values).as_dict()
            for metric, values in sorted(metrics.items())
        }
        for provider_capability, metrics in sorted(metric_series.items())
    }
    return {
        "schema": PULSE_SCHEMA,
        "as_of": observed_as_of.isoformat().replace("+00:00", "Z"),
        "source_schema": RUN_FACT_SCHEMA,
        "receipt_count": len(rows),
        "ratings": capability_elo.ratings(rows, min_samples=min_samples),
        "drift": drift,
        "disagreements": second_opinion.disagreements(rows),
        "routing_authority": False,
        "recommended_provider": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts-json", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--max-age-days", type=int, default=30)
    parser.add_argument("--min-samples", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        records = json.loads(args.receipts_json.read_text(encoding="utf-8"))
        report = build_report(
            records,
            as_of=args.as_of,
            max_age_days=args.max_age_days,
            min_samples=args.min_samples,
        )
    except (OSError, json.JSONDecodeError, PulseError) as exc:
        print(f"PULSE ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
