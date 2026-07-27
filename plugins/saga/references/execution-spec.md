# Legacy execution-spec source lineage

`scripts/execution_spec.py` and `scripts/team_emitter.py` preserve the prior
Claude execution-spec format for source comparison and bounded migration tests.
They are not active Antigravity planning or dispatch surfaces.

## Active Antigravity contract

- `/plan` writes a builder-ready implementation plan.
- `orchestration_mode=multi-agent-consensus` points
  `orchestration_ref` at that plan.
- `/work` loads
  `plugins/multi-agent-consensus/skills/multi-agent-consensus/SKILL.md` and uses
  Antigravity's native subagent controls.
- A capability receipt must prove `agy.agent.execution` and every requested
  isolation capability before dispatch.
- `unknown`, `unavailable`, or `failed` required capability states halt.

Active routing must not emit a `.workflow.js`, invoke a Claude-only tool, or
translate `multi-agent-consensus` into `team-execution`.

## Retained source format

The legacy JSON format contains named units, dependencies, requested model and
effort, return keys, enumerated fan-out targets, pilot relationships, and
verification panels. Its validators remain useful when evaluating future source
deltas, but requested model, effort, concurrency, or isolation values are not
evidence that Antigravity enforced them.

`recompile_for_tier(..., "multi-agent-consensus")` rejects before emission.
Explicit legacy source modes may still be exercised by isolated tests; the
active outcome dispatcher rejects them before an emitter is reached.

## Inline recovery

`emit_inline_baseline` remains a host-independent rendering helper for legacy
specs. Unattended recovery may use `inline` only when the saga records the
downgrade and the work is not guarantee-bearing. An attended or
guarantee-bearing run halts for an operator decision instead of silently losing
independent execution.
