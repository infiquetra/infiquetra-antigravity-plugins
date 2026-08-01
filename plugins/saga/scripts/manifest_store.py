#!/usr/bin/env python3
"""Manifest store: the git-common-dir carrier for provenance manifests (U2/KTD1/R19).

One JSON file per delegated invocation at
``<git-common-dir>/saga-manifests/<saga-id>/<execution-id>.json``, resolved through the same
``resolve_common_dir()`` ``outcome_store.py`` uses for the outcome cache — the only candidate
that satisfies R19 for delegations that never emit a ``CompletionEvent`` (agy runs during plain
``/work``, multi-agent-consensus outside an outcome). Rejected carriers (KTD1): ``CompletionEvent.payload``
alone (outcome leaves only), a saga tick pointer (per-checkout, git-ignored, worktree-local).

This module also owns the typed ``manifest_ref`` pointer helper for the outcome-leaf case: a
manifest written here can be referenced from a ``CompletionEvent.payload["manifest_ref"]`` as a
common-dir-relative path, giving R19-breadth *and* a documented reader contract on the previously
open ``payload`` dict.

House pattern (mirrors ``outcome_store.py``): pure-ish functions over an explicit ``Store`` value,
dependency-injected ``runner`` so this is unit-testable offline with no real git repo. No I/O at
import.

CLI::

    python3 manifest_store.py write --repo-root <path> --saga-id <id> --execution-id <id> --file <manifest.json>
    python3 manifest_store.py read --repo-root <path> --saga-id <id> --execution-id <id>
    python3 manifest_store.py list --repo-root <path> --saga-id <id> [--json]
    python3 manifest_store.py record-completeness --repo-root <path> --saga-id <id> \\
        --spec <spec.json> --results <results.json>

``record-completeness`` (U4/KTD7) is the driver-materialized path for
multi-agent-consensus runs: the *driving session* persists one manifest per
spec-declared unit after the run, deriving the declared side of ``output_completeness`` from
``completeness_gate.Contract.from_unit`` and the produced side from ``--results`` (a JSON object
mapping ``unit_id`` -> that unit's returned result, the same shape ``completeness_gate.classify``
already consumes). A missing-output trip is reported (non-fatal to the write itself, but the CLI
exits non-zero) only for a contract-bearing unit (``Contract.expects_output``); prose/side-effect-
only leaves are never tripped (R10/AE3), matching ``classify()``'s existing semantics.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import completeness_gate  # noqa: E402  (after the sys.path shim, by design)
import execution_spec  # noqa: E402
import fleet_commons_shim  # noqa: E402
import outcome_store  # noqa: E402
import provenance_manifest  # noqa: E402

# Subdirectory under the git common dir that holds every saga's manifest tree. Namespaced
# separately from ``outcome_store.STORE_NAMESPACE`` — manifests exist independent of the
# OutcomeOrchestrator (R19 breadth: plain /work delegations never touch outcome-spec).
MANIFEST_NAMESPACE = "saga-manifests"

# The documented payload key a CompletionEvent uses to point at a manifest (closes the issue's
# "not yet a consumer surface" note on outcome_store.py's open payload dict).
MANIFEST_REF_KEY = "manifest_ref"


class ManifestStoreError(ValueError):
    """A manifest-store operation was rejected (bad id, missing file, malformed JSON)."""


def _safe_name(name: str, *, what: str = "id") -> str:
    """Reject a name that would escape the store directory (path traversal / separators).

    Delegates to ``outcome_store._safe_name`` — one implementation of the security-relevant
    traversal guard (this module already leans on the sibling's private helpers, e.g.
    ``_atomic_write``), translated into this store's error type.
    """
    try:
        return str(outcome_store._safe_name(name, what=what))
    except outcome_store.OutcomeStoreError as exc:
        raise ManifestStoreError(str(exc)) from exc


@dataclass(frozen=True)
class Store:
    """A handle to one saga's manifest directory under the git common dir.

    ``root`` is the per-saga directory (``<common-dir>/saga-manifests/<saga-id>``). A store is
    constructed either by resolving the common dir (``Store.for_saga``) or with a direct path
    (tests, or any caller that already knows the location).
    """

    root: Path

    @classmethod
    def for_saga(
        cls,
        saga_id: str,
        repo_root: Path,
        *,
        runner: Any = None,
    ) -> Store:
        common = outcome_store.resolve_common_dir(repo_root, runner=runner)
        return cls(root=common / MANIFEST_NAMESPACE / _safe_name(saga_id, what="saga_id"))

    def ensure(self) -> Store:
        """Create the directory tree (idempotent). Returns self for chaining."""
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def manifest_path(self, execution_id: str) -> Path:
        safe = _safe_name(execution_id, what="execution_id")
        return self.root / f"{safe}.json"


# ---------------------------------------------------------------------------
# Write / read / list
# ---------------------------------------------------------------------------


def write_manifest(store: Store, execution_id: str, manifest: dict[str, Any]) -> Path:
    """Write ``manifest`` (a plain dict — already-validated ``to_dict()`` output) atomically.

    Overwrites any prior manifest for the same execution id (a manifest may be updated in place,
    e.g. an adjudication written after the claimed-layer manifest, D5/U3) — never write-once.
    """
    parsed = provenance_manifest.Manifest.from_dict(manifest)
    if parsed.execution_id != execution_id:
        raise ManifestStoreError("manifest execution_id does not match store identity")
    path = store.manifest_path(execution_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    outcome_store._atomic_write(path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path


def build_evidence_manifest(
    *,
    execution_id: str,
    saga_ref: str,
    assignment_id: str,
    owner_id: str,
    input_value: Any,
    output_value: Any,
    created_at: str,
) -> dict[str, Any]:
    """Build a manifest using Fleet Core's canonical output attestation."""

    attestation = fleet_commons_shim.load("output_attestation")
    output_receipt = attestation.attest_output(
        run_id=saga_ref,
        assignment_id=assignment_id,
        worker_id=owner_id,
        output=output_value,
    )
    manifest = provenance_manifest.Manifest(
        execution_id=execution_id,
        saga_ref=saga_ref,
        attribution=provenance_manifest.Attribution(
            kind=provenance_manifest.ProducerKind.MULTI_AGENT_CONSENSUS,
            identity=owner_id,
        ),
        disposition=provenance_manifest.Disposition.RAN_AS_REQUESTED,
        created_at=created_at,
        evidence_binding=provenance_manifest.EvidenceBinding(
            input_sha256=attestation.canonical_digest(input_value),
            output_sha256=attestation.canonical_digest(output_value),
            owner_id=owner_id,
            attestation=output_receipt,
        ),
    )
    return manifest.to_dict()


