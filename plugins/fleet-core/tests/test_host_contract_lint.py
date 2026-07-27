from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

FLEET_CORE = Path(__file__).resolve().parent.parent
REPO_ROOT = FLEET_CORE.parent.parent
os.environ["FLEET_COMMONS_ROOT"] = str(FLEET_CORE)
sys.path.insert(0, str(FLEET_CORE / "scripts"))

import fleet_commons_shim  # noqa: E402

LINT = fleet_commons_shim.load("host_contract_lint")
CAPS = fleet_commons_shim.load("antigravity_capabilities")
FIXTURES = Path(__file__).parent / "fixtures" / "host-contract"
SELECTOR_PATH = FLEET_CORE / "references" / "antigravity-host-contract-surfaces.json"


def _selector():
    return LINT.load_selector(SELECTOR_PATH, REPO_ROOT)


def _known_capabilities() -> set[str]:
    catalog = CAPS.load_catalog(FLEET_CORE / "references" / "antigravity-capability-probes.yaml")
    return {row["id"] for row in catalog["capabilities"]}


def test_selector_is_closed_and_declared_paths_exist() -> None:
    selector = _selector()
    assert LINT.validate_selector(selector, REPO_ROOT) == []
    assert LINT.selector_digest(selector) == LINT.selector_digest(copy.deepcopy(selector))
    paths = LINT.selected_active_paths(REPO_ROOT, selector)
    assert REPO_ROOT / "plugins/saga/skills/work/SKILL.md" in paths
    assert REPO_ROOT / ".agents/skills/port-claude-plugins/SKILL.md" in paths


def test_named_active_rules_emit_exact_ids_and_unresolved_findings() -> None:
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        (FIXTURES / "active-all.md").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert [finding["rule"] for finding in findings] == [
        "AGHC001",
        "AGHC002",
        "AGHC003",
        "AGHC004",
        "AGHC005",
        "AGHC006",
    ]
    assert all(finding["classification"] == "active" for finding in findings)
    assert all(finding["unresolved"] for finding in findings)
    assert all("excerpt" not in finding for finding in findings)


