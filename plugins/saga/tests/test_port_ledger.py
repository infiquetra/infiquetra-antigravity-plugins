from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from scripts import port_claude_plugin, port_ledger

FIXTURES = Path(__file__).parent / "fixtures" / "port-ledger"
CAMPAIGN_LEDGER = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "ports"
    / "2026-07-30-saga-reliability"
    / "ledger.yaml"
)
COMMITS = {
    "antigravity": "a" * 40,
    "claude": "b" * 40,
    "codex": "c" * 40,
}


def load_fixture(name: str = "complete.yaml") -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load((FIXTURES / name).read_text()))


def inventory_errors(ledger: object) -> list[str]:
    return cast(list[str], port_ledger.validate_ledger(ledger, inventory_only=True))


def pending_ledger() -> dict[str, Any]:
    ledger = load_fixture()
    for candidate in ledger["candidates"]:
        candidate["decision"] = {
            "state": "pending",
            "rationale": (
                "The maintainer recommendation is evidence for review, not an operator decision."
            ),
            "revisit_trigger": (
                "Reassess when the source contract or Antigravity capability evidence changes."
            ),
            "operator": None,
            "decided_at": None,
        }
    return ledger


class FakeGitRunner:
    def __init__(self, *, divergent_host: str | None = None) -> None:
        self.divergent_host = divergent_host
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
        host = repository.name
        self.calls.append((host, arguments))
        command = arguments[0]
        if command == "rev-parse":
            if arguments[1] == "HEAD" and host == self.divergent_host:
                return ("f" * 40 + "\n").encode()
            if arguments[1].endswith("^{commit}"):
                return ("1" * 40 + "\n").encode()
            return (COMMITS[host] + "\n").encode()
        if command == "ls-tree":
            return b"plugins/saga/README.md\0"
        if command == "show":
            return f"{host}:{arguments[2]}".encode()
        if command == "diff":
            return b"M\0plugins/saga/README.md\0"
        raise AssertionError(arguments)


def make_repositories(tmp_path: Path) -> dict[str, Path]:
    repositories: dict[str, Path] = {}
    for host in sorted(port_ledger.HOSTS):
        repository = tmp_path / host
        repository.mkdir()
        (repository / "sentinel.txt").write_text(host)
        repositories[host] = repository
    return repositories


def run_controlled_git(repository: Path, *arguments: str) -> str:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_AUTHOR_NAME": "Port Ledger Fixture",
            "GIT_AUTHOR_EMAIL": "port-ledger@example.invalid",
            "GIT_COMMITTER_NAME": "Port Ledger Fixture",
            "GIT_COMMITTER_EMAIL": "port-ledger@example.invalid",
            "GIT_AUTHOR_DATE": "2026-07-30T12:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-07-30T12:00:00+00:00",
        }
    )
    completed = subprocess.run(  # nosec B603
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    return completed.stdout.strip()


def make_controlled_git_repositories(
    tmp_path: Path,
) -> tuple[dict[str, Path], dict[str, str], str]:
    repositories: dict[str, Path] = {}
    snapshots: dict[str, str] = {}
    claude_seed = ""
    for host in sorted(port_ledger.HOSTS):
        repository = tmp_path / host
        repository.mkdir()
        run_controlled_git(repository, "init", "-q", "--initial-branch=main")
        source = repository / "plugins" / "saga" / "README.md"
        source.parent.mkdir(parents=True)
        source.write_text(f"{host} seed\n")
        run_controlled_git(repository, "add", "plugins/saga/README.md")
        run_controlled_git(repository, "commit", "-q", "-m", f"{host} seed")
        if host == "claude":
            claude_seed = run_controlled_git(repository, "rev-parse", "HEAD")
            source.write_text("claude current\n")
            run_controlled_git(repository, "add", "plugins/saga/README.md")
            run_controlled_git(repository, "commit", "-q", "-m", "claude current")
        head = run_controlled_git(repository, "rev-parse", "HEAD")
        run_controlled_git(repository, "update-ref", "refs/remotes/origin/main", head)
        assert run_controlled_git(repository, "remote") == ""
        repositories[host] = repository
        snapshots[host] = head
    return repositories, snapshots, claude_seed


def prepare_controlled_release_ledger(
    tmp_path: Path,
) -> tuple[dict[str, Path], dict[str, str], str, Path]:
    repositories, snapshots, claude_seed = make_controlled_git_repositories(tmp_path)
    output = campaign_output(repositories)
    ledger = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=snapshots,
        claude_seed=claude_seed,
        host_receipt=promotable_receipt(),
        checked_at="2026-07-30T12:00:00Z",
    )
    attach_decided_candidate(ledger)
    assert port_ledger.validate_ledger(ledger) == []
    port_ledger.write_ledger(output, ledger)
    return repositories, snapshots, claude_seed, output


def promotable_receipt() -> dict[str, Any]:
    return {
        "schema": "antigravity.capabilities.v1",
        "catalog_digest": "d" * 64,
        "agy_cli_version": None,
        "antigravity_host_version": None,
        "supported_flags": [],
        "runtime_roots": ["repository"],
        "requested_facts": {},
        "observed_facts": {},
        "results": [
            {
                "id": "agy.agent.execution",
                "probe_revision": 1,
                "state": "passed",
                "evidence": ["agent-execution-proof"],
            }
        ],
    }


def migration_plan(ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    source = ledger or load_fixture()
    approved = [
        candidate
        for candidate in source["candidates"]
        if candidate["decision"]["state"] == "approved-survivor"
    ]
    return {
        "schema": port_ledger.MIGRATION_PLAN_SCHEMA,
        "campaign_id": source["campaign"]["id"],
        "ledger_schema": port_ledger.SCHEMA_V2,
        "candidates": {
            candidate["id"]: {
                "semantic_contract": candidate["semantic_contract"],
                "final_antigravity_state": "present",
                "target_paths": ["plugins/saga/tests/test_port_ledger.py"],
                "test_node_ids": [
                    "plugins/saga/tests/test_port_ledger.py::test_packet_set_digest_vectors"
                ],
                "negative_test_node_ids": [
                    "plugins/saga/tests/test_port_ledger.py::"
                    "test_migration_plan_rejects_scope_and_containment_failures"
                ],
                "intentional_differences": [
                    "Uses the Antigravity ledger contract instead of a source runtime API."
                ],
            }
            for candidate in approved
        },
    }


def campaign_output(repositories: dict[str, Path]) -> Path:
    return repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"


def attach_decided_candidate(ledger: dict[str, Any]) -> None:
    packet_ids = [packet["id"] for packet in ledger["campaign"]["edit_packets"]]
    packet_by_id = {packet["id"]: packet for packet in ledger["campaign"]["edit_packets"]}
    ledger["candidates"] = [
        {
            "id": "stable-capability",
            "title": "Stable capability",
            "edit_packet_ids": packet_ids,
            "provenance": port_ledger._provenance_for(packet_ids, packet_by_id),
            "semantic_contract": "The capability retains stable edit ownership.",
            "adjacent_dependencies": [],
            "required_host_capabilities": [],
            "antigravity_state": "partial",
            "proposed_disposition": "antigravity-adapt",
            "ranking": {
                "operator_value": 3,
                "antigravity_fit": 3,
                "proof_feasibility": 3,
                "maintenance_cost": 3,
            },
            "evidence_expectation": ["Refresh retains the stable candidate ID."],
            "decision": {
                "state": "approved-survivor",
                "rationale": "The operator approved the evidence-bound capability.",
                "revisit_trigger": "Reassess if the source evidence changes.",
                "operator": "Jeff",
                "decided_at": "2026-07-30T12:30:00Z",
            },
        }
    ]
    ledger["campaign"]["unmatched_edit_packet_ids"] = []
    ledger["campaign"]["release_drift"]["status"] = "clean"
    ledger["campaign"]["release_drift"]["unmatched_edit_packet_ids"] = []


def attach_two_decided_candidates(ledger: dict[str, Any]) -> None:
    attach_decided_candidate(ledger)
    template = ledger["candidates"][0]
    packet_by_id = {packet["id"]: packet for packet in ledger["campaign"]["edit_packets"]}
    first_ids = [
        packet_id
        for packet_id in template["edit_packet_ids"]
        if packet_by_id[packet_id]["host"] == "codex"
    ]
    second_ids = [
        packet_id for packet_id in template["edit_packet_ids"] if packet_id not in first_ids
    ]
    first = copy.deepcopy(template)
    first["id"] = "codex-capability"
    first["title"] = "Codex capability"
    first["edit_packet_ids"] = first_ids
    first["provenance"] = port_ledger._provenance_for(first_ids, packet_by_id)
    second = copy.deepcopy(template)
    second["id"] = "other-capability"
    second["title"] = "Other capability"
    second["edit_packet_ids"] = second_ids
    second["provenance"] = port_ledger._provenance_for(second_ids, packet_by_id)
    ledger["candidates"] = [first, second]


def test_complete_ledger_validates_and_round_trips_deterministically(tmp_path: Path) -> None:
    ledger = load_fixture()
    assert inventory_errors(ledger) == []
    assert port_ledger.validate_ledger(ledger) == []

    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    port_ledger.write_ledger(first, ledger)
    port_ledger.write_ledger(second, port_ledger.load_ledger(first))
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(schema="unknown.v2"), "ledger.schema"),
        (lambda value: value.update(extra=True), "unknown field 'extra'"),
        (
            lambda value: value["campaign"]["snapshots"][0].update(extra=True),
            "unknown field 'extra'",
        ),
        (
            lambda value: value["campaign"]["edit_packets"][0].update(path="../escape"),
            "safe repository-relative",
        ),
        (
            lambda value: value["candidates"][0]["ranking"].update(operator_value=6),
            "integer from 1 through 5",
        ),
        (
            lambda value: value["campaign"].update(snapshots=value["campaign"]["snapshots"][:-1]),
            "must contain Claude, Codex, and Antigravity",
        ),
        (
            lambda value: value["candidates"][0].pop("semantic_contract"),
            "missing required field 'semantic_contract'",
        ),
        (
            lambda value: value["candidates"].append(copy.deepcopy(value["candidates"][0])),
            "duplicate candidate ID",
        ),
        (
            lambda value: value["candidates"][0].update(migration_units=[]),
            "unknown field 'migration_units'",
        ),
        (
            lambda value: value["candidates"][0].update(estimate="small"),
            "unknown field 'estimate'",
        ),
        (
            lambda value: value["candidates"][0].update(implementation_order=1),
            "unknown field 'implementation_order'",
        ),
    ],
)
def test_closed_schema_rejects_malformed_inputs(mutation: Any, message: str) -> None:
    ledger = load_fixture()
    mutation(ledger)
    assert any(message in error for error in inventory_errors(ledger))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["campaign"]["edit_packets"][0].update(commit="f" * 40),
            "must match the antigravity inventory snapshot",
        ),
        (
            lambda value: value["campaign"]["edit_packets"][0].update(
                path="docs/outside-selected-surface.md"
            ),
            "must remain inside the declared antigravity selected surface",
        ),
        (
            lambda value: value["campaign"]["selected_surfaces"][0].update(
                repository="different-repository"
            ),
            "must match the host snapshot repository identity",
        ),
        (
            lambda value: value["campaign"]["edit_packets"][0].update(
                id="edit-antigravity-arbitrary"
            ),
            "must equal deterministic packet ID",
        ),
    ],
)
def test_packet_provenance_is_bound_to_snapshot_surface_and_identity(
    mutation: Any, message: str
) -> None:
    ledger = load_fixture()
    mutation(ledger)
    assert any(message in error for error in inventory_errors(ledger))


