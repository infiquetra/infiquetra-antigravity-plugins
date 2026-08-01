#!/usr/bin/env python3
"""Parent-owned completion barrier + harvest + cascade (U5).

"Done" in the OutcomeOrchestrator is a **parent-owned barrier predicate over the returned evidence**
(R9), never a child's self-report. This module owns that predicate and the per-subplot completion
**contract** (R11):

* a **code** leaf is done only when its **PR reads merged** (canonical on GitHub, R10/R11);
* a **non-code** leaf is done on its local completion tick **plus** a durable canonical marker — its
  tracking sub-issue reads **closed** (the cache-less-reconstructable path: a fresh machine reading
  GitHub sees it done), or, for untracked local work, a ``canonical``-flagged completion event in the
  store (cache-resident only — a wipe loses it; the committed-spec completion-log path is future);
* a **child-outcome** node (``child_spec_ref``, KTD10) is done only when the child outcome's own
  terminal state reads **successful** — the reconcile recurses into the child rather than reading its
  branch spec across worktrees.

``harvest`` runs the barrier over the whole spec each reconcile tick and **materializes** every
newly-satisfied contract as a success completion event in the store, so the existing frontier read
(``outcome_store.completed_subplots``) unlocks the next Kahn layer (R10) — and a cache-less machine
re-derives the same completions from GitHub. ``blocked_subtree`` is the R22 cascade: only the
downstream subtree of a hard-blocked node pauses; independent siblings keep running.

This module READS GitHub (``outcome_github``); the merge/close *actions* are U6. House pattern: pure
functions over injectable readers, no I/O at import.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lifecycle_reconciliation  # noqa: E402
import manifest_store  # noqa: E402
import outcome_github  # noqa: E402  (after the sys.path shim, by design)
import outcome_spec  # noqa: E402
import outcome_store  # noqa: E402

# Per-subplot completion contracts (R11) — the thing the parent barrier verifies.
CONTRACT_CODE = "code:pr-merged"
CONTRACT_NONCODE = "non-code:tick+canonical-marker"
CONTRACT_CHILD = "child-outcome:terminal-success"

# A reader that returns a child outcome's terminal state ("done"/"failed"/"rejected"/.../"unknown")
# given its ``child_spec_ref`` — injected so the recursion is testable without a real child on disk.
ChildStateReader = Callable[[str], str]


@dataclass
class BarrierVerdict:
    """The parent's verdict on one subplot's completion contract (R9)."""

    subplot_id: str
    satisfied: bool
    contract: str
    state: str  # the canonical state read (merged/closed/open/unknown/done/failed/...)
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subplot_id": self.subplot_id,
            "satisfied": self.satisfied,
            "contract": self.contract,
            "state": self.state,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }


def verified_lifecycle_settlement(node: Any, *, repo_root: Path) -> BarrierVerdict | None:
    """Verify U4 contract, transition receipts, manifest attestation, and leaf ownership."""

    if not node.obligation_contract_ref and not node.transition_receipt_refs:
        return None
    sid = node.subplot_id
    if not node.leaf_saga_id:
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            "orphan",
            "proof-carrying node has no owning leaf_saga_id",
        )
    if not node.obligation_contract_ref:
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            "incomplete",
            "transition receipt references require an obligation contract",
        )
    try:
        contract = lifecycle_reconciliation.load_contract(repo_root, node.obligation_contract_ref)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return BarrierVerdict(
            sid, False, "lifecycle:settlement", "invalid", f"contract invalid: {exc}"
        )
    if contract.workstream_id != node.leaf_saga_id:
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            "wrong-owner",
            "contract workstream does not match leaf_saga_id",
        )

    manifest = node.evidence.get("manifest")
    owner_id = str(node.evidence.get("manifest_owner_id", ""))
    assignment_id = str(node.evidence.get("manifest_assignment_id", ""))
    if owner_id != node.leaf_saga_id or not assignment_id or not isinstance(manifest, dict):
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            "unattested",
            "leaf requires a canonical manifest bound to its owner and assignment",
        )
    manifest_errors = manifest_store.validate_evidence_manifest(
        manifest,
        assignment_id=assignment_id,
        owner_id=owner_id,
        input_value=node.evidence.get("manifest_input"),
        output_value=node.evidence.get("manifest_output"),
    )
    if manifest_errors:
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            "unattested",
            "manifest invalid: " + "; ".join(manifest_errors),
        )

    try:
        reconciliation = lifecycle_reconciliation.reconcile_required_obligations(
            contract,
            lifecycle_reconciliation.load_receipts(repo_root, node.transition_receipt_refs),
            repo_root=repo_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return BarrierVerdict(
            sid, False, "lifecycle:settlement", "invalid", f"receipt invalid: {exc}"
        )
    if not reconciliation.complete:
        return BarrierVerdict(
            sid,
            False,
            "lifecycle:settlement",
            reconciliation.settlement_state.value,
            f"required obligation {reconciliation.obligation_id!r} is "
            f"{reconciliation.settlement_state.value}",
            evidence={"reconciliation": reconciliation.to_dict()},
        )
    return BarrierVerdict(
        sid,
        True,
        "lifecycle:settlement",
        "satisfied",
        "owned leaf has attested manifest and verified required receipts",
        evidence={
            "leaf_saga_id": node.leaf_saga_id,
            "manifest_execution_id": manifest.get("execution_id", ""),
            "receipt_refs": list(node.transition_receipt_refs),
            "reconciliation": reconciliation.to_dict(),
        },
    )


def barrier_satisfied(
    node: Any,
    *,
    store: Any,
    github_runner: Callable[..., Any] | None = None,
    child_state_reader: ChildStateReader | None = None,
    repo_root: Path | None = None,
) -> BarrierVerdict:
    """The parent-owned barrier predicate (R9/R11). Returns satisfied=False (a HALT) on an unmet
    contract — never a child's self-report, always evidence the parent can re-verify on GitHub."""
    sid = node.subplot_id
    if node.obligation_contract_ref or node.transition_receipt_refs:
        if repo_root is None:
            return BarrierVerdict(
                sid,
                False,
                "lifecycle:settlement",
                "unresolved",
                "proof-carrying completion requires repo_root",
            )
        lifecycle = verified_lifecycle_settlement(node, repo_root=repo_root)
        if lifecycle is not None and not lifecycle.satisfied:
            return lifecycle

    if node.is_outcome:  # child_spec_ref -> recurse into the child outcome's terminal state (KTD10)
        child = node.child_spec_ref
        state = child_state_reader(child) if child_state_reader is not None else "unknown"
        ok = state in outcome_spec.SUCCESS_STATES
        return BarrierVerdict(
            sid,
            ok,
            CONTRACT_CHILD,
            state,
            reason=(
                "child outcome terminal-successful" if ok else f"child {child!r} not done ({state})"
            ),
            evidence={"child_spec_ref": child, "child_state": state},
        )

    if node.kind == "code":
        pr = str(node.github.get("pr", ""))
        if not pr:
            return BarrierVerdict(sid, False, CONTRACT_CODE, "open", "no PR ref yet", {})
        state = outcome_github.pr_state(pr, runner=github_runner)
        return BarrierVerdict(
            sid,
            state == "merged",
            CONTRACT_CODE,
            state,
            reason=("PR merged" if state == "merged" else f"PR not merged ({state})"),
            evidence={"pr": pr, "pr_state": state},
        )

    # non-code: the canonical marker must read done so a cache-less machine reconstructs it.
    issue = str(node.github.get("issue", ""))
    if issue:
        marker = outcome_github.issue_state(issue, runner=github_runner)
        return BarrierVerdict(
            sid,
            marker == "closed",
            CONTRACT_NONCODE,
            marker,
            reason=("tracking issue closed" if marker == "closed" else f"tracking issue {marker}"),
            evidence={"issue": issue, "issue_state": marker},
        )
    # No tracking issue: the only marker is a completion event flagged ``canonical`` in the STORE.
    # This is **cache-resident** (NOT on GitHub or the committed spec), so unlike the issue-closed
    # path it is NOT cache-less-reconstructable — a wipe loses it. Acceptable for untracked local
    # non-code work; a cache-less non-code leaf needs a tracking sub-issue. (A committed-spec
    # completion-log marker is the future fully-cache-less path; not yet wired.)
    events = outcome_store.read_completion_events(store, sid)
    canonical = any(e.is_success and bool(e.payload.get("canonical")) for e in events)
    return BarrierVerdict(
        sid,
        canonical,
        CONTRACT_NONCODE,
        "done" if canonical else "open",
        reason=(
            "canonical completion tick recorded" if canonical else "no canonical completion marker"
        ),
        evidence={"has_canonical_event": canonical},
    )


