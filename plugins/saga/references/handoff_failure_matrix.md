# Visual Handoff Failure Matrix

The Saga plugin orchestration relies entirely on visual markdown layout parsing (by LLM-based tools) rather than strict regex or explicit checkpointing databases. When an artifact is malformed visually, downstream plugins silently fail or misinterpret the state machine. 

This matrix documents explicit "visually valid but parse-failing" layouts vs "correct" visual states.

## The Matrix

| Artifact | Downstream Consumer | Visually Valid but Parse-Failing | Correct Visual State | Why it Fails |
|----------|---------------------|----------------------------------|----------------------|--------------|
| `implementation_plan.md` | `/plan`, `/work` | Wrapping the file path in backticks: ``[NEW] `path/to/file.py` `` | Markdown linked path: `[NEW] [basename](file:///path/to/file.py)` | Markdown link parsers strip formatting differently. Backticks break the Antigravity URL extraction logic. |
| `implementation_plan.md` | `/plan`, `/work` | Grouping without boundaries: `### Auth Changes` | Grouping with visual breaks: `--- \n\n ### Auth Changes` | Visual breaks (horizontal rules) tell the parser where a component cluster ends. Without them, unrelated files bleed into context windows. |
| `task.md` | `/work` | Nested checkboxes without parent state: <br>`- Task Group`<br>&nbsp;&nbsp;`- [ ] Subtask` | Flat or explicitly state-mapped parents: <br>`- [ ] Task Group`<br>&nbsp;&nbsp;`- [ ] Subtask` | The parser looks for leading `[ ]`, `[/]`, or `[x]` tokens to determine node completeness. Missing tokens break progress rollup. |
| `task.md` | `/work` | Using `[-]` or `[~]` for in-progress. | Using `[/]` for in-progress. | `[/]` is the only token registered by the native state tracker for WIP states. |
| `walkthrough.md` | `/qa` | Emitting a dump of git diffs under an `## All Code` header. | Grouping by feature: `## Changes Made` and `## Verification`. | The QA agent looks for explicit human-readable verification steps, not raw diffs. |

## Protective Rules for Operators

1. **Do not format paths:** If you manually edit the `implementation_plan.md`, never wrap the `[file basename](path)` link in backticks.
2. **Respect the Tokens:** Only use `[ ]`, `[/]`, and `[x]` in `task.md`.
3. **Keep Headers Predictable:** While the layout is visual, the top-level section headers (`## Proposed Changes`, `## Verification Plan`) act as anchors. Do not rename them.
