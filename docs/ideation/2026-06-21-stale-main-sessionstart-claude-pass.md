---
date: 2026-06-21
topic: stale-main-sessionstart-claude-pass
focus: Port the generalized stale-main SessionStart behavior from infiquetra-claude-plugins PR #249 into this repo as Antigravity-native
scope: narrow
repo: infiquetra-antigravity-plugins
maturity: idea-ready
---

# Ideation: Stale-Main SessionStart Port (Claude Pass)

> Independent ideation pass. Do not read `docs/ideation/2026-06-21-stale-main-sessionstart-antigravity-port.md` before or during this pass — the intent is an independent survivor set from a Claude lens.

## Grounding Context

**Repo:** `infiquetra-antigravity-plugins` is a Google Antigravity plugin ecosystem (`STRATEGY.md`, updated 2026-06-17) targeting parity with `infiquetra-claude-plugins` via "thoughtful adaptation — not mechanical regex." The plugin spec (`ANTIGRAVITY.md`) defines two plugin types (skills-based and CLI-based). Plugin manifests are flat `plugin.json` files. Scripts live under `plugins/<name>/scripts/` (per `DECISIONS.md` 2026-05-31 `#consolidate-scripts-src`). The saga plugin (`plugins/saga/`) is version 1.2.0, has 17 lifecycle skills, and carries `plugins/saga/scripts/` for Python helpers. There is **no `hooks/` directory** anywhere in this repo, and **`ANTIGRAVITY.md` contains no mention of a hooks mechanism** in the plugin spec.

**Source change (cross-repo basis):** Claude plugins commit `df67968` / PR #249 (`feat(saga): generalize stale-main SessionStart hook to any repo (auto-ff when safe)`) supersedes PR #248. Key behavior kernel:
1. At session start, resolve the git repo root and verify an `origin` remote exists.
2. Detect the default branch generically (`git symbolic-ref --short refs/remotes/origin/HEAD`, fallback probe `origin/main` → `origin/master`).
3. `git fetch origin` (silent on offline failure).
4. Count commits behind: `git rev-list --count <branch>..origin/<branch>`.
5. If behind AND current branch IS the default branch AND tree is clean → `git merge --ff-only origin/<default>` (auto-FF). Otherwise warn. Always exit 0 (non-blocking).
6. Emit result via Claude Code `hookSpecificOutput` / `additionalContext` JSON shape.

Steps 1–5 are **pure Python subprocess calls** with no platform dependency. Step 6 is **Claude Code-specific protocol**.

**Critical discovery — Antigravity hook surface:** `~/.gemini/antigravity-cli/settings.json` (the Antigravity-specific config) has **no `hooks` key**. `~/.gemini/settings.json` (shared with Claude Code) does have `hooks.SessionStart`, `hooks.SessionEnd`, `hooks.BeforeAgent`, and `hooks.AfterAgent` — but these are populated by Claude Code's CMUX infrastructure, using shell command strings, not Python scripts. Whether `agy` (Antigravity) reads and interprets `~/.gemini/settings.json`'s `hooks` section is **unverified**. LEARNINGS.md (`#agy-marketplace-resolution`) confirms `agy` parses `~/.gemini/settings.json` for marketplace config — the hooks section may follow, but this is a spike target, not a confirmed fact.

**Journal learnings:** `DECISIONS.md` 2026-05-31 (`#consolidate-scripts-src`) establishes `plugins/<name>/scripts/` as the canonical home for Python scripts. `DECISIONS.md` 2026-06-06 (`Porting Claude Plugins`) records that legacy `.claude/` checkpoint logic was stripped, not ported. `LEARNINGS.md` (`#cross-plugin-path-mismatch`) warns that path migrations need full consumer audits. The prior port ideation (`docs/ideation/2026-06-05-port-claude-plugins.md`) explicitly rejected a compatibility-layer approach: "introduces excessive technical debt and prevents utilizing Antigravity's native tools."

**Context-libraries:** None consulted — topic is internal to this repo.

**Named repos:** Source repo `infiquetra-claude-plugins` read for commit `df67968` diff only.

---

## Topic Axes

