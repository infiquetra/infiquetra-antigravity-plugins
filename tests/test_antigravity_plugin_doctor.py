from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import validate_plugins


def write_plugin(root: Path, name: str = "demo", manifest: dict | None = None) -> Path:
    plugin_dir = root / "plugins" / name
    plugin_dir.mkdir(parents=True)
    payload = manifest or {"name": name, "version": "1.0.0", "description": "Demo plugin"}
    (plugin_dir / "plugin.json").write_text(json.dumps(payload))
    return plugin_dir


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