def validate_evidence_manifest(
    manifest: object,
    *,
    assignment_id: str,
    owner_id: str,
    input_value: Any,
    output_value: Any,
) -> list[str]:
    """Validate schema, content digests, ownership, and Fleet Core attestation."""

    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    try:
        parsed = provenance_manifest.Manifest.from_dict(manifest)
    except provenance_manifest.ManifestError as exc:
        return [str(exc)]
    binding = parsed.evidence_binding
    if binding is None:
        return ["manifest is missing evidence_binding"]
    attestation = fleet_commons_shim.load("output_attestation")
    errors: list[str] = []
    if binding.input_sha256 != attestation.canonical_digest(input_value):
        errors.append("manifest input digest does not match")
    if binding.output_sha256 != attestation.canonical_digest(output_value):
        errors.append("manifest output digest does not match")
    if binding.owner_id != owner_id or parsed.attribution.identity != owner_id:
        errors.append("manifest owner does not match")
    errors.extend(
        attestation.validate_attestation(
            binding.attestation,
            run_id=parsed.saga_ref,
            assignment_id=assignment_id,
            worker_id=owner_id,
            output=output_value,
        )
    )
    return errors


def write_evidence_manifest(
    store: Store,
    execution_id: str,
    manifest: dict[str, Any],
) -> Path:
    """Write once by execution identity; an exact replay is idempotent."""

    existing = read_manifest(store, execution_id)
    if existing is not None and existing != manifest:
        raise ManifestStoreError("duplicate execution identity has different evidence")
    if existing == manifest:
        return store.manifest_path(execution_id)
    return write_manifest(store, execution_id, manifest)