1. **Hook equivalence** — What Antigravity mechanism (if any) maps to Claude's plugin-level `SessionStart` hook? (Unknown until spiked; the central architectural risk.)
2. **Logic portability** — How much of `stale_main_session_hook.py` transfers unchanged vs. needs adaptation? (Steps 1–5 are pure Python; only step 6 is protocol-specific.)
3. **Activation model** — Fully automatic at session start vs. agent-initiated at skill entry vs. operator-invoked on demand.
4. **Packaging path** — Plugin-level (if hooks.json becomes supported) vs. user-settings-level vs. skill-level instruction vs. outside-plugin.

---

## Ranked Survivors

### 1. Spike the Antigravity hook contract first — do not port before verifying the delivery surface

Verify whether `agy` interprets `hooks.SessionStart` entries in `~/.gemini/settings.json` before committing to any implementation approach.

The entire value of this feature is automatic injection at session start without operator action. That delivery depends entirely on whether Antigravity has a functional `SessionStart` hook mechanism. The `~/.gemini/antigravity-cli/settings.json` has no `hooks` key. `ANTIGRAVITY.md` plugin spec has no hooks section. LEARNINGS `#agy-marketplace-resolution` confirms `agy` reads `~/.gemini/settings.json` for marketplaces — hooks could follow the same read path, or could be Claude Code-only. A spike (register a trivial no-op hook entry in `~/.gemini/settings.json` `hooks.SessionStart`, start `agy`, observe whether it fires) costs one session and resolves the central uncertainty. Without it, any implementation commits to a delivery mechanism that may not work.

The spike also determines the correct output protocol: Claude Code expects `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`. If `agy` has a different expected format (or interprets hooks as pure shell with stdout-to-context, or has no equivalent), the script's output section must match.

| field | value |
|-------|-------|
| basis | `reasoned:` ANTIGRAVITY.md plugin spec omits hooks entirely; `~/.gemini/antigravity-cli/settings.json` has no hooks key; `~/.gemini/settings.json` has hooks but populated by Claude Code CMUX — the read path for `agy` is unconfirmed. Any implementation without verification is building on an untested assumption. |
| confidence | 95 |
| complexity | Low |
| axis | Hook equivalence |
| status | Unexplored |

---

### 2. Port the Python logic to `plugins/saga/scripts/stale_main_check.py`, deliver via `~/.gemini/settings.json` hook if spike confirms support

If the spike (Survivor 1) confirms that `agy` reads `hooks.SessionStart` from `~/.gemini/settings.json`, register the script there as a shell command hook. The Python logic (steps 1–5) ports unchanged; only the output format needs adaptation to whatever protocol `agy` expects.

`stale_main_session_hook.py` steps 1–5 have zero platform dependency — they are `subprocess.run(["git", ...])` calls. The `_run` helper, `_repo_root`, `_has_origin_remote`, `_default_branch`, `_commits_behind`, `_current_branch`, `_working_tree_is_clean`, and `_fast_forward` functions copy verbatim (or near-verbatim). Only `main()` changes: instead of emitting `hookSpecificOutput` JSON, it emits whatever format `agy` expects (plain stdout message, or a different JSON envelope, or nothing if `agy` passes stdout directly as context). Packaging: `plugins/saga/scripts/stale_main_check.py` (follows `#consolidate-scripts-src`). The hook registration is a one-line addition to `~/.gemini/settings.json` `hooks.SessionStart` (or delivered via plugin mechanism if Antigravity adds one). Tests port from `tests/test_stale_main_session_hook.py` — they use real temp git repos with no mocks and are fully portable.

The downside: if `agy` does not support `~/.gemini/settings.json` hooks, the script exists but the auto-injection doesn't work. In that case this survivor degrades cleanly to Survivor 4 (standalone script, manual invocation).

| field | value |
|-------|-------|
| basis | `direct:` source `plugins/saga/hooks/stale_main_session_hook.py` (df67968) steps 1–5 are pure Python subprocess; `DECISIONS.md #consolidate-scripts-src` places scripts at `plugins/saga/scripts/`; LEARNINGS `#agy-marketplace-resolution` confirms `agy` reads `~/.gemini/settings.json` (hook section read is unconfirmed but plausible same path) |
| confidence | 72 |
| complexity | Low |
| axis | Logic portability |
| status | Unexplored |

---

### 3. Skill-embedded staleness preamble — inject check instruction into `/resume` and `/work` SKILL.md

Add a short git-staleness check step to the preambles of the saga skills most likely to open a work session: `plugins/saga/skills/` entries for `/resume` and `/work`. The instruction tells the agent to run `git fetch origin && git status` and check if the default branch is behind before doing any other work.

