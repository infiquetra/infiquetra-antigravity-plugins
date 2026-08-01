from __future__ import annotations

import copy
import hashlib
from pathlib import Path

from scripts import validate_plugins as validator


def _evidence():
    root = Path(__file__).resolve().parents[3]
    fixture_path = "plugins/fleet-core/tests/fixtures/orphan-evidence/valid.json"
    return {
        "schema": validator.QUALITY_EVIDENCE_SCHEMA,
        "fixtures": [
            {
                "path": fixture_path,
                "owner": "repository-quality-guards",
                "purpose": "negative contract case",
                "provenance": "synthetic",
                "sha256": hashlib.sha256((root / fixture_path).read_bytes()).hexdigest(),
            }
        ],
        "ownership": [
            {
                "path": fixture_path,
                "stable_ids": ["repository-quality-guards"],
            },
            {"path": "scripts/validate_plugins.py", "stable_ids": ["repository-quality-guards"]},
            {"path": "plugins/fleet-core/tests/test_repository_quality_guards.py", "stable_ids": ["repository-quality-guards"]},
        ],
        "journals": [
            {
                "path": "docs/engineering-journal/DECISIONS.md",
                "status": "completed",
                "evidence": [
                    fixture_path,
                    "plugins/fleet-core/tests/test_repository_quality_guards.py",
                ],
            }
        ],
        "tests": [
            {
                "stable_id": "repository-quality-guards",
                "kind": "positive",
                "node_id": (
                    "plugins/fleet-core/tests/test_repository_quality_guards.py::"
                    "test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps"
                ),
            },
            {
                "stable_id": "repository-quality-guards",
                "kind": "negative",
                "node_id": (
                    "plugins/fleet-core/tests/test_repository_quality_guards.py::"
                    "test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps_"
                    "rejects_negative_cases"
                ),
            },
        ],
    }


def test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps() -> None:
    root = Path(__file__).resolve().parents[3]
    assert validator.validate_repository_quality_evidence(_evidence(), repo_root=root) == []


def test_validate_plugins_rejects_fake_fixture_ownership_and_test_shape_gaps_rejects_negative_cases() -> None:
    cases = []
    fake = _evidence()
    fake["fixtures"][0]["provenance"] = "claimed-live"
    cases.append(fake)
    ownership_gap = _evidence()
    ownership_gap["ownership"][0]["stable_ids"] = []
    cases.append(ownership_gap)
    misleading = _evidence()
    misleading["journals"][0]["evidence"] = []
    cases.append(misleading)
    weak = _evidence()
    weak["tests"] = [copy.deepcopy(weak["tests"][0])]
    cases.append(weak)
    wrong_negative = _evidence()
    wrong_negative["tests"][1]["node_id"] = "tests/test_quality.py::test_negative"
    cases.append(wrong_negative)
    nonexistent = _evidence()
    nonexistent["fixtures"][0]["path"] = "plugins/fleet-core/tests/fixtures/missing.json"
    cases.append(nonexistent)
    escaping = _evidence()
    escaping["fixtures"][0]["path"] = "../outside.json"
    cases.append(escaping)
    unknown = _evidence()
    unknown["ownership"][0]["stable_ids"] = ["not-a-ledger-id"]
    cases.append(unknown)
    fake_digest = _evidence()
    fake_digest["fixtures"][0]["sha256"] = "0" * 64
    cases.append(fake_digest)
    fake_journal = _evidence()
    fake_journal["journals"][0]["evidence"] = ["docs/missing-proof.md"]
    cases.append(fake_journal)
    uncollected = _evidence()
    uncollected["tests"][0]["node_id"] = (
        "plugins/fleet-core/tests/test_repository_quality_guards.py::test_does_not_exist"
    )
    cases.append(uncollected)

    for evidence in cases:
        assert validator.validate_repository_quality_evidence(evidence, repo_root=Path(__file__).resolve().parents[3])
