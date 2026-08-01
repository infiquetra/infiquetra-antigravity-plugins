#!/usr/bin/env python3
"""Derive advisory provider quality ratings from supplied ``run_fact.v1`` receipts.

The fold is deliberately read-only.  A rating is telemetry, never provider-selection
authority, and sparse input produces no rating rather than a fabricated baseline result.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

ELO_BASE = 1200.0
K_FACTOR = 32.0


class CapabilityEloError(ValueError):
    """The supplied quality observations are malformed."""


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CapabilityEloError(f"{field} must be numeric")
    return float(value)


def ratings(
    records: Iterable[Mapping[str, Any]], *, min_samples: int = 3
) -> dict[str, dict[str, float | int]]:
    """Fold observed quality into per-provider/capability advisory ratings.

    ``quality`` is an observed value in the closed interval 0..1.  Each observation
    competes against a neutral expected score of 0.5.  Keys below ``min_samples`` are
    omitted so an isolated result cannot masquerade as a quality trend.
    """

    if min_samples < 1:
        raise CapabilityEloError("min_samples must be positive")
    grouped: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    for record in records:
        provider = record.get("provider")
        capability = record.get("capability")
        at = record.get("at")
        if (
            not isinstance(provider, str)
            or not provider
            or not isinstance(capability, str)
            or not capability
            or not isinstance(at, str)
            or not at
        ):
            raise CapabilityEloError("provider, capability, and at must be non-empty strings")
        quality = _number(record.get("quality"), "quality")
        if not 0.0 <= quality <= 1.0:
            raise CapabilityEloError("quality must be between 0 and 1")
        grouped[(provider, capability)].append((at, quality))

    output: dict[str, dict[str, float | int]] = {}
    for (provider, capability), observations in sorted(grouped.items()):
        if len(observations) < min_samples:
            continue
        rating = ELO_BASE
        for _, quality in sorted(observations):
            rating += K_FACTOR * (quality - 0.5)
        output[f"{provider}::{capability}"] = {
            "rating": round(rating, 2),
            "samples": len(observations),
        }
    return output
