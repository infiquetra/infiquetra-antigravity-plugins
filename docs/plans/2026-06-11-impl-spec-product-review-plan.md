---
title: Implementation Spec Pipeline and Product Review
type: feat
status: active
date: 2026-06-11
origin: docs/brainstorms/2026-06-11-impl-spec-and-product-review-requirements.md
deepened: 2026-06-11
---

# Implementation Spec Pipeline and Product Review

## Summary

Add two new saga skills (`/impl-spec`, `/product-review`), a buildability-probe mode to `/doc-review`,
two shared reference docs, and dispatch table updates. The total change is 7 new files, 2 modified
files, 0 scripts.

## Problem Frame

Context-library repos need multi-document spec sets (5-25K lines across 8+ folders) that the existing
single-doc `/spec` skill cannot produce. The campps methodology proved a 6-stage pipeline works but
exists only as prose. Separately, the lifecycle lacks a structured "should we experiment first?" gate.
See the requirements doc for the full problem frame.

## Requirements

From `docs/brainstorms/2026-06-11-impl-spec-and-product-review-requirements.md`:

- R1-R11: `/impl-spec` skill (6-stage pipeline, parallel subagent authoring, configurable interaction,
  schema discovery, off-chain, bounded probe-remediation loop)
- R12-R16: `/product-review` skill (off-chain advisory gate, riskiest assumption, experiment routing,
  threshold enforcement)
- R17-R21: Buildability probe mode in `/doc-review` (fresh subagent, forced enumeration, boundary test,
  hard verdict)
- R22-R23: Shared reference docs (probe protocol, lifecycle closure matrix template)
- R24-R25: Lifecycle integration (dispatch table entries, routing chain updates)

## Key Technical Decisions

KTD1. **`/impl-spec` SKILL.md stays under 250 lines; stage protocols go to `references/`.** The
6-stage pipeline is complex. The SKILL.md carries the orchestration skeleton (phases, gates, routing),
while `references/impl-spec-stages.md` carries per-stage entry/exit criteria, the authoring subagent
system prompt template, and the schema-discovery protocol. This follows the founder-review pattern
(240-line SKILL.md + 2 reference files totaling ~22K).

KTD2. **Shared reference docs live in `plugins/saga/references/`, not in a skill-specific
`references/` directory.** `buildability-probe-protocol.md` and `lifecycle-closure-matrix-template.md`
are consumed by both `/impl-spec` and `/doc-review`. Placing them at plugin level follows the
`formatting-style.md` and `operator-choice.md` precedent.

KTD3. **`/doc-review` modification is additive.** A new `## Buildability Probe Mode` section is
inserted after the existing `## Classification` section. The probe-mode classification is added to the
Classification precedence list. No existing behavior is changed. Total file grows from 199 to ~270
lines.

KTD4. **`/product-review` follows the Archetype A (advisory gate) pattern.** Linear phases: enter →
analyze → produce artifact → route. Off-chain, no saga write. Artifact goes to
`docs/product-reviews/`. Follows the founder-review structural conventions (frontmatter, core
principles, phased structure, hard boundary, reference files section).

KTD5. **No new Python scripts.** The vecu `/product-review` has `scripts/product_review.py` for
revival computation and routing. For Infiquetra, the `/product-review` skill is simple enough that the
agent handles the logic inline (name assumption, design experiment, set threshold, route). Adding a
script would be premature — the skill can be upgraded later if revival logic is needed.

KTD6. **`/impl-spec` uses Antigravity-native subagent fanout, not operator-choice backends.** The
skill itself calls `define_subagent` and `invoke_subagent` for parallel authoring waves and probe
spawning. This is different from `/optimize` (which delegates fan-out to operator-choice). The
rationale: `/impl-spec`'s subagent orchestration IS the core behavior, not an optional acceleration.

KTD7. **Dispatch table grows from 17 to 19 routable commands.** Both new entries are off-chain +
advisory. `/impl-spec` parallels `/spec` (off-chain spec engine). `/product-review` parallels
`/founder-review` (off-chain review gate). Neither carries a hard routing gate.

## Implementation Units

### U1. Shared reference docs

**Goal:** Create the two shared reference docs that `/impl-spec` and `/doc-review` will load.

**Files:**
- `plugins/saga/references/buildability-probe-protocol.md` (new, ~80-100 lines)
- `plugins/saga/references/lifecycle-closure-matrix-template.md` (new, ~60-80 lines)