def harvest(
    spec: Any,
    *,
    store: Any,
    github_runner: Callable[..., Any] | None = None,
    child_state_reader: ChildStateReader | None = None,
    repo_root: Path | None = None,
    at: str = "",
) -> list[str]:
    """Run the barrier over the spec and materialize each newly-satisfied contract as a success
    completion event in the store. Returns the newly-harvested subplot ids (R9/R10/R11).

    Idempotent: a subplot already success-completed in the store is skipped, and the write itself is
    idempotency-keyed, so re-harvesting (or a second machine) never double-records. This is the
    GitHub-canonical-completion -> cache materialization that unlocks the next Kahn layer.
    """
    already = outcome_store.completed_subplots(store)
    harvested: list[str] = []
    for node in spec.nodes:
        sid = node.subplot_id
        if sid in already:
            continue
        verdict = barrier_satisfied(
            node,
            store=store,
            github_runner=github_runner,
            child_state_reader=child_state_reader,
            repo_root=repo_root,
        )
        if not verdict.satisfied:
            continue
        # Write to a FRESH attempt slot, never the implicit attempt 1: a subplot that already holds a
        # NON-success terminal (failed/rejected/stalled) at attempt 1 is not in `already`
        # (success-only), so a hardcoded attempt-1 write would collide with that slot's different
        # idempotency key and raise — wedging the whole reconcile loop. The constant idempotency key
        # plus the success-sticky `already` skip keep this idempotent regardless of attempt number.
        existing = outcome_store.read_completion_events(store, sid)
        attempt = max((e.attempt for e in existing), default=0) + 1
        payload = {"contract": verdict.contract, "evidence": verdict.evidence, "canonical": True}
        # Attach the advisory manifest pointer (R19/KTD1) when this leaf's dispatch recorded a
        # provenance manifest: saga_id convention = outcome id, execution_id = subplot id. Only
        # derivable when the store sits in the canonical <common>/saga-outcomes/<id> layout;
        # the pointer is advisory (R8) — any other layout, unsafe id, or absent manifest simply
        # means no pointer.
        if store.root.parent.name == outcome_store.STORE_NAMESPACE:
            outcome_id = store.root.name
            mstore = manifest_store.Store(
                root=store.root.parent.parent / manifest_store.MANIFEST_NAMESPACE / outcome_id
            )
            try:
                if mstore.manifest_path(sid).is_file():
                    payload = manifest_store.set_manifest_ref(payload, outcome_id, sid)
            except manifest_store.ManifestStoreError:
                pass
        event = outcome_store.CompletionEvent(
            subplot_id=sid,
            state="done",
            idempotency_key=f"harvest:{sid}:{verdict.contract}",
            attempt=attempt,
            at=at,
            payload=payload,
        )
        outcome_store.write_completion_event(store, event)
        harvested.append(sid)
    return harvested


