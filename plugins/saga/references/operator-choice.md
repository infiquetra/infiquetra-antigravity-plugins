# Operator-Choice Framework

**Status:** canonical contract
**Companion:** [`saga-spec.md`](./saga-spec.md)
**Audience:** Saga skills that choose how work executes.

This is the decision contract for Saga execution. Saga recommends a backend, asks
the operator to confirm it, and records the choice. The selected backend owns the
work.

## 1. Antigravity execution backends

The recorded value is exactly one of:

- `inline` — the current agent executes serially in the current session.
- `multi-agent-consensus` — the Antigravity plugin orchestrates native subagents
  with `invoke_subagent` and `send_message`, then applies its reviewer and
  validator protocol.

Claude `team-execution` and the historical source enum
<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003","reason":"named source enum is explicitly quarantined","revisit":"remove when source lineage support is retired"} -->
`cc-workflows-ultracode` are source-lineage mechanisms, not Antigravity
backends. Both map to `multi-agent-consensus`; a Claude Workflow script must
never be emitted or invoked from active Antigravity routing.

Lifecycle owns the choice, not execution. It points to the
`multi-agent-consensus` skill when that backend is selected and does not reproduce
its worker, reviewer, or validator machinery.

## 2. Recommendation

Recommend `inline` when the task is small, serial, and does not require independent
review or parallel coverage.

Recommend `multi-agent-consensus` when any of these signals is present:

- eight or more materially affected files;
- four or more implementation phases;
- security, infrastructure, deployment, or cross-repository risk;
- a verdict that must block or persist;
- broad independent fan-out;
- explicit adversarial or perspective-diverse verification.

For pure documentation, specification, or research work, do not infer code risk
from keywords alone. Cross-repository coordination and an explicit consensus
requirement remain valid escalation signals.

The recommendation is advisory. Ask one blocking question through the current
session, recommend one option when useful, and stop until the operator answers.
Use a structured interaction surface only when a capability receipt proves it;
otherwise ask inline. In a `redis-channel` session, use the channel-inline
convention in [`../skills/brainstorm/SKILL.md`](../skills/brainstorm/SKILL.md).

## 3. Capability gate

`multi-agent-consensus` is available only when all of the following are true:

1. the plugin is installed and valid;
2. the current Antigravity session exposes the native subagent controls required
   by the plugin;
3. capability `agy.agent.execution` is `passed` for the current environment;
4. any requested sandbox or worktree isolation capability is also `passed`.

An `unknown`, `unavailable`, or `failed` required capability is not proof. When the
operator is present, halt and ask them to choose `inline` or move to an environment
with a passing receipt. During unattended recovery, a downgrade to `inline` is
allowed only when the saga records the downgrade and the work is not
guarantee-bearing.

Do not convert an independent-agent requirement to sequential execution. That
would change the selected guarantee rather than degrade the mechanism.

## 4. Recording the choice

The saga envelope stores:

- `orchestration_mode` — `inline` or `multi-agent-consensus`;
- `orchestration_ref` — empty for `inline`; for
  `multi-agent-consensus`, the durable plan path or backend receipt path;
- `orchestration_operator_choice` — the operator-confirmed mode;
- `orchestration_downgrade` — a visible reason when unattended recovery moves to
  a lower mode.

The plan artifact is the durable input to `multi-agent-consensus`. Antigravity
does not promise a workflow identifier, so Saga must not require or fabricate one.
If the backend emits a receipt, Saga may replace the plan pointer with that receipt
path after the run.

A change from `orchestration_operator_choice` to a different mode without a
non-empty `orchestration_downgrade` is invalid.

## 5. Active dispatch

When `multi-agent-consensus` is selected:

1. verify the plan path and required capability receipt;
2. load `plugins/multi-agent-consensus/skills/multi-agent-consensus/SKILL.md`;
3. invoke the skill's native subagent flow;
4. persist its review and validator evidence;
5. record a receipt path when one exists.

Never route the selection through `execution_spec.py`, a generated
`.workflow.js`, or a Claude-only tool call. Those are legacy source lineage and
are rejected by the active Antigravity dispatcher.
