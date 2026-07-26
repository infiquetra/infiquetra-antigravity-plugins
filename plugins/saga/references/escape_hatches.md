# "The Stuck Loop" / Break-Glass Escape Hatch Scenarios

Saga is an orchestration layer running over LLM interactions. Sometimes, the state machine stalls due to misinterpretation, legacy path migration breaks, or invalid markdown formatting in the brain artifacts. 

Saga restores from repository `docs/` artifacts plus machine-local
`.gemini/saga/` state. Native brain artifacts may help diagnose a stalled
interaction, but manually editing them is not a durable Saga transition.

## Scenario 1: Infinite Planner Loop
**Symptoms:** `/plan` keeps rewriting the same `implementation_plan.md` over and over without handing off to execution.
**Cause:** The planner agent detects unresolved "Open Questions" or "User Review Required" alert blocks and blocks progress until the user physically types an answer.
**The Escape Hatch:**
1. Open the `.gemini/antigravity/brain/<conversation-id>/implementation_plan.md` file locally.
2. Manually delete the `## Open Questions` and `## User Review Required` sections.
3. (Optional) Add a line at the top: `> [!NOTE]\n> The operator has manually approved this plan.`
4. Execute `/work` to force the state machine into the execution phase.

## Scenario 2: The Agent Refuses to Run `/qa`
**Symptoms:** `/work` finished but `/qa` refuses to start or loops, claiming no evidence exists.
**Cause:** The QA parser didn't find the `walkthrough.md` or its visual headers were stripped by the executor.
**The Escape Hatch:**
1. Manually create or open `walkthrough.md` in the current brain directory.
2. Ensure it has the exact `## Changes Made` and `## Verification` headers.
3. Add a single line under Verification: "Changes were manually verified by the operator."
4. Execute `/qa`.

## Scenario 3: Legacy Path Breakage (Cross-Plugin Confusion)
**Symptoms:** A downstream plugin parses the plan but fails to locate files
because it retained a legacy Claude state path.
**Cause:** The plan was written for a foreign host instead of Antigravity's
logical `.gemini` roles.
**The Escape Hatch:**
1. Halt the agent execution.
2. Open the active `implementation_plan.md` and `task.md`.
3. Replace the stale path with the doctor-resolved logical role; do not guess a
   machine-specific absolute path.
4. Run the host doctor, then retry only after the corrected artifact passes.

## Safe Reset (The Final Hatch)
If all else fails, you can cleanly sever the orchestrator from its state loop without losing your work:
1. Copy the current `implementation_plan.md` to a safe location (e.g., your Desktop).
2. Start a brand new conversational session (which mints a fresh, empty `brain/` directory).
3. Paste the contents into the new chat: "Here is an approved implementation plan, execute it immediately without planning: \n\n <plan text>"