def test_multiple_source_edits_remain_one_candidate_report_row() -> None:
    report = port_ledger.render_report(load_fixture())
    assert report.count("planning-contract: Planning contract alignment") == 1
    assert "source hosts: antigravity, claude" in report


def test_duplicate_candidate_ownership_fails() -> None:
    ledger = load_fixture()
    mutation = load_fixture("duplicate-source-edits.yaml")
    candidate = next(row for row in ledger["candidates"] if row["id"] == mutation["candidate_id"])
    candidate["edit_packet_ids"].append(mutation["packet_id"])
    packet = next(
        row for row in ledger["campaign"]["edit_packets"] if row["id"] == mutation["packet_id"]
    )
    candidate["provenance"].append(
        {"host": packet["host"], "commit": packet["commit"], "path": packet["path"]}
    )
    assert any(mutation["expected_error"] in error for error in inventory_errors(ledger))


def test_unclassified_packet_blocks_inventory_validation() -> None:
    ledger = load_fixture()
    mutation = load_fixture("unclassified.yaml")
    owner = next(
        candidate
        for candidate in ledger["candidates"]
        if mutation["packet_id"] in candidate["edit_packet_ids"]
    )
    owner["edit_packet_ids"].remove(mutation["packet_id"])
    owner["provenance"] = []
    ledger["campaign"]["unmatched_edit_packet_ids"] = [mutation["packet_id"]]
    ledger["campaign"]["release_drift"]["status"] = "unmatched"
    ledger["campaign"]["release_drift"]["unmatched_edit_packet_ids"] = [mutation["packet_id"]]
    assert any(mutation["expected_error"] in error for error in inventory_errors(ledger))


def test_inventory_only_permits_pending_but_plain_validation_blocks() -> None:
    ledger = pending_ledger()
    assert inventory_errors(ledger) == []
    errors = port_ledger.validate_ledger(ledger)
    assert len(errors) == 1
    assert errors[0].startswith("decision gate: pending candidates")


def test_pending_decision_may_not_claim_operator_or_time() -> None:
    ledger = pending_ledger()
    ledger["candidates"][0]["decision"]["operator"] = "Jeff"
    assert any("pending decisions may not record" in error for error in inventory_errors(ledger))


def test_pending_decision_requires_review_rationale_and_revisit_trigger() -> None:
    ledger = pending_ledger()
    ledger["candidates"][0]["decision"]["rationale"] = ""
    ledger["candidates"][1]["decision"]["revisit_trigger"] = ""
    errors = inventory_errors(ledger)
    assert any(".decision.rationale: expected a non-empty string" in error for error in errors)
    assert any(
        ".decision.revisit_trigger: expected a non-empty string" in error for error in errors
    )


def test_nonpending_decision_requires_rationale_revisit_operator_and_time() -> None:
    ledger = load_fixture()
    ledger["candidates"][0]["decision"] = {
        "state": "rejected",
        "rationale": "",
        "revisit_trigger": "",
        "operator": None,
        "decided_at": None,
    }
    errors = inventory_errors(ledger)
    assert any("require a rationale" in error for error in errors)
    assert any("require a trigger" in error for error in errors)
    assert any(".operator" in error for error in errors)
    assert any(".decided_at" in error for error in errors)


def test_record_decisions_rejects_partial_extra_and_pending_mappings() -> None:
    ledger = pending_ledger()
    partial = load_fixture("unapproved-survivors.yaml")
    with pytest.raises(port_ledger.LedgerError, match="missing codex-independent-execution"):
        port_ledger.record_decisions(
            ledger,
            partial,
            operator="Jeff",
            decided_at="2026-07-30T13:00:00Z",
        )
    complete = {
        **partial,
        "codex-independent-execution": {
            "state": "metadata-only",
            "rationale": "Existing Antigravity behavior covers the contract.",
            "revisit_trigger": "Revisit if host semantics change.",
        },
        "stale-id": {
            "state": "rejected",
            "rationale": "Stale.",
            "revisit_trigger": "Never.",
        },
    }
    with pytest.raises(port_ledger.LedgerError, match="extra/stale stale-id"):
        port_ledger.record_decisions(
            ledger,
            complete,
            operator="Jeff",
            decided_at="2026-07-30T13:00:00Z",
        )
    complete.pop("stale-id")
    complete["codex-independent-execution"]["state"] = "pending"
    with pytest.raises(port_ledger.LedgerError, match="non-pending decision state"):
        port_ledger.record_decisions(
            ledger,
            complete,
            operator="Jeff",
            decided_at="2026-07-30T13:00:00Z",
        )


def test_record_decisions_applies_complete_mapping_without_planning_fields() -> None:
    ledger = pending_ledger()
    mapping = {
        "planning-contract": {
            "state": "approved-survivor",
            "rationale": "Jeff selected the contract.",
            "revisit_trigger": "Revisit if planning is removed.",
        },
        "codex-independent-execution": {
            "state": "rejected",
            "rationale": "Jeff rejected this candidate.",
            "revisit_trigger": "Revisit if host execution changes.",
        },
    }
    updated = port_ledger.record_decisions(
        ledger,
        mapping,
        operator="Jeff",
        decided_at="2026-07-30T13:00:00Z",
    )
    assert port_ledger.validate_ledger(updated) == []
    for candidate in updated["candidates"]:
        assert candidate["decision"]["operator"] == "Jeff"
        assert candidate["decision"]["decided_at"] == "2026-07-30T13:00:00Z"
        assert "migration_units" not in candidate
        assert "estimate" not in candidate


