# Decisions — Infiquetra Claude Plugins

> **ADR-style records of plugin-pattern / convention / tooling choices.** When you commit a chosen path over alternatives — pick A over B, flip a flag, change a threshold, choose a category, adopt a tool — capture rationale + tradeoff + revisit-when condition + commit hash.
>
> The point is to make **revisit conditions explicit** so a future Claude (or human) reading "why did we pick X?" gets the answer cold, including when it would be right to reconsider.
>
> **Append new entries to the top.** Format:
>
> ```markdown
> ## YYYY-MM-DD
>
> ### Short title (commit hash)  {#slug}
>
> **Decision.** What we picked.
> **Rejected alternatives.** What we considered and didn't pick.
> **Rationale.** Why this won.
> **Revisit when.** Condition that would change the calculus.
> **Refs.** Related LEARNINGS / QUEUED / narratives.
> ```
>
> When new evidence invalidates a decision, **update inline AND move the pre-correction version to `ARCHIVE.md` as SUPERSEDED**.

---

## 2026-08-16

### Split the two senses of "objective" rather than purging the word (commit pending)  {#objective-field-not-issue-type}

**Decision.** In mission-control, `objective` as an **issue type** is removed — from `_ISSUE_TYPES`, `_ISSUE_TYPE_LABELS`, `_ISSUE_TYPE_TIER_BANDS`, `_CAPABILITY_ADAPTIVE_TYPES`, both `--type` argparse choice lists, the `rollout gap-analysis` template list, the interactive decision tree, and the prompt/skill/reference docs. `Objective` as a **project board field** and `### Objective` as a **card-body section heading** are kept untouched, including every `objective` key in `config/sdlc-schema.json` and the vendored `config/generated/issue_contract_data.py`. `_apply_post_create_metadata` now raises `RuntimeError` on an unknown or retired type instead of applying whatever labels it finds.

**Rejected alternatives.** Deleting every `objective` string in the plugin (would break the card contract, whose always-required first section is literally `### Objective`, and would force a re-vendor of a generated artifact guarded by a pinned SHA256 oracle). Leaving the type in place as a harmless extra choice (it is offered to operators by the interactive decision tree and by `--type`, so it is not inert — it produces cards no template exists for). Silently dropping unknown types in the metadata step rather than raising (an operator who types a retired type would get a half-configured card and no error).

**Rationale.** One word carried two live meanings and one dead one. Grepping for the word cannot distinguish them, so the retirement had to be done by sense, not by string. The two surviving senses are load-bearing: the field is how Objectives are actually tracked (2026-05-03 decision), and the section heading is the first required field of every actionable card. Verified against the live source of truth rather than memory — `infiquetra-sdlc` `origin/main` ships exactly five issue templates with no `objective.yml`, and its `config/labels.json` has five `title_contains_*` auto-label rules with no objective rule, which is why the documented rule row was removed as fiction rather than migrated.

**Revisit when.** A board contract reintroduces a dated Outcome proof card as a real issue type; that is a new type with its own template, not a revival of `objective`.

**Refs.** [[template-sync-cross-repo-coupling]], `plugins/mission-control/scripts/sdlc_manager.py`, `plugins/mission-control/skills/issues/references/issue-types.md`.

## 2026-08-13

### Approval tables render from the native outcome spec, not an ExecutionSpec  {#approval-table-native-outcome}

**Decision.** The ported `spec_table.py` renders the approval table from Antigravity's committed `docs/outcomes/<id>/outcome-spec.json` via a native `--outcome` mode (`render_outcome`), wired into the `outcome` skill at the `approve`/`advance` dispatch points. Plan step 5 and work-before-execution keep their existing approval surfaces and never author an `ExecutionSpec`.