def test_only_reviewed_historical_lines_are_allowlisted() -> None:
    synthetic = LINT.scan_text(
        "docs/history.md",
        (FIXTURES / "historical-all.md").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert synthetic
    assert all(finding["classification"] == "active" for finding in synthetic)
    assert all(finding["unresolved"] for finding in synthetic)

    receipt = LINT.scan_repository(
        REPO_ROOT,
        _selector(),
        known_capabilities=_known_capabilities(),
    )
    reviewed = [
        finding
        for finding in receipt["findings"]
        if finding["classification"] == "historical" and finding["reason"] == "annotated-historical"
    ]
    assert len(reviewed) == len(LINT._HISTORICAL_LINE_ALLOWLIST)
    assert not any(finding["unresolved"] for finding in reviewed)


def test_repository_scan_classifies_comparison_matches(tmp_path: Path) -> None:
    for relative in LINT.REQUIRED_EXACT_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Clean\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/history.md").write_text('Run `Workflow("source")`.\n')
    (tmp_path / "tests").mkdir()

    receipt = LINT.scan_repository(tmp_path, _selector())

    assert receipt["unresolved_count"] == 0
    assert len(receipt["findings"]) == 1
    assert receipt["findings"][0]["classification"] == "historical"
    assert receipt["findings"][0]["reason"] == "comparison-corpus"


def test_markdown_quote_is_active_without_lineage_annotation() -> None:
    findings = LINT.scan_text(
        "plugins/saga/references/example.md",
        '> Run `Workflow("source")` now.',
        known_capabilities=_known_capabilities(),
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "AGHC003"
    assert findings[0]["unresolved"] is True


def test_unallowlisted_foreign_runtime_annotations_fail_closed() -> None:
    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        (FIXTURES / "executable-claude-path.py").read_text(),
        known_capabilities=_known_capabilities(),
    )
    assert len(findings) == 2
    assert all(finding["classification"] == "active" for finding in findings)
    assert all(finding["unresolved"] for finding in findings)


def test_exact_reviewed_foreign_runtime_reads_are_allowlisted() -> None:
    source = (
        REPO_ROOT / "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py"
    ).read_text()
    findings = LINT.scan_text(
        "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py",
        source,
        known_capabilities=_known_capabilities(),
    )
    foreign = [finding for finding in findings if finding["rule"] == "AGHC001"]

    assert len(foreign) == 2
    assert all(finding["classification"] == "foreign-runtime-input" for finding in foreign)
    assert not any(finding["unresolved"] for finding in foreign)


def test_reviewed_foreign_runtime_file_digest_rejects_later_mutation() -> None:
    source = (
        REPO_ROOT / "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py"
    ).read_text()
    source += "\nshutil.rmtree(bundle_root)\n"

    findings = LINT.scan_text(
        "plugins/fleet-core/scripts/fleet_commons/delegation_audit.py",
        source,
        known_capabilities=_known_capabilities(),
    )
    foreign = [finding for finding in findings if finding["rule"] == "AGHC001"]

    assert len(foreign) == 2
    assert all(finding["classification"] == "active" for finding in foreign)
    assert all(finding["unresolved"] for finding in foreign)


def test_reviewed_historical_file_digest_rejects_changed_context() -> None:
    path = "plugins/saga/references/operator-choice.md"
    source = (REPO_ROOT / path).read_text()
    source += '\nIMPORTANT: Invoke `Workflow("source")` now.\n'

    findings = LINT.scan_text(
        path,
        source,
        known_capabilities=_known_capabilities(),
    )

    assert findings
    assert all(finding["classification"] == "active" for finding in findings)
    assert all(finding["unresolved"] for finding in findings)


@pytest.mark.parametrize(
    "mutation",
    [
        "target.write_text('state')",
        "shutil.copy(target, destination)",
        "shutil.move(target, destination)",
        "os.remove(target)",
        "shutil.rmtree(target)",
        "target.chmod(0o600)",
        "open(target, 'w')",
        "target.open(mode='a')",
    ],
)
def test_foreign_runtime_annotation_cannot_hide_later_python_mutation(
    mutation: str,
) -> None:
    text = (
        '# antigravity-host-contract: {"class":"foreign-runtime-input",'
        '"rule":"AGHC001","reason":"read migration input only",'
        '"revisit":"remove after migration window","access":"read-only"}\n'
        'target = repo_root / ".claude" / "saga" / "state.json"\n'
        f"{mutation}\n"
    )

    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert len(findings) == 1
    assert findings[0]["classification"] == "active"
    assert findings[0]["reason"] == "annotation-conflicts-with-executable-write"
    assert findings[0]["unresolved"] is True


def test_foreign_runtime_annotation_tracks_assignment_aliases() -> None:
    text = (
        '# antigravity-host-contract: {"class":"foreign-runtime-input",'
        '"rule":"AGHC001","reason":"read migration input only",'
        '"revisit":"remove after migration window","access":"read-only"}\n'
        'source = repo_root / ".claude" / "saga" / "state.json"\n'
        "alias = source\n"
        "alias.unlink()\n"
    )

    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert findings[0]["unresolved"] is True
    assert findings[0]["reason"] == "annotation-conflicts-with-executable-write"


@pytest.mark.parametrize(
    "use",
    [
        "mutate_foreign_path(target)",
        "callback(target)",
        "os.open(target, os.O_WRONLY)",
        "holder.path = target\nholder.path.unlink()",
        "container = {}\ncontainer['path'] = target\ncontainer['path'].unlink()",
        "alias = identity(target)\nalias.unlink()",
    ],
)
def test_foreign_runtime_annotation_fails_closed_for_unproven_flows(
    use: str,
) -> None:
    text = (
        '# antigravity-host-contract: {"class":"foreign-runtime-input",'
        '"rule":"AGHC001","reason":"read migration input only",'
        '"revisit":"remove after migration window","access":"read-only"}\n'
        'target = repo_root / ".claude" / "saga" / "state.json"\n'
        f"{use}\n"
    )

    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert findings[0]["classification"] == "active"
    assert findings[0]["reason"] == "annotation-conflicts-with-executable-write"
    assert findings[0]["unresolved"] is True


@pytest.mark.parametrize(
    "use",
    [
        "target.read_text()",
        "target.read_bytes()",
        "target.exists()",
        "open(target, 'r').read()",
    ],
)
def test_unallowlisted_read_operations_remain_unresolved(use: str) -> None:
    text = (
        '# antigravity-host-contract: {"class":"foreign-runtime-input",'
        '"rule":"AGHC001","reason":"read migration input only",'
        '"revisit":"remove after migration window","access":"read-only"}\n'
        'target = repo_root / ".claude" / "saga" / "state.json"\n'
        f"{use}\n"
    )

    findings = LINT.scan_text(
        "plugins/saga/hooks/example.py",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert findings[0]["classification"] == "active"
    assert findings[0]["unresolved"] is True


def test_constructed_claude_path_is_an_active_violation() -> None:
    findings = LINT.scan_text(
        "plugins/saga/scripts/example.py",
        'ledger = repo_root / ".claude" / "saga" / "ledger"',
        known_capabilities=_known_capabilities(),
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "AGHC001"
    assert findings[0]["unresolved"] is True


@pytest.mark.parametrize(("state", "unresolved"), [("passed", False), ("unknown", True)])
def test_capability_gate_requires_passing_evidence(state: str, unresolved: bool) -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"capability-gated",'
        '"rule":"AGHC006","reason":"runtime isolation is required",'
        '"revisit":"remove when host contract changes",'
        '"capability":"agy.sandbox.isolation"} -->\n'
        "The host guarantees isolated worktree execution."
    )
    findings = LINT.scan_text(
        "plugins/saga/skills/work/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
        capability_states={"agy.sandbox.isolation": state},
    )
    assert findings[0]["classification"] == "capability-gated"
    assert findings[0]["unresolved"] is unresolved


def test_capability_annotation_must_use_the_rule_specific_capability() -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"capability-gated",'
        '"rule":"AGHC006","reason":"runtime isolation is required",'
        '"revisit":"remove when host contract changes",'
        '"capability":"agy.cli.flags"} -->\n'
        "The host guarantees isolated worktree execution."
    )
    findings = LINT.scan_text(
        "plugins/saga/skills/work/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
        capability_states={"agy.cli.flags": "passed"},
    )
    assert findings[0]["unresolved"] is True
    assert findings[0]["reason"] == "annotation-unknown-capability"


@pytest.mark.parametrize(
    "annotation",
    [
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC999",'
        '"reason":"legacy","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"foreign-runtime-input","rule":"AGHC003",'
        '"reason":"legacy","revisit":"later"} -->',
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"all * workflows","revisit":"later"} -->',
    ],
)
def test_exemption_abuse_fails_closed(annotation: str) -> None:
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        f'{annotation}\nRun `Workflow("source")`.',
        known_capabilities=_known_capabilities(),
    )
    assert findings[0]["classification"] == "active"
    assert findings[0]["unresolved"] is True