def test_record_decisions_preserves_all_pinned_decision_bytes_when_mapping_is_unchanged() -> None:
    ledger = port_ledger.load_ledger(CAMPAIGN_LEDGER)
    before = {
        row["id"]: port_ledger._canonical_json_bytes(row["decision"])
        for row in ledger["candidates"]
    }
    mapping = {
        row["id"]: {
            "state": row["decision"]["state"],
            "rationale": row["decision"]["rationale"],
            "revisit_trigger": row["decision"]["revisit_trigger"],
        }
        for row in ledger["candidates"]
    }

    updated = port_ledger.record_decisions(
        ledger,
        mapping,
        operator="Jeff",
        decided_at="2026-07-31T20:00:00Z",
    )
    after = {
        row["id"]: port_ledger._canonical_json_bytes(row["decision"])
        for row in updated["candidates"]
    }
    assert after == before


def test_report_is_advisory_complete_and_deterministic() -> None:
    ledger = load_fixture()
    ledger["candidates"][0]["decision"]["state"] = "rejected"
    first = port_ledger.render_report(ledger)
    second = port_ledger.render_report(ledger)
    assert first == second
    assert first.index("planning-contract") < first.index("codex-independent-execution")
    assert "actual decision: rejected" in first
    assert "actual decision: metadata-only" in first
    assert "ranking never selects or hides" in first
    assert "Antigravity state:" in first
    assert "semantic contract:" in first
    assert "required host capabilities:" in first
    assert "rationale:" in first
    assert "revisit trigger:" in first


def test_first_campaign_owns_every_packet_and_records_exact_decisions() -> None:
    ledger = port_ledger.load_ledger(CAMPAIGN_LEDGER)
    packets = ledger["campaign"]["edit_packets"]
    candidates = ledger["candidates"]

    assert len(packets) == 1475
    assert len(candidates) == 80
    assert ledger["campaign"]["unmatched_edit_packet_ids"] == []
    assert inventory_errors(ledger) == []
    assert Counter(candidate["decision"]["state"] for candidate in candidates) == Counter(
        {
            "approved-survivor": 51,
            "blocked": 19,
            "metadata-only": 8,
            "rejected": 1,
            "superseded": 1,
        }
    )
    assert sum(len(candidate["edit_packet_ids"]) for candidate in candidates) == len(packets)
    assert set(ledger["campaign"]["host_receipt"]) == {
        "schema",
        "catalog_digest",
        "receipt_sha256",
        "states",
    }
    assert port_ledger.validate_ledger(ledger) == []


def test_release_drift_must_match_exact_unowned_packet_set() -> None:
    ledger = load_fixture()
    mutation = load_fixture("release-drift.yaml")
    ledger["campaign"]["release_drift"]["status"] = mutation["expected_status"]
    ledger["campaign"]["release_drift"]["unmatched_edit_packet_ids"] = [mutation["packet_id"]]
    assert any(
        "must match campaign unmatched packets" in error for error in inventory_errors(ledger)
    )


def test_antigravity_snapshot_allows_feature_head_but_binds_origin_main() -> None:
    ledger = load_fixture()
    snapshot = next(row for row in ledger["campaign"]["snapshots"] if row["host"] == "antigravity")
    snapshot["head_commit"] = "f" * 40
    assert inventory_errors(ledger) == []

    snapshot["inventory_commit"] = "f" * 40
    errors = inventory_errors(ledger)
    assert any(
        "Antigravity inventory_commit must equal local origin/main" in error for error in errors
    )


def test_release_drift_commit_must_bind_to_local_origin_main() -> None:
    ledger = load_fixture()
    drift = next(
        row
        for row in ledger["campaign"]["release_drift"]["snapshots"]
        if row["host"] == "antigravity"
    )
    drift["current_commit"] = "f" * 40
    assert any(
        "current_commit: must match local origin/main" in error
        for error in inventory_errors(ledger)
    )


def test_nonpassing_required_host_capability_blocks_candidate() -> None:
    ledger = load_fixture()
    candidate = ledger["candidates"][0]
    candidate["required_host_capabilities"] = ["agy.effort.selection"]
    errors = inventory_errors(ledger)
    assert any("required non-passing host capabilities" in error for error in errors)
    candidate["antigravity_state"] = "blocked-by-host"
    candidate["proposed_disposition"] = "blocked"
    assert inventory_errors(ledger) == []


def test_receipt_binding_retains_only_digest_and_sanitized_states() -> None:
    receipt = promotable_receipt()
    binding = port_ledger._sanitize_receipt_binding(receipt)
    assert set(binding) == {"schema", "catalog_digest", "receipt_sha256", "states"}
    assert binding["states"] == [{"capability": "agy.agent.execution", "state": "passed"}]
    assert "runtime_roots" not in binding
    assert len(binding["receipt_sha256"]) == 64


