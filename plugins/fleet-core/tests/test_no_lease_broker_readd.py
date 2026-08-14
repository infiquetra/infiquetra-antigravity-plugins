"""Re-add guard for the fleet lease broker and orphan evidence (U7, #684).

The broker and its companion were deleted in U7. This guard prevents them being
reintroduced, scanning resolved module paths and the repo tree.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGINS = ROOT / "plugins"

FORBIDDEN = ("lease_broker", "orphan_evidence", "lease_authority", "fleet_leases")

_SELF = Path(__file__).resolve()


def _scan_tree(root: Path = PLUGINS) -> list[Path]:
    """Return every Python file under *root* that mentions a forbidden name.

    The guard file itself is excluded — it necessarily names the forbidden modules.
    """
    offenders: list[Path] = []
    for path in root.rglob("*.py"):
        if path.resolve() == _SELF:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(name in text for name in FORBIDDEN):
            offenders.append(path)
    return offenders


def _scan_with_fixture(root: Path, fixture: Path) -> list[Path]:
    """Scan *root* plus one extra *fixture* file — proves the scanner can fail."""
    offenders = _scan_tree(root)
    if fixture.exists():
        try:
            text = fixture.read_text(encoding="utf-8")
            if any(name in text for name in FORBIDDEN):
                offenders.append(fixture)
        except OSError:
            pass
    return offenders


def _shim_resolved_paths() -> list[Path]:
    """Return shim-resolved fleet-commons candidates, if any."""
    candidates: list[Path] = []
    for shim_name in ("fleet_commons_shim",):
        for search_root in (
            ROOT / "plugins" / "saga" / "scripts",
            ROOT / "plugins" / "fleet-core" / "scripts",
        ):
            shim_path = search_root / f"{shim_name}.py"
            if not shim_path.is_file():
                continue
            try:
                spec = importlib.util.spec_from_file_location(shim_name, shim_path)
                assert spec is not None and spec.loader is not None
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                for target in FORBIDDEN:
                    try:
                        loaded = mod.load(target)
                        if loaded is not None and hasattr(loaded, "__file__") and loaded.__file__:
                            candidates.append(Path(loaded.__file__).parent)
                    except Exception:
                        continue
            except Exception:
                continue

    seen: set[Path] = set()
    resolved: list[Path] = []
    for cand in candidates:
        try:
            cand = cand.resolve()
        except OSError:
            continue
        if cand.is_dir() and cand not in seen:
            seen.add(cand)
            resolved.append(cand)
    return resolved


def test_no_file_under_plugins_imports_lease_broker_or_orphan_evidence() -> None:
    offenders = _scan_tree(PLUGINS)
    assert offenders == [], (
        "re-add guard: forbidden lease import still present under plugins/: "
        + ", ".join(str(p.relative_to(ROOT)) for p in offenders)
    )
    for resolved in _shim_resolved_paths():
        offenders = _scan_tree(resolved)
        assert offenders == [], (
            f"re-add guard: forbidden import via shim-resolved {resolved}: {offenders}"
        )


def test_guard_fails_when_handed_a_lease_broker_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture_leases.py"
    fixture.write_text("import lease_broker as fleet_leases\n", encoding="utf-8")
    offenders = _scan_with_fixture(PLUGINS, fixture)
    assert fixture in offenders, "guard should fail when handed a file that imports lease_broker"
    assert all(p == fixture or p.is_relative_to(PLUGINS) for p in offenders)


def test_guard_fails_when_handed_an_orphan_evidence_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture_orphan.py"
    fixture.write_text("import orphan_evidence\n", encoding="utf-8")
    offenders = _scan_with_fixture(PLUGINS, fixture)
    assert fixture in offenders, "guard should fail when handed a file that imports orphan_evidence"


def test_guard_inspects_shim_resolved_paths_not_just_the_tree(tmp_path: Path) -> None:
    fake_root = tmp_path / "fake-plugins" / "fleet-core" / "scripts" / "fleet_commons"
    fake_root.mkdir(parents=True)
    (fake_root / "lease_broker.py").write_text(
        "import lease_broker  # stale cache\n", encoding="utf-8"
    )
    assert _scan_tree(PLUGINS) == []
    offenders = _scan_tree(fake_root)
    assert offenders == [fake_root / "lease_broker.py"]
