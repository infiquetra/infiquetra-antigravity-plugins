#!/usr/bin/env python3
"""Reconcile required lifecycle obligations from canonical transition receipts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lifecycle_obligations  # noqa: E402
import transition_receipts  # noqa: E402

_NEGATIVE_STATE_PRIORITY = {
    lifecycle_obligations.SettlementState.UNSATISFIED: 1,
    lifecycle_obligations.SettlementState.DEGRADED: 2,
    lifecycle_obligations.SettlementState.UNAVAILABLE: 3,
    lifecycle_obligations.SettlementState.CONFLICTING: 4,
}


@dataclass(frozen=True)
class ReconciliationResult:
    """The next required obligation selected from one canonical contract."""

    complete: bool
    obligation_id: str
    settlement_state: lifecycle_obligations.SettlementState
    destination: str
    operator_adjudication_required: bool = False
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "obligation_id": self.obligation_id,
            "settlement_state": self.settlement_state.value,
            "destination": self.destination,
            "operator_adjudication_required": self.operator_adjudication_required,
            "reasons": list(self.reasons),
        }


def _destination(obligation: lifecycle_obligations.Obligation) -> str:
    if obligation.command:
        return f"/{obligation.command}"
    if obligation.phase:
        return f"/{obligation.phase}"
    return str(obligation.producer)


def _blocking_result(
    evaluations: Iterable[lifecycle_obligations.SettlementResult],
) -> lifecycle_obligations.SettlementResult | None:
    evaluated = tuple(evaluations)
    conflicts = tuple(
        result
        for result in evaluated
        if result.state is lifecycle_obligations.SettlementState.CONFLICTING
    )
    if conflicts:
        return max(conflicts, key=lambda result: (result.reasons, result.evidence_ids))
    if any(result.state is lifecycle_obligations.SettlementState.SATISFIED for result in evaluated):
        return None
    if not evaluated:
        return lifecycle_obligations.SettlementResult(
            obligation_id="",
            state=lifecycle_obligations.SettlementState.UNSATISFIED,
            reasons=("no transition receipt settles this required obligation",),
        )
    return max(
        evaluated,
        key=lambda result: (
            _NEGATIVE_STATE_PRIORITY[result.state],
            result.reasons,
            result.evidence_ids,
        ),
    )


def reconcile_required_obligations(
    contract: lifecycle_obligations.ObligationContract,
    receipts: Iterable[transition_receipts.TransitionReceipt],
    *,
    repo_root: Path | None = None,
) -> ReconciliationResult:
    """Return the earliest required obligation not verifiably satisfied."""

    contract = lifecycle_obligations.ObligationContract.from_dict(contract.to_dict())
    normalized_receipts = tuple(
        transition_receipts.TransitionReceipt.from_dict(receipt.to_dict()) for receipt in receipts
    )
    contract.validate()
    by_obligation: dict[str, list[transition_receipts.TransitionReceipt]] = {}
    for receipt in normalized_receipts:
        receipt.validate_shape()
        contract.obligation(receipt.obligation_id)
        by_obligation.setdefault(receipt.obligation_id, []).append(receipt)

    for obligation in contract.obligations:
        if obligation.requirement is not lifecycle_obligations.RequirementLevel.REQUIRED:
            continue
        blocking = _blocking_result(
            transition_receipts.evaluate_transition_receipt(
                receipt,
                contract,
                repo_root=repo_root,
            )
            for receipt in by_obligation.get(obligation.obligation_id, ())
        )
        if blocking is None:
            continue
        return ReconciliationResult(
            complete=False,
            obligation_id=obligation.obligation_id,
            settlement_state=blocking.state,
            destination=_destination(obligation),
            operator_adjudication_required=(
                blocking.state is lifecycle_obligations.SettlementState.CONFLICTING
            ),
            reasons=blocking.reasons,
        )

    return ReconciliationResult(
        complete=True,
        obligation_id="",
        settlement_state=lifecycle_obligations.SettlementState.SATISFIED,
        destination="",
    )


def _repository_json(repo_root: Path, reference: str) -> dict[str, Any]:
    reference_path = Path(reference)
    if not reference or reference_path.is_absolute() or ".." in reference_path.parts:
        raise ValueError(
            "lifecycle evidence reference must be a canonical repository-relative path"
        )
    root = repo_root.resolve()
    target = (root / reference_path).resolve(strict=True)
    if target != root and root not in target.parents:
        raise ValueError("lifecycle evidence reference escapes the repository")
    loaded = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("lifecycle evidence document must be an object")
    return loaded


def load_contract(repo_root: Path, reference: str) -> lifecycle_obligations.ObligationContract:
    """Load and validate one repository-relative obligation contract."""

    return lifecycle_obligations.ObligationContract.from_dict(
        _repository_json(repo_root, reference)
    )


def load_receipts(
    repo_root: Path, references: Iterable[str]
) -> tuple[transition_receipts.TransitionReceipt, ...]:
    """Load and validate repository-relative transition receipts."""

    return tuple(
        transition_receipts.TransitionReceipt.from_dict(_repository_json(repo_root, reference))
        for reference in references
    )


def reconcile_repository_refs(
    repo_root: Path,
    contract_ref: str,
    receipt_refs: Iterable[str],
) -> ReconciliationResult:
    """Load canonical references and reconcile them without mutating the repository."""

    contract = load_contract(repo_root, contract_ref)
    receipts = load_receipts(repo_root, receipt_refs)
    return reconcile_required_obligations(contract, receipts, repo_root=repo_root)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--contract", required=True, help="Repository-relative contract JSON")
    parser.add_argument(
        "--receipt",
        action="append",
        default=[],
        help="Repository-relative receipt JSON; repeat for each receipt",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = reconcile_repository_refs(args.repo_root, args.contract, args.receipt)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