def test_packet_set_digest_vectors() -> None:
    assert (
        port_ledger.packet_set_sha256([])
        == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert (
        port_ledger.packet_set_sha256(["packet-a"])
        == "280974ba2126ccefddb24654e6dfaa24657498b97586fc8c6a4bf72fd89d184b"
    )
    assert (
        port_ledger.packet_set_sha256(["packet-b", "packet-a"])
        == "8e87fbe7e0b6ed4766ec752f3b932df2e0bf78b6026c44d5090bd8aa9d1996d9"
    )
    with pytest.raises(port_ledger.LedgerError, match="unique"):
        port_ledger.packet_set_sha256(["packet-a", "packet-a"])
    with pytest.raises(port_ledger.LedgerError, match="line feeds"):
        port_ledger.packet_set_sha256(["packet-a\npacket-b"])


def test_v1_compatibility_and_version_fail_closed() -> None:
    assert port_ledger.validate_ledger(load_fixture("complete.yaml")) == []
    mislabeled = load_fixture("migration-v1-mislabeled.yaml")
    assert any("unknown field 'migration'" in error for error in inventory_errors(mislabeled))
    unknown = load_fixture("migration-unknown-version.yaml")
    assert any("unknown versions fail closed" in error for error in inventory_errors(unknown))


def test_upgrade_v2_is_deterministic_and_preserves_every_v1_field() -> None:
    original = load_fixture()
    plan = migration_plan(original)
    first = port_ledger.upgrade_v2(original, plan)
    second = port_ledger.upgrade_v2(copy.deepcopy(original), copy.deepcopy(plan))
    assert first == second
    assert first["schema"] == port_ledger.SCHEMA_V2
    assert first["campaign"] == original["campaign"]
    original_by_id = {candidate["id"]: candidate for candidate in original["candidates"]}
    for candidate in first["candidates"]:
        preserved = {key: value for key, value in candidate.items() if key != "migration"}
        assert preserved == original_by_id[candidate["id"]]
        if candidate["decision"]["state"] == "approved-survivor":
            assert candidate["migration"]["state"] == "planned"
            assert candidate["migration"]["packet_set_sha256"] == port_ledger.packet_set_sha256(
                candidate["edit_packet_ids"]
            )
        else:
            assert "migration" not in candidate
    assert port_ledger.validate_ledger(first) == []


def test_migration_plan_rejects_scope_and_containment_failures() -> None:
    ledger = load_fixture()
    base = migration_plan(ledger)
    approved_id = next(iter(base["candidates"]))

    missing = copy.deepcopy(base)
    missing["candidates"].pop(approved_id)
    assert any(
        "exact approved-survivor ID set" in error
        for error in port_ledger.validate_migration_plan(missing, ledger)
    )

    extra = copy.deepcopy(base)
    extra["candidates"]["codex-independent-execution"] = copy.deepcopy(
        base["candidates"][approved_id]
    )
    assert any(
        "extra/non-survivor" in error
        for error in port_ledger.validate_migration_plan(extra, ledger)
    )

    escaped = copy.deepcopy(base)
    escaped["candidates"][approved_id]["target_paths"] = ["../escape.py"]
    assert any(
        "safe repository-relative" in error
        for error in port_ledger.validate_migration_plan(escaped, ledger)
    )

    source_target = copy.deepcopy(base)
    source_target["candidates"][approved_id]["target_paths"] = [
        "plugins/team-execution/tests/test_source.py",
        "plugins/saga/tests/test_port_ledger.py",
    ]
    assert any(
        "team-execution targets are forbidden" in error
        for error in port_ledger.validate_migration_plan(source_target, ledger)
    )


def test_planned_blocked_and_migrated_v2_fixtures_enforce_state_rules() -> None:
    planned = load_fixture("migration-planned.yaml")
    blocked = load_fixture("migration-blocked.yaml")
    migrated = load_fixture("migration-migrated.yaml")
    assert port_ledger.validate_ledger(planned) == []
    assert port_ledger.validate_ledger(blocked) == []
    assert port_ledger.validate_ledger(migrated, require_migrated=True) == []
    assert any(
        "--require-migrated" in error
        for error in port_ledger.validate_ledger(planned, require_migrated=True)
    )
    planned["candidates"][0]["migration"]["state"] = "migrated"
    assert any(
        "require evidence and validation time" in error for error in inventory_errors(planned)
    )
    planned = load_fixture("migration-planned.yaml")
    planned["candidates"][0]["migration"]["packet_set_sha256"] = "0" * 64
    assert any("exact owned packet set" in error for error in inventory_errors(planned))


def test_real_migration_plan_equals_ratified_survivors_contracts_packets_and_nodes() -> None:
    ledger = port_ledger.load_ledger(CAMPAIGN_LEDGER)
    plan_path = CAMPAIGN_LEDGER.parent / "migration-plan.v1.yaml"
    plan = port_ledger.load_migration_plan(plan_path, ledger)
    approved = {
        candidate["id"]: candidate
        for candidate in ledger["candidates"]
        if candidate["decision"]["state"] == "approved-survivor"
    }
    assert len(approved) == len(plan["candidates"]) == 51
    assert set(approved) == set(plan["candidates"])
    assert len(port_ledger.migration_plan_nodes(plan)) == 102
    for candidate_id, candidate in approved.items():
        assert (
            plan["candidates"][candidate_id]["semantic_contract"] == candidate["semantic_contract"]
        )
        assert candidate["migration"]["packet_set_sha256"] == port_ledger.packet_set_sha256(
            candidate["edit_packet_ids"]
        )


def test_canonical_evidence_records_all_migrations_or_rejects_atomically(tmp_path: Path) -> None:
    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    valid_path = FIXTURES / "migration-evidence-valid.json"
    evidence = port_ledger.load_migration_evidence(valid_path, planned, plan)
    migrated = port_ledger.record_migrations(
        planned,
        plan,
        evidence,
        validated_at="2026-07-30T18:00:00Z",
    )
    assert port_ledger.validate_ledger(migrated, require_migrated=True) == []
    assert (
        migrated["candidates"][0]["migration"]["evidence_manifest_sha256"]
        == evidence["manifest_sha256"]
    )

    ledger_path = tmp_path / "ledger.yaml"
    plan_path = tmp_path / "migration-plan.v1.yaml"
    evidence_path = FIXTURES / "migration-evidence-invalid.json"
    port_ledger.write_ledger(ledger_path, planned)
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    before = ledger_path.read_bytes()
    result = port_ledger.main(
        [
            "record-migrations",
            str(ledger_path),
            str(plan_path),
            str(evidence_path),
            "--validated-at",
            "2026-07-30T18:00:00Z",
        ]
    )
    assert result == 1
    assert ledger_path.read_bytes() == before


def test_recording_preserves_campaign_decisions_packets_and_nonmigration_candidates() -> None:
    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    evidence = port_ledger.load_migration_evidence(
        FIXTURES / "migration-evidence-valid.json", planned, plan
    )
    migrated = port_ledger.record_migrations(
        planned,
        plan,
        evidence,
        validated_at="2026-07-30T18:00:00Z",
    )
    assert port_ledger._migration_preservation_errors(
        planned, migrated, set(plan["candidates"])
    ) == []
    tampered = copy.deepcopy(migrated)
    tampered["candidates"][0]["decision"]["rationale"] += " Changed after approval."
    assert any(
        "source decision or packet authority changed" in error
        for error in port_ledger._migration_preservation_errors(
            planned, tampered, set(plan["candidates"])
        )
    )
    reordered = copy.deepcopy(migrated)
    reordered["candidates"].reverse()
    assert any(
        "changed candidate order" in error
        for error in port_ledger._migration_preservation_errors(
            planned, reordered, set(plan["candidates"])
        )
    )


def test_upgrade_rejects_partial_plan_with_v1_bytes_unchanged(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.yaml"
    plan_path = tmp_path / "migration-plan.v1.yaml"
    original = load_fixture()
    port_ledger.write_ledger(ledger_path, original)
    plan = migration_plan(original)
    plan["candidates"].clear()
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    before = ledger_path.read_bytes()

    result = port_ledger.main(["upgrade-v2", str(ledger_path), str(plan_path)])

    assert result == 1
    assert ledger_path.read_bytes() == before


def test_evidence_requires_canonical_json_and_closed_typed_results(tmp_path: Path) -> None:
    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    valid = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    valid["results"]["implement-migration-gate"]["extra"] = True
    valid["manifest_sha256"] = port_ledger._canonical_json_sha256(
        {key: value for key, value in valid.items() if key != "manifest_sha256"}
    )
    errors = port_ledger.validate_migration_evidence(valid, planned, plan)
    assert any("unknown field 'extra'" in error for error in errors)

    noncanonical = tmp_path / "evidence.json"
    noncanonical.write_text(
        json.dumps(json.loads((FIXTURES / "migration-evidence-valid.json").read_text()), indent=2)
        + "\n"
    )
    with pytest.raises(port_ledger.LedgerError, match="canonical JSON"):
        port_ledger.load_migration_evidence(noncanonical, planned, plan)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["host_binding"].update(receipt_sha256="0" * 64),
            "sanitized host receipt",
        ),
        (
            lambda value: value["source_binding"].update(operator_gate_state="reset"),
            "operator_gate_state",
        ),
        (
            lambda value: value["candidate_evidence"].clear(),
            "exact approved-survivor ID set",
        ),
        (
            lambda value: value["results"]["implement-migration-gate"].update(
                terminal_status="failed"
            ),
            "did not pass",
        ),
        (
            lambda value: value["candidate_evidence"]["planning-contract"]["pytest_outcomes"][
                0
            ].update(status="skipped"),
            "every mapped node must pass",
        ),
        (
            lambda value: value["results"]["review-migration-evidence"].update(
                verdict="needs-revision"
            ),
            "did not pass",
        ),
    ],
)
def test_evidence_rejects_stale_failed_incomplete_and_nonaccepting_content(
    mutation: Any,
    message: str,
) -> None:
    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    mutation(evidence)
    evidence["manifest_sha256"] = port_ledger._canonical_json_sha256(
        {key: value for key, value in evidence.items() if key != "manifest_sha256"}
    )
    assert any(
        message in error
        for error in port_ledger.validate_migration_evidence(evidence, planned, plan)
    )


def _redigest_evidence(evidence: dict[str, Any]) -> None:
    evidence["manifest_sha256"] = port_ledger._canonical_json_sha256(
        {key: value for key, value in evidence.items() if key != "manifest_sha256"}
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["results"]["implement-migration-gate"].update(
                agent_path="/root/spoofed"
            ),
            "unknown field 'agent_path'",
        ),
        (
            lambda value: value["results"]["implement-migration-gate"].update(
                role_id="unrelated-worker"
            ),
            "unknown field 'role_id'",
        ),
        (
            lambda value: value["candidate_evidence"]["planning-contract"].update(
                owning_result_ids=["missing-result"]
            ),
            "did not pass",
        ),
        (
            lambda value: value["candidate_evidence"]["planning-contract"]["pytest_outcomes"][
                0
            ].update(node_id="plugins/saga/tests/test_port_ledger.py::test_does_not_exist"),
            "exact mapped node set",
        ),
        (
            lambda value: value["results"]["review-migration-evidence"].update(
                dimensions=[]
            ),
            "unknown field 'dimensions'",
        ),
    ],
)
def test_evidence_binds_results_to_checks_without_workflow_identity(
    mutation: Any, message: str
) -> None:
    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    mutation(evidence)
    _redigest_evidence(evidence)
    assert any(
        message in error
        for error in port_ledger.validate_migration_evidence(evidence, planned, plan)
    )


def test_evidence_allows_irrelevant_results_and_empty_reviewed_unchanged_paths() -> None:
    planned = load_fixture("migration-planned.yaml")
    planned["campaign"]["id"] = "2026-07-30-saga-reliability"
    plan = migration_plan(planned)
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    evidence["campaign_id"] = "2026-07-30-saga-reliability"
    evidence["results"].pop("recheck-migration-once")
    evidence["candidate_evidence"]["planning-contract"]["reviewed_unchanged_paths"] = []
    _redigest_evidence(evidence)
    assert port_ledger.validate_migration_evidence(evidence, planned, plan) == []


@pytest.mark.parametrize(
    "field",
    ["attempt_id", "agent_path", "role_id", "profile_id", "coverage"],
)
def test_result_schema_rejects_workflow_identity_and_custom_coverage(field: str) -> None:
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    result = copy.deepcopy(evidence["results"]["implement-migration-gate"])
    result[field] = {} if field == "coverage" else "workflow-specific-value"
    errors: list[str] = []
    assert not port_ledger._validate_result(
        result, "result", "implement-migration-gate", errors
    )
    assert any(f"unknown field '{field}'" in error for error in errors)


def test_source_binding_rejects_decision_mutation_without_pinned_campaign_digests() -> None:
    ledger = load_fixture("migration-planned.yaml")
    plan = migration_plan(ledger)
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    candidate = ledger["candidates"][0]
    candidate["decision"]["rationale"] += " Tampered."
    assert port_ledger.validate_ledger(ledger) == []
    assert any(
        "decision_sha256" in error
        for error in port_ledger.validate_migration_evidence(evidence, ledger, plan)
    )


