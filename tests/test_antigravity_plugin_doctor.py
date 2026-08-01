from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from scripts import validate_plugins

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = cast(
    dict[str, Any],
    json.loads(
        (REPO_ROOT / "plugins/fleet-core/references/antigravity-capability-probes.yaml").read_text()
    ),
)


def write_plugin(root: Path, name: str = "demo", manifest: dict | None = None) -> Path:
    plugin_dir = root / "plugins" / name
    plugin_dir.mkdir(parents=True)
    payload = manifest or {"name": name, "version": "1.0.0", "description": "Demo plugin"}
    (plugin_dir / "plugin.json").write_text(json.dumps(payload))
    return plugin_dir


def contract_repo(root: Path, active_text: str = "# Clean\n") -> dict[str, Any]:
    write_plugin(
        root,
        "fleet-core",
        {
            "name": "fleet-core",
            "version": "1.0.0",
            "description": "Fleet core",
        },
    )
    active = root / "plugins/saga/skills/demo/SKILL.md"
    active.parent.mkdir(parents=True)
    active.write_text(active_text)
    selector = cast(
        dict[str, Any],
        json.loads(
            (
                REPO_ROOT / "plugins/fleet-core/references/antigravity-host-contract-surfaces.json"
            ).read_text()
        ),
    )
    for relative in selector["exact_paths"]:
        exact = root / relative
        exact.parent.mkdir(parents=True, exist_ok=True)
        exact.write_text("# Clean\n")
    (root / "docs").mkdir()
    (root / "tests").mkdir()
    return selector


def receipt_with_states(**states: str) -> dict[str, Any]:
    capabilities, probes, _host_lint = validate_plugins._contract_modules()
    receipt = cast(dict[str, Any], probes.probe_catalog(CATALOG))
    rows = {row["id"]: row for row in CATALOG["capabilities"]}
    for result in receipt["results"]:
        state = states.get(result["id"], result["state"])
        result["state"] = state
        result["evidence"] = (
            list(rows[result["id"]]["expected_evidence"]) if state in {"passed", "failed"} else []
        )
        fact_id = capabilities.CAPABILITY_FACT_IDS.get(result["id"])
        if fact_id is None:
            continue
        requested: Any
        observed: Any
        if fact_id == "model-selection":
            requested, observed = "gemini-3.1-pro", "gemini-3.1-pro"
            if state == "failed":
                observed = "gpt-5"
        elif fact_id == "effort-selection":
            requested, observed = "high", "high"
            if state == "failed":
                observed = "low"
        else:
            requested, observed = True, state == "passed"
        if state in {"unknown", "unavailable"}:
            observed = None
        receipt["requested_facts"][fact_id] = requested
        receipt["observed_facts"][fact_id] = observed
    if states.get("agy.cli.version") == "passed":
        receipt["agy_cli_version"] = "9.1.0"
    if states.get("antigravity.host.version") == "passed":
        receipt["antigravity_host_version"] = "10.2.0"
    if states.get("antigravity.runtime.roots") == "passed":
        receipt["runtime_roots"] = sorted(capabilities.RUNTIME_ROOT_ROLES)
    assert capabilities.validate_receipt(receipt, CATALOG) == []
    return receipt


class RecordingRunner:
    safe_for_passive_observation = True
    safe_for_stateful_observation = False

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv, *, timeout_s: float):
        self.calls.append(tuple(argv))
        if tuple(argv) == ("agy", "--version"):
            return validate_plugins._contract_modules()[1].CommandResult(0, "agy 9.1.0")
        return validate_plugins._contract_modules()[1].CommandResult(0, "agy [--model] [--effort]")


def test_valid_plugin_reports_surfaces_and_linked_install(tmp_path: Path) -> None:
    plugin_dir = write_plugin(tmp_path)
    (plugin_dir / "skills" / "demo").mkdir(parents=True)
    (plugin_dir / "skills" / "demo" / "SKILL.md").write_text("# Demo\n")
    (plugin_dir / "commands").mkdir()
    (plugin_dir / "commands" / "demo.md").write_text("# Demo\n")
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    (install_dir / "demo").symlink_to(plugin_dir)

    result = validate_plugins.run_doctor(tmp_path, install_dir)

    assert result.ok is True
    assert result.plugins[0].skills == 1
    assert result.plugins[0].commands == 1
    assert result.plugins[0].install_state == "linked"