def blocked_subtree(spec: Any, blocked_ids: set[str]) -> set[str]:
    """R22 cascade: the set of subplots transitively DOWNSTREAM of any hard-blocked node.

    Only the downstream subtree of a block pauses; a subplot with no dependency path to a blocked node
    keeps running. The blocked nodes themselves are NOT included (they are the cause, not the cascade).
    """
    dependents: dict[str, list[str]] = {n.subplot_id: [] for n in spec.nodes}
    for node in spec.nodes:
        for dep in node.depends_on:
            if dep in dependents:
                dependents[dep].append(node.subplot_id)
    paused: set[str] = set()
    stack = [b for b in blocked_ids if b in dependents]
    while stack:
        cur = stack.pop()
        for dependent in dependents.get(cur, []):
            if dependent not in paused:
                paused.add(dependent)
                stack.append(dependent)
    return paused


def barrier_report(
    spec: Any,
    *,
    store: Any,
    github_runner: Callable[..., Any] | None = None,
    child_state_reader: ChildStateReader | None = None,
    repo_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Every node's barrier verdict (derived-on-read, for the cockpit/report). No writes."""
    return {
        node.subplot_id: barrier_satisfied(
            node,
            store=store,
            github_runner=github_runner,
            child_state_reader=child_state_reader,
            repo_root=repo_root,
        ).to_dict()
        for node in spec.nodes
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Outcome completion barrier — report verdicts.")
    parser.add_argument("spec_json", help="path to an outcome-spec.json")
    args = parser.parse_args(argv)

    spec = outcome_spec.OutcomeSpec.from_json(Path(args.spec_json).read_text(encoding="utf-8"))
    spec.validate()
    # A bare-report CLI cannot resolve the per-outcome store/GitHub without more context; it prints
    # the static contract per node so an operator can see what each leaf must satisfy.
    contracts = {
        n.subplot_id: (
            CONTRACT_CHILD
            if n.is_outcome
            else CONTRACT_CODE
            if n.kind == "code"
            else CONTRACT_NONCODE
        )
        for n in spec.nodes
    }
    print(json.dumps({"outcome_id": spec.outcome_id, "contracts": contracts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
