# Antigravity Prompt Systems Review

## 1. Strongest Disagreement
Better prompts alone are insufficient because Gemini's literal and sycophantic tendencies will subvert them unless constrained by structural execution rules like fresh-session isolation, forced first-line disagreement, and explicitly verified file:line citations.

## 2. Evidence Summary
- "Be brutally honest" fails on Gemini because it gets absorbed as a sycophantic answer with a brutal preface (`reference_gemini_prompting_best_practices.md:17`).
- Gemini defaults to `medium` thinking on 3.5 Flash; deep critique requires explicit `thinking_level=high` (`reference_gemini_prompting_best_practices.md:30-33`).
- Constraints placed in the middle of a prompt are often dropped; they must go LAST (`reference_gemini_prompting_best_practices.md:41`).
- In-session agreement drift compounds sycophancy, necessitating a fresh context-free session (`reference_gemini_prompting_best_practices.md:52`).
- A forced first-line disagreement prevents the model from softening its critique (`reference_gemini_prompting_best_practices.md:51`).
- Codex and agy (Gemini) caught non-overlapping P1 findings (e.g., wave scheduling vs. shared state mutation), proving the value of independent, multi-model second opinions (`docs/reviews/2026-06-27-worker-model-cache-scheduling-review.md:21-27`).
- Without file-path data in `Unit`, the proposed segmentation was unbuildable, which both models caught because they were forced to verify against specific files (`agy_docreview2.txt:3`, `codex_prompt.txt:18`).

## 3. Recommended Antigravity Operating Pattern
- **Model choice / thinking level**: Use Gemini 3.1 Pro (High) or explicitly set `thinking_level=high` on 3.5 Flash. Leave temperature at default 1.0. Use explicit task decomposition instead of "think step by step".
- **Fresh session policy**: Run adversarial reviews in a completely fresh session to prevent in-session agreement drift and sycophancy.
- **Project rules vs one-shot prompts**: Put read-only constraints, citation requirements, and operating patterns in durable project rules. Keep the adversarial persona, specific output schema, and file targets as one-shot prompts to avoid poisoning normal generative coding tasks.
- **Skills**: Package the second-opinion and doc-review engines as reusable skills that trigger fresh, read-only sessions with `thinking_level=high`.
- **Read-only review runs**: Restrict the sandbox or agent capabilities to read-only during reviews to prevent hallucinated fixes or premature execution.
- **Evidence/citation requirements**: Demand `file:line` format for all claims. Reject any finding that lacks explicit grounding in the read files.
- **Artifact review**: Use a strict tabular output format for findings (`[Priority] | claim | evidence | fix`) to force terseness and prevent burying the lead.

## 4. Reusable Prompt Templates

### Template 1: Adversarial Plan/Doc Review
```xml
<role>You are a hostile, adversarial peer reviewer. Your sole function is to find defects, gaps, and dangerously assumed claims. You are trying to BREAK the document. Positive notes are out of scope.</role>
<task>
Read the target document and verify its claims against the provided source context. Do not evaluate anything outside the stated text.
</task>
<context>
TARGET DOC: [INSERT_DOC_PATH]
SOURCE FILES TO VERIFY AGAINST:
- [INSERT_FILE_1]
- [INSERT_FILE_2]
</context>
<constraints>
- Read-only analysis. Do not invent fixes or write code.
- Do not agree with any claim without naming one way it could be wrong.
- Evaluate only what is stated; introduce no new ideas. You may draw logical deductions but no outside facts.
- Every claim must be supported by a file:line citation.
- Place all constraints at the end of your instructions.
</constraints>
<output_schema>
FIRST LINE: State your single strongest disagreement with the document in one sentence.
Then enumerate findings, one per line in this format:
[P0|P1|P2|P3] | plan claim or gap | contradicting or missing evidence (file:line) | fix.
</output_schema>
```

### Template 2: Implementation-Plan Critique
```xml
<role>You are a skeptical staff engineer doing a READINESS review of an implementation plan. Your goal is to find what would cause WRONG or BLOCKED implementation.</role>
<task>
Verify the plan claims against the upstream requirements and the existing codebase. The plan must drive implementation without an agent inventing missing decisions.
</task>
<context>
PLAN: [INSERT_PLAN_PATH]
UPSTREAM REQUIREMENTS: [INSERT_REQUIREMENTS_PATH]
SOURCE FILES TO VERIFY:
- [INSERT_FILE_1]
- [INSERT_FILE_2]
</context>
<constraints>
- Check specifically: Are the plan file:line citations accurate? Are there unhandled failure modes?
- Read-only analysis. Cite file:line for every claim.
- Be terse. Output findings only, no summary preamble.
- No hedge language to soften a critique.
</constraints>
<output_schema>
FIRST LINE: Verdict (Advance to execution OR Rework required).
Then enumerate findings:
1. Core assumption failures (file:line).
2. Missing dependencies or unmet requirements (file:line).
3. Single highest-confidence P0 or P1 finding.
</output_schema>
```

### Template 3: Second-Opinion Comparison against Codex
```xml
<role>You are an independent reviewing engineer verifying findings from a prior Codex (gpt-5.5) review. You must confirm or refute its claims based on your own reading of the source.</role>
<task>
Review the target plan and the provided Codex findings. Confirm where Codex is correct, but actively look for false positives or issues Codex missed.
</task>
<context>
PLAN: [INSERT_PLAN_PATH]
CODEX FINDINGS: [PASTE_CODEX_OUTPUT]
SOURCE FILES:
- [INSERT_FILE_1]
</context>
<constraints>
- Do not flatter the prior review. Invite disagreement.
- You must cite file:line for every confirmation or refutation.
- Read-only analysis.
- Do not use loaded negative framing; evaluate strictly on technical merit.
</constraints>
<output_schema>
FIRST LINE: State the most significant error or omission in the Codex review.
Then output:
1. Confirmed Codex findings (with file:line verification).
2. Refuted Codex findings (with file:line contradiction).
3. Net-new findings Codex missed (Priority | claim | file:line | fix).
</output_schema>
```

## 5. Do Not Do
- Do not use "be brutally honest"; it triggers sycophantic agreement with a brutal preface.
- Do not use "think step by step" on Gemini; it suppresses structured reasoning. Use explicit task decomposition instead.
- Do not place constraints in the middle of the prompt; they will be under-weighted or ignored. Always place them last.
- Do not put adversarial or hostile personas in the global system prompt; it degrades normal execution tasks by making the agent combative.
- Do not run adversarial critique in the same session as the generation; it causes agreement drift.
- Do not use loaded negative framing (e.g., "this is obviously wrong, agree?"), as it just shifts the sycophancy to mirror the negative framing.
- Do not allow uncited claims; always force explicit `file:line` verification.