def read_manifest(store: Store, execution_id: str) -> dict[str, Any] | None:
    """Read a manifest by execution id. Returns None if absent or malformed (never fatal)."""
    path = store.manifest_path(execution_id)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def list_manifests(store: Store) -> list[str]:
    """List execution ids with a manifest under ``store.root`` (empty list if the dir is absent)."""
    if not store.root.is_dir():
        return []
    return sorted(p.stem for p in store.root.glob("*.json"))


# ---------------------------------------------------------------------------
# CompletionEvent.payload["manifest_ref"] pointer helper (outcome-leaf case)
# ---------------------------------------------------------------------------


def manifest_ref(saga_id: str, execution_id: str) -> str:
    """The typed ``manifest_ref`` pointer value: a common-dir-relative path.

    Relative to the git common dir (not absolute) so the pointer stays valid across machines/
    clones — a reader resolves it against its own ``resolve_common_dir()`` call, exactly the way
    the manifest tree itself is resolved.
    """
    safe_saga = _safe_name(saga_id, what="saga_id")
    safe_execution = _safe_name(execution_id, what="execution_id")
    return f"{MANIFEST_NAMESPACE}/{safe_saga}/{safe_execution}.json"


def set_manifest_ref(payload: dict[str, Any], saga_id: str, execution_id: str) -> dict[str, Any]:
    """Return a copy of ``payload`` with ``manifest_ref`` set (does not mutate the input)."""
    updated = dict(payload)
    updated[MANIFEST_REF_KEY] = manifest_ref(saga_id, execution_id)
    return updated


def resolve_manifest_ref(
    payload: dict[str, Any],
    repo_root: Path,
    *,
    runner: Any = None,
) -> dict[str, Any] | None:
    """Resolve a ``CompletionEvent.payload["manifest_ref"]`` pointer back to its manifest dict.

    Returns None when the payload carries no pointer, the pointer is malformed, or the target
    file is absent/unreadable — the pointer is advisory (R8), never a hard dependency.
    """
    ref = payload.get(MANIFEST_REF_KEY)
    if not isinstance(ref, str) or not ref.strip():
        return None
    common = outcome_store.resolve_common_dir(repo_root, runner=runner)
    path = (common / ref).resolve()
    # Refuse to read outside the manifest tree even if a stray pointer tries to escape it.
    root = (common / MANIFEST_NAMESPACE).resolve()
    if root not in path.parents and path != root:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


# ---------------------------------------------------------------------------
# record-completeness (U4/KTD7) — driver-materialized output_completeness
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletenessRecord:
    """One unit's persisted manifest plus the completeness_gate verdict that produced it."""

    unit_id: str
    path: Path
    manifest: dict[str, Any]
    failure: completeness_gate.Failure | None


def _output_completeness_for(
    unit: execution_spec.Unit, result: Any
) -> tuple[provenance_manifest.OutputCompleteness, completeness_gate.Failure | None]:
    """Derive the declared-vs-produced subrecord and any completeness_gate trip for one unit."""
    contract = completeness_gate.Contract.from_unit(unit)
    failure = completeness_gate.classify(result, contract=contract, unit_id=unit.unit_id)
    parsed = completeness_gate._parse_result(result)
    if isinstance(parsed, dict):
        produced_keys: list[str] = list(parsed.keys())
    else:
        produced_keys = []
    produced_count: int | None = None
    if isinstance(parsed, (list, dict, set, tuple)):
        produced_count = len(parsed)
    output_completeness = provenance_manifest.OutputCompleteness.derive(
        declared_keys=list(contract.returns),
        target_count=contract.target_count,
        produced_keys=produced_keys,
        produced_count=produced_count,
    )
    return output_completeness, failure


