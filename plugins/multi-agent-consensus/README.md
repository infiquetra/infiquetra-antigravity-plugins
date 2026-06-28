# multi-agent-consensus

Native Antigravity multi-agent consensus workflow. Spawns parallel workers and reviewers with a 0-10 scoring loop and automatic fix routing.

This plugin provides a structured workflow for executing non-trivial plans. The main agent acts as the Team Lead, delegating work to specialized subagents and running a strict review cycle before calling the work complete.

---

## Quick Start

```
/multi-agent-consensus
```

Or provide a plan directly:
```
/multi-agent-consensus [paste plan here or provide file path]
```

When triggered, the main agent will read your plan and automatically execute it using the consensus workflow.

---

## How It Works

This skill leverages Antigravity's native `invoke_subagent` and `send_message` tools to orchestrate a team.

```
Step 1: Worker Kickoff
  → The main agent breaks the plan into independent streams.
  → Spawns parallel worker subagents using `invoke_subagent`.
  → Workers implement the code.
  → Main agent waits for completion (via native reactive wakeups).

Step 2: Reviewer Kickoff
  → Main agent filters the git diff (ignoring lockfiles/binaries).
  → Spawns Reviewer subagents (Security, Architecture, Devil's Advocate, etc.).
  → Reviewers evaluate the diff against strict rubrics and score 0-10.

Step 3: Consensus Cycle (Max 3 Iterations)
  → If ALL reviewers score >= 9.0: Consensus reached! Done.
  → If ANY reviewer scores < 9.0:
      → Minor fixes: Main agent applies them directly to save time.
      → Major fixes: Main agent sends feedback to the original worker subagent.
      → Code is updated.
      → Main agent sends the new diff back to the active reviewers who scored < 9.0.
      → Cycle repeats.

Step 4: Completion
  → Main agent presents a final report with scores, verdicts, and any unresolved issues.
```

---

## Reviewer Personas

### Always Included

| Reviewer | Focus |
|----------|-------|
| Devil's Advocate | Assumptions, edge cases, failure modes, scope creep |
| Security Reviewer | OWASP Top 10, secrets, auth/authZ, PII |
| Architecture Reviewer | Design patterns, separation of concerns, convention adherence |

### Optional Additions

Depending on the plan content, the main agent may also pull in personas like:
- 🔵 **Infra Reviewer** (CDK, Lambda, AWS)
- 🟢 **API Reviewer** (REST, OpenAPI)
- 🟡 **Testing Reviewer** (pytest, coverage, mocks)
- 🩵 **Code Quality Reviewer** (DRY, SOLID, complexity)
- 🩷 **Privacy Reviewer** (GDPR, retention)

These personas are stored in `skills/multi-agent-consensus/references/personas/` and are injected into the subagent's system prompt at invocation time.

---

## Consensus Protocol

All reviewers must score **>= 9.0/10** to reach consensus.

If consensus is not reached, fix requests are consolidated and routed to workers (or applied by the Team Lead directly if minor). Only reviewers that scored < 9.0 re-run in the next iteration. Maximum 3 iterations.

After 3 cycles, execution proceeds with the best available version and documents any unresolved issues.

**Hard stop**: Any security or auth dimension scoring < 5.0 is treated as a blocking issue and flags to the user immediately.

### Reference Files
- `multi-agent-consensus/skills/multi-agent-consensus/references/reviewer-registry.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/review-criteria.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/consensus-protocol.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/validator-registry.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/validator-criteria.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/validator-execution-order.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/validator-evidence-state.md`
- `multi-agent-consensus/skills/multi-agent-consensus/references/validator-spawn-quirks.md`