def test_invalid_manifest_json_fails(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins" / "bad"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text("{bad")

    result = validate_plugins.run_doctor(tmp_path, tmp_path / "install")

    assert result.ok is False
    assert "bad: invalid JSON" in result.errors[0]


def test_quality_evidence_closed_schema_reports_every_malformed_section() -> None:
    evidence = {
        "schema": "wrong",
        "fixtures": [
            None,
            {
                "path": "",
                "owner": "",
                "purpose": "",
                "provenance": "claimed-real",
                "sha256": "bad",
            },
        ],
        "ownership": [
            None,
            {"path": "duplicate", "stable_ids": []},
            {"path": "duplicate", "stable_ids": ["owner", "owner"]},
        ],
        "journals": [
            None,
            {"path": "missing", "status": "wrong", "evidence": None},
            {"path": "missing", "status": "completed", "evidence": []},
        ],
        "tests": [
            None,
            {"stable_id": "owner", "kind": "wrong", "node_id": "bad"},
            {"stable_id": "", "kind": "positive", "node_id": "bad"},
            {"stable_id": "owner", "kind": "negative", "node_id": "x.py::test_wrong"},
            {"stable_id": "positive-only", "kind": "positive", "node_id": "x.py::test_ok"},
        ],
    }
    errors = validate_plugins.validate_repository_quality_evidence(evidence)
    assert "quality evidence schema is invalid" in errors
    assert any("invalid shape" in error for error in errors)
    assert any("unverified fixture provenance" in error for error in errors)
    assert any("missing or duplicated" in error for error in errors)
    assert any("claims completion without evidence" in error for error in errors)
    assert any("lack positive or negative coverage" in error for error in errors)
    assert validate_plugins.validate_repository_quality_evidence(None) == [
        "quality evidence must be an object"
    ]
    missing_lists = {"schema": validate_plugins.QUALITY_EVIDENCE_SCHEMA}
    list_errors = validate_plugins.validate_repository_quality_evidence(missing_lists)
    assert any("fixtures must be a list" in error for error in list_errors)
    assert any("ownership must be a list" in error for error in list_errors)
    assert any("journals must be a list" in error for error in list_errors)
    assert any("tests must be a list" in error for error in list_errors)


def test_repository_path_and_pytest_node_resolution_fail_closed(tmp_path: Path) -> None:
    for value in (None, "", "/absolute", "../escape", "with\\slash"):
        resolved, error = validate_plugins._resolve_repository_file(tmp_path, value, "path")
        assert resolved is None
        assert error
    directory = tmp_path / "directory"
    directory.mkdir()
    assert validate_plugins._resolve_repository_file(tmp_path, "directory", "path")[1]
    source = tmp_path / "test_sample.py"
    source.write_text("def test_present():\n    pass\n", encoding="utf-8")
    assert validate_plugins._pytest_node_exists(tmp_path, "test_sample.py::test_present")
    for node in (
        "test_sample.py",
        "test_sample.py::helper",
        "test_sample.py::test_present::nested",
        "missing.py::test_missing",
        "directory::test_missing",
    ):
        assert not validate_plugins._pytest_node_exists(tmp_path, node)
    source.write_text("def broken(", encoding="utf-8")
    assert not validate_plugins._pytest_node_exists(tmp_path, "test_sample.py::test_present")


def test_manifest_install_and_human_output_edge_states(tmp_path: Path, capsys) -> None:
    plugin = tmp_path / "plugins" / "demo"
    plugin.mkdir(parents=True)
    manifest = plugin / "plugin.json"
    manifest.write_text("[]", encoding="utf-8")
    status = validate_plugins.inspect_plugin(manifest, tmp_path / "install", True)
    assert "JSON object" in status.errors[0]

    manifest.write_text(
        json.dumps({"name": "other", "version": "invalid", "description": ""}),
        encoding="utf-8",
    )
    install = tmp_path / "install"
    install.mkdir()
    (install / "other").mkdir()
    status = validate_plugins.inspect_plugin(manifest, install, True)
    assert any("does not match directory" in error for error in status.errors)
    assert any("not semver-like" in error for error in status.errors)
    assert "repair plugin manifest" in status.next_actions

    copied = validate_plugins.PluginStatus(name="demo", path="plugins/demo")
    (install / "demo").mkdir()
    validate_plugins.inspect_install(plugin, install, copied, False)
    assert copied.install_state == "copied"
    file_plugin = validate_plugins.PluginStatus(name="file", path="plugins/file")
    (install / "file").write_text("not-a-directory", encoding="utf-8")
    validate_plugins.inspect_install(tmp_path / "plugins/file", install, file_plugin, True)
    assert file_plugin.errors

    result = validate_plugins.DoctorResult(
        ok=False,
        plugins=[
            validate_plugins.PluginStatus(
                name="demo",
                path="plugins/demo",
                errors=["broken"],
                warnings=["warn"],
            )
        ],
        warnings=["global: warning"],
        errors=["failure"],
        next_actions=["repair"],
        catalog=validate_plugins.CatalogStatus(
            status="passed", schema="v1", revision=1, capabilities=2
        ),
        capability=validate_plugins.CapabilityStatus(
            status="degraded",
            source="fixture",
            evaluation={
                "blocking_capabilities": ["blocked"],
                "degraded_capabilities": ["degraded"],
                "fallbacks": {"blocked": "fallback"},
            },
        ),
    )
    validate_plugins.print_human(result)
    output = capsys.readouterr().out
    assert "blocking: blocked" in output
    assert "degraded: degraded" in output
    assert "fallback: blocked -> fallback" in output
    assert "error: broken" in output
    assert "warning: global: warning" in output
    assert "next actions:" in output


def test_doctor_cli_renders_json_and_human_results(monkeypatch, capsys) -> None:
    result = validate_plugins.DoctorResult(True, [], [], [], [])
    monkeypatch.setattr(validate_plugins, "run_doctor", lambda *args, **kwargs: result)
    assert validate_plugins.main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert validate_plugins.main([]) == 0
    assert "Antigravity plugin doctor" in capsys.readouterr().out


def test_empty_agent_and_wrong_symlink_warn(tmp_path: Path) -> None:
    plugin_dir = write_plugin(tmp_path)
    (plugin_dir / "agents").mkdir()
    (plugin_dir / "agents" / "demo.md").write_text("")
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    wrong_target = tmp_path / "wrong"
    wrong_target.mkdir()
    (install_dir / "demo").symlink_to(wrong_target)

    result = validate_plugins.run_doctor(tmp_path, install_dir)

    assert result.ok is True
    joined = "\n".join(result.warnings)
    assert "inert empty agent file" in joined
    assert "symlink points at" in joined


def test_supplied_install_dir_avoids_default_home_lookup(tmp_path: Path, monkeypatch) -> None:
    write_plugin(tmp_path)

    def fail_home() -> Path:
        raise AssertionError("default install dir should not be read")

    monkeypatch.setattr(validate_plugins, "default_install_dir", fail_home)

    result = validate_plugins.run_doctor(tmp_path, tmp_path / "install")

    assert result.ok is True
    assert "install directory not found" in "\n".join(result.warnings)


def test_stale_current_spec_text_warns(tmp_path: Path) -> None:
    write_plugin(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PLUGIN_SPEC.md").write_text("Use .claude-plugin for current setup.")

    result = validate_plugins.run_doctor(tmp_path, tmp_path / "install")

    assert any("stale" in warning for warning in result.warnings)


def test_marketplace_wrapper_delegates_to_canonical_doctor(tmp_path: Path) -> None:
    write_plugin(tmp_path)
    install_dir = tmp_path / "install"
    script = Path("marketplace/validator/validate.py").resolve()

    wrapper = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(tmp_path),
            "--install-dir",
            str(install_dir),
            "--json",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    canonical = subprocess.run(
        [
            sys.executable,
            "scripts/validate_plugins.py",
            "--repo-root",
            str(tmp_path),
            "--install-dir",
            str(install_dir),
            "--json",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert wrapper.returncode == canonical.returncode == 0
    assert json.loads(wrapper.stdout) == json.loads(canonical.stdout)


def test_repository_profile_is_deterministic_and_executes_no_runner(
    tmp_path: Path,
) -> None:
    selector = contract_repo(tmp_path)
    runner = RecordingRunner()

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        runner=runner,
        catalog=CATALOG,
        selector=selector,
    )

    assert result.ok is True
    assert runner.calls == []
    assert result.catalog.status == "passed"
    assert result.capability.status == "passed"
    assert result.capability.source == "deterministic"
    assert result.receipt_privacy.promotable is True
    assert result.host_contract.unresolved_count == 0


def test_observe_host_runs_only_registered_passive_vectors(tmp_path: Path) -> None:
    selector = contract_repo(tmp_path)
    runner = RecordingRunner()

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        observe_host=True,
        runner=runner,
        catalog=CATALOG,
        selector=selector,
    )

    assert result.ok is True
    assert runner.calls == [("agy", "--version"), ("agy", "--help")]
    assert result.capability.receipt is not None
    assert result.capability.receipt["agy_cli_version"] == "9.1.0"


def test_required_profile_failure_blocks_with_exact_capability(tmp_path: Path) -> None:
    selector = contract_repo(tmp_path)
    states = {row["id"]: "passed" for row in CATALOG["capabilities"]}
    states["agy.agent.execution"] = "failed"
    receipt = receipt_with_states(**states)

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        capability_profile="live-canary",
        catalog=CATALOG,
        receipt=receipt,
        selector=selector,
    )

    assert result.ok is False
    assert result.capability.status == "blocked"
    assert result.capability.evaluation is not None
    assert result.capability.evaluation["blocking_capabilities"] == ["agy.agent.execution"]


def test_optional_proven_fallback_reports_degraded_without_failure(
    tmp_path: Path,
) -> None:
    selector = contract_repo(tmp_path)
    states = {
        row["id"]: "passed" for row in CATALOG["capabilities"] if "saga.work" in row["required_for"]
    }
    states["agy.agent.execution"] = "unavailable"
    states["agy.sequential.isolation"] = "passed"
    receipt = receipt_with_states(**states)

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        capability_profile="saga.work",
        catalog=CATALOG,
        receipt=receipt,
        selector=selector,
    )

    assert result.ok is True
    assert result.capability.status == "degraded"
    assert result.capability.evaluation is not None
    assert result.capability.evaluation["fallbacks"] == {
        "agy.agent.execution": "agy.sequential.isolation"
    }


def test_unresolved_lint_finding_fails_with_structured_remediation(tmp_path: Path, capsys) -> None:
    selector = contract_repo(tmp_path)
    selected_path = "plugins/saga/skills/work/SKILL.md"
    (tmp_path / selected_path).write_text("Call AskUserQuestion now.\n")

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        catalog=CATALOG,
        selector=selector,
    )

    assert result.ok is False
    assert result.host_contract.status == "failed"
    assert result.host_contract.unresolved_count == 1
    finding = result.host_contract.findings[0]
    assert finding["path_sha256"] == (
        "db5f9b3661ae7b73710ee1fb07f6040fd83af119a8bcecb804b6060c655bb6e7"
    )
    assert finding["rule"] == "AGHC002"
    assert finding["line"] == 1
    assert finding["remediation"] == "use-session-blocking-question"
    validate_plugins.print_human(result)
    human = capsys.readouterr().out
    assert (
        "path-sha256=db5f9b3661ae7b73710ee1fb07f6040fd83af119a8bcecb804b6060c655bb6e7 "
        "line=1 AGHC002 remediation=use-session-blocking-question"
    ) in human
    encoded = json.dumps(validate_plugins.asdict(result))
    assert '"rule": "AGHC002"' in encoded


