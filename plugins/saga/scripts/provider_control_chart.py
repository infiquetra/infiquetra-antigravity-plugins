#!/usr/bin/env python3
"""Deterministic provider-drift signals over supplied telemetry values."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

LIMIT_FACTOR = 2.66


class ControlChartError(ValueError):
    """The supplied metric series cannot form a valid control chart."""


@dataclass(frozen=True)
class ChartVerdict:
    status: str
    centerline: float | None
    lower_limit: float | None
    upper_limit: float | None
    breach_indices: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def control_chart(series: list[float], *, baseline_n: int = 4) -> ChartVerdict:
    """Compare post-baseline values with an individuals/moving-range band."""

    if baseline_n < 2:
        raise ControlChartError("baseline_n must be at least 2")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in series
    ):
        raise ControlChartError("series values must be finite numbers")
    if len(series) < baseline_n + 1:
        return ChartVerdict("insufficient-evidence", None, None, None, ())
    baseline = [float(value) for value in series[:baseline_n]]
    centerline = sum(baseline) / len(baseline)
    moving_ranges = [abs(right - left) for left, right in zip(baseline, baseline[1:], strict=False)]
    mean_range = sum(moving_ranges) / len(moving_ranges)
    lower = centerline - LIMIT_FACTOR * mean_range
    upper = centerline + LIMIT_FACTOR * mean_range
    breaches = tuple(
        index
        for index, value in enumerate(series[baseline_n:], start=baseline_n)
        if float(value) < lower or float(value) > upper
    )
    return ChartVerdict(
        "drift" if breaches else "stable",
        round(centerline, 6),
        round(lower, 6),
        round(upper, 6),
        breaches,
    )
