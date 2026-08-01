"""Coverage guard for the Saga documentation model and manual.

The comprehensive Saga docs are curated, but their coverage should not drift from
the command surface, readiness model, or generated visual inventory. These tests
check structure and references rather than prose style.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAGA_ROOT = REPO_ROOT / "plugins" / "saga"
MODEL_PATH = SAGA_ROOT / "docs" / "model" / "saga-docs-model.yaml"
RENDERER_PATH = SAGA_ROOT / "scripts" / "render_docs_visuals.py"

REQUIRED_CARD_FIELDS = {
    "command",
    "phase",
    "lifecycle_role",
    "source_refs",
    "purpose",
    "use_when",
    "do_not_use_when",
    "inputs",
    "outputs",
    "durable_artifacts",
    "saga_state_behavior",
    "routes_in",
    "routes_out",
    "gates",
    "ownership_boundary",
    "common_mistakes",
    "example_invocation",
}

REQUIRED_ADJACENT_PAIRS = {
    ("/office-hours", "/ideate"),
    ("/ideate", "/brainstorm"),
    ("/brainstorm", "/spec"),
    ("/plan", "/doc-review"),
    ("/qa", "/optimize"),
    ("/strategy", "/founder-review"),
    ("/loop", "/resume"),
}

REQUIRED_SCENARIOS = {
    "vague-idea",
    "chosen-idea",
    "vague-what",
    "requirements-ready-handoff",
    "plan-review",
    "pr-boundary",
    "post-merge-qa",
    "qa-failure",
    "root-cause-investigation",
    "metric-optimization",
    "strategy-refresh",
    "cross-team-handoff",
    "cold-resume",
    "retro-learning",
}

REQUIRED_VISUALS = {
    "lifecycle-atlas",
    "state-readiness-ladder",
    "command-matrix",
    "ownership-boundary-map",
}

MANUAL_PAGES = [
    SAGA_ROOT / "README.md",
    SAGA_ROOT / "docs" / "README.md",
    SAGA_ROOT / "docs" / "commands.md",
    SAGA_ROOT / "docs" / "lifecycle.md",
    SAGA_ROOT / "docs" / "state-readiness.md",
    SAGA_ROOT / "docs" / "scenarios.md",
    SAGA_ROOT / "docs" / "boundaries.md",
    SAGA_ROOT / "docs" / "portability.md",
    SAGA_ROOT / "docs" / "visuals.md",
]


def _load_model() -> dict[str, Any]:
    assert MODEL_PATH.is_file(), f"missing docs model: {MODEL_PATH}"
    data = yaml.safe_load(MODEL_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _load_renderer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("render_docs_visuals", RENDERER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _command_wrapper_names() -> set[str]:
    return {path.stem for path in (SAGA_ROOT / "commands").glob("*.md")}


def _resolve_repo_path(path_text: str) -> Path:
    return (REPO_ROOT / path_text).resolve()


def _portability_errors(model: dict[str, Any]) -> list[str]:
    portability = model.get("portability")
    if not isinstance(portability, dict):
        return ["missing portability contract"]
    errors: list[str] = []
    if portability.get("canonical_authority") != "repository-documents":
        errors.append("canonical authority must be repository-documents")
    if portability.get("projection_authority") != "advisory":
        errors.append("projection authority must be advisory")
    if portability.get("native_backends") != ["inline", "multi-agent-consensus"]:
        errors.append("native backends must be inline and multi-agent-consensus")

    allowed = set(portability.get("allowed_classifications", []))
    if portability.get("packet_mapping_candidate") != "codex-portability-contracts":
        errors.append("packet mappings must bind the canonical ledger candidate")
    mappings = portability.get("packet_mappings")
    if not isinstance(mappings, dict):
        errors.append("packet mappings must be a mapping")
        mappings = {}
    if portability.get("packet_inventory_count") != len(mappings):
        errors.append("packet inventory count must equal exact mapping rows")
    ledger = yaml.safe_load(
        (REPO_ROOT / "docs/ports/2026-07-30-saga-reliability/ledger.yaml").read_text()
    )
    candidate = next(
        row for row in ledger["candidates"] if row["id"] == "codex-portability-contracts"
    )
    packets = {row["id"]: row for row in ledger["campaign"]["edit_packets"]}
    if set(mappings) != set(candidate["edit_packet_ids"]):
        errors.append("packet mappings must exactly cover all candidate-owned packets")
    for packet_id, mapping in mappings.items():
        if not isinstance(mapping, list) or len(mapping) != 4:
            errors.append(f"packet mapping {packet_id}: invalid shape")
            continue
        source_path, source_commit, target, classification = mapping
        packet = packets.get(packet_id)
        if packet is None or source_path != packet["path"] or source_commit != packet["commit"]:
            errors.append(f"packet mapping {packet_id}: stale source provenance")
        if classification not in allowed:
            errors.append(f"packet mapping {packet_id}: unsupported classification")
        if not isinstance(target, str) or not target.startswith("plugins/") or not _resolve_repo_path(target).is_file():
            errors.append(f"packet mapping {packet_id}: target boundary is missing")
    contracts = portability.get("runtime_contracts")
    if not isinstance(contracts, dict) or not contracts:
        errors.append("runtime contracts must be a non-empty mapping")
        return errors

    for contract_id, contract in contracts.items():
        if not isinstance(contract, dict):
            errors.append(f"{contract_id}: contract must be a mapping")
            continue
        lineage = contract.get("source_lineage")
        if not isinstance(lineage, list) or not lineage:
            errors.append(f"{contract_id}: source lineage is required")
        classification = contract.get("classification")
        if classification not in allowed:
            errors.append(f"{contract_id}: unsupported classification")
        target = contract.get("target_boundary")
        if not isinstance(target, str) or not target.startswith("plugins/saga/"):
            errors.append(f"{contract_id}: target boundary must stay inside Saga")
            continue
        if any(part in {".claude", ".gemini", "brain"} for part in Path(target).parts):
            errors.append(f"{contract_id}: target boundary cannot be runtime state")
            continue
        if not _resolve_repo_path(target).is_file():
            errors.append(f"{contract_id}: target boundary does not exist")
    return errors


def test_portability_page_maps_every_runtime_specific_contract_to_antigravity() -> None:
    model = _load_model()

    assert set(model["execution_backends"]) == {"inline", "multi-agent-consensus"}
    assert _portability_errors(model) == []
    portability_text = (SAGA_ROOT / "docs" / "portability.md").read_text(encoding="utf-8")
    for contract_id in model["portability"]["runtime_contracts"]:
        label = contract_id.replace("-", " ")
        assert label in portability_text.lower()
    assert len(model["portability"]["packet_mappings"]) == 45
    mappings = list(model["portability"]["packet_mappings"].values())
    assert {mapping[1] for mapping in mappings} == {
        "0c2072446c7e136caa274b5f637ca2c8c03725e4"
    }
    classifications = [mapping[3] for mapping in mappings]
    assert classifications.count("adapted") == 26
    assert classifications.count("preserved") == 15
    assert classifications.count("shed") == 4
    assert "packets: 26 adapted, 15 preserved, and 4 shed" in portability_text
    assert "0c2072446c7e136caa274b5f637ca2c8c03725e4" in portability_text
    assert "does not consume them as source-oracle behavior" in portability_text


def test_portability_page_maps_every_runtime_specific_contract_to_antigravity_rejects_negative_cases() -> None:
    model = _load_model()
    portability = model["portability"]

    portability["native_backends"] = ["inline", "source-workflow"]
    portability["runtime_contracts"]["capability-evidence"]["classification"] = "copied"
    portability["runtime_contracts"]["runtime-state-projections"]["target_boundary"] = (
        ".gemini/saga/state.json"
    )
    portability["packet_mappings"].pop(next(iter(portability["packet_mappings"])))

    errors = _portability_errors(model)
    assert "native backends must be inline and multi-agent-consensus" in errors
    assert "capability-evidence: unsupported classification" in errors
    assert "runtime-state-projections: target boundary must stay inside Saga" in errors
    assert "packet inventory count must equal exact mapping rows" in errors
    assert "packet mappings must exactly cover all candidate-owned packets" in errors


def test_docs_model_matches_command_surface() -> None:
    model = _load_model()
    wrappers = _command_wrapper_names()
    commands = set(model["commands"])
    aliases = set(model["aliases"])

    assert model["command_surface"]["command_files"] == 23
    assert model["command_surface"]["routable_commands"] == 22
    assert wrappers == commands | aliases
    assert aliases == {"ceo-review"}
    assert model["aliases"]["ceo-review"]["aliases"] == "/founder-review"


def test_every_command_card_has_required_fields_and_existing_sources() -> None:
    model = _load_model()

    for command_id, card in model["commands"].items():
        missing = REQUIRED_CARD_FIELDS - set(card)
        assert not missing, f"{command_id} missing card fields: {sorted(missing)}"
        assert card["command"] == f"/{command_id}"
        for field in ("use_when", "do_not_use_when", "common_mistakes"):
            assert isinstance(card[field], list) and card[field], f"{command_id}.{field} empty"
        for source_ref in card["source_refs"]:
            path = _resolve_repo_path(source_ref)
            assert path.exists(), f"{command_id} source_ref missing: {source_ref}"

    for alias_id, alias in model["aliases"].items():
        for source_ref in alias["source_refs"]:
            path = _resolve_repo_path(source_ref)
            assert path.exists(), f"{alias_id} source_ref missing: {source_ref}"


def test_readiness_is_derived_not_stored() -> None:
    model = _load_model()
    state_axes = set(model["state_axes"])
    maturity = model["maturity"]

    assert state_axes == {"lifecycle_phase", "phase_status", "status"}
    assert "maturity" not in state_axes
    assert maturity["derived_not_stored"] is True
    assert set(maturity["values"]) >= {
        "idea-ready",
        "requirements-ready",
        "plan-ready",
        "resume-ready",
    }
    assert "docs/specs/" in maturity["values"]["requirements-ready"]["from"]


def test_required_scenarios_pairs_and_visual_inventory_are_present() -> None:
    model = _load_model()

    assert set(model["scenarios"]) >= REQUIRED_SCENARIOS
    assert set(model["visuals"]) >= REQUIRED_VISUALS
    assert {tuple(pair) for pair in model["adjacent_pairs"]} >= REQUIRED_ADJACENT_PAIRS

    for scenario_id, scenario in model["scenarios"].items():
        for field in (
            "starting_statement",
            "selected_command",
            "effect",
            "stop_condition",
            "next_route",
        ):
            assert scenario.get(field), f"{scenario_id} missing {field}"


def test_manual_pages_exist_and_reference_model_coverage() -> None:
    model = _load_model()
    for page in MANUAL_PAGES:
        assert page.is_file(), f"missing manual page: {page.relative_to(REPO_ROOT)}"

    commands_text = (SAGA_ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
    for command_id, card in model["commands"].items():
        assert f"### {card['command']}" in commands_text, f"missing card for {command_id}"
    assert "### /ceo-review" in commands_text

    scenarios_text = (SAGA_ROOT / "docs" / "scenarios.md").read_text(encoding="utf-8")
    for scenario_id in REQUIRED_SCENARIOS:
        assert scenario_id in scenarios_text

    visuals_text = (SAGA_ROOT / "docs" / "visuals.md").read_text(encoding="utf-8")
    for visual in model["visuals"].values():
        assert Path(visual["file"]).name in visuals_text


def test_manual_relative_links_resolve() -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\((?!https?://|#)([^)]+)\)")

    for page in MANUAL_PAGES:
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target_without_anchor = raw_target.split("#", maxsplit=1)[0]
            if not target_without_anchor:
                continue
            target = (page.parent / target_without_anchor).resolve()
            assert target.exists(), f"{page.relative_to(REPO_ROOT)} has broken link: {raw_target}"


def test_generated_visual_assets_match_model() -> None:
    model = _load_model()
    renderer = _load_renderer()
    rendered = renderer.render_all(model)

    for visual_id, svg in rendered.items():
        visual = model["visuals"][visual_id]
        path = REPO_ROOT / visual["file"]
        assert path.is_file(), f"missing generated visual: {visual['file']}"
        assert path.read_text(encoding="utf-8") == svg, (
            f"{visual['file']} is stale; run "
            "uv run python plugins/saga/scripts/render_docs_visuals.py"
        )
        assert f'<title id="title">{visual["title"]}</title>' in svg
        assert "Do not edit by hand" in svg
