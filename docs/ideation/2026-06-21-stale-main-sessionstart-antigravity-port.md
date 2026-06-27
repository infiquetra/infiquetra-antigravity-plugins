---
date: 2026-06-21
topic: stale-main-sessionstart-antigravity-port
focus: Port the generalized stale-main SessionStart behavior, but make it Antigravity-native.
scope: standard
repo: infiquetra-antigravity-plugins
maturity: idea-ready
---

# Ideation: Porting the Stale-Main SessionStart Hook to Antigravity

## Grounding Context

**Repo:** The `infiquetra-antigravity-plugins` repository uses a flat plugin structure configured by `plugins/saga/plugin.json`. Scripts are strictly consolidated into `src/` (per `docs/engineering-journal/DECISIONS.md`). The environment orchestrates native agents using tools like `invoke_subagent` and `schedule`. Notably absent from `ANTIGRAVITY.md` and current strategy docs is any mention of a plugin "hook" registry or a `SessionStart` equivalent that allows Python scripts to silently intercept the agent's startup to inject context.

**Named repos:** `infiquetra-claude-plugins` (Source). Commit `df67968144c86b42377d70482c43242b4aec0f6a` removed repo-specific `stale_main_guard.py` dependencies. The hook now reads the working directory from Claude's `SessionStart` JSON payload on `sys.stdin`, performs generic git checks (finding default branch, checking commits behind, verifying cleanliness), auto-fast-forwards if safe, and outputs a `hookSpecificOutput` JSON object to inject `additionalContext` into the Claude agent's prompt. 

## Topic Axes

1. **Trigger mechanism:** How and when the stale-main check executes, given Antigravity's unknown hook architecture.
2. **Context surfacing:** How the agent and operator are notified of warnings or fast-forwards.
3. **Packaging:** Where the logic lives in the Antigravity plugin layout.

## Ranked Survivors

### 1. Native Hook Discovery Spike & Port

Port the core logic to `src/`, but block full integration on a spike to determine Antigravity's actual startup hook contract.

Package the exact generic git logic from the source repo into `plugins/saga/src/stale_main_hook.py`. Because `ANTIGRAVITY.md` does not document a `SessionStart` equivalent, run a brief engineering spike to find out if `plugin.json` or `.gemini/` supports startup hooks. If it does, adapt the stdin/stdout JSON contract. If it does not, fallback to Survivor 2.

We cannot blindly copy `hooks/hooks.json` because Antigravity does not use Claude's plugin manifest shape. Inventing a hook contract that doesn't exist will break silently. Spiking first isolates the risk while securing the generic python port.

| field | value |
|-------|-------|
| basis | `reasoned:` No documented hook system exists in `ANTIGRAVITY.md`, making assumption dangerous. |
| confidence | 85 |
| complexity | Low |
| axis | Trigger mechanism |
| status | Explored |

### 2. Explicit Preflight in `/loop` Router

Wire the fast-forward check directly into the saga `loop` router instead of relying on a global session hook.

Expose `src/stale_main_hook.py` as an Antigravity tool/command. Since `/loop` is the entrypoint and router for the entire Infiquetra lifecycle (`plugins/saga/skills/loop/SKILL.md`), we instruct `/loop` to execute this tool as its very first step on any invocation.

This guarantees the check runs before any real work starts without requiring an undocumented global session hook. It keeps the logic agent-driven and natively observable, though it misses users who bypass `/loop` to call specific skills directly.

| field | value |
|-------|-------|
| basis | `direct:` The `loop` skill acts as the front-door for saga state (per `STRATEGY.md`). |
| confidence | 80 |
| complexity | Low |
| axis | Trigger mechanism |
| status | Explored |

### 3. Recurring Background Guard via `schedule`

Convert the hook into an ongoing background monitor using Antigravity's native cron scheduling.

When the plugin loads, use the `schedule` tool to run the stale-main check as a background task (e.g., every 30 minutes). When the default branch falls behind, the script terminates and the task's `Prompt` configuration dynamically pushes the warning as a high-priority message into the agent's context.

This leverages purely native Antigravity primitives (`schedule` tool) and provides continuous protection, rather than only checking at session start. However, it requires wrapping the python script in a way that signals the schedule tool correctly.

| field | value |
|-------|-------|
| basis | `direct:` Antigravity's `schedule` tool natively supports background cron notifications. |
| confidence | 70 |
| complexity | Med |
| axis | Context surfacing |
| status | Explored |

## Did not survive (revivable)

Explicit rejection is the quality mechanism. Cut ideas keep stable ids so they can be revived (which re-enters the Phase 3 filter with new evidence). Never renumber on a status change.

| id | title | summary | reason | status |
|----|-------|---------|--------|--------|
| R1 | Direct `hooks.json` copy | Copy the `.claude/hooks.json` pattern directly | Antigravity doesn't use `.claude` or Claude's plugin shape; it would be a dead file. | rejected |
| R2 | Git `post-checkout` Hook | Enforce auto-ff via local git hooks | Breaks plugin distribution; forces users to manually install git hooks per-repo instead of centralizing in the agent. | rejected |

## Co-ideation log

Records partnership provenance: which ideas came from the operator (seeds) vs. the frame agents, and how each seed fared under the identical critique.

| source | entered | idea / seed | outcome |
|--------|---------|-------------|---------|
| user-seed | Phase 0 | port the generalized stale-main SessionStart behavior, but make it Antigravity-native. | survived as #1, #2, #3 (adapted into spike, loop preflight, and background guard given hook uncertainties) |
| frame-agent | Phase 2 | Explicit Preflight in `/loop` Router | survived as #2 |
| frame-agent | Phase 2 | Recurring Background Guard via `schedule` | survived as #3 |
| frame-agent | Phase 2 | Git `post-checkout` Hook | cut → R2 (abandoned agent plugin pattern) |
