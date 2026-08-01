#!/usr/bin/env python3
"""Derive advisory projection acceptance rates from reconciliation receipts."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import reconcile


def summarize(receipts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return counts and rate; no local state root is inferred."""

    accepted = 0
    rejected = 0
    for receipt in receipts:
        if receipt.get("schema") != reconcile.RECONCILIATION_SCHEMA:
            raise reconcile.ReconciliationError("reconciliation receipt schema is invalid")
        projections = receipt.get("projections")
        if not isinstance(projections, list):
            raise reconcile.ReconciliationError("reconciliation projections must be a list")
        for row in projections:
            if not isinstance(row, Mapping):
                raise reconcile.ReconciliationError("reconciliation projection row is invalid")
            state = row.get("state")
            if state == "accepted":
                accepted += 1
            elif state == "rejected":
                rejected += 1
            else:
                raise reconcile.ReconciliationError("reconciliation projection state is invalid")
    total = accepted + rejected
    return {
        "accepted": accepted,
        "rejected": rejected,
        "total": total,
        "acceptance_rate": None if total == 0 else accepted / total,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read explicit Saga reconciliation receipts; no runtime root is inferred"
    )
    parser.add_argument("--receipts", required=True, type=Path)
    args = parser.parse_args(argv)
    data = json.loads(args.receipts.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        parser.error("--receipts must contain a JSON list")
    print(json.dumps(summarize(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