def test_repository_release_refresh_is_pinned_to_approved_antigravity_source() -> None:
    ledger = port_ledger.load_ledger(CAMPAIGN_LEDGER)
    approved_commit = "45463432612ff271c9a12b02aa1fab9390ba9ac1"
    snapshots = {row["host"]: row for row in ledger["campaign"]["snapshots"]}
    assert snapshots["antigravity"]["inventory_commit"] == approved_commit
    assert snapshots["antigravity"]["origin_main_commit"] == approved_commit

    candidate = next(
        row for row in ledger["candidates"] if row["id"] == "repository-release-validation"
    )
    assert {row["commit"] for row in candidate["provenance"] if row["host"] == "antigravity"} == {
        approved_commit
    }
    packet_by_id = {row["id"]: row for row in ledger["campaign"]["edit_packets"]}
    helper_packet = next(
        packet_by_id[packet_id]
        for packet_id in candidate["edit_packet_ids"]
        if packet_by_id[packet_id]["path"] == "scripts/port_claude_plugin.py"
    )
    assert helper_packet["content_sha256"] == (
        "3c4f49b8b677dda7cdbb93b729fc051e5c188e136ade2c1dccb0fe8a9f6b998f"
    )
    assert candidate["decision"] == {
        "state": "metadata-only",
        "rationale": (
            "Retain metadata-only after reviewing Antigravity origin/main "
            f"{approved_commit}. The owned helper now labels destructive bulk-copying as "
            "legacy, directs normal campaigns to the semantic port ledger, and emits a "
            "warning. This strengthens the existing Antigravity-native release and port "
            "governance contract without adding survivor behavior."
        ),
        "revisit_trigger": (
            "Reassess if scripts/port_claude_plugin.py gains new supported port behavior, "
            "stops directing normal campaigns to the semantic ledger, or release and "
            "installation validation stops passing."
        ),
        "operator": "Jeff",
        "decided_at": "2026-07-31T23:31:53Z",
    }


def test_generic_result_requires_completed_checks_and_declared_test_outcomes() -> None:
    evidence = json.loads((FIXTURES / "migration-evidence-valid.json").read_text())
    result = copy.deepcopy(evidence["results"]["test-git-free-migration"])
    errors: list[str] = []
    assert port_ledger._validate_result(
        result, "result", "test-git-free-migration", errors
    )
    assert errors == []
    result["pytest_outcomes"][0]["status"] = "failed"
    failed_errors: list[str] = []
    assert not port_ledger._validate_result(
        result, "result", "test-git-free-migration", failed_errors
    )
    assert any("tester evidence must pass" in error for error in failed_errors)


def test_closed_schema_helpers_report_malformed_boundary_values() -> None:
    errors: list[str] = []
    assert port_ledger._mapping([], "row", errors) is None
    assert port_ledger._mapping({1: "value"}, "row", errors) is None
    assert port_ledger._sequence("value", "items", errors) is None
    port_ledger._closed({"extra": True}, frozenset({"required"}), "row", errors)
    assert port_ledger._required_string("", "name", errors) is None
    assert port_ledger._required_string(1, "name", errors, allow_empty=True) is None
    assert port_ledger._identifier("Not-Stable", "id", errors) is None
    assert port_ledger._sha("xyz", "digest", errors, port_ledger.SHA256_RE) is None
    for value in ("/absolute", "../escape", "with\\backslash", ".git/config"):
        assert port_ledger._repository_path(value, "path", errors) is None
    assert port_ledger._string_list("bad", "list", errors) == []
    assert port_ledger._string_list(["same", "same"], "list", errors) == ["same", "same"]
    assert port_ledger._string_list([], "list", errors, nonempty=True) == []
    assert any("unknown field" in error for error in errors)
    assert any("duplicate values" in error for error in errors)


def test_campaign_boundary_validators_report_complete_malformed_inputs() -> None:
    sha = "a" * 40
    other = "b" * 40
    snapshots = [
        {
            "host": "claude",
            "repository": "plugins/claude",
            "planning_commit": sha,
            "inventory_commit": sha,
            "head_commit": other,
            "origin_main_commit": sha,
        },
        {
            "host": "codex",
            "repository": "plugins/codex",
            "planning_commit": sha,
            "inventory_commit": sha,
            "head_commit": sha,
            "origin_main_commit": other,
        },
        {
            "host": "antigravity",
            "repository": "plugins/antigravity",
            "planning_commit": sha,
            "inventory_commit": sha,
            "head_commit": sha,
            "origin_main_commit": other,
        },
        {
            "host": "claude",
            "repository": "../escape",
            "planning_commit": "bad",
            "inventory_commit": "bad",
            "head_commit": "bad",
            "origin_main_commit": "bad",
        },
        None,
    ]
    errors: list[str] = []
    parsed_snapshots = port_ledger._validate_snapshots(snapshots, errors)
    surfaces = [
        {"host": "claude", "repository": "different", "paths": ["plugins"]},
        {"host": "codex", "repository": "plugins/codex", "paths": []},
        {"host": "antigravity", "repository": "plugins/antigravity", "paths": ["scripts"]},
        {"host": "claude", "repository": "plugins/claude", "paths": ["plugins"]},
        None,
    ]
    parsed_surfaces = port_ledger._validate_surfaces(surfaces, errors)
    port_ledger._validate_snapshot_surface_repositories(parsed_snapshots, parsed_surfaces, errors)
    port_ledger._validate_seeds(
        [
            {"host": "codex", "commit": "bad"},
            {"host": "codex", "commit": sha},
            {"host": "unknown", "commit": sha},
            None,
        ],
        errors,
    )
    states = port_ledger._validate_host_receipt(
        {
            "schema": "wrong",
            "catalog_digest": "bad",
            "receipt_sha256": "bad",
            "states": [
                {"capability": "agy.agent.execution", "state": "wrong"},
                {"capability": "agy.agent.execution", "state": "passed"},
                {"capability": "agy.agent.execution", "state": "failed"},
                None,
            ],
        },
        errors,
    )
    assert states["agy.agent.execution"] == "wrong"
    port_ledger._validate_release_drift(
        {
            "checked_at": "not-a-time",
            "status": "wrong",
            "snapshots": [
                {"host": "claude", "inventory_commit": other, "current_commit": other},
                {"host": "claude", "inventory_commit": sha, "current_commit": sha},
                {"host": "unknown", "inventory_commit": "bad", "current_commit": "bad"},
                None,
            ],
            "unmatched_edit_packet_ids": ["unknown-packet"],
        },
        [],
        parsed_snapshots,
        errors,
    )
    assert any("duplicate host snapshot" in error for error in errors)
    assert any("must disclose every host" in error for error in errors)
    assert any("expected an ISO-8601" in error for error in errors)


def test_read_only_git_argument_grammar_fails_closed_without_running_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = [
        ("rev-parse", "HEAD"),
        ("rev-parse", "abc^{commit}"),
        ("diff", "--name-status", "-z", "left..right", "--", "plugins"),
        ("ls-tree", "-r", "-z", "--full-tree", "--name-only", "commit", "--", "plugins"),
        ("show", "--no-ext-diff", "commit:path"),
    ]
    for arguments in valid:
        port_ledger._validate_git_arguments(arguments)
    invalid = [
        (),
        ("status",),
        ("rev-parse", "--bad"),
        ("rev-parse", "HEAD", "extra"),
        ("diff", "bad"),
        ("diff", "--name-status", "-z", "left..right", "plugins"),
        ("ls-tree", "bad"),
        ("ls-tree", "-r", "-z", "--full-tree", "--name-only", "commit", "plugins"),
        ("show", "bad"),
        ("show", "--no-ext-diff", "path-without-commit"),
        ("show", "--no-ext-diff", "-bad:path"),
        ("show", "--no-ext-diff", "commit:path\x00unsafe"),
        ("show", "--no-ext-diff", "-Cunsafe:path"),
    ]
    for arguments in invalid:
        with pytest.raises(port_ledger.LedgerError):
            port_ledger._validate_git_arguments(arguments)

    def fail_run(*args: Any, **kwargs: Any) -> None:
        raise OSError("unavailable")

    monkeypatch.setattr(port_ledger.subprocess, "run", fail_run)
    with pytest.raises(port_ledger.LedgerError, match="read-only Git command failed"):
        port_ledger.ReadOnlyGitRunner().run(Path("repo"), ("rev-parse", "HEAD"))


