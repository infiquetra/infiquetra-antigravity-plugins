from __future__ import annotations

import copy
import hashlib
import shutil
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

    assert refreshed["candidates"][0]["decision"] == first["candidates"][0]["decision"]
    assert port_ledger.validate_ledger(refreshed) == []


@pytest.mark.parametrize("change_kind", ["content", "snapshot"])
def test_changed_refresh_evidence_invalidates_decision_authority(
    tmp_path: Path, change_kind: str
) -> None:
    class ChangedEvidenceRunner(FakeGitRunner):
        def run(self, repository: Path, arguments: tuple[str, ...]) -> bytes:
            if change_kind == "content" and arguments[0] == "show":
                self.calls.append((repository.name, arguments))
                return f"changed:{repository.name}:{arguments[2]}".encode()
            if (
                change_kind == "snapshot"
                and repository.name == "codex"
                and arguments[0] == "rev-parse"
            ):
                self.calls.append((repository.name, arguments))
                return ("e" * 40 + "\n").encode()
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
        runner=ChangedEvidenceRunner(),
        checked_at="2026-07-30T13:00:00Z",
    )

    decision = refreshed["candidates"][0]["decision"]
    assert refreshed["candidates"][0]["id"] == "stable-capability"
    assert decision["state"] == "pending"
    assert decision["operator"] is None
    assert decision["decided_at"] is None
    errors = port_ledger.validate_ledger(refreshed)
    assert len(errors) == 1
    assert errors[0].startswith("decision gate: pending candidates")


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