def record_completeness(
    spec: execution_spec.ExecutionSpec,
    results: dict[str, Any],
    *,
    saga_id: str,
    store: Store,
) -> list[CompletenessRecord]:
    """Persist one driver-materialized manifest per unit in ``spec`` (KTD7).

    Every declared unit gets an ``output_completeness`` subrecord (not only contract-bearing
    ones) — the missing-output *trip* is what's restricted to contract-bearing units (R10/AE3);
    a prose/side-effect-only leaf still gets a (zero-declared, always-passing) subrecord so the
    manifest tree stays a complete per-unit ledger.
    """
    records: list[CompletenessRecord] = []
    created_at = datetime.now(UTC).isoformat()
    for unit in spec.units:
        result = results.get(unit.unit_id)
        output_completeness, failure = _output_completeness_for(unit, result)
        manifest = provenance_manifest.Manifest(
            execution_id=unit.unit_id,
            saga_ref=saga_id,
            attribution=provenance_manifest.Attribution(
                kind=provenance_manifest.ProducerKind.MULTI_AGENT_CONSENSUS,
                identity=unit.label or unit.unit_id,
                effort=unit.tier.effort,
                protocol="",
            ),
            disposition=provenance_manifest.Disposition.RAN_AS_REQUESTED,
            created_at=created_at,
            output_completeness=output_completeness,
        )
        manifest_dict = manifest.to_dict()
        path = write_manifest(store, unit.unit_id, manifest_dict)
        records.append(
            CompletenessRecord(
                unit_id=unit.unit_id, path=path, manifest=manifest_dict, failure=failure
            )
        )
    return records


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manifest store: write/read/list carrier CLI.")
    parser.add_argument("--repo-root", default=".", help="Repo root (any worktree; default cwd).")
    parser.add_argument("--saga-id", required=True, help="Saga id the manifest belongs to.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_write = sub.add_parser("write", help="Write a manifest from a JSON file.")
    p_write.add_argument("--execution-id", required=True)
    p_write.add_argument("--file", required=True, help="Path to a JSON manifest dict.")

    p_read = sub.add_parser("read", help="Read a manifest and print it as JSON.")
    p_read.add_argument("--execution-id", required=True)

    sub.add_parser("list", help="List execution ids with a manifest for this saga.")

    p_completeness = sub.add_parser(
        "record-completeness",
        help="Persist a driver-materialized output_completeness manifest per spec unit (U4/KTD7).",
    )
    p_completeness.add_argument("--spec", required=True, help="Path to the execution spec JSON.")
    p_completeness.add_argument(
        "--results", required=True, help="Path to a JSON object mapping unit_id -> result."
    )

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    store = Store.for_saga(args.saga_id, repo_root).ensure()

    if args.command == "write":
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            print("manifest file must contain a JSON object", file=sys.stderr)
            return 1
        path = write_manifest(store, args.execution_id, data)
        print(str(path))
        return 0

    if args.command == "read":
        manifest = read_manifest(store, args.execution_id)
        if manifest is None:
            print(f"no manifest for execution_id={args.execution_id!r}", file=sys.stderr)
            return 1
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    if args.command == "list":
        for execution_id in list_manifests(store):
            print(execution_id)
        return 0

    if args.command == "record-completeness":
        spec_data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        spec = execution_spec.ExecutionSpec.from_dict(spec_data)
        results_data = json.loads(Path(args.results).read_text(encoding="utf-8"))
        if not isinstance(results_data, dict):
            print("results file must contain a JSON object of unit_id -> result", file=sys.stderr)
            return 1
        records = record_completeness(spec, results_data, saga_id=args.saga_id, store=store)
        tripped = [r for r in records if r.failure is not None]
        for record in records:
            print(str(record.path))
        if tripped:
            for record in tripped:
                failure = record.failure
                if failure is None:
                    continue
                print(
                    f"missing-output: unit={record.unit_id} "
                    f"class={failure.failure_class.value} "
                    f"{failure.message}",
                    file=sys.stderr,
                )
            return 1
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
