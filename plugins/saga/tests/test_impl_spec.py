"""Deterministic profile and folder-contract tests for `/impl-spec`."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import impl_spec as M  # noqa: E402, N812

FIXTURES = Path(__file__).parent / "fixtures" / "impl-spec"
VALID = FIXTURES / "valid-profile"


def test_valid_profile_discovers_contract_waves_and_complete_set() -> None:
    profile, contract = M.discover(VALID, "profile.json")
    validation = M.validate_spec_set(VALID, profile, contract)

    assert profile.profile_id == "reference-service"
    assert [folder.folder for folder in contract.folders] == [
        "architecture",
        "api",
        "operations",
    ]
    assert contract.waves == (("architecture",), ("api",), ("operations",))
    assert validation.complete is True
    assert validation.missing == ()


def test_complete_spec_set_manifest_is_stable_and_binds_every_required_file() -> None:
    profile, contract = M.discover(VALID, "profile.json")
    first = M.build_spec_set_manifest(VALID, profile, contract)
    second = M.build_spec_set_manifest(VALID, profile, contract)

    assert first == second
    assert first["schema"] == M.SPEC_SET_SCHEMA
    assert len(first["spec_set_id"]) == 64
    assert {row["reference"] for row in first["files"]} == {
        "docs/specs/reference-service/README.md",
        "docs/specs/reference-service/architecture/overview.md",
        "docs/specs/reference-service/architecture/security.md",
        "docs/specs/reference-service/api/openapi.yaml",
        "docs/specs/reference-service/api/endpoint-specifications.md",
        "docs/specs/reference-service/operations/runbook.md",
    }
    assert all(len(row["sha256"]) == 64 for row in first["files"])


def test_missing_profile_contract_stops_as_unavailable() -> None:
    missing = FIXTURES / "missing-folder-contract"
    with pytest.raises(M.ImplSpecError, match="unavailable"):
        M.discover(missing, "profile.json")


def test_unparseable_contract_is_rejected_without_inventing_folders(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "profile.json").write_text(
        json.dumps(
            {
                "schema": M.PROFILE_SCHEMA,
                "profile_id": "bad-readme",
                "spec_root": "docs/specs/service",
                "folder_contract_readme": "docs/specs/service/README.md",
            }
        )
    )
    readme = root / "docs/specs/service/README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# Service\n\nNo folder contract is declared.\n")

    with pytest.raises(M.ImplSpecError, match="exactly one parseable"):
        M.discover(root, "profile.json")


def test_contract_without_dependency_column_defaults_every_folder_to_wave_one() -> None:
    folders = M.parse_folder_contract(
        """
| Folder | Required files | Completeness |
|---|---|---|
| api | openapi.yaml | Contract validates. |
| operations | runbook.md | Recovery is explicit. |
"""
    )
    assert M.dependency_waves(folders) == (("api", "operations"),)


def test_duplicate_required_files_are_rejected() -> None:
    with pytest.raises(M.ImplSpecError, match="duplicate required files"):
        M.parse_folder_contract(
            """
| Folder | Required files | Completeness |
|---|---|---|
| api | openapi.yaml, openapi.yaml | Contract validates. |
"""
        )


@pytest.mark.parametrize(
    "table",
    [
        """
| Folder | Required files | Completeness | Depends on |
|---|---|---|---|
| api | openapi.yaml | Complete. | missing |
""",
        """
| Folder | Required files | Completeness | Depends on |
|---|---|---|---|
| api | openapi.yaml | Complete. | operations |
| operations | runbook.md | Complete. | api |
""",
    ],
)
def test_unknown_and_cyclic_dependencies_fail_closed(table: str) -> None:
    if "missing" in table:
        with pytest.raises(M.ImplSpecError, match="unknown or self"):
            M.parse_folder_contract(table)
    else:
        folders = M.parse_folder_contract(table)
        with pytest.raises(M.ImplSpecError, match="cycle"):
            M.dependency_waves(folders)


def test_incomplete_spec_set_cannot_emit_manifest(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    shutil.copytree(VALID, root)
    missing = root / "docs/specs/reference-service/api/openapi.yaml"
    missing.unlink()
    profile, contract = M.discover(root, "profile.json")

    validation = M.validate_spec_set(root, profile, contract)
    assert validation.complete is False
    assert validation.missing == ("docs/specs/reference-service/api/openapi.yaml",)
    with pytest.raises(M.ImplSpecError, match="incomplete"):
        M.build_spec_set_manifest(root, profile, contract)


@pytest.mark.parametrize(
    "field,value",
    [
        ("spec_root", "../outside"),
        ("folder_contract_readme", "/tmp/README.md"),
        ("folder_contract_readme", "other/README.md"),
    ],
)
def test_profile_paths_are_repository_relative_and_contained(field: str, value: str) -> None:
    profile = {
        "schema": M.PROFILE_SCHEMA,
        "profile_id": "unsafe",
        "spec_root": "docs/specs/service",
        "folder_contract_readme": "docs/specs/service/README.md",
    }
    profile[field] = value
    with pytest.raises(M.ImplSpecError):
        M.Profile.from_dict(profile)


def test_symlinked_profile_path_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "profile.json").write_text("{}")
    root = tmp_path / "repo"
    root.mkdir()
    (root / "profile.json").symlink_to(outside / "profile.json")
    with pytest.raises(M.ImplSpecError, match="symlink"):
        M.load_profile(root, "profile.json")


def test_profile_rejects_noncanonical_spec_root() -> None:
    with pytest.raises(M.ImplSpecError, match="canonical docs/specs"):
        M.Profile.from_dict(
            {
                "schema": M.PROFILE_SCHEMA,
                "profile_id": "staged",
                "spec_root": "specs/service",
                "folder_contract_readme": "specs/service/README.md",
            }
        )


def test_impl_spec_contract_has_no_execution_or_remote_mutation_surface() -> None:
    source = (ROOT / "scripts/impl_spec.py").read_text(encoding="utf-8")
    for forbidden in ("subprocess", "requests", "urlopen", "git push", "gh pr", "invoke_subagent"):
        assert forbidden not in source


def test_six_stage_skill_preserves_independence_promotion_and_lifecycle_boundaries() -> None:
    skill = (ROOT / "skills/impl-spec/SKILL.md").read_text(encoding="utf-8")
    stages = (ROOT / "skills/impl-spec/references/impl-spec-stages.md").read_text(
        encoding="utf-8"
    )
    authoring = (ROOT / "skills/impl-spec/references/authoring-subagent-prompt.md").read_text(
        encoding="utf-8"
    )
    plan = (ROOT / "skills/plan/SKILL.md").read_text(encoding="utf-8")
    dispatch = (ROOT / "skills/loop/references/dispatch-table.md").read_text(encoding="utf-8")

    stage_names = ("Research", "Author", "Assemble", "Verify", "Review", "Probe+Remediate")
    for number, stage in enumerate(stage_names, start=1):
        assert f"Stage {number} — {stage}" in stages
    for marker in (
        "agy.agent.execution=passed",
        "agy.sequential.isolation=passed",
        "same-context roleplay",
        "capped at three rounds",
        "never writes a stored Saga lifecycle phase",
        "saga.impl-spec-set.v1",
        "artifact_promotion.py",
        ".gemini/saga/impl-spec/<profile-id>/workspace/",
    ):
        assert marker in skill
    assert "Never write directly to canonical `docs/specs/`" in authoring
    assert "saga.impl-spec-set.v1" in plan
    assert "later `/doc-review` readiness gate" in " ".join(plan.split())
    assert "/impl-spec" in dispatch
    assert "/product-review" not in dispatch