def test_migration_plan_node_reader_rejects_malformed_shapes() -> None:
    with pytest.raises(port_ledger.LedgerError, match="expected an object"):
        port_ledger.migration_plan_nodes([])
    malformed = {
        "schema": "wrong",
        "ledger_schema": "wrong",
        "campaign_id": "",
        "candidates": {
            "Bad ID": None,
            "valid-id": {
                "candidate_id": "valid-id",
                "semantic_contract": "contract",
                "edit_packet_ids": ["packet"],
                "target_paths": ["scripts/port_ledger.py"],
                "test_node_ids": [
                    "plugins/saga/tests/test_port_ledger.py::test_packet_set_digest_vectors"
                ],
                "negative_test_node_ids": [
                    "plugins/saga/tests/test_port_ledger.py::test_packet_set_digest_vectors"
                ],
                "final_antigravity_state": "present",
                "intentional_differences": ["none"],
                "extra": True,
            },
        },
        "extra": True,
    }
    with pytest.raises(port_ledger.LedgerError, match="duplicate node IDs"):
        port_ledger.migration_plan_nodes(malformed)


def test_non_git_cli_paths_render_results_and_failures(tmp_path: Path, capsys) -> None:
    ledger_path = tmp_path / "ledger.yaml"
    port_ledger.write_ledger(ledger_path, load_fixture())
    assert port_ledger.main(["validate", "--inventory-only", str(ledger_path)]) == 0
    assert "inventory is complete" in capsys.readouterr().out
    assert port_ledger.main(["validate", str(ledger_path)]) == 0
    assert "fully decided" in capsys.readouterr().out
    pending = load_fixture()
    pending["candidates"][0]["decision"]["state"] = "pending"
    port_ledger.write_ledger(ledger_path, pending)
    assert port_ledger.main(["validate", str(ledger_path)]) == 1
    assert "Ledger validation failed" in capsys.readouterr().err
    port_ledger.write_ledger(ledger_path, load_fixture())
    assert port_ledger.main(["report", str(ledger_path)]) == 0
    assert "Semantic port campaign" in capsys.readouterr().out

    plan = yaml.safe_load(
        (CAMPAIGN_LEDGER.parent / "migration-plan.v1.yaml").read_text(encoding="utf-8")
    )
    plan_path = tmp_path / "plan.yaml"
    port_ledger.write_ledger(plan_path, plan)
    assert port_ledger.main(["pytest-args", str(plan_path), "--partition", "non-git"]) == 0
    output = capsys.readouterr().out
    assert "test_release_refresh_uses_controlled_temporary_repositories" not in output
    assert port_ledger.main(["test-nodes", str(plan_path)]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 102

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("[unterminated", encoding="utf-8")
    assert port_ledger.main(["validate", str(invalid)]) == 1
    assert "could not load YAML input" in capsys.readouterr().err


def test_mutating_cli_commands_succeed_only_on_temporary_files(tmp_path: Path, capsys) -> None:
    ledger_path = tmp_path / "ledger.yaml"
    mapping_path = tmp_path / "mapping.yaml"
    ledger = pending_ledger()
    port_ledger.write_ledger(ledger_path, ledger)
    mapping = {
        "planning-contract": {
            "state": "approved-survivor",
            "rationale": "Jeff selected the contract.",
            "revisit_trigger": "Revisit if planning is removed.",
        },
        "codex-independent-execution": {
            "state": "rejected",
            "rationale": "Jeff rejected this candidate.",
            "revisit_trigger": "Revisit if host execution changes.",
        },
    }
    port_ledger.write_ledger(mapping_path, mapping)
    assert (
        port_ledger.main(
            [
                "record-decisions",
                str(ledger_path),
                str(mapping_path),
                "--operator",
                "Jeff",
                "--decided-at",
                "2026-07-30T13:00:00Z",
            ]
        )
        == 0
    )
    assert "Recorded complete decisions" in capsys.readouterr().out

    v1 = load_fixture()
    port_ledger.write_ledger(ledger_path, v1)
    plan_path = tmp_path / "migration-plan.yaml"
    port_ledger.write_ledger(plan_path, migration_plan(v1))
    assert port_ledger.main(["upgrade-v2", str(ledger_path), str(plan_path)]) == 0
    assert "Upgraded semantic-port ledger" in capsys.readouterr().out

    planned = load_fixture("migration-planned.yaml")
    plan = migration_plan(planned)
    port_ledger.write_ledger(ledger_path, planned)
    port_ledger.write_ledger(plan_path, plan)
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_bytes((FIXTURES / "migration-evidence-valid.json").read_bytes())
    assert (
        port_ledger.main(
            [
                "record-migrations",
                str(ledger_path),
                str(plan_path),
                str(evidence_path),
                "--validated-at",
                "2026-07-30T18:00:00Z",
            ]
        )
        == 0
    )
    assert "Recorded complete migration evidence" in capsys.readouterr().out


def test_discover_cli_wiring_validates_receipt_without_running_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    receipt_path = tmp_path / "receipt.yaml"
    port_ledger.write_ledger(receipt_path, promotable_receipt())
    observed: dict[str, Any] = {}

    def fake_discover(**kwargs: Any) -> dict[str, Any]:
        observed.update(kwargs)
        return {}

    monkeypatch.setattr(port_ledger, "discover", fake_discover)
    output = tmp_path / "output.yaml"
    repositories = {host: tmp_path / host for host in ("claude", "codex", "antigravity")}
    assert (
        port_ledger.main(
            [
                "discover",
                "--campaign-id",
                "2026-07-30-fixture",
                "--output",
                str(output),
                "--claude-repo",
                str(repositories["claude"]),
                "--codex-repo",
                str(repositories["codex"]),
                "--antigravity-repo",
                str(repositories["antigravity"]),
                "--claude-seed",
                "a" * 40,
                "--claude-planning-snapshot",
                "b" * 40,
                "--codex-planning-snapshot",
                "c" * 40,
                "--antigravity-planning-snapshot",
                "d" * 40,
                "--host-receipt",
                str(receipt_path),
                "--checked-at",
                "2026-07-31T12:00:00Z",
            ]
        )
        == 0
    )
    assert observed["repositories"] == repositories
    assert observed["output"] == output
    assert "Refreshed discovery ledger" in capsys.readouterr().out

    invalid = tmp_path / "invalid-receipt.yaml"
    port_ledger.write_ledger(invalid, [])
    arguments = [
        "discover",
        "--campaign-id",
        "2026-07-30-fixture",
        "--output",
        str(output),
        "--claude-seed",
        "a" * 40,
        "--claude-planning-snapshot",
        "b" * 40,
        "--codex-planning-snapshot",
        "c" * 40,
        "--antigravity-planning-snapshot",
        "d" * 40,
        "--host-receipt",
        str(invalid),
        "--checked-at",
        "2026-07-31T12:00:00Z",
    ]
    assert port_ledger.main(arguments) == 1
    assert "host receipt must be an object" in capsys.readouterr().err


def test_atomic_write_rejects_ledger_and_evidence_races(tmp_path: Path) -> None:
    target = tmp_path / "ledger.yaml"
    evidence_path = tmp_path / "evidence.json"
    port_ledger.write_ledger(target, load_fixture())
    evidence_path.write_text("original", encoding="utf-8")
    original_target = target.read_bytes()
    original_evidence = evidence_path.read_bytes()

    def change_ledger() -> None:
        target.write_text("concurrent-ledger", encoding="utf-8")

    with pytest.raises(port_ledger.LedgerError, match="changed during validation"):
        port_ledger.write_ledger(
            target,
            load_fixture(),
            compare_inputs={target: original_target, evidence_path: original_evidence},
            before_replace=change_ledger,
        )
    assert target.read_text() == "concurrent-ledger"

    target.write_bytes(original_target)

    def change_evidence() -> None:
        evidence_path.write_text("concurrent-evidence", encoding="utf-8")

    with pytest.raises(port_ledger.LedgerError, match="changed during validation"):
        port_ledger.write_ledger(
            target,
            load_fixture(),
            compare_inputs={target: original_target, evidence_path: original_evidence},
            before_replace=change_evidence,
        )
    assert target.read_bytes() == original_target
    assert evidence_path.read_text() == "concurrent-evidence"


def test_git_runner_allowlist_rejects_source_write_commands() -> None:
    for arguments in [
        ("checkout", "main"),
        ("fetch",),
        ("pull",),
        ("add", "."),
        ("commit", "-m", "no"),
        ("push",),
        ("reset", "--hard"),
        ("clean", "-fd"),
        ("status",),
    ]:
        with pytest.raises(port_ledger.LedgerError):
            port_ledger._validate_git_arguments(arguments)


def test_discovery_rejects_escaped_output_before_any_repository_command(
    tmp_path: Path,
) -> None:
    repositories = make_repositories(tmp_path)
    runner = FakeGitRunner()
    with pytest.raises(port_ledger.LedgerError, match="must remain beneath"):
        port_ledger.discover(
            campaign_id="2026-07-30-fixture",
            output=tmp_path / "escaped.yaml",
            repositories=repositories,
            planning_snapshots=COMMITS,
            claude_seed="1" * 40,
            host_receipt=promotable_receipt(),
            runner=runner,
            checked_at="2026-07-30T12:00:00Z",
        )
    assert runner.calls == []


def test_discovery_rejects_symlinked_campaign_before_repository_commands(
    tmp_path: Path,
) -> None:
    repositories = make_repositories(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    campaign_parent = repositories["antigravity"] / "docs" / "ports"
    campaign_parent.mkdir(parents=True)
    campaign = campaign_parent / "2026-07-30-fixture"
    campaign.symlink_to(outside, target_is_directory=True)
    output = campaign / "ledger.yaml"
    runner = FakeGitRunner()

    with pytest.raises(port_ledger.LedgerError, match="symbolic link"):
        port_ledger.discover(
            campaign_id="2026-07-30-fixture",
            output=output,
            repositories=repositories,
            planning_snapshots=COMMITS,
            claude_seed="1" * 40,
            host_receipt=promotable_receipt(),
            runner=runner,
            checked_at="2026-07-30T12:00:00Z",
        )

    assert runner.calls == []
    assert not (outside / "ledger.yaml").exists()


def test_discovery_rejects_symlinked_nested_parent_before_repository_commands(
    tmp_path: Path,
) -> None:
    repositories = make_repositories(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    campaign = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture"
    campaign.mkdir(parents=True)
    nested = campaign / "nested"
    nested.symlink_to(outside, target_is_directory=True)
    output = nested / "ledger.yaml"
    runner = FakeGitRunner()

    with pytest.raises(port_ledger.LedgerError, match="symbolic link"):
        port_ledger.discover(
            campaign_id="2026-07-30-fixture",
            output=output,
            repositories=repositories,
            planning_snapshots=COMMITS,
            claude_seed="1" * 40,
            host_receipt=promotable_receipt(),
            runner=runner,
            checked_at="2026-07-30T12:00:00Z",
        )

    assert runner.calls == []
    assert not (outside / "ledger.yaml").exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_source_discovery_stops_on_local_head_origin_divergence(tmp_path: Path, host: str) -> None:
    repositories = make_repositories(tmp_path)
    output = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"
    runner = FakeGitRunner(divergent_host=host)
    with pytest.raises(port_ledger.LedgerError, match="HEAD differs"):
        port_ledger.discover(
            campaign_id="2026-07-30-fixture",
            output=output,
            repositories=repositories,
            planning_snapshots=COMMITS,
            claude_seed="1" * 40,
            host_receipt=promotable_receipt(),
            runner=runner,
            checked_at="2026-07-30T12:00:00Z",
        )
    assert not output.exists()


def test_antigravity_feature_head_is_recorded_but_origin_main_is_inventoried(
    tmp_path: Path,
) -> None:
    repositories = make_repositories(tmp_path)
    output = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"
    ledger = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(divergent_host="antigravity"),
        checked_at="2026-07-30T12:00:00Z",
    )

    snapshot = next(row for row in ledger["campaign"]["snapshots"] if row["host"] == "antigravity")
    drift = next(
        row
        for row in ledger["campaign"]["release_drift"]["snapshots"]
        if row["host"] == "antigravity"
    )
    antigravity_packets = [
        packet for packet in ledger["campaign"]["edit_packets"] if packet["host"] == "antigravity"
    ]

    assert snapshot == {
        "host": "antigravity",
        "repository": "antigravity",
        "planning_commit": COMMITS["antigravity"],
        "inventory_commit": COMMITS["antigravity"],
        "head_commit": "f" * 40,
        "origin_main_commit": COMMITS["antigravity"],
    }
    assert drift == {
        "host": "antigravity",
        "inventory_commit": COMMITS["antigravity"],
        "current_commit": COMMITS["antigravity"],
    }
    assert antigravity_packets
    assert {packet["commit"] for packet in antigravity_packets} == {COMMITS["antigravity"]}


def test_discovery_is_read_only_except_for_explicit_campaign_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("legacy bulk-copy helper reached by discovery")

    monkeypatch.setattr(port_claude_plugin, "port_plugin", forbidden)
    repositories = make_repositories(tmp_path)
    before = {
        host: hashlib.sha256((repository / "sentinel.txt").read_bytes()).hexdigest()
        for host, repository in repositories.items()
    }
    output = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"
    runner = FakeGitRunner()
    ledger = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=runner,
        checked_at="2026-07-30T12:00:00Z",
    )
    after = {
        host: hashlib.sha256((repository / "sentinel.txt").read_bytes()).hexdigest()
        for host, repository in repositories.items()
    }
    assert before == after
    assert output.is_file()
    assert len(ledger["campaign"]["edit_packets"]) == 4
    assert all(call[1][0] in {"rev-parse", "diff", "ls-tree", "show"} for call in runner.calls)


def test_discovery_cannot_reach_legacy_copy_or_delete_functions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("legacy copy/delete function reached by discovery")

    monkeypatch.setattr(port_claude_plugin, "port_plugin", forbidden)
    monkeypatch.setattr(shutil, "copytree", forbidden)
    monkeypatch.setattr(shutil, "rmtree", forbidden)
    repositories = make_repositories(tmp_path)
    output = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"

    port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )

    assert output.is_file()