def test_historical_annotation_cannot_hide_an_imperative_workflow() -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"legacy workflow example","revisit":"remove with legacy notes"} -->\n'
        'Run `Workflow("source")` now.'
    )

    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert findings[0]["classification"] == "active"
    assert findings[0]["reason"] == "annotation-conflicts-with-executable-write"
    assert findings[0]["unresolved"] is True


@pytest.mark.parametrize(
    "instruction",
    [
        '- Run `Workflow("source")` now.',
        '1. Run `Workflow("source")` now.',
        '> Run `Workflow("source")` now.',
        '- [ ] Run `Workflow("source")` now.',
        '**Run** `Workflow("source")` now.',
        'You must run `Workflow("source")` now.',
        'Please execute `Workflow("source")` now.',
        'Always call `Workflow("source")` now.',
        'IMPORTANT: Run `Workflow("source")` now.',
        'You are required to call `Workflow("source")` now.',
        'Dispatch `Workflow("source")` now.',
        'Open `Workflow("source")` now.',
        'Route through `Workflow("source")` now.',
    ],
)
def test_historical_annotation_rejects_structured_imperatives(
    instruction: str,
) -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"legacy workflow example","revisit":"remove with legacy notes"} -->\n'
        f"{instruction}"
    )

    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
    )

    assert findings[0]["classification"] == "active"
    assert findings[0]["unresolved"] is True


def test_nonadjacent_annotation_is_an_unresolved_finding() -> None:
    text = (
        '<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003",'
        '"reason":"legacy","revisit":"later"} -->\n\n'
        'Run `Workflow("source")`.'
    )
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        text,
        known_capabilities=_known_capabilities(),
    )
    assert {finding["rule"] for finding in findings} == {"AGHC000", "AGHC003"}
    assert all(finding["unresolved"] for finding in findings)


