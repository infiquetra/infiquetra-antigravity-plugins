#!/usr/bin/env python3
"""Infiquetra lifecycle destination and escalation helpers."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

DESTINATION_ALIASES = {
    "plan": "plan-only",
    "plan only": "plan-only",
    "plan-only": "plan-only",
    "planning": "plan-only",
    "pr": "pr",
    "pull request": "pr",
    "pull-request": "pr",
    "merge": "merge",
    "merged": "merge",
    "nonprod": "nonprod-deploy",
    "nonprod deploy": "nonprod-deploy",
    "nonprod-deploy": "nonprod-deploy",
    "deploy": "nonprod-deploy",
}


def normalize_destination(value: str) -> str:
    """Normalize user-facing destination labels."""

    key = " ".join(value.strip().lower().replace("_", "-").split())
    key = key.replace("nonprod-deployment", "nonprod-deploy")
    if key in DESTINATION_ALIASES:
        return DESTINATION_ALIASES[key]
    raise ValueError("destination must be one of: plan-only, pr, merge, nonprod-deploy")


def destination_includes_deploy(destination: str) -> bool:
    """Return whether the selected destination needs deployment orchestration."""

    return normalize_destination(destination) == "nonprod-deploy"


def should_offer_consensus(
    *,
    file_count: int,
    phase_count: int,
    has_security: bool,
    has_infra: bool,
    cross_repo: bool,
    deployment_sensitive: bool,
    has_code_surface: bool = True,
) -> bool:
    """Decide whether the loop should offer Antigravity multi-agent consensus.

    ``has_code_surface`` defaults True, so every existing caller is unchanged.
    Set it False for pure docs/spec/research/journal work (no code, no IaC, no
    API contract, no deployable artifact). It neutralizes the OUTPUT-BLIND
    proxies — the ones that fire on the *mention* or *volume* of risk rather than
    a real ship/scanner surface that consensus review can act on:

    * ``file_count`` / ``phase_count`` — volume and sequencing, not governance.
    * ``has_infra`` / ``has_security`` — ``parse_issue.py`` keyword regexes
      (terraform, lambda, auth, iam, ...) trip on infra/security DOCS that touch
      nothing deployable.
    * ``deployment_sensitive`` — cannot truthfully hold when there is no deploy.

    ``cross_repo`` SURVIVES the neutralizer: crossing a repo boundary crosses an
    OWNERSHIP boundary, a multi-party coordination/consensus need that holds even
    for docs. (``needs_consensus`` survives in ``recommend_execution_backend`` for
    the same reason.)
    """

    code_shaped = any(
        (
            file_count >= 8,
            phase_count >= 4,
            has_security,
            has_infra,
            deployment_sensitive,
        )
    )
    return (code_shaped and has_code_surface) or cross_repo


def should_prompt_for_issue(*, has_issue: bool, is_trivial: bool, user_declined: bool) -> bool:
    """Ask whether to file an SDLC issue for non-trivial ad-hoc work."""

    return not has_issue and not is_trivial and not user_declined


def requires_hard_test_gate(change_kinds: Sequence[str]) -> bool:
    """Return whether a change kind requires explicit tests before shipping."""

    risky = {"behavior", "security", "infra", "api", "deployment", "data"}
    return bool(risky.intersection(kind.lower() for kind in change_kinds))


def recommend_execution_backend(
    *,
    file_count: int = 0,
    phase_count: int = 0,
    has_security: bool = False,
    has_infra: bool = False,
    cross_repo: bool = False,
    deployment_sensitive: bool = False,
    needs_consensus: bool = False,
    consensus_is_gated: bool = True,
    broad_independent_fanout: bool = False,
    adversarial_confidence: bool = False,
    has_code_surface: bool = True,
    consensus_available: bool = False,
) -> dict[str, object]:
    """Recommend one of the two active Antigravity execution backends.

    Imported orchestration concepts map to ``multi-agent-consensus``. The
    gated/advisory distinction remains useful to that skill's review policy,
    but it does not select a different backend.
    """

    escalation = (
        should_offer_consensus(
            file_count=file_count,
            phase_count=phase_count,
            has_security=has_security,
            has_infra=has_infra,
            cross_repo=cross_repo,
            deployment_sensitive=deployment_sensitive,
            has_code_surface=has_code_surface,
        )
        or needs_consensus
        or broad_independent_fanout
        or adversarial_confidence
    )

    if escalation and consensus_available:
        recommended = "multi-agent-consensus"
        governance = "gated" if needs_consensus and consensus_is_gated else "advisory"
        rationale = f"size, risk, or independent-review signal -> {governance} native consensus"
    elif escalation:
        recommended = "inline"
        rationale = "consensus was indicated but its required capabilities are not proven"
    else:
        recommended = "inline"
        rationale = "no escalation signal -> the agent does the work itself"

    reachable = ["inline", "multi-agent-consensus"]
    if not consensus_available:
        reachable.remove("multi-agent-consensus")
    alternatives = [backend for backend in reachable if backend != recommended]

    return {
        "recommended": recommended,
        "rationale": rationale,
        "alternatives": alternatives,
        "omit_multi_agent_consensus": not consensus_available,
    }


ORCHESTRATION_TIERS = ("multi-agent-consensus", "inline")
_HOST_DEPENDENT_TIERS = frozenset({"multi-agent-consensus"})


def recheck_orchestration_capability(
    *,
    orchestration_mode: str,
    consensus_available: bool,
    fallback_mode: str = "inline",
) -> dict[str, object]:
    """Re-check host capability on resume and recompile ONLY the orchestration tier (R11).

    Capability-portable degradation. Every authored plan carries a runnable inline/serial
    baseline; the dynamic-workflow layer applies only on a capable host. On an off-host
    resume the native consensus runtime is re-checked here; if the chosen tier is host-dependent
    (``multi-agent-consensus``) and the host cannot run it, this recompiles ONLY the
    orchestration tier DOWN the :data:`ORCHESTRATION_TIERS` ladder. The unit specs and
    per-unit ``{model, effort}`` tiers are NOT touched here — they survive the recompile
    untouched (that preservation is the emitter's job; this function decides the new
    orchestration tier and the human-readable downgrade note).

    ``inline`` is the only lower active Antigravity tier. A required independent
    execution guarantee must be handled by the caller before this unattended
    recovery helper is used.

    AE3 contract — this NEVER errors and NEVER silently runs nothing:

    * **Host CAN run the chosen tier** (``consensus_available`` True, or the mode is not
      host-dependent): ``downgraded=False``, ``to == orchestration_mode`` — run as authored.
    * **Host CANNOT run the chosen tier**: ``downgraded=True``, ``to`` is a runnable tier
      (never empty), and ``note`` is a one-line, surfaceable downgrade message.
    * **Unknown / empty mode**: treated as the inline baseline — ``downgraded=False``,
      ``to == "inline"`` — never an exception, never an empty target.

    Returns a JSON-serializable dict::

        {
          "downgraded": bool,
          "from": <the mode as resumed>,       # echoed input
          "to": <the runnable orchestration tier>,   # NEVER empty
          "note": <one-line downgrade note, or ""> ,
          "consensus_available": bool,          # echoed capability probe
        }
    """

    resumed = orchestration_mode or "inline"

    # An unknown stored mode is floored to the inline baseline rather than trusted — a
    # host that cannot identify the tier still runs SOMETHING (AE3: never run nothing).
    if resumed not in ORCHESTRATION_TIERS:
        return {
            "downgraded": False,
            "from": resumed,
            "to": "inline",
            "note": "",
            "consensus_available": consensus_available,
        }

    host_can_run = consensus_available or resumed not in _HOST_DEPENDENT_TIERS
    if host_can_run:
        # The authored tier is runnable here — no downgrade, run as authored.
        return {
            "downgraded": False,
            "from": resumed,
            "to": resumed,
            "note": "",
            "consensus_available": consensus_available,
        }

    # Off-host: recompile the orchestration tier DOWN. Prefer the requested fallback, but
    # only if it is itself a runnable (host-portable, known) tier; otherwise floor to
    # inline — never land on another host-dependent tier that might also be unavailable.
    if fallback_mode in ORCHESTRATION_TIERS and fallback_mode not in _HOST_DEPENDENT_TIERS:
        target = fallback_mode
    else:
        target = "inline"

    note = (
        f"Downgraded orchestration {resumed} -> {target}: the native consensus runtime is "
        f"unavailable on this host. Unit specs and per-unit tiers preserved; only "
        f"the orchestration tier recompiled."
    )
    return {
        "downgraded": True,
        "from": resumed,
        "to": target,
        "note": note,
        "consensus_available": consensus_available,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser("normalize", help="normalize a user-facing destination label")
    normalize.add_argument("destination")

    backend = subparsers.add_parser(
        "recommend-backend", help="recommend an execution backend as JSON"
    )
    backend.add_argument("--file-count", type=int, default=0)
    backend.add_argument("--phase-count", type=int, default=0)
    backend.add_argument("--has-security", action="store_true")
    backend.add_argument("--has-infra", action="store_true")
    backend.add_argument("--cross-repo", action="store_true")
    backend.add_argument("--deployment-sensitive", action="store_true")
    backend.add_argument("--needs-consensus", action="store_true")
    backend.add_argument(
        "--advisory-consensus",
        action="store_true",
        help="mark the consensus request as advisory rather than a persistent gate",
    )
    backend.add_argument("--broad-fanout", action="store_true")
    backend.add_argument("--adversarial-confidence", action="store_true")
    backend.add_argument("--no-code-surface", action="store_true")
    backend.add_argument(
        "--consensus-proven",
        action="store_true",
        help="a separate capability gate proved the native consensus runtime",
    )

    recheck = subparsers.add_parser(
        "recheck-capability",
        help="re-check host capability on resume and recompile the orchestration tier (R11)",
    )
    recheck.add_argument(
        "--orchestration-mode",
        default="inline",
        help="the tier as resumed (multi-agent-consensus|inline)",
    )
    recheck.add_argument(
        "--consensus-proven",
        action="store_true",
        help="a separate capability gate proved the native consensus runtime",
    )
    recheck.add_argument(
        "--fallback-mode",
        default="inline",
        help="preferred landing tier on a downgrade (only inline is active)",
    )

    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "normalize":
        print(normalize_destination(args.destination))
        return 0
    if args.command == "recommend-backend":
        result = recommend_execution_backend(
            file_count=args.file_count,
            phase_count=args.phase_count,
            has_security=args.has_security,
            has_infra=args.has_infra,
            cross_repo=args.cross_repo,
            deployment_sensitive=args.deployment_sensitive,
            needs_consensus=args.needs_consensus,
            consensus_is_gated=not args.advisory_consensus,
            broad_independent_fanout=args.broad_fanout,
            adversarial_confidence=args.adversarial_confidence,
            has_code_surface=not args.no_code_surface,
            consensus_available=args.consensus_proven,
        )
        print(json.dumps(result))
        return 0
    if args.command == "recheck-capability":
        result = recheck_orchestration_capability(
            orchestration_mode=args.orchestration_mode,
            consensus_available=args.consensus_proven,
            fallback_mode=args.fallback_mode,
        )
        print(json.dumps(result))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