def test_stale_or_absent_history_delta_still_emits_complete_tree_packets(
    tmp_path: Path,
) -> None:
    class NoHistoryRunner(FakeGitRunner):
        def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
            if arguments[0] == "diff":
                self.calls.append((repository.name, arguments))
                return b""
            return super().run(repository, arguments)

    repositories = make_repositories(tmp_path)
    output = repositories["antigravity"] / "docs" / "ports" / "2026-07-30-fixture" / "ledger.yaml"
    ledger = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=NoHistoryRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    tree_hosts = {
        packet["host"]
        for packet in ledger["campaign"]["edit_packets"]
        if packet["source"] == "tree"
    }
    assert tree_hosts == port_ledger.HOSTS


def test_discovery_refresh_preserves_stable_candidate_ownership(tmp_path: Path) -> None:
    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    first = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    packet_ids = [packet["id"] for packet in first["campaign"]["edit_packets"]]
    packet_by_id = {packet["id"]: packet for packet in first["campaign"]["edit_packets"]}
    first["candidates"] = [
        {
            "id": "stable-capability",
            "title": "Stable capability",
            "edit_packet_ids": packet_ids,
            "provenance": port_ledger._provenance_for(packet_ids, packet_by_id),
            "semantic_contract": "The capability retains stable edit ownership.",
            "adjacent_dependencies": [],
            "required_host_capabilities": [],
            "antigravity_state": "partial",
            "proposed_disposition": "antigravity-adapt",
            "ranking": {
                "operator_value": 3,
                "antigravity_fit": 3,
                "proof_feasibility": 3,
                "maintenance_cost": 3,
            },
            "evidence_expectation": ["Refresh retains the stable candidate ID."],
            "decision": {
                "state": "pending",
                "rationale": (
                    "Stable ownership is ready for operator review but does not "
                    "choose a disposition."
                ),
                "revisit_trigger": (
                    "Reassess if refresh changes the packet set or source contract."
                ),
                "operator": None,
                "decided_at": None,
            },
        }
    ]
    first["campaign"]["unmatched_edit_packet_ids"] = []
    first["campaign"]["release_drift"]["status"] = "clean"
    first["campaign"]["release_drift"]["unmatched_edit_packet_ids"] = []
    assert inventory_errors(first) == []
    port_ledger.write_ledger(output, first)

    refreshed = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T13:00:00Z",
    )
    assert refreshed["candidates"][0]["id"] == "stable-capability"
    assert refreshed["candidates"][0]["edit_packet_ids"] == packet_ids
    assert refreshed["campaign"]["unmatched_edit_packet_ids"] == []


def test_identical_evidence_refresh_preserves_decision_authority(tmp_path: Path) -> None:
    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    first = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    attach_decided_candidate(first)
    assert port_ledger.validate_ledger(first) == []
    port_ledger.write_ledger(output, first)
    before = output.read_bytes()

    refreshed = port_ledger.release_refresh(
        ledger_path=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )

    assert refreshed["candidates"][0]["decision"] == first["candidates"][0]["decision"]
    assert port_ledger.validate_ledger(refreshed) == []
    assert output.read_bytes() == before


