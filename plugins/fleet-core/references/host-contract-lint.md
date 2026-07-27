# Antigravity Host Contract Lint

The host-contract linter scans the versioned active surface selected by
`antigravity-host-contract-surfaces.json`. It reports these stable rules:

| rule | condition |
|---|---|
| `AGHC001` | executable or active `.claude/` state path |
| `AGHC002` | Claude-only `AskUserQuestion` or `ToolSearch` interaction API |
| `AGHC003` | direct Claude Workflow invocation or source-only workflow backend |
| `AGHC004` | fixed Antigravity brain/session root |
| `AGHC005` | scheduling behavior asserted without capability evidence |
| `AGHC006` | isolation or sandbox behavior asserted without capability evidence |

An unannotated match in the active surface is unresolved. Narrow classifications
use a JSON object on the immediately preceding line:

```markdown
<!-- antigravity-host-contract: {"class":"historical","rule":"AGHC003","reason":"quoted source lineage","revisit":"remove when lineage is retired"} -->
```

Python uses the same object after `# antigravity-host-contract:`. Allowed
classes are `historical`, `foreign-runtime-input`, and `capability-gated`.
Every annotation needs `class`, `rule`, `reason`, and `revisit`.
`foreign-runtime-input` additionally requires `"access":"read-only"`.
`capability-gated` additionally requires a catalog capability ID. An unknown or
non-passing capability leaves the finding unresolved.

Annotations apply to one immediately following matched statement. Wildcards,
file-wide exemptions, missing reasons, stale rule IDs, unknown capabilities,
and non-adjacent annotations fail closed. Historical exceptions are bound to a
closed repository-relative path and line-digest allowlist. Python
foreign-runtime reads are bound to a closed path, complete-file digest, and
line-digest allowlist. Adding or changing either kind of exception requires an
explicit code review; arbitrary annotations, helpers, or later data-flow
changes remain unresolved.

The active globs, exact adjacent paths, and comparison roots are independently
bound to the canonical policy in the linter. Editing the selector cannot narrow
the scan or reclassify active paths without updating that reviewed policy.
Promotable finding paths reject credential-shaped, machine-hostname, and
unbounded high-entropy path segments without echoing the rejected value.
