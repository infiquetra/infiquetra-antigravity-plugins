"""Regression coverage for Antigravity's canonical Saga state root."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str) -> ModuleType:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SAGA = _load("saga")
EFFORT = _load("effort_ledger")
GATE_READER = _load("gate_divergence_reader")


def test_default_state_paths_share_gemini_saga_root() -> None:
    assert Path(".gemini/saga") == SAGA.STATE_DIR
    assert EFFORT.DEFAULT_LEDGER_PATH.parent == SAGA.STATE_DIR
    assert SAGA.SAGAS_DIR == GATE_READER._SAGAS_DIR


def test_gate_reader_discovers_envelope_written_to_canonical_root(tmp_path: Path) -> None:
    encoded = SAGA.encode_gate_divergence_entry(
        "review@r1", "approve", "hold", True, latency_seconds=2
    )
    envelope = SAGA.Saga(
        saga_id="task-state-root",
        kind="task",
        id="state-root",
        gate_divergence=[encoded],
    )
    saga_dir = tmp_path / SAGA.SAGAS_DIR / envelope.saga_id
    saga_dir.mkdir(parents=True)
    (saga_dir / "20260711-210000.md").write_text(SAGA.render_envelope(envelope))

    summaries = GATE_READER.read_gate_divergence(tmp_path)

    assert summaries["review@r1"].interaction_count == 1
    assert summaries["review@r1"].divergence_count == 1
