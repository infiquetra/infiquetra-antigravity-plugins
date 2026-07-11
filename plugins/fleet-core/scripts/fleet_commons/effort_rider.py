#!/usr/bin/env python3
"""Fleet effort-honoring seam — the one place that decides *how* a resolved effort is honored.

`effort` is a first-class value across the fleet (authored in agent frontmatter and the
multi-agent-consensus worker registry, validated against the canonical `tier_palette.EFFORTS`
vocabulary, resolved through the three-layer cascade).

The seam understands three ``spawn_kind`` values:
* ``workflow`` (Workflow/ultracode) and ``external-engine`` are real-knob pass-throughs:
  the prompt is returned unchanged with an empty payload.
* ``agent`` (native Agent-tool teammate) returns the prompt unchanged and a Gemini-native
  configuration payload: ``{"generation_config": {"thinking_level": gemini_level}}``.

Routing all three kinds through one ``inject_effort()`` seam means "how effort is honored" lives
in exactly one function.

Vocabulary is sourced from ``tier_palette.EFFORTS`` (KTD3) — never re-declared here.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import fleet_commons_shim  # noqa: E402

EFFORTS: tuple[str, ...] = fleet_commons_shim.load("tier_palette").EFFORTS

# The set of spawn kinds the seam understands.
_PASS_THROUGH_KINDS = ("workflow", "external-engine")
_RIDER_KIND = "agent"
SPAWN_KINDS = (_RIDER_KIND, *_PASS_THROUGH_KINDS)

# Canonical EFFORTS registry mapped values for reference and validation. Keep one entry per
# EFFORTS member; the validation below guards parity.
EFFORT_RIDER: dict[str, str] = {
    "low": (
        "EFFORT (low): this is a light task. Move fast and direct — do the minimum reasoning "
        "the task needs, avoid deep exploration or exhaustive verification, and return promptly."
    ),
    "medium": (
        "EFFORT (medium): apply balanced effort. Reason carefully through the core of the task "
        "and check the obvious failure modes, but do not over-explore tangents or gold-plate."
    ),
    "high": (
        "EFFORT (high): this task warrants deep effort. Reason thoroughly, consider edge cases "
        "and alternative approaches, verify your work, and do not cut the analysis short."
    ),
    "xhigh": (
        "EFFORT (xhigh): apply maximum rigor. Exhaustively explore the problem space, "
        "adversarially stress-test your reasoning, enumerate and check edge cases, and verify "
        "every load-bearing claim before concluding."
    ),
}

if set(EFFORT_RIDER) != set(EFFORTS):
    raise RuntimeError(
        f"EFFORT_RIDER keys {sorted(EFFORT_RIDER)} must exactly match tier_palette.EFFORTS "
        f"{sorted(EFFORTS)}"
    )


def inject_effort(prompt: str, effort: str, spawn_kind: str) -> tuple[str, dict]:
    """Return ``(prompt, payload)`` with the resolved ``effort`` honored for ``spawn_kind``.

    * ``spawn_kind`` in ``{"workflow", "external-engine"}`` → pass-through: ``prompt`` is
      returned unchanged and payload is empty, because the effort already rides as a real
      per-call knob on that path.
    * ``spawn_kind == "agent"`` → returns the unchanged prompt and a Gemini-native thinking
      effort payload ``{"generation_config": {"thinking_level": gemini_level}}``.

    Raises ``ValueError`` for an unknown ``effort`` (not in ``tier_palette.EFFORTS``) or an
    unknown ``spawn_kind``.
    """
    if effort not in EFFORT_RIDER:
        raise ValueError(f"unknown effort {effort!r}; expected one of {EFFORTS}")
    if spawn_kind in _PASS_THROUGH_KINDS:
        return prompt, {}
    if spawn_kind == _RIDER_KIND:
        gemini_level = "high" if effort == "xhigh" else effort
        return prompt, {"generation_config": {"thinking_level": gemini_level}}
    raise ValueError(f"unknown spawn_kind {spawn_kind!r}; expected one of {SPAWN_KINDS}")


def reconcile_effort(
    resolved_effort: str,
    spawn_kind: str,
    *,
    manifest_effort: str | None = None,
    spawn_payload: dict | None = None,
) -> str | None:
    """Post-run reconciliation (R9): compare the cascade-resolved effort against what the worker
    manifest recorded for that teammate, honest per path (KTD7).

    Returns ``None`` on a match — R9's "nothing on match". Returns a named ``tiering-drift`` line
    on a mismatch. The comparison is **honest per path**:

    * ``spawn_kind`` in ``{"workflow", "external-engine"}`` (real-knob paths) — ``manifest_effort``
      is the effort value the worker manifest recorded as actually passed to ``agent()`` / the
      engine (``worker-manifest.md:48,54``). Reconciliation compares it directly against
      ``resolved_effort``; a mismatch names both values.
    * ``spawn_kind == "agent"`` (native Agent-tool teammate) — reconciliation confirms the
      Gemini native payload ``{"generation_config": {"thinking_level": level}}`` was passed.

    Raises ``ValueError`` for an unknown ``resolved_effort``/``spawn_kind``, or when the
    path-appropriate evidence argument (``manifest_effort`` for real-knob paths, ``spawn_payload``
    for the agent path) is omitted.
    """
    if resolved_effort not in EFFORT_RIDER:
        raise ValueError(f"unknown effort {resolved_effort!r}; expected one of {EFFORTS}")
    if spawn_kind in _PASS_THROUGH_KINDS:
        if manifest_effort is None:
            raise ValueError(f"reconcile_effort({spawn_kind!r}) requires manifest_effort")
        if manifest_effort == resolved_effort:
            return None
        return (
            f"tiering-drift[{spawn_kind}]: resolved effort {resolved_effort!r} vs "
            f"manifest-recorded effort {manifest_effort!r}"
        )
    if spawn_kind == _RIDER_KIND:
        if spawn_payload is None:
            raise ValueError(f"reconcile_effort({spawn_kind!r}) requires spawn_payload")

        gemini_level = "high" if resolved_effort == "xhigh" else resolved_effort
        expected_payload = {"generation_config": {"thinking_level": gemini_level}}
        if spawn_payload.get("generation_config", {}).get("thinking_level") == gemini_level:
            return None
        return (
            f"tiering-drift[{spawn_kind}]: resolved effort {resolved_effort!r} — "
            f"compared payload not found in constructed spawn payload "
            f"(expected {expected_payload}, got {spawn_payload})"
        )
    raise ValueError(f"unknown spawn_kind {spawn_kind!r}; expected one of {SPAWN_KINDS}")
