# Ideation Survivors

## 1. Auto-Generated Subway Map & Topography
Instead of manually drawing abstract diagrams that rot, script a dynamic Mermaid subway-style map from real `brain/` artifact states to document the state machine and cross-plugin implicit dependencies.

This completely automates the user's request for "presentation-worthy diagrams" while guaranteeing they never lie about the state machine. Since plugins have deep dependencies on each other's visual states, an auto-generated map based on real artifact handoffs exposes implicit topology safely.

| Field | Value |
| --- | --- |
| **basis** | `direct:` (Journal learning states plugins directly inspect each other's native state folders) |
| **confidence** | 90 |
| **complexity** | Med |
| **axis** | 3. State Machine & Artifact Handoffs |
| **status** | Unexplored |

## 2. The Executable Visual Lexicon Sandbox
Interactive dummy saga execution (`saga --sandbox`) that physically pauses to explain state transitions and the required visual markdown layouts, anchoring new developers directly to native Antigravity state.

This inverts the onboarding process from "read then do" to "do while being explained." It aggressively teaches the "Visual Saga Artifacts" paradigm by showing a new developer exactly how the artifacts mutate in the `brain/` directory during a live, safe run.

| Field | Value |
| --- | --- |
| **basis** | `reasoned:` (Interactive, executable execution is vastly superior to static text for internalizing complex state transitions) |
| **confidence** | 85 |
| **complexity** | High |
| **axis** | 1. Developer Onboarding & Mental Model |
| **status** | Unexplored |

## 3. Visual Handoff Failure Matrix
A table of "visually valid but parse-failing" vs "correct" visual states, teaching operators exactly what visual markdown layout anomalies will silently break the downstream plugins.

This directly grounds the documentation in the reality of visual LLM parsing rather than regex. It protects maintainers from accidentally breaking the state machine when they try to "clean up" the markdown layout, turning silent failures into recognizable patterns.

| Field | Value |
| --- | --- |
| **basis** | `direct:` (Grounding states saga artifacts use visual formatting optimized for human readability, not strict regex) |
| **confidence** | 95 |
| **complexity** | Low |
| **axis** | 3. State Machine & Artifact Handoffs |
| **status** | Unexplored |

## 4. Orchestration Command Dry-Run Diagrams
A presentation-grade reference showing exactly which `brain/` artifacts are consumed, mutated, and emitted by every major CLI command *before* they hit enter.

Without explicit `.claude/` checkpoints to easily revert, executing the wrong orchestration command carries a higher friction cost. Dry-run visual maps remove zero-checkpoint execution anxiety.

| Field | Value |
| --- | --- |
| **basis** | `reasoned:` (Gives operators confidence to use complex orchestration commands by providing a zero-risk preview of the state mutation) |
| **confidence** | 80 |
| **complexity** | Med |
| **axis** | 2. Commands & Lifecycle Orchestration |
| **status** | Unexplored |

## 5. "The Stuck Loop" / Break-Glass Escape Hatch Scenarios
Scenario-based documentation on how to manually unstick a deadlocked saga (e.g. from legacy path migration breaks) by physically overriding the `brain/` artifacts to force a maturity stage transition.

Developers in a multi-agent orchestrated system struggle when the state machine stalls. Documenting the failure modes and how to manually hack the artifacts removes the mystery and panic of a stalled orchestration layer.

| Field | Value |
| --- | --- |
| **basis** | `direct:` (Grounding explicitly lists "legacy path migration breaks" as a known pain point) |
| **confidence** | 90 |
| **complexity** | Low |
| **axis** | 4. Scenarios & Practical Usage |
| **status** | Unexplored |

## Did not survive (revivable)
- **R1:** The "Invisible State" Autopsy Guide — absorbed into The Executable Visual Lexicon Sandbox (Survivor 2) — `rejected`
- **R2:** The "Friction-First" Lifecycle Tour — duplicates stronger idea (Executable Visual Lexicon Sandbox) — `rejected`
- **R3:** The "What We Removed" Contrast-Based Onboarding — too narrow; better handled as a brief note than a dedicated chapter — `rejected`
- **R4:** The "Reverse Engineering" Setup — duplicates stronger idea (Executable Visual Lexicon Sandbox) — `rejected`
- **R5:** Experiential Artifact Tracing Model — duplicates stronger idea (Auto-Generated Subway Map) — `rejected`
- **R6:** Just-In-Time Contextual Orchestration Documentation (`saga doc --current`) — too expensive relative to likely value (requires building new CLI diagnostic tools) — `rejected`
- **R7:** The Runtime "Time-Travel" Visualizer — too expensive relative to likely value — `rejected`
- **R8:** Blueprint-Driven Maturity Progression — too abstract; not actionable enough for immediate documentation — `rejected`
- **R9:** Legacy Path Migration Break-Glass Protocol — absorbed into The Stuck Loop / Break-Glass Escape Hatch Scenarios (Survivor 5) — `rejected`
- **R10:** Narrative Scenario Replay Generator — duplicates stronger idea (Auto-Generated Subway Map) — `rejected`
- **R11:** The Feature "Storyboard" Comic Strip — too expensive/difficult to maintain presentation-worthy comics — `rejected`
- **R12:** Executable Saga Playbooks — absorbed into The Executable Visual Lexicon Sandbox (Survivor 2) — `rejected`
