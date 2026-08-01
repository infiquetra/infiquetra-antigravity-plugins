"""Semantic contract tests for receipt-driven provider pulse telemetry."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pulse  # noqa: E402


def _records() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for provider, qualities in (
        ("gemini-a", (0.9, 0.8, 0.9, 0.9, 0.8)),
        ("gemini-b", (0.5, 0.5, 0.4, 0.4, 0.3)),
    ):
        for index, quality in enumerate(qualities, start=1):
            rows.append(
                {
                    "schema": "run_fact.v1",
                    "kind": "engine",
                    "subplot_id": f"worker-{provider}-{index}",
                    "at": f"2026-07-{20 + index:02d}T12:00:00Z",
                    "provider": provider,
                    "capability": "review",
                    "quality": quality,
                    "latency_seconds": 2.0 + index / 10,
                    "cost": 0.1 + index / 100,
                    "evidence_sha256": hashlib.sha256(
                        f"{provider}:{index}:review".encode()
                    ).hexdigest(),
                }
            )
    return rows


def test_provider_pulse_reports_quality_drift_without_routing_authority() -> None:
    report = pulse.build_report(_records(), as_of="2026-07-31T12:00:00Z")

    assert report["schema"] == "pulse_snapshot.v1"
    assert report["source_schema"] == "run_fact.v1"
    assert report["receipt_count"] == 10
    assert set(report["ratings"]) == {"gemini-a::review", "gemini-b::review"}
    assert report["disagreements"] == [
        {
            "capability": "review",
            "providers": ["gemini-a", "gemini-b"],
            "quality_gap": 0.44,
            "requires_operator_review": True,
        }
    ]
    assert report["routing_authority"] is False
    assert report["recommended_provider"] is None
    assert set(report["drift"]) == {"gemini-a::review", "gemini-b::review"}


def test_provider_pulse_reports_quality_drift_without_routing_authority_rejects_negative_cases() -> (
    None
):
    sparse = _records()[:2]
    with pytest.raises(pulse.PulseError, match="insufficient evidence"):
        pulse.build_report(sparse, as_of="2026-07-31T12:00:00Z")

    stale = _records()
    stale[0]["at"] = "2026-01-01T12:00:00Z"
    with pytest.raises(pulse.PulseError, match="stale"):
        pulse.build_report(stale, as_of="2026-07-31T12:00:00Z")

    sensitive = copy.deepcopy(_records())
    sensitive[0]["api_key"] = "not-a-real-secret"
    with pytest.raises(pulse.PulseError, match="sensitive"):
        pulse.build_report(sensitive, as_of="2026-07-31T12:00:00Z")

    with pytest.raises(pulse.PulseError, match="no automatic routing authority"):
        pulse.build_report(_records(), as_of="2026-07-31T12:00:00Z", auto_route=True)

    for field in ("subplot_id", "evidence_sha256"):
        replay = _records()
        replay[1][field] = replay[0][field]
        with pytest.raises(pulse.PulseError, match="replays"):
            pulse.build_report(replay, as_of="2026-07-31T12:00:00Z")

    for invalid in (float("nan"), float("inf"), float("-inf")):
        non_finite = _records()
        non_finite[0]["quality"] = invalid
        with pytest.raises(pulse.PulseError, match="invalid quality"):
            pulse.build_report(non_finite, as_of="2026-07-31T12:00:00Z")


def test_provider_pulse_keeps_capability_drift_series_distinct() -> None:
    records = _records()
    for index, row in enumerate(copy.deepcopy(records[:5])):
        row["subplot_id"] = f"writer-{index}"
        row["capability"] = "write"
        row["evidence_sha256"] = hashlib.sha256(f"write:{index}".encode()).hexdigest()
        records.append(row)

    report = pulse.build_report(records, as_of="2026-07-31T12:00:00Z")

    assert "gemini-a::review" in report["drift"]
    assert "gemini-a::write" in report["drift"]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "ISO-8601 string"),
        ("not-a-time", "ISO-8601 string"),
        ("2026-07-31T12:00:00", "include a timezone"),
    ],
)
def test_pulse_rejects_invalid_time_boundaries(value: object, message: str) -> None:
    with pytest.raises(pulse.PulseError, match=message):
        pulse._parse_time(value, "observed_at")


def test_pulse_rejects_malformed_receipt_boundaries() -> None:
    as_of = datetime(2026, 7, 31, 12, tzinfo=UTC)
    with pytest.raises(pulse.PulseError, match="non-empty list"):
        pulse._validated_records([], as_of=as_of, max_age=timedelta(days=1), min_samples=1)
    with pytest.raises(pulse.PulseError, match="min_samples"):
        pulse._validated_records(_records(), as_of=as_of, max_age=timedelta(days=30), min_samples=0)
    cases: list[tuple[object, str]] = [
        ([None], "must be an object"),
        ([{**_records()[0], "schema": "wrong"}], "engine run_fact"),
        ([{**_records()[0], "provider": ""}], "invalid provider"),
        ([{**_records()[0], "evidence_sha256": "bad"}], "invalid evidence_sha256"),
        ([{**_records()[0], "at": "2026-08-01T12:00:00Z"}], "future-dated"),
        ([{**_records()[0], "cost": -1}], "invalid cost"),
        ([{**_records()[0], "quality": 1.1}], "between 0 and 1"),
    ]
    for records, message in cases:
        with pytest.raises(pulse.PulseError, match=message):
            pulse._validated_records(
                records, as_of=as_of, max_age=timedelta(days=30), min_samples=1
            )
    with pytest.raises(pulse.PulseError, match="max_age_days"):
        pulse.build_report(_records(), as_of="2026-07-31T12:00:00Z", max_age_days=0)


def test_pulse_cli_reports_valid_input_and_parse_errors(tmp_path: Path, capsys) -> None:
    valid = tmp_path / "receipts.json"
    valid.write_text(json.dumps(_records()), encoding="utf-8")
    assert pulse.main(["--receipts-json", str(valid), "--as-of", "2026-07-31T12:00:00Z"]) == 0
    assert json.loads(capsys.readouterr().out)["routing_authority"] is False

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    assert pulse.main(["--receipts-json", str(invalid), "--as-of", "2026-07-31T12:00:00Z"]) == 2
    assert "PULSE ERROR" in capsys.readouterr().err


def test_control_chart_rejects_invalid_inputs_and_reports_sparse_series() -> None:
    chart = pulse.provider_control_chart
    with pytest.raises(chart.ControlChartError, match="at least 2"):
        chart.control_chart([1.0, 2.0], baseline_n=1)
    for invalid in (True, float("nan"), float("inf")):
        with pytest.raises(chart.ControlChartError, match="finite numbers"):
            chart.control_chart([1.0, 2.0, 3.0, invalid, 4.0])
    assert chart.control_chart([1.0, 2.0, 3.0]).status == "insufficient-evidence"
