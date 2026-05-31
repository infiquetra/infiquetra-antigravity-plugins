# Consensus Protocol — team-execution

This file defines the review-revise cycle used in Step B3 of the orchestration protocol.
Read this before running the review cycle to understand scoring, fix routing, and escalation.

---

## Overview

After implementation is complete (Step B2), the **Team Lead** (the main orchestrator agent, Claude/Gemini) coordinates a structured review cycle with all spawned **Reviewers** (the specialized reviewer subagents).

The goal is a mutual consensus agreement between the Team Lead and the Reviewers:
1. **Reviewers** evaluate the implementation and score 5 dimensions. Each reviewer must achieve an overall score of **>= 9.0/10** to signal acceptance.
2. **Team Lead** reviews each reviewer's assessment, verifies that all requested fixes are soundly implemented, and provides the final lead consensus sign-off.
3. The **Human User (Client/Stakeholder)** is **not** part of this consensus loop or the review-revise iterations. They are kept informed of progress and only alerted for severe escalations.

Maximum iterations: **3**. After 3 cycles, proceed with the best available version regardless of scores.

---

## Cycle Structure

```
For iteration 1..3:

  B3a. Spawn all reviewers upfront (warm pooling) with a bootstrap prompt, then dispatch full review tasks via send_message to max 2 concurrent reviewers at a time:
        - Full plan context (what was being built)
        - git diff of all changes made
        - Intended outcome (what success looks like)
        - Path to review-criteria.md for scoring rubrics
        
  B3b. Each reviewer:
        - Scores 5 dimensions (0-10 each)
        - Produces overall score (average of 5 dimensions)
        - Issues verdict: ACCEPT (>= 9.0) or NEEDS REVISION (< 9.0)
        - If NEEDS REVISION: provides specific fix requests
 
  B3c. Collect and display scores:
        Devil's Advocate:      8.7/10 — NEEDS REVISION (2 fixes)
        Security Reviewer:     9.2/10 — ACCEPT
        Architecture Reviewer: 9.4/10 — ACCEPT
        [Optional reviewers if spawned...]
 
  B3d. If ALL >= 9.0 → consensus reached → proceed to Step B4
 
  B3e. Else:
        - Consolidate and deduplicate fix requests from all reviewers scoring < 9.0.
        - Apply Hybrid Fix Routing:
            * Lead-Level Fixes: If minor (formatting, badges, link correction, typos, text search-and-replace), 
              the Team Lead (orchestrator) implements them directly for speed and token savings.
            * Worker Delegation: If complex (logic, stack updates, structural changes), route back to active workers.
        - Keep subagents active! Re-run B3a..B3d for ONLY the reviewers that scored < 9.0
          by sending a re-review message via send_message rather than spawning a new subagent.
          (Reviewers who already ACCEPTED do not re-review).
```
 
After 3 iterations: proceed with best version, document final scores in completion report.
 
---
 
## Concurrency & Rate Limit Mitigation (Warm Session Pooling & Throttled Work Distribution)
 
To prevent `RESOURCE_EXHAUSTED` (429) rate limit errors during high-context or multi-file reviews while eliminating startup latency, the Team Lead must enforce a strict, multi-layered concurrency and quota management protocol:
 
1. **Warm Session Spawning (All Upfront)**:
   - At the beginning of the review phase, spawn ALL confirmed reviewers in a single parallel step using `invoke_subagent`.
   - **Important**: To prevent token quota exhaustion during creation, use a minimal "bootstrap prompt" (e.g., `"You are the [Role] Reviewer. Initialize your session and wait for review instructions."`). This establishes warm, active sessions without triggering parallel LLM execution.
 
2. **Throttled Task Dispatch (Max 2 Active LLM Calls)**:
   - The Team Lead manages the review dispatch queue. Send the full, high-context review task (the git diff, plan context, and review criteria) via `send_message` to a maximum of **2 subagents concurrently**.
   - **Synchronization**: Wait for the active subagents to return their scorecards and verdicts before dispatching work to the next queued reviewers in the pool.

2. **Strict Sequential Fallback**:
   - If any subagent execution triggers a `RESOURCE_EXHAUSTED` (429) rate limit error, the Team Lead must immediately degrade the concurrency limit to **1 (Strict Sequential Mode)**.
   - For the rest of the review cycle, run all remaining subagents strictly one-by-one, waiting for each to complete before starting the next.

