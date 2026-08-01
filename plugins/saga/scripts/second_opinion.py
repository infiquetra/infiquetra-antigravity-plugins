#!/usr/bin/env python3
"""Advisory disagreement signals from already-observed provider quality."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


def disagreements(
    records: Iterable[Mapping[str, Any]], *, minimum_gap: float = 0.2
) -> list[dict[str, object]]:
    """Report capability-level quality gaps without selecting or invoking a provider."""

    if not 0.0 <= minimum_gap <= 1.0:
        raise ValueError("minimum_gap must be between 0 and 1")
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        provider = record.get("provider")
        capability = record.get("capability")
        quality = record.get("quality")
        if (
            not isinstance(provider, str)
            or not provider
            or not isinstance(capability, str)
            or not capability
            or isinstance(quality, bool)
            or not isinstance(quality, (int, float))
        ):
            raise ValueError("provider, capability, and numeric quality are required")
        values[capability][provider].append(float(quality))

    output: list[dict[str, object]] = []
    for capability, providers in sorted(values.items()):
        means = {name: sum(rows) / len(rows) for name, rows in providers.items()}
        if len(means) < 2:
            continue
        high = max(means, key=means.__getitem__)
        low = min(means, key=means.__getitem__)
        gap = means[high] - means[low]
        if gap >= minimum_gap:
            output.append(
                {
                    "capability": capability,
                    "providers": sorted(means),
                    "quality_gap": round(gap, 6),
                    "requires_operator_review": True,
                }
            )
    return output