**Approach:** Author `buildability-probe-protocol.md` from the campps narrative's probe protocol
sections: boundary test definition, probe input constraints (exactly what the probe subagent receives
and does NOT receive), forced enumeration requirement (every category must be enumerated — empty
categories declared explicitly), per-question boundary-test classification protocol (reasoning +
verdict per question), and the hard verdict rule (PASS only at zero defects; fix the spec, never the
probe). Author `lifecycle-closure-matrix-template.md` from the campps closure matrix sections: the
entity × lifecycle-operation matrix template with column definitions (origination, mutation,
revocation/termination, reads, events, audit, LWW verdict/conflict strategy, retention, re-grant
rules) and the blank-or-contradictory-cell-is-defect rule.

**Dependencies:** None. This unit has no dependencies on other units.

**Test scenarios:**
- `tests/unit/test_reference_docs.py`: Validate both reference docs exist, contain required section
  headers (boundary test definition, probe input constraints for probe-protocol; column definitions,
  defect rule for closure-matrix), and have no broken internal markdown links.

---

### U2. `/product-review` skill

**Goal:** Create the off-chain advisory gate skill for experiment-vs-full-build decisions.

**Files:**
- `plugins/saga/skills/product-review/SKILL.md` (new, ~150-180 lines)
- `plugins/saga/skills/product-review/references/product-review-template.md` (new, ~40-60 lines)

**Approach:** Follow Archetype A (advisory gate) from founder-review. Structure:

