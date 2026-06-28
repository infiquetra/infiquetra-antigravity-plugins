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
- [formatting-style.md](file:///Users/jefcox/workspace/infiquetra/infiquetra-antigravity-plugins/plugins/saga/references/formatting-style.md)

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
