#!/usr/bin/env python3
"""Evaluate one Saga consumer against the shared Antigravity capability receipt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

import fleet_commons_shim

CATALOG_RELATIVE_PATH = Path("references/antigravity-capability-probes.yaml")


class GateError(ValueError):
    """The shared capability evidence could not authorize this consumer."""


def load_capability_evidence(
    receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Load the canonical catalog and a validated, bounded capability receipt."""

    try:
        fleet_root, _rung = fleet_commons_shim.resolve_root()
        capabilities = fleet_commons_shim.load("antigravity_capabilities")
        catalog = capabilities.load_catalog(fleet_root / CATALOG_RELATIVE_PATH)
    except (OSError, RuntimeError, ValueError) as exc:
        raise GateError(
            "fleet-core capability contract is unavailable; install or repair fleet-core"
        ) from exc
    try:
        receipt = capabilities.load_receipt(receipt_path, catalog)
    except (OSError, ValueError) as exc:
        raise GateError("receipt failed strict schema and privacy validation") from exc
    states = {result["id"]: result["state"] for result in receipt["results"]}
    return catalog, receipt, states


def _known_consumers(catalog: dict[str, Any]) -> set[str]:
    consumers: set[str] = set()
    for row in catalog["capabilities"]:
        consumers.update(row["required_for"])
        fallback = row.get("fallback")
        if isinstance(fallback, dict):
            consumers.update(fallback["for_consumers"])
    return consumers


def evaluate_gate(consumer: str, receipt_path: Path) -> dict[str, Any]:
    """Return fleet-core's unchanged consumer evaluation or reject the evidence."""

    catalog, receipt, _states = load_capability_evidence(receipt_path)
    return evaluate_loaded_evidence(consumer, catalog, receipt)


def evaluate_loaded_evidence(
    consumer: str,
    catalog: dict[str, Any],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate already validated evidence for one declared consumer."""

    capabilities = fleet_commons_shim.load("antigravity_capabilities")
    if consumer not in _known_consumers(catalog):
        raise GateError("consumer is not declared by the capability catalog")
    try:
        return cast(
            dict[str, Any],
            capabilities.evaluate_for_consumer(receipt, catalog, consumer),
        )
    except ValueError as exc:
        raise GateError("receipt could not be evaluated for the consumer") from exc


def print_human(evaluation: dict[str, Any]) -> None:
    print("Saga host capability gate")
    print(f"consumer: {evaluation['consumer']}")
    print(f"state: {evaluation['state']}")
    for capability in evaluation["blocking_capabilities"]:
        print(f"blocking: {capability}")
    for capability in evaluation["degraded_capabilities"]:
        print(f"degraded: {capability}")
    for capability, fallback in evaluation["fallbacks"].items():
        print(f"fallback: {capability} -> {fallback}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gate one Saga consumer on a promotable Antigravity capability receipt"
    )
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evaluation = evaluate_gate(args.consumer, args.receipt)
    except GateError as exc:
        print(f"Saga host capability gate failed: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        import json

        print(json.dumps(evaluation, indent=2, sort_keys=True))
    else:
        print_human(evaluation)
    return 1 if evaluation["state"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