This is purely Antigravity-native and zero-risk: it uses the established SKILL.md instruction mechanism with no new packaging primitives needed. The agent can run the git commands inline with its Bash tool access and surface the warning or confirm the auto-FF. The downside vs. a true hook is that it only fires when those skills are explicitly invoked — it won't fire on a raw `agy` session start that doesn't invoke a skill. It also requires the operator to use a skill that carries the preamble, rather than being guaranteed at every session open.

This approach is most valuable as a fallback or complement to Survivor 2: if hooks aren't available, a skill preamble captures the most common entry points. It also decouples the behavior from hook infrastructure entirely.

| field | value |
|-------|-------|
| basis | `direct:` `plugins/saga/skills/` contains `/resume` and `/work` SKILL.md files — these are the natural session-entry lifecycle skills; STRATEGY.md confirms skill-based delivery as the primary Antigravity-native pattern; `docs/ideation/2026-06-05-port-claude-plugins.md` accepted "Drop legacy patterns, adopt Native Agents" as an approach direction |
| confidence | 85 |
| complexity | Low |
| axis | Activation model |
| status | Unexplored |

---

### 4. Queue plugin-hook packaging to QUEUED.md; ship the standalone script and `/stale-check` command now

Port the Python logic to `plugins/saga/scripts/stale_main_check.py` (manual invocation, no hook wiring). Add a minimal `commands/stale-check.md` Antigravity command that operators can invoke explicitly. Queue the auto-injection path in `docs/engineering-journal/QUEUED.md` with a "worth it when Antigravity publishes a plugin hooks contract" trigger.

This separates two concerns: (a) the git logic is useful and portable now; (b) the auto-injection delivery depends on an unverified platform mechanism. Shipping (a) immediately gives the operator a usable tool and creates the test coverage. Queueing (b) means we don't block on the spike or invent a delivery hack. The cost: the behavior is no longer automatic — the operator must remember to invoke `/stale-check` at session start. The benefit: the logic is tested and ready; wiring it to a hook later is a small incremental change.

If the spike (Survivor 1) runs and confirms `agy` hook support, this survivor and Survivor 2 converge: promote the standalone script to auto-injected hook.

| field | value |
|-------|-------|
| basis | `reasoned:` Separating logic-port from delivery-mechanism-port is the established pattern in this repo (DECISIONS `Porting Claude Plugins` 2026-06-06 records stripping `.claude/` checkpoint syncing rather than carrying it forward); delivering a usable tool first and queuing the automation is lower blast radius than committing to unverified hook infrastructure |
| confidence | 80 |
| complexity | Low |
| axis | Packaging path |
| status | Unexplored |

---

### 5. Dual-format output: detect runtime and emit the right hook protocol

If the spike reveals that `agy` does support `hooks.SessionStart` but uses a different output format than Claude Code's `hookSpecificOutput` envelope, make the script runtime-aware and emit the correct format for each host.

The script can detect the runtime cheaply: check for an env var set by each runtime (e.g., `CLAUDE_SESSION_ID` or `GEMINI_SESSION_ID`, or similar), or probe stdin for runtime-identifying keys in the hook payload. Emit `hookSpecificOutput` JSON for Claude Code; emit whatever `agy` expects (plain text? a different JSON schema?) for Antigravity. This keeps a single script deployable in both plugin repos without forking.

The downside: if the formats are similar (or if `agy` adopts the same Gemini/Claude Code `hookSpecificOutput` protocol, which is plausible given shared `~/.gemini/` config), this complexity is unnecessary. Revisit after spike.

| field | value |
|-------|-------|
| basis | `reasoned:` Both Claude Code and `agy` parse `~/.gemini/settings.json` (confirmed for marketplaces by LEARNINGS `#agy-marketplace-resolution`); they may share the hook protocol (same format), or may diverge; a runtime-detect branch costs ~10 lines and eliminates the risk of the same script breaking one runtime while serving the other |
| confidence | 60 |
| complexity | Low |
| axis | Logic portability |
| status | Unexplored |

---

## Did not survive (revivable)

