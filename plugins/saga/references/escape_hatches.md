# Stuck-loop and break-glass recovery

Saga restores from canonical repository `docs/` artifacts plus machine-local
`.gemini/saga/` coordination state. Native brain artifacts may help diagnose a
stalled interaction, but they are staging projections. Editing a projection
cannot approve a plan, create evidence, or complete a lifecycle transition.

## Scenario 1: Infinite Planner Loop
**Symptoms:** `/plan` keeps rewriting the same `implementation_plan.md` over and over without handing off to execution.
**Cause:** The planner agent detects unresolved "Open Questions" or "User Review Required" alert blocks and blocks progress until the user physically types an answer.
**Safe recovery:**

1. Stop the planner and preserve the brain artifact as diagnostic evidence.
2. Resolve each open question in the canonical repository plan under `docs/`.
3. Record the operator's explicit approval through the current interaction
   surface. A note written into a file is not an approval receipt.
4. Re-run plan validation. Start `/work` only after the canonical plan and its
   approval receipt both pass.

## Scenario 2: The Agent Refuses to Run `/qa`
**Symptoms:** `/work` finished but `/qa` refuses to start or loops, claiming no evidence exists.
**Cause:** The QA parser didn't find the `walkthrough.md` or its visual headers were stripped by the executor.
**Safe recovery:**

1. Stop before QA and identify the missing evidence.
2. Restore the canonical walkthrough from actual work receipts, changed paths,
   and check results. Do not synthesize or relabel evidence.
3. Keep the lifecycle obligation unsatisfied while required evidence is
   missing, unknown, or unavailable.
4. Run `/qa` only after the evidence validator accepts the canonical
   walkthrough.

## Scenario 3: Legacy Path Breakage (Cross-Plugin Confusion)
**Symptoms:** A downstream plugin parses the plan but fails to locate files
because it retained a foreign runtime state path.
**Cause:** The plan was written for a foreign host instead of Antigravity's
logical runtime roles.
**Safe recovery:**

1. Halt the agent execution.
2. Open the active `implementation_plan.md` and `task.md`.
3. Replace the stale path with the doctor-resolved logical role; do not guess a
   machine-specific absolute path.
4. Run the host doctor, then retry only after the corrected artifact passes.

## Safe reset

If recovery still fails:

1. Preserve the canonical repository plan and any validated receipts.
2. Start a new session and run Fleet Doctor before resuming.
3. Load the canonical plan by repository-relative path.
4. Re-establish approval and capability receipts in the new session. Never
   infer approval from copied text or from an earlier brain projection.