def test_false_positive_controls_do_not_match() -> None:
    text = "\n".join(
        [
            "The hermes-claude-code-router product name is historical.",
            "Schedules belong in the issue tracker.",
            "Networking isolation prose is descriptive.",
            "The test uses a generic workflow object.",
        ]
    )
    assert LINT.scan_text("plugins/saga/references/control.md", text) == []


def test_comparison_corpus_is_classified_not_silently_ignored() -> None:
    findings = LINT.scan_text(
        "tests/source_lineage.md",
        "The source called `AskUserQuestion`.",
        default_classification="historical",
    )
    assert findings[0]["classification"] == "historical"
    assert findings[0]["unresolved"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda selector: selector.update({"unknown": True}),
        lambda selector: selector["exact_paths"].append("/tmp/absolute"),
        lambda selector: selector["exact_paths"].append("../escape"),
        lambda selector: selector["exact_paths"].append("missing-file.md"),
        lambda selector: selector["active_globs"].append("**"),
        lambda selector: selector.update({"digest_inputs": ["schema"]}),
    ],
)
def test_selector_abuse_fails_before_scanning(mutation) -> None:
    selector = _selector()
    mutation(selector)
    assert LINT.validate_selector(selector, REPO_ROOT)


def test_selector_restricts_comparison_roots_to_controlled_corpora() -> None:
    selector = _selector()
    selector["comparison_roots"] = ["plugins/saga"]

    errors = LINT.validate_selector(selector, REPO_ROOT)

    assert any("controlled allowlist" in error for error in errors)


def test_selector_rejects_active_overlap_with_comparison_root() -> None:
    selector = _selector()
    selector["active_globs"].append("docs/**/*.md")

    errors = LINT.validate_selector(selector, REPO_ROOT)

    assert any("active selection overlaps comparison root" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("active_globs", ["plugins/saga/skills/no-match/**/*.md"]),
        ("active_globs", list(LINT.REQUIRED_ACTIVE_GLOBS[:-1])),
        ("exact_paths", list(LINT.REQUIRED_EXACT_PATHS[:-1])),
        ("comparison_roots", ["tests"]),
    ],
)
def test_selector_rejects_narrowed_canonical_policy(
    field: str,
    replacement: list[str],
) -> None:
    selector = _selector()
    selector[field] = replacement

    errors = LINT.validate_selector(selector, REPO_ROOT)

    assert any("canonical surface policy" in error for error in errors)


def test_lint_receipt_is_bound_to_canonical_selector_policy() -> None:
    selector = _selector()
    selector["active_globs"] = ["plugins/saga/skills/no-match/**/*.md"]

    with pytest.raises(LINT.HostContractError, match="canonical surface policy"):
        LINT.build_lint_receipt(selector, [])

    receipt = {
        "schema": LINT.LINT_RECEIPT_SCHEMA,
        "selector_digest": LINT.selector_digest(selector),
        "findings": [],
        "unresolved_count": 0,
    }
    errors = LINT.validate_lint_receipt(receipt)
    assert any("does not match canonical policy" in error for error in errors)


def test_selector_rejects_symlinked_exact_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("outside")
    linked = tmp_path / "linked.md"
    linked.symlink_to(outside)
    (tmp_path / "docs").mkdir()
    selector = {
        "schema": LINT.SELECTOR_SCHEMA,
        "active_globs": ["*.md"],
        "exact_paths": ["linked.md"],
        "comparison_roots": ["docs"],
        "digest_inputs": list(LINT._SELECTOR_DIGEST_INPUTS),
    }
    errors = LINT.validate_selector(selector, tmp_path)
    assert any("symlinks are not allowed" in error for error in errors)


def test_selector_rejects_symlinked_comparison_root(tmp_path: Path) -> None:
    active = tmp_path / "active.md"
    active.write_text("active")
    outside = tmp_path.parent / f"{tmp_path.name}-comparison"
    outside.mkdir()
    (tmp_path / "tests").symlink_to(outside, target_is_directory=True)
    selector = {
        "schema": LINT.SELECTOR_SCHEMA,
        "active_globs": ["*.md"],
        "exact_paths": ["active.md"],
        "comparison_roots": ["tests"],
        "digest_inputs": list(LINT._SELECTOR_DIGEST_INPUTS),
    }

    errors = LINT.validate_selector(selector, tmp_path)

    assert any("comparison_roots: symlinks are not allowed" in error for error in errors)