def test_host_contract_read_error_does_not_echo_private_path(tmp_path: Path, capsys) -> None:
    selector = contract_repo(tmp_path)
    private_path = tmp_path / selector["exact_paths"][0]
    private_path.write_bytes(b"\xff")

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        catalog=CATALOG,
        selector=selector,
    )
    rendered = json.dumps(validate_plugins.asdict(result))

    assert result.ok is False
    assert result.host_contract.status == "failed"
    assert private_path.as_posix() not in rendered
    validate_plugins.print_human(result)
    human = capsys.readouterr().out
    assert private_path.as_posix() not in human


@pytest.mark.parametrize("method", ["glob", "rglob"])
def test_host_contract_enumeration_error_does_not_echo_private_path(
    tmp_path: Path, capsys, monkeypatch, method: str
) -> None:
    selector = contract_repo(tmp_path)
    private_path = f"/Users/alice/ghp_examplecredential-{method}"
    if method == "glob":
        selected_path = tmp_path / selector["exact_paths"][0]
        original_is_file = Path.is_file

        def fail_exact_path(path: Path):
            if path == selected_path:
                raise PermissionError(13, "permission denied", private_path)
            return original_is_file(path)

        monkeypatch.setattr(Path, "is_file", fail_exact_path)
    else:
        original_enumeration = Path.rglob

        def fail_enumeration(path: Path, pattern: str):
            if path == tmp_path / "docs":
                raise PermissionError(13, "permission denied", private_path)
            return original_enumeration(path, pattern)

        monkeypatch.setattr(Path, "rglob", fail_enumeration)
    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        catalog=CATALOG,
        selector=selector,
    )
    rendered = json.dumps(validate_plugins.asdict(result))

    assert result.ok is False
    assert result.host_contract.status == "failed"
    assert private_path not in rendered
    assert "ghp_examplecredential" not in rendered
    validate_plugins.print_human(result)
    human = capsys.readouterr().out
    assert private_path not in human
    assert "ghp_examplecredential" not in human


def test_unsafe_supplied_receipt_fails_without_echoing_private_value(
    tmp_path: Path,
) -> None:
    selector = contract_repo(tmp_path)
    unsafe = receipt_with_states()
    private_value = "/Users/alice/.gemini/private"
    unsafe["agy_cli_version"] = private_value

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        catalog=CATALOG,
        receipt=unsafe,
        selector=selector,
    )
    rendered = json.dumps(validate_plugins.asdict(result))

    assert result.ok is False
    assert result.receipt_privacy.status == "failed"
    assert result.capability.receipt is None
    assert private_value not in rendered


def test_unknown_profile_is_rejected_instead_of_passing_vacuously(
    tmp_path: Path,
) -> None:
    selector = contract_repo(tmp_path)

    result = validate_plugins.run_doctor(
        tmp_path,
        tmp_path / "install",
        capability_profile="saga.unknown",
        catalog=deepcopy(CATALOG),
        selector=selector,
    )

    assert result.ok is False
    assert result.capability.errors == ["unknown capability profile"]