**Rejected alternatives.** Authoring Claude-lineage `ExecutionSpec` JSONs at plan/work time (violates the plan skill's 5.2a guard); wiring the table to points with no structured spec artifact (renders nothing real).

**Rationale.** An operator cannot approve what they cannot read, but Antigravity's outcome layer owns a different, concurrent-DAG spec schema. The table must render from the artifact that actually exists at each approval gate, without importing the Claude execution path.

**Revisit when.** Antigravity gains an execution-spec authoring flow with its own JSON artifact; then the Claude-source `render` path gets a native producer.

**Refs.** Porting Plan U2/R6, `plugins/saga/scripts/spec_table.py`, `plugins/saga/skills/outcome/SKILL.md`.

### Enforce same-file concurrency safety via compile-time wave conflict halting (commit pending) {#wave-file-collision-halt}

**Decision.** Enforce same-file concurrency safety during execution-spec compilation by computing wave file sets and halting if two concurrent tasks in the same topological barrier wave declare overlapping write paths (`assert_no_wave_file_conflicts`). Unwind the dead runtime `lease_broker` abstraction.

**Rejected alternatives.** Runtime file lease brokers; optimistic file locking during team execution; allowing overlapping file writes within the same barrier wave.

**Rationale.** File collisions during multi-agent team execution are deterministic structural bugs in task decomposition. Detecting and halting during execution plan emission eliminates runtime races, file corruption, and deadlocks without requiring distributed leasing overhead.

**Revisit when.** Dynamic branch-based worktrees allow concurrent modification of the same repository file on distinct Git branches that are reconciled via semantic merge drivers.

**Refs.** Porting Plan U4, U7, `plugins/saga/scripts/execution_spec.py`, `plugins/saga/scripts/team_emitter.py`.

### Bind Claude port plans to origin/main, not working-tree or feature-branch HEAD (commit pending) {#port-plan-origin-main-baseline}

**Decision.** Port plans inventory Antigravity local `origin/main` and Claude local `origin/main`. Working-tree untracked files and a Claude feature-branch HEAD are not source candidates.

**Rejected alternatives.** Treating the current checkout as current when it is behind `origin/main`; pinning `infiquetra-claude-plugins@541b36b9` (`feat(orchestrate): U5`) because it was session HEAD; using an untracked `plugins/hermes-profile-evolution/` copy as the Hermes baseline.

**Rationale.** A stale checkout presents missing files as work to invent, which is worse than a known gap. `541b36b9` is not an ancestor of Claude `origin/main` and is inside the orchestrate non-goal. Antigravity `origin/main` already has the Hermes plugin (`18eaa18` and follow-ups through `e0f08ce`).

**Revisit when.** A port campaign is intentionally bound to a named feature branch that the operator has approved as the source snapshot.

**Refs.** Plan: `docs/plans/2026-08-13-claude-plugins-porting-plan.md`. Review: `docs/reviews/2026-08-13-claude-plugins-porting-plan-doc-review.md`. Learning: `{#stale-wt-untracked-vs-origin}`.

### Schema v2 is additive on the Gemini registry (commit pending) {#models-json-schema-v2-additive}

**Decision.** When porting Claude fleet-core schema v2, add `execution_classes`, `scalar_efforts`, and `root_orchestration_profiles`, plus `resolve_for_runtime()`. Keep Antigravity `models` (`gemini-3.1-pro`, `gemini-3.5-flash`) and `efforts` (`low`/`medium`/`high`/`xhigh`).

**Rejected alternatives.** Replacing `models.json` with Claude's live `fable`/`opus`/`sonnet`/`haiku` vocabulary; importing Codex `lineage_models`/`lineage_efforts`; inventing execution-class aliases (`fast_read`, `deep_reason`, `heavy_refactor`).

**Rationale.** Claude #715 itself treats `models`/`efforts` as the host's live vocabulary and the v2 objects as the portable subset. Antigravity `tier_palette.MODELS` and `CHEAP_MODELS` are derived from the Gemini registry.

**Revisit when.** Antigravity publishes a multi-vendor live model list that should replace Gemini as `models`, or Claude changes the portable class names.

**Refs.** Plan KTD1. Claude `13b02343`. Antigravity `plugins/fleet-core/scripts/fleet_commons/models.json` on `origin/main`.

---

## 2026-07-30

### Use complete current trees and non-authoritative ranking for semantic ports (commit pending) {#semantic-port-ledger-current-tree-ranking}

**Decision.** Govern future Claude and Codex reconciliation through the
schema-versioned semantic ledger at
`docs/ports/<campaign-id>/ledger.yaml`. Discovery combines the historical
Claude delta with complete current-tree manifests for Claude, Codex, and
Antigravity. Every normalized edit packet has exactly one stable candidate
owner. The command boundary permits only commit-bound read operations and the
explicit campaign output.

Store candidate recommendation and operator decision separately. Sort reports
by operator value, Antigravity fit, proof feasibility, inverse maintenance
cost, and stable ID, but never derive an approval, rejection, or hidden row
from those scores. Plain validation fails while any candidate remains pending;
only inventory-only validation permits the reviewed pre-decision packet.

Bind final fit assessments to the fleet-core host contract using only the
promotable receipt digest, capability-catalog digest, and sanitized capability
states. Do not promote paths, hostnames, transcripts, runtime roots, or rich
diagnostics into the ledger.

**Rejected alternatives.** Treating the historical sync marker as current
coverage; diffing only file counts; clustering automatically by path or commit
message; copying the source tree before classification; using a ranking
threshold as an implicit survivor decision; storing a second candidate
database; or attaching raw host diagnostics to campaign evidence.

**Rationale.** A historical marker cannot reveal a current capability that
never existed in its range, including Codex-native behavior. Complete tree
comparison makes those capabilities visible and also exposes Antigravity
behavior that already supersedes a source change. Human-curated stable IDs
keep repeated edits as evidence for one semantic contract. Separate ranking
and decision fields preserve Jeff's authority over every survivor and
non-survivor.

The first campaign applied that contract to 1,475 normalized packets and
curated 80 stable candidates with zero unmatched or duplicate ownership. On
2026-07-30, Jeff recorded the complete mapping: 51 approved survivors, 19
blocked candidates, 8 metadata-only candidates, 1 rejected candidate, and 1
superseded candidate. Unavailable sanitized host capabilities block the 19
affected candidates without promoting hostnames, paths, transcripts, or
diagnostics. A blocked candidate requires a host-capability change before
reconsideration.

The 51 approved survivors only unlock later planning in GitHub issue #15.
They do not authorize migration units, estimates, sequencing, code, or
implementation recommendations.

**Revisit when.** A source repository publishes a stronger signed semantic
manifest that covers history and the complete tree, the host receipt schema
changes, or the operator adopts a different explicit candidate-decision
authority.

**Refs.** Plan:
`docs/plans/2026-07-30-semantic-port-ledger-plan.md`. Campaign:
`docs/ports/2026-07-30-saga-reliability/`. Issue:
`infiquetra/infiquetra-antigravity-plugins#16`.

---

## 2026-07-26

### Antigravity host contract and capability doctor plan decisions (commit pending) {#antigravity-host-contract-plan}

**Decision.** Establish the host contract in fleet-core as a comment-free JSON-compatible, schema-versioned YAML catalog plus a closed Python probe registry, strict `antigravity.capabilities.v1` receipt, and strict `antigravity.host-contract-lint.v1` receipt. Requiredness is consumer-scoped; raw probe outcomes are `passed`, `failed`, `unknown`, or `unavailable`, while consumer evaluation is `passed`, `blocked`, or `degraded`, and only an optional capability with a proven declared fallback may evaluate as `degraded`.

Promotable receipts and ignored local diagnostics are separate contracts. The canonical doctor remains `scripts/validate_plugins.py`; its default repository profile executes no `agy` subprocess, and explicit host observation runs only passive registered probes that can prove they do not refresh credentials, access remote systems, or write durable host state. Saga consumes the fleet-core evaluator directly through its existing shim.

The active-surface linter uses a versioned closed selector and adjacent JSON annotations with stable rules and narrow reasoned classifications rather than broad ignores. Issue #20 remains one capability and one PR because the doctor, remediation, privacy contract, and direct consumer form one acceptance boundary; eight atomic unit commits and focused checkpoints keep it reviewable. Fleet-core, Saga, mission-control, and multi-agent-consensus receive the next non-conflicting minor versions from rebased `origin/main` because all four ship materially changed runtime or instruction behavior.

**Rejected alternatives.** Version allowlists; executable shell commands in catalog data; comments or general YAML features in the JSON-parsed catalog; a PyYAML runtime dependency in fleet-core; one permissive local/promoted receipt; global hostname regexes across every string; default host subprocess observation; implicit or broadly ignored linter surfaces; globally required capabilities; a second doctor CLI; Saga-specific state translation; and coordination-only sub-issues for schema pieces that do not independently satisfy issue #20.

**Rationale.** Runtime behavior, not installed-version identity or prompt wording, is the support boundary. Keeping probe execution closed, default validation deterministic, selectors reviewable, and promotable evidence strict makes the contract safe to reuse, while consumer-scoped evaluation preserves fail-closed Saga and canary gates.

**Revisit when.** Antigravity publishes a stable machine-readable capability API that can replace controlled probes, documents a no-write/no-network observation mode, fleet-core gains an explicit dependency installation contract, the active surface becomes too large for the atomic-unit review boundary, or a future receipt schema needs a breaking semantic change.

**Refs.** Plan: `docs/plans/2026-07-26-antigravity-host-contract-capability-doctor-plan.md`. Requirements: `docs/brainstorms/2026-07-26-antigravity-saga-reliability-system-requirements.md`. Issue: `infiquetra/infiquetra-antigravity-plugins#20`.

---

## 2026-06-27

### Antigravity harness plan decisions (commit pending) {#antigravity-harness-plan}

**Decision.** Plan the Antigravity harness as one integrated v1: a single canonical doctor in `scripts/validate_plugins.py`, repo-local `plugins/*/plugin.json` inventory, read-only host-isolated install checks, saga generic-ask routing through `/loop` plus a narrow router agent, `/doc-review`-scoped Gemini review appliance, static review canaries, and shared cheap-first escalation policy.

**Rejected alternatives.** Keep independent validator entrypoints; add a new `/fix` command; put adversarial review behavior in global context; run live Gemini canaries in CI; make multi-agent consensus the default for routine tasks.

**Rationale.** Runtime truth is the cheapest foundation: if Antigravity cannot see the expected plugin surfaces, prompt tuning cannot fix the failure. Reusing `/loop` and `/doc-review` avoids new command sprawl, while static canaries keep CI deterministic.

**Revisit when.** Antigravity publishes a stronger plugin/hook contract, live `agy` invocation becomes stable enough for optional non-CI review runs, or the canary corpus grows large enough to justify a richer evaluator.

**Refs.** Plan: `docs/plans/2026-06-27-antigravity-harness-plan.md`. Requirements: `docs/brainstorms/2026-06-27-antigravity-harness-requirements.md`. Review: `docs/reviews/2026-06-27-antigravity-harness-requirements-review.md`.

---

## 2026-06-11

### `/impl-spec` and `/product-review` plan decisions (commit pending)  {#impl-spec-product-review-plan}

**Decision.** Introduce 2 new saga skills and extend 1:

1. `/impl-spec` — a 6-stage implementation spec pipeline (Archetype B: multi-stage loop). SKILL.md
   stays under 250 lines; stage protocols go to `references/impl-spec-stages.md`. Uses Antigravity-
   native `define_subagent`/`invoke_subagent` for parallel authoring waves and probe spawning (the
   subagent orchestration IS the core behavior, unlike `/optimize` which delegates fan-out to
   operator-choice).
2. `/product-review` — an off-chain advisory experiment gate (Archetype A: advisory gate). No Python
   scripts; the skill is simple enough that the agent handles logic inline. Simplified from vecu's
   version: no revival ceremony.
3. `/doc-review` — gains a buildability-probe mode (~70 lines additive). Probe mode is highest-
   precedence in classification (explicit request first). No existing behavior modified.
4. Shared reference docs (`buildability-probe-protocol.md`, `lifecycle-closure-matrix-template.md`)
   live at `plugins/saga/references/` (plugin-level, following `formatting-style.md` precedent).
5. Dispatch table grows from 17 → 19 routable commands. Both new entries are off-chain + advisory.

**Rejected alternatives.**
- *Add implementation spec as a mode of `/spec`.* Rejected: would make `/spec` monolithic (the vecu
  `/work-loop` at 621 lines is the cautionary example). `/spec` stays WHAT-only.
- *Add a `product_review.py` script.* Rejected: `/product-review` is simple enough to work without
  one. Premature script — can be added later if revival logic is needed.
- *Probe mode as a separate skill.* Rejected: the probe is a quality gate, not a lifecycle phase. It
  belongs in `/doc-review` as a composable mode, callable independently or by `/impl-spec`.

**Rationale.** Each new skill follows an established archetype (advisory gate or multi-stage loop) to
maintain pattern consistency. The shared reference docs avoid duplication between `/impl-spec` and
`/doc-review`. No scripts means less maintenance surface; no probe skill means the probe is composable.

**Revisit when.** `/product-review` needs revival logic (pulling near-miss ideas from `/ideate`), or
`/impl-spec` needs a crash-recovery checkpoint mechanism beyond the scratch-file approach.

**Refs.** Plan: `docs/plans/2026-06-11-impl-spec-product-review-plan.md`. Requirements:
`docs/brainstorms/2026-06-11-impl-spec-and-product-review-requirements.md`.

---

## 2026-06-09

### Track renamed Hermes plugin repo in Mission Control (commit `eb1c9bd`)  {#mission-control-hermes-plugin-repo-rename}

**Decision.** Update the vendored Mission Control repository mapping to use
`infiquetra-hermes-plugins`, and repair the adjacent syntax corruptions that prevented the mapping
test from collecting.

**Rejected alternatives.**
- *Rely on GitHub redirects.* Rejected: project mapping data is not a clone URL and must match the
  canonical repository name used for board routing.
- *Skip the test because the repo already had syntax corruption.* Rejected: the changed mapping is a
  routing contract, so the local test needed to import before this branch was PR-ready.

**Rationale.** Antigravity carries the same Mission Control board-routing surface as the Claude and
Codex plugin repos. Keeping its vendored repo list current prevents future issue preparation or board
adds from targeting the retired repository identity.

**Revisit when.** Mission Control discovers repositories live instead of using vendored canonical
sets, or Antigravity stops carrying Mission Control as an active plugin.

**Refs.** `plugins/mission-control/config/project-mappings.json`;
`plugins/mission-control/tests/test_project_mappings_resolution.py`.

---

## 2026-06-08

### Adopt shared formatting contract for saga documents (commit pending)  {#adopt-shared-formatting-contract}

**Decision.** Adopt a single, shared formatting contract (`plugins/saga/references/formatting-style.md`) across all saga doc-generating plugins, enforcing clean markdown syntax (such as short paragraphs, lead-with-a-summary, comparative data as tables, and blank-line-separated labels to avoid fatal bold-label collapse).

**Rejected alternatives.**
- *Keep formatting guidelines embedded locally within each individual skill or script.* Rejected: This led to divergent styling rules, drift, and formatting inconsistencies between the different phases of the lifecycle.
- *Rely on raw regex patterns for validation.* Rejected: Generating strict markdown is better validated by structural markdown syntax tests rather than complex and brittle regular expressions.

**Rationale.** A central formatting reference ensures consistency across all generated artifacts (such as plans, specs, strategy files, and reviews). Adding a structural test ensures that these rules are automatically validated and that the formatting contract does not drift.

**Revisit when.** The markdown viewer tools in our runtime environment change, or we adopt a rich web interface that renders structured data instead of markdown files.

**Refs.**
- LEARNINGS [saga formatting parser constraints](#saga-formatting-parser-constraints)
- [formatting-style.md](../../plugins/saga/references/formatting-style.md)
- [test_saga_doc_formatting.py](../../tests/test_saga_doc_formatting.py)

---

## 2026-05-31

### Promote agent and SRE personas to root-level `agents/` directories (commit `41c9a94`)  {#promote-agents-root-layout}

**Decision.** Promote all passive nested personas (e.g. `skills/.../references/personas/`) to active root-level `agents/` directories at each plugin root, adhering strictly to the official layout standard defined in `ANTIGRAVITY.md`.

**Rejected alternatives.**
- *Keep nested markdown personas under `references/personas/`.* Rejected: This violates the official Antigravity plugin layout structure and hides SRE/agent configs, making them passive instead of active subagent definitions.
- *Define agents as raw system prompts inside `plugin.json`.* Rejected: Keeping system prompts inside structured markdown files under `agents/` is infinitely more readable, easier to maintain, and supports clean version control.

**Rationale.** Promoted personas in the root `agents/` directory are automatically discovered and can be natively invoked using the `invoke_subagent` tool. This simplifies subagent definition and orchestration while maintaining repository layout consistency.

**Revisit when.** The Antigravity SDK changes its agent discovery rules or introduces a centralized agents directory at the repository root.

**Refs.** ANTIGRAVITY.md [Plugin Types](ANTIGRAVITY.md#L41-L83).

---

### Consolidate executable scripts in a root-level `src/` directory (commit `41c9a94`)  {#consolidate-scripts-src}

**Decision.** Consolidate all executable python scripts under a root-level `src/` directory within each plugin's folder (such as relocating `unifi` scripts from `skills/unifi-network/scripts/` to `src/`).

**Rejected alternatives.**
- *Leave scripts nested within skill subfolders (e.g., `skills/.../scripts/`).* Rejected: This makes importing shared helper classes and utilities across different skills in the same plugin difficult and results in duplicate code/helpers. It also breaks repository layout consistency.

**Rationale.** Grouping python files under a unified root-level `src/` directory provides a consistent codebase architecture across all CLI-based plugins, simplifies import paths for tests and commands, and mirrors the architecture of other modernized plugins like `sdlc-manager` and `infiquetra-lifecycle`.

**Revisit when.** A plugin requires isolation of python runtimes or dependencies on a per-skill basis.

---

## 2026-05-08

### Adopt uv as canonical dependency sync (commit pending)  {#uv-canonical-sync}

**Decision.** Use uv as the canonical repository dependency sync tool. Track `uv.lock`, install CI dependencies with `uv sync --locked --extra dev`, and run local and CI checks through `uv run`.

**Rejected alternatives.**
- *Keep using pip in CI.* Rejected: it contradicts the desired repository standard and leaves installs unreproducible.
- *Use `uv pip install` without a lockfile.* Rejected: it is still an ad hoc install path and does not satisfy the existing revisit condition for tracking `uv.lock`.
- *Move all dev dependencies to `[dependency-groups]` now.* Rejected: the existing `dev` extra maps directly from the prior `pip install -e ".[dev]"` workflow, so moving dependency ownership would add churn without improving the conversion.

**Rationale.** The repository already has `pyproject.toml` metadata and had a documented revisit condition to track `uv.lock` once uv became canonical. A checked lockfile plus `uv sync --locked --extra dev` makes CI and local development use the same dependency graph.

**Revisit when.** uv stops being the repository development standard, or the project intentionally changes from extras-based dev dependencies to uv dependency groups.

**Refs.** Supersedes the `uv.lock` portion of [gitignore `.claude/` + no `uv.lock`](#gitignore-claude-and-no-uv-lock); archived pre-correction version in [ARCHIVE](ARCHIVE.md#superseded-no-uv-lock-decision).

---

## 2026-05-01

### Gitignore `.claude/`; `uv.lock` decision superseded (commit `4da5705`)  {#gitignore-claude-and-no-uv-lock}

**Decision.** Add `.claude/` to `.gitignore`. The prior decision not to track `uv.lock` is superseded by [Adopt uv as canonical dependency sync](#uv-canonical-sync).

**Rejected alternatives.**
- *Track `.claude/settings.local.json`.* Rejected: file holds per-user permission grants for the Claude Code session. Sharing one user's allowed-tool list would either leak local preferences or get blindly overwritten by the next user. The file is named `.local.json` for a reason.
- *Track `.claude/context/sdlc-plan-state.json`.* Rejected: mid-session orchestration state from `sdlc-manager`. Stale immediately after the session ends; would create misleading commits if pushed.

**Rationale.** `.claude/` content is per-user / per-session by design (settings.local + context state). The earlier `uv.lock` rationale was correct when the repo used ad hoc pip/uv installs, but no longer applies now that uv is the canonical lock-and-install path.

**Revisit when.** Claude Code introduces a *shared* settings file under `.claude/` that's intended to be checked in. At that point, narrow the gitignore from `.claude/` to specifically `.claude/settings.local.json` and `.claude/context/`.

**Refs.**
- DECISIONS [uv canonical sync](#uv-canonical-sync) — supersedes the lockfile portion of this decision.
- LEARNINGS [marketplace registry drift](LEARNINGS.md#marketplace-drift) — same PR (#112).
- ARCHIVE [PR #112](ARCHIVE.md#pr-112-marketplace-fix) — shipped record.
- ARCHIVE [superseded no-uv-lock decision](ARCHIVE.md#superseded-no-uv-lock-decision) — pre-correction record.

---

## Porting Claude Plugins: Hardcoded Script & Native State
**Date:** 2026-06-06
**Commit:** 8fb23bf

**Decision.** To port `saga`, `deploy`, and `mission-control` from Claude to Antigravity, we wrote a single-purpose script (`scripts/port_claude_plugin.py`) instead of a generic CLI framework. Additionally, we completely stripped out the legacy `.claude/` checkpoint syncing logic.

**Rationale.**
1. **Hardcoded > Generic:** We only needed to port three specific, known plugins. Building a generic framework to handle any arbitrary legacy plugin would have been over-engineering, increasing scope without adding value.
2. **Native State Management:** Antigravity natively manages state in its `brain/` directory (via `implementation_plan.md`, `task.md`, `walkthrough.md`). The legacy plugins manually wrote state checkpoints to `.claude/saga/`. Syncing these into Antigravity would have meant fighting the native architecture. We deleted scripts like `scaffold_checkpoint.py` instead.

**Revisit when.** If we find that subagents lose context too quickly without checkpoints, we may need to implement a native Antigravity state checkpointing mechanism.

---

## 2026-07-12 — Ship Ceremony Safety Pack KTDs

**Context.** Porting the ship-ceremony safety pack (issue #346: ceremony hazards, merge watcher, ship undo, operator-confirmed gate) from `infiquetra-claude-plugins` into the antigravity saga plugin. Plan at `docs/plans/2026-07-12-ship-ceremony-safety-pack-plan.md`.

**KTD1 — Strip teardown wiring from ported transition runners.** The claude `ship_ceremony.py` weaves `ship_teardown.register()`/`_close_if_registered()` through the transition runners. Those modules (issue #347, 1245 lines) are out of scope. Ported runners strip all teardown calls; rollback-manifest fields stay. Rejected: port teardown too — doubles scope, explicitly excluded.

**KTD2 — Import safety modules via `sys.path.insert(0, str(SCRIPT_DIR))`.** Matches the claude side's import pattern and the antigravity test-loading convention. Rejected: restructure as a package — existing scripts are standalone files, restructuring is out of scope.

**KTD3 — `ceremony_hazards.py` has no `STATE_DIR`.** Pure probe layer, no sidecar storage. No path adaptation needed for this module.

**KTD4 — `merge_watcher.py` and `ship_undo.py` use `.gemini/saga` state paths.** Change `STATE_DIR = Path(".claude/saga")` to `Path(".gemini/saga")` to match `saga.py:45`. Rejected: import `STATE_DIR` from `saga.py` — the claude modules document "Depends on: nothing" to keep the import graph one-directional; matching that avoids a circular import risk.

**KTD5 — Port `run()` safety wiring, not the teardown transition.** The safety preflights (operator-confirmed gate, hazard detection, merge-watcher validate) are self-contained in `run()`. The `teardown` transition and helper functions are stripped. `TRANSITIONS` stays at 7 entries.

**KTD6 — R23 (already-deleted branch) is a new adaptation, not a claude port.** The claude hazard detection prevents the scenario, but `gh pr merge --auto --delete-branch` can race ahead. The port adds a `git ls-remote` check before deletion; if the remote ref is absent, records `branch_already_deleted: true` and returns success.

---

## 2026-07-30 — Proof-carrying lifecycle obligation contracts

**Context.** GitHub issue #21 establishes the reusable settlement contract used
later by `/outcome`, `/loop`, `/resume`, promotion, deliberation, and
conformance work. Plan:
`docs/plans/2026-07-30-lifecycle-obligation-transition-receipts-plan.md`.

**Decision.** Use strict, JSON-compatible v1 contracts with standard-library
runtime validation. Version 1 is the first supported version; schema-less legacy
and unknown future versions fail closed until an explicit upgrader exists.
Rejected: adding the development-only `jsonschema` package to the installed
plugin.

**Decision.** Keep settlement separate from the generic Saga lifecycle state.
The forward workstream contract treats `/impl-spec` and `/retro` as off-chain
obligations and does not migrate the legacy envelope's historical `retro` value.
Rejected: changing the stored public lifecycle enum inside this contract leaf.

**Decision.** Compute settlement from role-scoped evidence and verify
repository references against real files and SHA-256 digests. Execution, review,
and quality-assurance proof must be independent of the obligation producer;
GitHub facts satisfy only an explicitly typed external obligation. Rejected:
model narration, free-form claims, issue closure, or PR merge as aggregate
proof.

**Decision.** Persist canonical receipts beneath
`docs/outcomes/<outcome-id>/receipts/` using deterministic identities and
atomic create-or-compare writes. Keep `outcome_store.py` as rebuildable cache
and `run_ledger.py` as local telemetry. Rejected: making either host-local
surface a second canonical receipt authority.

**Decision.** Add optional contract and receipt references to outcome nodes
without activating the new completion gate. Full routing remains owned by
GitHub issue #14.

**Revisit when.** Routing integration begins, a v2 schema is required, or the
legacy stored `retro` value is migrated with an explicit compatibility plan.

---

## 2026-08-02 — Keep profile evolution behind producer-owned contracts

**Context.** The Antigravity recovery adapter must distinguish ordinary Team Mimir work from
profile-owned influence without copying the Team Mimir classifier or inventing a Hermes command
schema. The imported producer fixtures pin both contracts and their source provenance.

**Decision.** Antigravity exposes only its native root manifest, command, and skill. Its thin Python
transport verifies the imported fixture digests, executes the active Team Mimir repository's real
`scripts/classify_profile_change.py`, and sends canonical proposal envelopes to
`hermes profile-request` on standard input. Ordinary work never contacts Hermes. A profile-owned or
mixed request may enter live dialogue only when its classifier result names exactly one target.

**Rejected alternatives.** A copied classifier could agree with consumer-owned tests while drifting
from Team Mimir. A hook would claim an Antigravity contract this repository cannot prove. An offline
queue would change chat semantics and target autonomy. A Saga semantic-port ledger would add
campaign machinery unrelated to this one adapter.

**Rationale.** Producer-owned executable conformance makes compatibility independently observable.
The adapter validates transport bounds and closed response shapes but leaves custody, proposal
policy, credentials, routing, and mutation with their owners.

**Revisit when.** Team Mimir or Hermes publishes a new schema version, or Antigravity documents and
this repository proves a native hook contract. Do not infer support from a new field or happy-path
response alone.

**Refs.** Recovery approval binding
`c88d1b592adb68ad782d11bf17cb5e13895c9d9c1c5d8c37b99c9ebb3389e1a6`; compact receipt
`docs/ports/2026-08-01-hermes-profile-evolution/receipt.yaml`.