def test_lint_receipt_is_strict_excerpt_free_and_digest_bound() -> None:
    selector = _selector()
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        'Run `Workflow("source")`.',
        known_capabilities=_known_capabilities(),
    )
    receipt = LINT.build_lint_receipt(selector, findings)
    assert receipt["schema"] == LINT.LINT_RECEIPT_SCHEMA
    assert receipt["unresolved_count"] == 1
    assert LINT.validate_lint_receipt(receipt) == []

    unsafe = copy.deepcopy(receipt)
    unsafe["findings"][0]["path"] = "/Users/alice/private.md"
    unsafe["findings"][0]["excerpt"] = "private prompt"
    errors = LINT.validate_lint_receipt(unsafe)
    assert errors
    assert "/Users/alice" not in json.dumps(errors)
    assert "private prompt" not in json.dumps(errors)


@pytest.mark.parametrize(
    "private_path",
    [
        "plugins/saga/skills/jeffs-macbook-pro.local.md",
        "plugins/saga/skills/ghp_examplecredential.md",
        "plugins/saga/skills/abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnop.md",
    ],
)
def test_lint_receipt_rejects_raw_paths_without_echo(
    private_path: str,
) -> None:
    selector = _selector()
    findings = LINT.scan_text(
        "plugins/saga/skills/example/SKILL.md",
        'Run `Workflow("source")`.',
        known_capabilities=_known_capabilities(),
    )
    receipt = LINT.build_lint_receipt(selector, findings)
    assert "path" not in receipt["findings"][0]
    assert "path_sha256" in receipt["findings"][0]
    receipt["findings"][0]["path"] = private_path

    rendered = json.dumps(LINT.validate_lint_receipt(receipt))

    assert rendered != "[]"
    assert private_path not in rendered


def test_selector_loader_does_not_echo_private_paths(tmp_path: Path) -> None:
    private_path = tmp_path / "ghp_examplecredential.local" / "selector.json"

    with pytest.raises(LINT.HostContractError) as captured:
        LINT.load_selector(private_path, tmp_path)

    assert "ghp_examplecredential" not in str(captured.value)
    assert str(tmp_path) not in str(captured.value)


def test_selector_enumeration_error_does_not_echo_private_path(tmp_path: Path, monkeypatch) -> None:
    private_path = "/Users/alice/private-active-glob"
    selector = _selector()

    def fail_glob(_path: Path, _pattern: str):
        raise PermissionError(13, "permission denied", private_path)

    monkeypatch.setattr(Path, "glob", fail_glob)

    rendered = json.dumps(LINT.validate_selector(selector, tmp_path))

    assert private_path not in rendered
    assert "alice" not in rendered


@pytest.mark.parametrize("method", ["glob", "rglob"])
def test_repository_enumeration_error_does_not_echo_private_path(
    tmp_path: Path, monkeypatch, method: str
) -> None:
    private_path = f"/Users/alice/private-{method}-path"
    selector = _selector()

    def fail_enumeration(_path: Path, _pattern: str):
        raise PermissionError(13, "permission denied", private_path)

    monkeypatch.setattr(Path, method, fail_enumeration)

    with pytest.raises(LINT.HostContractError) as captured:
        LINT.scan_repository(tmp_path, selector)

    assert private_path not in str(captured.value)
    assert "alice" not in str(captured.value)


def test_repository_scan_read_error_does_not_echo_private_path(tmp_path: Path) -> None:
    private_path = tmp_path / "plugins/saga/skills/ghp_examplecredential/SKILL.md"
    private_path.parent.mkdir(parents=True)
    private_path.write_bytes(b"\xff")
    selector = _selector()

    with pytest.raises(LINT.HostContractError) as captured:
        LINT.scan_repository(tmp_path, selector)

    assert "ghp_examplecredential" not in str(captured.value)
    assert private_path.as_posix() not in str(captured.value)


def test_repository_scan_os_error_does_not_echo_private_path(tmp_path: Path, monkeypatch) -> None:
    private_path = tmp_path / "plugins/saga/skills/ghp_examplecredential/SKILL.md"
    private_path.parent.mkdir(parents=True)
    private_path.write_text("# Clean\n")
    original_read_bytes = Path.read_bytes

    def fail_private_read(path: Path) -> bytes:
        if path == private_path:
            raise OSError("private read failure")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_private_read)

    with pytest.raises(LINT.HostContractError) as captured:
        LINT.scan_repository(tmp_path, _selector())

    assert "ghp_examplecredential" not in str(captured.value)
    assert private_path.as_posix() not in str(captured.value)
