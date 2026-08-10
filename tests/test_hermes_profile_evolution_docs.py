from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hermes-profile-evolution"
DOCS = PLUGIN / "docs"
SCRIPT = PLUGIN / "scripts/profile_request.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_documentation_package_is_complete_and_uses_rendered_art() -> None:
    expected = {
        "usage.md",
        "architecture.md",
        "development.md",
        "troubleshooting.md",
        "assets/profile-evolution-antigravity-front-door.svg",
        "assets/profile-evolution-antigravity-front-door.png",
        "assets/renderer-receipt.md",
    }

    assert expected <= {
        path.relative_to(DOCS).as_posix() for path in DOCS.rglob("*") if path.is_file()
    }
    combined = "\n".join(path.read_text() for path in DOCS.rglob("*.md"))
    assert "```mermaid" not in combined
    assert "no proven native blocking-hook contract" in combined.lower()
    assert "Team Mimir operator hub" in combined
    assert "Hermes producer" in combined


def test_renderer_receipt_binds_the_committed_source_and_render() -> None:
    assets = DOCS / "assets"
    receipt = (assets / "renderer-receipt.md").read_text()
    assert re.search(r"rsvg-convert version \d+\.\d+\.\d+", receipt)
    for suffix in ("svg", "png"):
        path = assets / f"profile-evolution-antigravity-front-door.{suffix}"
        assert _sha256(path) in receipt


def test_usage_documents_every_public_operator_action() -> None:
    usage = (DOCS / "usage.md").read_text()
    assert '--team-mimir-root "$TEAM_MIMIR_ROOT" request' in usage
    for action in ("reply", "resume", "status", "doctor"):
        assert f'python3 "$PROFILE_ADAPTER" {action}' in usage

    request_match = re.search(r"request <<'JSON'\n(\{.*?\})\nJSON", usage, flags=re.DOTALL)
    assert request_match is not None
    request = json.loads(request_match.group(1))
    assert set(request) == {
        "target",
        "requester",
        "delegation_chain",
        "intent",
        "evidence_references",
        "paths",
    }
    assert request["target"] == "brokkr"
    assert request["delegation_chain"][0]["actor_id"] == "antigravity"


def test_cli_help_and_invalid_examples_have_documented_exit_contract() -> None:
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, check=False
    )
    assert help_result.returncode == 0
    for action in ("request", "reply", "resume", "status", "doctor"):
        assert action in help_result.stdout

    invalid = subprocess.run(
        [sys.executable, str(SCRIPT), "doctor"],
        input="{}",
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid.returncode == 2
    assert "doctor input is malformed" in invalid.stderr


def test_released_contract_surfaces_remain_version_010() -> None:
    manifest = json.loads((PLUGIN / "plugin.json").read_text())
    assert manifest["version"] == "0.1.1"
    assert (PLUGIN / "CHANGELOG.md").is_file()