3. **10-Second Jittered Backoff Protocol**:
   - When a 429 error is hit, the Team Lead must immediately pause/sleep for **10 seconds** before retrying or calling another tool.
   - This time window allows the API's Token-Per-Minute (TPM) and Request-Per-Minute (RPM) rate windows to clear.
   - Do not invoke file reads, writes, or commands during this backoff period.

4. **Git Diff Context Reduction (Filtering)**:
   - To reduce the token volume ingested by the subagents (which is the primary driver of 429 errors), the Team Lead must filter the git diff to exclude high-volume, non-semantic changes like lockfiles and binaries.
   - Execute the diff with precise command-level path filters:
     ```bash
     git diff -- . ':!*lock*' ':!*.png' ':!*.jpg' ':!*.jpeg' ':!*.ico' ':!*.pdf' ':!*.woff' ':!*.woff2'
     ```
   - Only supply semantic source code and documentation diffs to reviewers.

---

## Active Subagent Reuse Protocol

Launching fresh subagent sessions for re-reviews introduces heavy startup latency and duplicate token overhead. To optimize:
1. **Retain Sessions**: The Team Lead keeps all worker and reviewer subagent sessions active during the Phase B loop.
2. **Re-Review Message Format**: Instead of creating a new agent, send a message to the active reviewer's conversation ID via `send_message`:
   ```markdown
   We have implemented fixes in response to your review feedback.
   
   ## Revisions Made
   [List of changes or git diff showing the new state]
   
   Please re-run your evaluation against the modified code and return your updated scorecard and verdict.
   ```
3. **Shutdown**: Teammates are only sent a `shutdown_request` in Step B4c once the entire process (approval or 3-cycle cap) completes.

---

## Fix Routing & Consolidation

When multiple reviewers flag issues, the Team Lead consolidates and determines the optimal routing path:

1. **Group by File & Severity**: Gather all revision requests.
2. **Triage Routing**:
   - **Lead Fix Path**: If all fixes are simple/textual/documentation changes, the Team Lead patches the codebase directly using standard file editing tools.
   - **Worker Handoff Path**: If any logic is changed, send a structured revision request message to the active worker that originally completed the phase.
3. **Deduplicate**: Ensure no worker is asked to perform the same change twice.
4. **Conflict Resolution**: If two reviewers propose conflicting changes, the Team Lead resolves the conflict using engineering judgment or escalates to the user.

---

## Score Display Format

Display scores in this format after each review cycle:

```
## Review Cycle [N] Results

| Reviewer | Score | Verdict | Issues |
|----------|-------|---------|--------|
| Devil's Advocate | 8.7/10 | NEEDS REVISION | 2 fixes |
| Security Reviewer | 9.2/10 | ACCEPT | — |
| Architecture Reviewer | 9.4/10 | ACCEPT | — |
| Infra Reviewer | 8.0/10 | NEEDS REVISION | 3 fixes |

Consensus: NOT REACHED — proceeding to fixes
```

---

## After 3 Cycles

If consensus is not reached after 3 iterations:

1. Proceed to Step B4 (Completion) with the current best version
2. Document final scores in the completion report:
   ```
   Note: Consensus not reached after 3 review cycles.
   Final scores: DA=8.8, Security=9.4, Architecture=9.1, Infra=8.3
   Unresolved issues: [list remaining fix requests]
   ```
3. Flag to user: "3-cycle cap reached. The following issues were not resolved and may need follow-up."

---

## Reviewer Context Template

When spawning reviewers in Step B3a, provide this context:

```
You are reviewing the implementation of the following plan:

## Plan Summary
[1-3 sentence description of what was being built]

## Intended Outcome
[What success looks like — what should work after this change]

## Changes Made
[git diff or summary of files changed]

## Review Instructions
Score the implementation against your 5 dimensions from:
team-execution/skills/team-execution/references/review-criteria.md

Produce your score table, verdict, and fix requests (if NEEDS REVISION).
```

---

## Escalation

If a reviewer scores a dimension < 5.0 (severe), immediately:

1. Flag to user (do not wait for cycle to complete)
2. Pause other reviewers if the severe issue would affect their review scope
3. Route the fix to the responsible worker with high priority
4. Resume review cycle after fix is implemented

A score < 5.0 on any security or auth dimension is treated as a **blocking stop** — no
completion until that dimension reaches >= 7.0.