- Frontmatter: `name: product-review`, description with triggers ("product review", "is this worth
  building", "should we prototype or build", "what's the riskiest assumption").
- Position in lifecycle: between ideate/brainstorm and spec/plan. Off-chain, no saga write.
- Core principles (4): riskiest assumption first; smallest build-to-learn; metric needs threshold;
  premise check is a real gate.
- Phase 0 — Enter: accept input from any lifecycle point (ideation doc, brainstorm output, direct ask,
  issue reference). If no input, ask.
- Phase 1 — De-risk: per idea/proposal: (a) riskiest assumption, (b) smallest experiment, (c) success
  metric + threshold, (d) premise check.
- Phase 2 — Route: experiment → `/plan` with experiment scope; full build → `/brainstorm`; park → with
  "worth it when" trigger. Require concrete threshold before routing to experiment.
- Phase 3 — Persist + route: write `docs/product-reviews/YYYY-MM-DD-<topic>-product-review.md` per
  template. Follow formatting contract. Route onward.
- Hard boundary: no implementation, no commits, no saga, no SDLC issues.
- Reference files section.

Template (`references/product-review-template.md`): frontmatter (date, topic, source), per-idea
section (riskiest assumption, build-to-learn, metric + threshold, premise check), routing table
(idea × route × rationale), post-write checklist.

**Key difference from vecu:** No `product_review.py` script (no revival logic, no route computation
script). No `AskUserQuestion` tool call (Antigravity uses `ask_question`). No vecu-specific paths.
Simplified from vecu's 196 lines — no revival ceremony (Phase 0.2 in vecu), since Infiquetra's
`/product-review` is callable from anywhere, not specifically from `/ideate` survivors.

**Dependencies:** None.

**Test scenarios:**
- `tests/unit/test_product_review_skill.py`: Validate SKILL.md has required frontmatter fields
  (`name`, `description`), contains core principles section, has a hard boundary section, references
  the formatting-style contract, and the template file exists.

---

### U3. `/impl-spec` skill

**Goal:** Create the 6-stage implementation spec pipeline skill for context-library repos.

**Files:**
- `plugins/saga/skills/impl-spec/SKILL.md` (new, ~220-250 lines)
- `plugins/saga/skills/impl-spec/references/impl-spec-stages.md` (new, ~200-250 lines)
- `plugins/saga/skills/impl-spec/references/authoring-subagent-prompt.md` (new, ~60-80 lines)

**Approach:** Follow a hybrid of Archetype A (advisory, off-chain) and Archetype B (multi-stage loop
with crash-safe state). Structure:

SKILL.md:
- Frontmatter: `name: impl-spec`, description with triggers.
- Position in lifecycle: consumes settled WHAT from brainstorm/spec/issue; produces multi-document spec
  folder sets; routes to `/doc-review` (probe) and `/work` (build).
- Core principles (5): generalized method, project-specific schema; schema discovery not configuration;
  class-closure at authoring time; buildability probe as the hard gate; off-chain, no saga write.
- Phase 0 — Enter + schema discovery: accept target directory, discover spec schema from README folder
  contract table. Ask operator for autonomous vs interactive mode.
- Phase 1 — Research: compile grounding brief (settled decisions, entity inventories, cross-spec
  obligations, divergences, open questions with recommended resolution + cost-of-deciding-wrong). In
  interactive mode, pause for operator to decide open questions.
- Phase 2 — Author (parallel waves): derive wave ordering from schema (default: all Wave 1 if no
  dependencies declared). Spawn authoring subagents via `invoke_subagent` with system prompt from
  `references/authoring-subagent-prompt.md`. Enforce class-closure disciplines (load
  `../../references/lifecycle-closure-matrix-template.md`). In interactive mode, pause for operator to
  review closure matrix.
- Phase 3 — Assemble: rewrite the service/spec-set README last.
- Phase 4 — Verify: completeness checklist, link resolution, cross-document count consistency,
  optional validators (OpenAPI, Mermaid).
- Phase 5 — Review: security/access-control lens + consistency/standards lens. P0/P1 fixed before
  probe.
- Phase 6 — Probe+Remediate: invoke `/doc-review` probe mode. If FAIL, spawn remediation subagents
  (class-level fix, not line-level). Re-invoke with fresh probe subagent. Bounded at 3 rounds.
  Escalate on round 3 failure. In interactive mode, operator answers boundary-test failures.
- Progress checkpoint: write a scratch checkpoint file after each stage so a crashed session can resume
  (per R11).
- Hard boundary: no commits, no pushes, no saga write. Output is spec folder set on disk.
- Reference files section.

`references/impl-spec-stages.md`: per-stage entry/exit criteria, the schema-discovery parsing protocol
(how to read a folder contract table from a README), grounding brief structure, verification checklist
format, review lens protocols.

`references/authoring-subagent-prompt.md`: the system prompt template for authoring subagents —
includes the folder assignment, the class-closure disciplines to enforce, the formatting contract to
follow, and the cross-reference conventions.

**Dependencies:** U1 (shared reference docs — probe protocol and closure matrix template).

**Test scenarios:**
- `tests/unit/test_impl_spec_skill.py`: Validate SKILL.md has required frontmatter, contains all 7
  phases (0-6), references the shared probe protocol and closure matrix template by path, has a hard
  boundary section, and all referenced `references/` files exist.

---

### U4. Buildability probe mode in `/doc-review`

**Goal:** Add a buildability-probe mode to the existing `/doc-review` SKILL.md.

**Files:**
- `plugins/saga/skills/doc-review/SKILL.md` (modified, ~199 → ~270 lines)

**Approach:** Additive changes only — no existing behavior modified.

1. **Classification update** (line ~29-52): Add to the precedence list:
   - After item 1 (explicit user command context): "Explicit buildability-probe request → run the
     buildability probe mode (below)."
   - After item 2 (known SDLC paths): "Multi-document spec sets (multiple folders with markdown specs
     and contract files) → offer buildability-probe mode."

2. **New section: `## Buildability Probe Mode`** (insert after `## Classification`, before
   `## Formal SDLC Rubric Review`): ~60-70 lines covering:
   - When triggered (operator request, `/impl-spec` invocation, multi-document spec classification)
   - Probe subagent creation via `define_subagent` + `invoke_subagent`: the subagent receives ONLY the
     spec folder set and shared standards; the system prompt loads
     `../../references/buildability-probe-protocol.md` as first-class instructions
   - Input constraints: no authoring context, no prior probe artifacts, no remediation notes
   - Probe artifact structure: implementation breakdown, assumptions-and-questions enumeration,
     per-question boundary-test classification
   - Hard verdict: PASS at zero boundary-test defects; FAIL otherwise
   - Probe artifact path: `docs/reviews/YYYY-MM-DD-<subject>-buildability-probe[-rN].md`
   - When invoked by `/impl-spec`: return structured result (PASS/FAIL + finding list) so `/impl-spec`
     can drive remediation

3. **Existing sections unchanged:** Formal SDLC Rubric Review, Readiness-Skeptic Pass, Safe In-Place
   Fixes, Findings, Durable Review Artifacts, Loop And Work Integration, Output Shape — all untouched.