def test_release_refresh_uses_controlled_temporary_repositories(tmp_path: Path) -> None:
    repositories, snapshots, claude_seed, ledger_path = prepare_controlled_release_ledger(tmp_path)
    before = ledger_path.read_bytes()

    refreshed = port_ledger.release_refresh(
        ledger_path=ledger_path,
        repositories=repositories,
        planning_snapshots=snapshots,
        claude_seed=claude_seed,
        host_receipt=promotable_receipt(),
        checked_at="2026-07-30T12:00:00Z",
    )

    assert port_ledger._serialize_ledger(refreshed).encode("utf-8") == before
    assert ledger_path.read_bytes() == before
    assert all(
        run_controlled_git(repository, "remote") == "" for repository in repositories.values()
    )


def test_release_refresh_rejects_drift_byte_identically(tmp_path: Path) -> None:
    repositories, snapshots, claude_seed, ledger_path = prepare_controlled_release_ledger(tmp_path)
    before = ledger_path.read_bytes()
    codex_repository = repositories["codex"]
    source = codex_repository / "plugins" / "saga" / "README.md"
    source.write_text("codex drift\n")
    run_controlled_git(codex_repository, "add", "plugins/saga/README.md")
    run_controlled_git(codex_repository, "commit", "-q", "-m", "codex drift")
    run_controlled_git(
        codex_repository,
        "update-ref",
        "refs/remotes/origin/main",
        run_controlled_git(codex_repository, "rev-parse", "HEAD"),
    )

    with pytest.raises(port_ledger.LedgerError, match="release refresh detected drift"):
        port_ledger.release_refresh(
            ledger_path=ledger_path,
            repositories=repositories,
            planning_snapshots=snapshots,
            claude_seed=claude_seed,
            host_receipt=promotable_receipt(),
            checked_at="2026-07-30T12:00:00Z",
        )

    assert ledger_path.read_bytes() == before
    assert run_controlled_git(codex_repository, "remote") == ""


def test_snapshot_only_refresh_preserves_decision_authority_and_updates_provenance(
    tmp_path: Path,
) -> None:
    class SnapshotOnlyRunner(FakeGitRunner):
        def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
            if (
                repository.name == "codex"
                and arguments[0] == "rev-parse"
                and not arguments[1].endswith("^{commit}")
            ):
                self.calls.append((repository.name, arguments))
                return ("e" * 40 + "\n").encode()
            if repository.name == "codex" and arguments[0] == "show":
                self.calls.append((repository.name, arguments))
                path = arguments[2].split(":", 1)[1]
                return f"codex:{COMMITS['codex']}:{path}".encode()
            return super().run(repository, arguments)

    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    first = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    attach_decided_candidate(first)
    port_ledger.write_ledger(output, first)

    refreshed = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=SnapshotOnlyRunner(),
        checked_at="2026-07-30T13:00:00Z",
    )

    decision = refreshed["candidates"][0]["decision"]
    assert refreshed["candidates"][0]["id"] == "stable-capability"
    assert decision == first["candidates"][0]["decision"]
    codex_provenance = [
        row for row in refreshed["candidates"][0]["provenance"] if row["host"] == "codex"
    ]
    assert codex_provenance and {row["commit"] for row in codex_provenance} == {"e" * 40}
    assert port_ledger.validate_ledger(refreshed) == []


@pytest.mark.parametrize("change_kind", ["content", "owned-set"])
def test_owned_packet_change_invalidates_only_affected_candidate(
    tmp_path: Path, change_kind: str
) -> None:
    class ChangedOwnedEvidenceRunner(FakeGitRunner):
        def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
            if repository.name == "codex" and arguments[0] == "show" and change_kind == "content":
                self.calls.append((repository.name, arguments))
                return f"changed:{repository.name}:{arguments[2]}".encode()
            if (
                repository.name == "codex"
                and arguments[0] == "ls-tree"
                and change_kind == "owned-set"
            ):
                self.calls.append((repository.name, arguments))
                return b""
            return super().run(repository, arguments)

    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    first = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    attach_two_decided_candidates(first)
    port_ledger.write_ledger(output, first)

    refreshed = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=ChangedOwnedEvidenceRunner(),
        checked_at="2026-07-30T13:00:00Z",
    )
    decisions = {row["id"]: row["decision"] for row in refreshed["candidates"]}
    assert decisions["codex-capability"]["state"] == "pending"
    assert decisions["other-capability"] == first["candidates"][1]["decision"]


def test_required_capability_state_change_invalidates_only_affected_candidate(
    tmp_path: Path,
) -> None:
    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    first = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=FakeGitRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    attach_two_decided_candidates(first)
    first["candidates"][0]["required_host_capabilities"] = ["agy.agent.execution"]
    port_ledger.write_ledger(output, first)

    receipt = promotable_receipt()
    receipt["catalog_digest"] = "e" * 64
    receipt["observed_facts"] = {"unrelated": True}
    same_state = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=receipt,
        runner=FakeGitRunner(),
        checked_at="2026-07-30T13:00:00Z",
    )
    assert [row["decision"] for row in same_state["candidates"]] == [
        row["decision"] for row in first["candidates"]
    ]

    receipt["results"][0]["state"] = "unavailable"
    changed_state = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=receipt,
        runner=FakeGitRunner(),
        checked_at="2026-07-30T14:00:00Z",
    )
    decisions = {row["id"]: row["decision"] for row in changed_state["candidates"]}
    assert decisions["codex-capability"]["state"] == "pending"
    assert decisions["other-capability"] == first["candidates"][1]["decision"]


def test_issue_16_governance_outputs_are_not_source_candidate_inputs(tmp_path: Path) -> None:
    class GovernanceOutputRunner(FakeGitRunner):
        def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
            if repository.name == "antigravity" and arguments[0] == "ls-tree":
                self.calls.append((repository.name, arguments))
                paths = ["plugins/saga/README.md", *port_ledger.ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS]
                return ("\0".join(paths) + "\0").encode()
            return super().run(repository, arguments)

    repositories = make_repositories(tmp_path)
    output = campaign_output(repositories)
    discovered = port_ledger.discover(
        campaign_id="2026-07-30-fixture",
        output=output,
        repositories=repositories,
        planning_snapshots=COMMITS,
        claude_seed="1" * 40,
        host_receipt=promotable_receipt(),
        runner=GovernanceOutputRunner(),
        checked_at="2026-07-30T12:00:00Z",
    )
    paths = {packet["path"] for packet in discovered["campaign"]["edit_packets"]}
    assert len(port_ledger.ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS) == 7
    assert paths.isdisjoint(port_ledger.ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS)
    assert all(
        packet_id not in discovered["campaign"]["unmatched_edit_packet_ids"]
        for packet_id in {
            port_ledger._packet_id("antigravity", "tree", path, "tree")
            for path in port_ledger.ANTIGRAVITY_GOVERNANCE_OUTPUT_PATHS
        }
    )


def test_packet_identity_is_stable_across_content_refresh() -> None:
    first = port_ledger._packet_id("claude", "history", "plugins/saga/README.md", "modified")
    second = port_ledger._packet_id("claude", "history", "plugins/saga/README.md", "modified")
    assert first == second


def test_strict_loader_rejects_duplicate_top_level_key_with_location(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "duplicate-top-level.yaml"
    ledger_path.write_text(
        "schema: antigravity.semantic-port-ledger.v1\nschema: antigravity.semantic-port-ledger.v1\n"
    )
    with pytest.raises(
        port_ledger.LedgerError,
        match=r"duplicate YAML key 'schema' at line 2, column 1",
    ):
        port_ledger.load_ledger(ledger_path)


def test_strict_loader_rejects_duplicate_nested_key_with_location(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "duplicate-nested.yaml"
    ledger_path.write_text(
        "schema: antigravity.semantic-port-ledger.v1\n"
        "campaign:\n"
        "  id: 2026-07-30-fixture\n"
        "  id: 2026-07-30-fixture\n"
    )
    with pytest.raises(
        port_ledger.LedgerError,
        match=r"duplicate YAML key 'id' at line 4, column 3",
    ):
        port_ledger.load_ledger(ledger_path)


def test_duplicate_candidate_decision_key_preserves_ledger_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger_path = tmp_path / "ledger.yaml"
    mapping_path = tmp_path / "decisions.yaml"
    port_ledger.write_ledger(ledger_path, pending_ledger())
    before = ledger_path.read_bytes()
    mapping_path.write_text(
        "planning-contract:\n"
        "  state: rejected\n"
        "  rationale: First mapping.\n"
        "  revisit_trigger: Revisit later.\n"
        "planning-contract:\n"
        "  state: rejected\n"
        "  rationale: Duplicate mapping.\n"
        "  revisit_trigger: Revisit later.\n"
    )

    result = port_ledger.main(
        [
            "record-decisions",
            str(ledger_path),
            str(mapping_path),
            "--operator",
            "Jeff",
            "--decided-at",
            "2026-07-30T13:00:00Z",
        ]
    )

    assert result == 1
    assert "duplicate YAML key 'planning-contract' at line 5, column 1" in capsys.readouterr().err
    assert ledger_path.read_bytes() == before