| id | title | summary | reason | status |
|----|-------|---------|--------|--------|
| R1 | Mechanical copy of `hooks.json` | Copy `plugins/saga/hooks/hooks.json` structure verbatim into Antigravity saga plugin | `ANTIGRAVITY.md` plugin spec has no hooks section and no `hooks/` directory in the plugin layout. Would be dead config that neither the Antigravity runtime nor the marketplace validator would process. Revive only if Antigravity adds plugin-level hooks with this exact format. | rejected |
| R2 | Hardcode to `main` / `master` only | Simplify the detection logic by assuming `main` or `master` as the default branch | Regression from PR #249's explicit design goal. The source DECISIONS entry (`#stale-main-hook-generalized`) specifically calls out "never hardcoding `main`" as the rationale for generic detection. No basis for reverting this. | rejected |
| R3 | Shell profile hook (`.zshrc` / `.bashrc`) | Register the check as a shell function or alias that runs on terminal open | Outside plugin packaging entirely. Doesn't belong in this repo and can't be managed or distributed via the plugin system. | rejected |
| R4 | Piggyback on CMUX hook infrastructure | Add the stale-check script alongside the existing CMUX `SessionStart` hooks in `~/.gemini/settings.json` | CMUX hooks are Claude Code multiplexer infrastructure, not an Antigravity-native mechanism. Adding plugin behavior inside CMUX's config would be brittle and silently break if CMUX changes its registration path. | rejected |
| R5 | Agent-definition as session-init persona | Create a `plugins/saga/agents/session-init.md` agent that checks git state and is triggered at session start | Antigravity `agents/` are invoked via `invoke_subagent` by skills, not triggered automatically at session open. No evidence of an auto-trigger mechanism for agents in the plugin spec. Would effectively deliver Survivor 3 (skill-preamble) behavior but with more packaging overhead. Revive if Antigravity adds auto-agent-trigger at session start. | rejected |

---

## Co-ideation log

| source | entered | idea / seed | outcome |
|--------|---------|-------------|---------|
| frame-agent | Phase 2 (pain & friction) | Spike the hook contract first | survived as #1 |
| frame-agent | Phase 2 (leverage & compounding) | Port Python to scripts/, deliver via settings hook | survived as #2 |
| frame-agent | Phase 2 (inversion / removal) | Skill-embedded preamble instead of hook | survived as #3 |
| frame-agent | Phase 2 (constraint-flipping) | Separate logic port from delivery, queue the auto part | survived as #4 |
| frame-agent | Phase 2 (assumption-breaking) | Dual-format output for runtime detection | survived as #5 |
| frame-agent | Phase 2 (pain & friction) | Mechanical hooks.json copy | cut → R1 (plugin spec has no hooks section) |
| frame-agent | Phase 2 (inversion / removal) | Simplify branch detection | cut → R2 (regression from source design decision) |
| frame-agent | Phase 2 (constraint-flipping) | Shell profile hook | cut → R3 (outside plugin packaging) |
| frame-agent | Phase 2 (leverage & compounding) | Piggyback CMUX hooks | cut → R4 (brittle, Claude Code-specific infra) |
| frame-agent | Phase 2 (assumption-breaking) | Auto-trigger session-init agent persona | cut → R5 (no auto-trigger mechanism in agent spec) |

---

## Basis References

| ref | path / source |
|-----|--------------|
| Source hook (as changed in PR #249) | `infiquetra-claude-plugins: plugins/saga/hooks/stale_main_session_hook.py` @ df67968 |
| Source hooks manifest | `infiquetra-claude-plugins: plugins/saga/hooks/hooks.json` @ df67968 |
| Source decisions entry | `infiquetra-claude-plugins: docs/engineering-journal/DECISIONS.md` @ df67968 — `#stale-main-hook-generalized` |
| Target plugin spec | `ANTIGRAVITY.md` — plugin layout (no hooks section) |
| Target scripts layout decision | `docs/engineering-journal/DECISIONS.md` — `#consolidate-scripts-src` (2026-05-31) |
| Target port strategy decision | `docs/engineering-journal/DECISIONS.md` — `Porting Claude Plugins` (2026-06-06) |
| Antigravity marketplace learning | `docs/engineering-journal/LEARNINGS.md` — `#agy-marketplace-resolution` (agy reads `~/.gemini/settings.json`) |
| Prior port ideation | `docs/ideation/2026-06-05-port-claude-plugins.md` |
| Observed hook surface | `~/.gemini/settings.json` `hooks.SessionStart` (CMUX hooks, Claude Code origin); `~/.gemini/antigravity-cli/settings.json` (no hooks key) |
| Saga plugin manifest | `plugins/saga/plugin.json` (v1.2.0) |
