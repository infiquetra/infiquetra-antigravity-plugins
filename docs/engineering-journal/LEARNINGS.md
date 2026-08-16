# Learnings — Infiquetra Claude Plugins

> **Empirical findings + mechanisms + fixes + validations.** When something turns out to be true that wasn't obvious — about a plugin's runtime behavior, the marketplace registry, hook timing, skill activation, MCP env propagation, build/test tooling, or a deploy gotcha — it goes here. Include the **evidence** (PR / commit / file:line / reproduction) and the **mechanism** (why it's true), not just the observation.
>
> **Append new entries to the top.** Most-recent first. Format:
>
> ```markdown
> ## YYYY-MM-DD
>
> ### Short descriptive title  {#slug}
>
> **Context.** One paragraph framing the situation.
> **Evidence.** Specific PR / commit / file:line / reproduction recipe.
> **Mechanism.** Why it happened (or why it's true) — root cause, not just symptoms.
> **Fix (or queued).** Concrete action + commit hash, OR a QUEUED.md ref if deferred.
> **Validation (if applicable).** What later run / test / install proved the fix.
> **What surprised (optional).** The thing that wasn't in the original mental model.
> **Generalizable rule.** The lesson stripped of this specific incident — what would I tell a future-me hitting a similar shape?
> **Refs.** Cross-links to DECISIONS / QUEUED / narratives / other LEARNINGS entries.
> ```
>
> The `{#slug}` HTML anchor on the entry title makes the entry linkable from `README.md` quick-nav and from cross-references. Keep slugs short and stable.
>
> When new evidence invalidates a learning, **update inline AND move the pre-correction version to `ARCHIVE.md` as SUPERSEDED**. Never silently overwrite.

---

## 2026-08-16

### A cross-repo generated doc turns a sibling repo's merge into this repo's red test  {#template-sync-cross-repo-coupling}

**Context.** Porting the `hermes-task` / `hermes-not-actionable` retirement from `infiquetra-claude-plugins` (commit `bfc4ac67`) into mission-control. Before touching a single file, the baseline test run was already red — one failure, in a suite nobody here had changed.

**Evidence.** `uv run python -m pytest -q` on a clean `main` at `18164bc`: 1768 passed, 1 failed. The failure was `plugins/mission-control/tests/test_template_sync.py::test_generated_reference_matches_checked_in_file`, whose diff read `- bility\`, \`needs-plan` / `+ bility\`, \`hermes-task\`, \`needs-plan`. Nothing in this repo had moved; `infiquetra-sdlc` had. Its five issue templates on `origin/main` now carry `labels: ["capability", "needs-plan"]` with both markers gone.

**Mechanism.** `plugins/mission-control/scripts/sync_template_docs.py` renders `skills/issues/references/templates-reference.md` by reading the canonical GitHub issue templates *live* out of `$INFIQUETRA_SDLC_PATH` (default `~/workspace/infiquetra/infiquetra-sdlc`). The checked-in reference is therefore a function of another repository's working tree. When the sibling repo merged the paired label removal, this repo's regenerate-and-diff test started comparing fresh output against a stale committed file. In CI the same test skips, because the sibling checkout does not exist there — so the coupling is invisible to CI and visible only to whoever has both repos on disk.

**Fix.** Ported the change and regenerated: `uv run python plugins/mission-control/scripts/sync_template_docs.py`. The regenerated `templates-reference.md` came out byte-identical to the Claude plugin's post-change copy (both at blob `ac056f6`), which is a free cross-implementation check that the two renderers agree.

**What surprised.** The red test was a *correct* signal pointing at work not yet done, not a broken test — and it had been sitting there since the sibling repo merged. A baseline run before editing is what separated "pre-existing failure caused by the sibling repo" from "I broke this."

**Generalizable rule.** Always capture a full baseline test run before starting a port, and treat any generator that reads outside its own repository as a scheduled failure with no owner: it goes red on a *sibling repo's* merge, on the machine of whoever happens to have both checkouts, and never in CI. When you find one, record which sibling commit it tracks — otherwise the next person reads a confident local failure as their own regression.

**Refs.** `plugins/mission-control/scripts/sync_template_docs.py::render_reference`, `plugins/mission-control/tests/test_template_sync.py`.

## 2026-08-13

### Doctor `install=missing` can be a dangling host symlink, not a missing plugin  {#doctor-dangling-symlink}

**Context.** `scripts/validate_plugins.py --strict-install` reported `hermes-profile-evolution: install=missing` while the plugin directory existed in both the repo and the host install root.

**Evidence.** `~/.gemini/config/plugins/hermes-profile-evolution` was a symlink to a since-deleted worktree path (`infiquetra-antigravity-plugins-worktrees/profile-evolution-g3-e0f08ce/...`). `inspect_install` checks `install_path.exists()`, which returns False for a dangling symlink, so the doctor read it as not installed.

**Fix.** Repointed the host symlink at `plugins/hermes-profile-evolution` in the working repo (the same shape as the `fleet-core` link). Doctor returns `status: ok`.

**Generalizable rule.** When the plugin doctor reports `install=missing` for a plugin that demonstrably exists in the repo, check `readlink` on the host install entry before touching any repository code — dangling symlinks fail `.exists()` and masquerade as absence.

**Refs.** Porting Plan U8, `scripts/validate_plugins.py::inspect_install`.

### Pre-push gate detection must parse shell syntax, not only the git invocation  {#pre-push-shell-prefixes}

**Context.** The pre-push gate detects pushes by tokenizing the command; real pushes wrapped in shell prefixes or redirections went undetected and skipped the gate.

**Evidence.** `sudo git push`, `command git push`, `env --chdir=/repo git push`, `2>&1 git push`, and backslash-newline continuations all tokenize with the `git` head behind a prefix the old head-scan did not skip; `git -C/path push` (attached short-option value) extracted no target; `git submodule foreach git push` reads as subcommand `submodule`; `git push && cd /other` resolved the gate against `/other`.

**Fix.** `_skip_redirect_prefix` (leading fd/operator runs, incl. the `>&` single-token form), `_COMMAND_WRAPPERS` (one-level `sudo`/`command`/`nohup`), attached `--chdir=`/`-C=` env options, `-C<path>` in `_git_subcommand`, `_join_continuations` before line-splitting, `_nested_foreach_pushes` for submodule bodies, and `_cd_target` restricted to the leading segment.

**Generalizable rule.** A command-line safety gate must account for everything the shell allows in FRONT of the command it guards; a wrapper or redirection prefix is the cheapest bypass.

**Refs.** Porting Plan U2, `plugins/saga/hooks/pre_push_gate_hook.py`, `plugins/saga/tests/test_pre_push_gate.py`.

### Strict majority quorum floor for verify panels requires n // 2 + 1, not (n + 1) // 2  {#quorum-floor-strict-majority}

**Context.** Saga multi-agent consensus verify panels calculate a quorum threshold to reconcile independent verifier verdicts across parallel evaluation workers.

**Evidence.** For even panel size $N=2$, the expression `(2 + 1) // 2` evaluates to 1, allowing a single dissenting vote to claim quorum rather than requiring unanimous agreement of 2. For $N=4$, `(4 + 1) // 2` evaluates to 2 instead of the strict majority 3.

**Mechanism.** A strict majority requires $> N/2$. In integer division arithmetic, the floor of a strict majority is computed as `n // 2 + 1` (for odd $N=3 \implies 2$, for even $N=2 \implies 2$, $N=4 \implies 3$).

**Fix.** Updated `plugins/saga/scripts/execution_spec.py:_emit_panel_reconciliation` to use `const floor = Math.floor(n / 2) + 1` / `n // 2 + 1`. Added verification tests in `plugins/saga/tests/test_verify_panel_severity_axis.py`.

**Generalizable rule.** Quorum requiring a strict majority of $N$ participants must use `n // 2 + 1`, never `(n + 1) // 2` which evaluates to $\le N/2$ for all even $N$.

**Refs.** Porting Plan U3 (`refute-N severity axis and quorum`).

### Verifier severity separation prevents advisory feedback from blocking delivery  {#verifier-severity-separation}

**Context.** Readonly verifiers evaluate deliverable correctness and frequently encounter minor formatting, documentation, or advisory suggestions alongside blocking flaws.

**Evidence.** Under flat single-bucket evaluation, any reported finding was counted towards refutation quorum, causing minor advisory notes to falsely fail the build.

**Mechanism.** Combining gating defects and non-gating suggestions in one unranked schema forces verifiers into a false dilemma: suppress helpful observations or fail the delivery.

**Fix.** Split verifier schema into two explicit arrays: `refuted_deliverable` (which counts towards quorum and halts execution via `__halt`) and `advisory_corrections` (which are logged via `__logAdvisory` and returned in the run result envelope).

**Generalizable rule.** Automated reviewers must separate blocking rejection criteria from non-blocking advisory suggestions at the schema level before quorum reconciliation.

**Refs.** Porting Plan U3, `plugins/saga/scripts/execution_spec.py`, `plugins/saga/agents/readonly-verifier.md`.

### A checkout behind origin/main presents untracked files as the only copy  {#stale-wt-untracked-vs-origin}

**Context.** The 2026-08-13 Claude-to-Antigravity porting plan was drafted against the working tree. Local `HEAD` was twelve commits behind `origin/main`, and an untracked `plugins/hermes-profile-evolution/` tree sat beside that stale checkout.

**Evidence.** Antigravity `origin/main` `e0f08ce5` already contains `plugins/hermes-profile-evolution/` (`18eaa18`, timeout fix `83a1f5a`, later PRs through #39) with `SUBPROCESS_TIMEOUT_SECONDS = 45`. The untracked working-tree adapter uses `timeout=10`. Claude pin `541b36b9` is `feat(orchestrate): U5` and is not an ancestor of Claude `origin/main` `ff236284`.

**Mechanism.** An untracked directory plus a behind-`origin/main` checkout looks like "this plugin exists only locally and still needs the upstream boundary fixes." That is the opposite of the committed state. A plan that inventories the working tree therefore schedules destructive or duplicate work.

**Fix (or queued).** Rebound `docs/plans/2026-08-13-claude-plugins-porting-plan.md` to both `origin/main` tips and turned U6 into a non-regression check.

**Generalizable rule.** Before a plan says a file is missing, unimplemented, or only present untracked, read `origin/<default-branch>`, not just the working tree.

**Refs.** Decision `{#port-plan-origin-main-baseline}`. Review: `docs/reviews/2026-08-13-claude-plugins-porting-plan-doc-review.md`.

---

## 2026-08-10

### Adapter status validators must validate closed field bounds rather than single conformance samples  {#hermes-status-optional-deadline}

**Context.** Live canonical Hermes status responses for immediate `no_change` outcomes include core verification fields (`target`, `proposal_revision_digest`, `result`, `evidence_verification`, `public_evidence_digest`) but legitimately omit the proposal `deadline`.
**Evidence.** Running `profile_request.py status` against live Hermes PR #40 producer outputs failed closed because `_validate_status_output` strict-checked equality against a single pinned `result: "adopted"` conformance sample that required `deadline`.
**Mechanism.** Status outputs have mandatory core fields and optional fields (`deadline`, `public_evidence_digest`, `commit_state`, `drift_state`, `recovery_state`) that depend on proposal lifecycle disposition. Comparing exact key sets against a single lifecycle state sample falsely rejects valid status responses from alternate dispositions.
**Fix.** Updated `_validate_status_output` in `plugins/hermes-profile-evolution/scripts/profile_request.py` to enforce required status keys, bound allowed keys against the closed canonical status field set (`ALLOWED_STATUS_FIELDS`), and validate `deadline` only when present.
**Validation.** Unit tests in `tests/test_hermes_profile_evolution.py` verify canonical `no_change` without deadline passes, while secret keys, unallowed fields (`response_digest`), and malformed digests remain strictly rejected.
**Generalizable rule.** Validate output schemas against the closed contract bounds of the domain rather than pinning exact key-set identity to a single example case.
**Refs.** PR #40 Hermes profile evolution producer fix.

## 2026-07-26

### Consumer names must be closed before evaluating sparse capability receipts  {#capability-consumer-vacuous-pass}

**Context.** The capability receipt deliberately permits sparse result lists so
missing evidence evaluates as `unknown`, but `evaluate_for_consumer` accepts any
syntactically valid dotted consumer name.

**Evidence.** The U7/U8 doctor and Saga gate tests prove that a declared
`saga.resume` consumer blocks when `agy.conversation.resume` is unknown, while
an undeclared `saga.unknown` name is rejected before evaluation.

**Mechanism.** Requiredness lives on catalog rows. An undeclared consumer
matches no `required_for` row and would otherwise pass vacuously even though it
has no contract. Sparse receipts are safe only when the consumer itself is
known.

**Fix.** Both `scripts/validate_plugins.py` and
`plugins/saga/scripts/host_capability_gate.py` derive the closed consumer set
from catalog requiredness and fallback declarations before calling the shared
evaluator.

**Validation.** Doctor tests cover deterministic no-host validation, blocked
required evidence, optional degradation, and unknown profiles. Saga integration
tests cover unchanged degraded output, required uncertainty, schema drift,
local-diagnostic rejection, and fleet-core resolution failure.

**Generalizable rule.** When policy is expressed as per-resource membership,
validate the policy subject before evaluating its matching rules; an unknown
subject must not inherit an empty requirement set.

**Refs.** Decision
[`#antigravity-host-contract-plan`](DECISIONS.md#antigravity-host-contract-plan)
and issue `infiquetra/infiquetra-antigravity-plugins#20`.

## 2026-07-09

### Advisory locks must cover the read-compute-write cycle atomically for state ledgers  {#ledger-concurrency-flock}

**Context.** In `run_ledger.py`, facts are appended in a hash-chained sequence where each record carries the hash of the preceding record (the tail hash). When multiple subprocesses or concurrent threads attempt to write to the ledger simultaneously, they can read the same tail hash and generate conflicting hash chains, corrupting the chain sequence.

**Evidence.** [run_ledger.py](../../plugins/saga/scripts/run_ledger.py#L120-L137) and Finding 16 in the code review.

**Mechanism.** Simply opening the file with `a` or appending does not prevent a concurrent writer from reading the tail hash during the brief window before the write happens. Because `flock` is advisory, the file descriptor must be opened in read-write mode (`O_RDWR`), locked exclusively (`LOCK_EX`), read from the end to compute the hash, and then appended to while the lock is held.

**Fix.** Refactored `append_fact` in `run_ledger.py` to open the file via low-level `os.open(..., os.O_RDWR | os.O_CREAT)` to obtain a writable file descriptor, acquired an exclusive advisory lock using `fcntl.flock(fd, fcntl.LOCK_EX)`, and then read the tail hash, computed the new hash, and wrote the record while holding the lock.

**Validation.** Added [test_run_ledger.py](../../plugins/saga/tests/test_run_ledger.py) with concurrent append regression tests that prove the chaining logic under lock, which pass successfully.

**Generalizable rule.** When maintaining hash-chained or sequential log files, serialize access using advisory locks that wrap the entire read-compute-write operation (read tail, compute next, append write) on a single file descriptor rather than locking only the write phase.

## 2026-06-08

### Schema fields are consumed visually by humans/models, not regex-parsed  {#saga-formatting-parser-constraints}

**Context.** When designing formatting rules for the saga plugins, we needed to decide if fields (such as idea scores or plan details) must strictly remain in unstructured text or could be structured into tables. We investigated if existing parser scripts strictly depend on regex-parsing of markdown structures.

**Evidence.** Analysis of the codebase (such as `sdlc_manager.py` and `lifecycle_review.py`) reveals that no scripts programmatically parse the inside of markdown files using strict regular expressions or expect specific unstructured text formatting for metrics or survivors. Instead, scripts parse metadata files (such as `plugin.json` or JSON checkpoints) for structured details, while the markdown documents are consumed visually by the model or human operators.

**Mechanism.** Because markdown artifacts are for visual presentation and direct model consumption rather than downstream machine parsing, we can structure data using tables, summaries, and lists to maximize readability, without breaking integration scripts.

**Fix.** Standardized the presentation schema to use two-column markdown tables for compact, key-value data fields, and narrative paragraphs for descriptions. We also introduced `test_saga_doc_formatting.py` to assert correct markdown structure.

**Validation.** Pytest runs successfully and confirms that all modified files adhere to the formatting rules, and no downstream tool integrations fail.

**Generalizable rule.** Verify the true consumers of a document schema before freezing its layout. If the primary consumer is a human or a language model rather than a regex parser, prioritize layout readability (tables, visual structure) over keeping layout styles strictly identical.

**Refs.**
- DECISIONS [adopt-shared-formatting-contract](#adopt-shared-formatting-contract)
- [formatting-style.md](../../plugins/saga/references/formatting-style.md)

---

## 2026-05-31

### Agy CLI command-line marketplace installations require local path fallback or clean session reload  {#agy-marketplace-resolution}

**Context.** When a user attempted to install a plugin via the marketplace using the native `agy` CLI tool (e.g. `agy plugin install home-lab-ops@infiquetra-plugins`), the tool exited with `Error: unknown marketplace: infiquetra-plugins`. This occurred despite registering the marketplace under `extraKnownMarketplaces` in both the user's `~/.gemini/settings.json` and `~/.gemini/antigravity-cli/settings.json`.

**Evidence.** Running `/Users/jefcox/.local/bin/agy plugin install home-lab-ops@infiquetra-plugins` failed with `Error: unknown marketplace: infiquetra-plugins`.

**Mechanism.** The `agy` CLI is a client that delegates plugin/marketplace tasks to the running background language server daemon (started via `agy --continue` at shell session initialization). Because the background daemon caches `settings.json` at startup, any subsequent edits to register `extraKnownMarketplaces` in the configuration files are ignored by the active daemon. Furthermore, the `agy` binary parses its global configuration from the standard `~/.gemini/settings.json` file in a structured object format, not an array.

**Fix.** Configured the `extraKnownMarketplaces` and `marketplaces` keys with the correct object format across `/Users/jefcox/.gemini/settings.json` and `/Users/jefcox/.gemini/antigravity-cli/settings.json`. For immediate installation without restarting the background session, a local installation path fallback was successfully used: `agy plugin install /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/home-lab-ops`.

**Validation.** Running `agy plugin install /Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/home-lab-ops` successfully installed and enabled the plugin in the client runtime environment, and `agy plugin list` verified that it is registered.

**Generalizable rule.** Settings parsed by daemon-client architectures are cached by the server process at startup. When runtime configurations (such as plugin marketplaces) are updated, the background server/daemon must be reloaded (using slash commands or session restarts) or bypassed via local direct paths to register the changes.

---

## 2026-05-31

### Cross-plugin directory path changes require complete consumer audits  {#cross-plugin-path-mismatch}

**Context.** When porting the `infiquetra-lifecycle` plugin to the modern Antigravity layout, local loop checkpoint states were migrated from the `.claude/` directory to `.gemini/infiquetra-lifecycle/` in accordance with the Antigravity local state standards. However, the `sdlc-manager` plugin was left with hardcoded `.claude/` path searches for retrieving and verifying in-flight checkpoints.

**Evidence.** `plugins/sdlc-manager/src/sdlc_manager.py#L2674` and line 2815 were blind to checkpoints generated by the newly modernized lifecycle plugin, which broke the `/create-issue --prepare` and resuming workflows.

**Mechanism.** Deep dependencies exist between autonomous plugins (e.g., SDLC Manager inspecting Lifecycle checkpoints to determine ticket maturity). Migrating state folders in one plugin without auditing all corresponding path consumers across the repository isolates state and breaks workflows.

**Fix.** Refactored `sdlc_manager.py` (commit `41c9a94`) to search under both `.gemini/infiquetra-lifecycle` and `.claude/infiquetra-lifecycle` directories.

**Validation.** Verified prompt alignment and path resolution tests passed successfully, and confirmed that checkpoint status is correctly inferred by running the `sdlc-manager` test suite.

**Generalizable rule.** When migrating local state folders or environment configurations for any plugin, perform a recursive global search across all active plugins in the repository to locate and update any references to the legacy paths, ensuring backward-compatible fallback support.

**Refs.** DECISIONS [promote-agents-root-layout](#promote-agents-root-layout).

---

### Fallback-enabled path mocks must redirect both target and fallback paths in tests  {#defaults-test-fixture-isolation}

**Context.** When modernizing `sdlc_manager.py` to prioritize `~/.gemini/sdlc-defaults.json` for user settings, a fallback read check to `~/.claude/sdlc-defaults.json` was introduced. During testing, the `tmp_defaults_path` test fixture originally only mocked `_USER_DEFAULTS_PATH`.

**Evidence.** If the developer had a real `~/.claude/sdlc-defaults.json` file existing on their host machine, test cases that verified default reading would fall back and read the host file instead of staying in the isolated test sandbox, resulting in unpredictable test behavior.

**Mechanism.** Because the fallback path `_FALLBACK_DEFAULTS_PATH` was not mocked, `load_user_defaults` naturally queried the host filesystem when the mock prioritized `.gemini` path did not exist, leading to test environment leakage.

**Fix.** Updated `plugins/sdlc-manager/tests/test_user_defaults.py` (commit `41c9a94`) to explicitly mock both `_USER_DEFAULTS_PATH` and `_FALLBACK_DEFAULTS_PATH` to temporary directories inside `tmp_path`, and added a fallback-specific unit test.

**Validation.** All `test_user_defaults.py` tests passed with 100% success under isolated conditions.

**Generalizable rule.** Any test fixture mocking a prioritized filepath that includes fallback lookup mechanisms must mock both the primary destination and all fallback files to ensure absolute test isolation from the host filesystem.

---

## 2026-05-08

### Missing optional validator dependencies can hide invalid manifests  {#jsonschema-hidden-validation}

**Context.** CI consolidation restored `marketplace/validator/validate.py` and added `jsonschema` to dev dependencies so schema validation runs in normal CI installs.

**Evidence.** `python3 marketplace/validator/validate.py` passed in the system environment while warning `jsonschema not installed, skipping schema validation`. Running the same validator inside a temporary environment after `pip install -e ".[dev]"` failed on `plugins/sdlc-manager/.claude-plugin/plugin.json` because its description exceeded `marketplace/validator/schema.json`'s 200 character limit.

**Mechanism.** The validator treats missing `jsonschema` as a warning and continues. That made schema validation effectively optional in local and previous CI paths, so an invalid manifest could sit in the repository undetected until the dependency became available.

**Fix.** Added `jsonschema` to project dev dependencies and shortened the `sdlc-manager` plugin description to satisfy the schema limit.

**Validation.** `/tmp/infiquetra-plugins-verify-venv/bin/python marketplace/validator/validate.py` passes with `jsonschema` installed.

**Generalizable rule.** A validator's optional dependency is part of the validation contract. CI must install it, or invalid inputs can pass under a degraded "warning only" path.

**Refs.** `.github/workflows/ci.yml`; `pyproject.toml`; `marketplace/validator/validate.py`; `marketplace/validator/schema.json`.

---

## 2026-05-01

### Plugin code can ship without marketplace registration — the registry is a separate source of truth  {#marketplace-drift}

**Context.** A user reported that the `blueprint-reviewer` plugin did not appear when they tried to install plugins from this marketplace. The plugin's code lived under `plugins/blueprint-reviewer/` on `main` and was fully functional, but it was invisible to the marketplace UI.

**Evidence.**
- `plugins/blueprint-reviewer/` was added by PR #110 (merge commit `ae93035`) and Phase B work merged via PR #111 (commit `a7fea08`).
- Neither PR modified `.claude-plugin/marketplace.json`.
- At time of report: 15 plugin directories under `plugins/` but only 14 entries in `marketplace.json`.
- Fixed in PR #112 (commit `4da5705`).

**Mechanism.** Plugin code in `plugins/<name>/` and the marketplace registry in `.claude-plugin/marketplace.json` are independent files. PR review focused on the new plugin's code (skills, commands, scripts) and overlooked the one-line registry diff. Two PRs in a row missed it because the omission isn't visible in the plugin's own diff — it's a *missing* edit to a sibling file. Reviewers don't see absences.

**Fix.** PR #112 added the `blueprint-reviewer` entry to `marketplace.json` (mirrors `sdlc-manager`'s shape: `source`, `version`, `category: development`, keywords copied from the plugin manifest).

**Validation.** Post-merge: `python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); print(len(d['plugins']))"` returns `15`; `'blueprint-reviewer' in [p['name'] for p in d['plugins']]` is `True`.

**What surprised.** That the bug shipped *twice* in a row (#110 and #111). The second PR was specifically follow-up work on the same plugin; the registry omission was right there to be noticed but wasn't.

**Generalizable rule.** When two files must stay in sync (plugin dir + registry, schema + migration, code + docs index, env var + Lambda config), reviewers will drift one against the other given enough opportunities. Add a CI assertion that fails on drift — don't rely on PR review.

**Refs.**
- [QUEUED.md](QUEUED.md#marketplace-ci-guard) — P1 work item for the CI guard.
- [DECISIONS.md](DECISIONS.md#gitignore-claude-and-no-uv-lock) — repo hygiene shipped alongside.
- [ARCHIVE.md](ARCHIVE.md#pr-112-marketplace-fix) — SHIPPED record.

---

### `marketplace.json` `Edit` calls must include the array's closing `]` in `old_string`  {#marketplace-edit-guard}

**Context.** When appending a new plugin entry to `.claude-plugin/marketplace.json`, the `Edit` tool can produce invalid JSON if the `old_string` doesn't include enough context to capture the array's closing bracket. This has misfired multiple times.

**Evidence.** Repeated occurrences traced through prior memory record `marketplace.json Editing Guard`. The wrong-pattern shape:

```json
    }
  ],
    {
      "name": "new-plugin",
      ...
    }
  ],
  "version": "2.0.0"
}
```

— two closing `]`, parser fails. Caught only by post-edit validation.

**Mechanism.** When `old_string` ends at the last entry's closing `}`, the `Edit` tool inserts the new content *after* the line, which lands it after the array's `]` rather than inside the array. The fix is to include both the previous last entry's closing `}` AND the array's `]` in the `old_string`, so the new entry can be inserted *before* the `]` (with a `,` added to the prior `}`).

**Fix.** Standard pattern — `old_string` extends through the array's closing `]` and at least the next line:

```
old_string: "      \"workflow\"\n      ],\n      \"category\": \"development\"\n    }\n  ],\n  \"version\": \"2.0.0\"\n}"
```

Always validate immediately: `python3 -m json.tool .claude-plugin/marketplace.json > /dev/null`.

**Validation.** PR #112 (commit `4da5705`) used this exact pattern and produced valid JSON on first try.

**Generalizable rule.** When using `Edit` on a JSON/YAML file to append into a nested array, the `old_string` MUST include the array's closing bracket. Inserting "before the `]`" is correct; inserting "after the prior entry's `}`" is wrong because edits land on the line *after* the match. Always validate the file with the language's parser immediately after the edit.

**Refs.** Same lesson cached in `~/.claude/projects/.../memory/marketplace_editing_guard.md` for runtime convenience; this file is the durable project record.

---

### 2026-06-28
- **Context:** Porting the `saga` plugin from Claude to Antigravity.
- **Evidence:** User explicitly linked to `https://antigravity.google/docs/hooks` as proof of hook support.
- **Mechanism:** Antigravity provides a hook architecture similar to Claude. Thus, `hooks/` directories in plugins are valid and porting them is necessary.
- **Generalizable rule:** Do not assume structural limitations from Claude port without explicit documentation proof; Antigravity hooks are natively supported.