**Dependencies:** U1 (shared reference docs — probe protocol).

**Test scenarios:**
- `tests/unit/test_doc_review_probe_mode.py`: Validate SKILL.md contains the "Buildability Probe
  Mode" section header, references the `buildability-probe-protocol.md` shared reference, contains
  `define_subagent` and `invoke_subagent` instructions, and the existing section headers are still
  present (no regressions).

---

### U5. Dispatch table and lifecycle integration

**Goal:** Add both new skills to the dispatch table and update routing references.

**Files:**
- `plugins/saga/skills/loop/references/dispatch-table.md` (modified, ~159 → ~175 lines)

**Approach:**

1. **Update the count** (line 3-4): "17 routable commands" → "19 routable commands". Update the
   command list to include `/impl-spec` and `/product-review`.

2. **Stub-vs-shipped table** (line 21-38): Add two rows:
   - `| /impl-spec | shipped | advisory + off-chain — never block |`
   - `| /product-review | shipped | advisory + off-chain — never block |`

3. **Cold-start table** (line 46-57): Add one row:
   - `| "Should we prototype this?" / experiment-vs-build question | /product-review |`
   - `/impl-spec` doesn't have a cold-start entry — it's always invoked explicitly on a target
     directory, never from a bare ask.

4. **Off-chain commands table** (line 88-99): Add two rows:
   - `| Multi-document spec set authoring for context-library repos | /impl-spec | advisory, shipped
     (off-chain) |`
   - `| "Should we prototype or build?" / experiment-vs-full-build decision | /product-review |
     advisory, shipped (off-chain) |`

5. **Add `/product-review` routing note** after the `/founder-review` note (line ~101-103):
   `/product-review` fires as an experiment gate and produces experiment-ready or full-build-ready
   routing — experiment → `/plan`; full build → `/brainstorm`. It is off-chain and does not write the
   saga.

**Dependencies:** U2 (`/product-review`), U3 (`/impl-spec`) — the dispatch table references shipped
skills.

**Test scenarios:**
- `tests/unit/test_dispatch_table.py`: Validate dispatch table lists 19 commands, contains entries for
  both `/impl-spec` and `/product-review`, and the count in the header matches the actual number of
  entries in the stub-vs-shipped table.

## Scope Boundaries

**In scope:**
- SKILL.md files for `/impl-spec` and `/product-review`
- Reference files for both new skills
- Two shared reference docs at plugin level
- Buildability-probe mode addition to `/doc-review`
- Dispatch table updates

**Explicitly out of scope:**
- Python scripts — no new scripts (KTD5)
- Modifying existing `/spec` — stays as-is
- Modifying existing `/loop` SKILL.md — only its dispatch-table reference changes
- Tests beyond structural validation — behavioral tests require actually running the skills
- plugin.json changes — skills are auto-discovered from the `skills/` directory
- Rubric engine extensions — `/doc-review`'s probe mode is instruction-based, not rubric-based

## Deferred to Follow-Up Work

- `/impl-spec` crash-recovery checkpointing mechanism (the plan identifies the scratch-file approach
  per R11 but the detailed checkpoint format is left to `/work`)
- Revival logic for `/product-review` (the vecu version has revival ceremony; Infiquetra defers this
  until there's empirical evidence it's needed)
- New rubric phase for `saga/references/rubrics/plan/` — useful but separate from this work

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `/impl-spec` SKILL.md exceeds 250 lines | Medium | Low — readability | Stage protocols are in references; SKILL.md is the skeleton only |
| `/doc-review` probe mode interacts unexpectedly with existing classification | Low | Medium — wrong review type runs | Probe mode is highest-precedence in classification (explicit request first) |
| `define_subagent` isolation insufficient for probe freshness | Low | High — probe catches its own authoring bugs | Test empirically on first `/impl-spec` run; document finding in LEARNINGS.md |

## Unit Dependency Order

```
U1 (shared refs) → U3 (/impl-spec) → U4 (/doc-review probe mode)
                → U4 (/doc-review probe mode)
U2 (/product-review) — independent
U5 (dispatch table) — depends on U2 + U3 being complete
```

**Recommended execution order:** U1 → U2 (parallel with U3) → U4 → U5

This is parallelizable: U1 first (no deps), then U2 and U3 in parallel (U2 has no deps; U3 depends on
U1), then U4 (depends on U1), then U5 (depends on U2 + U3).
