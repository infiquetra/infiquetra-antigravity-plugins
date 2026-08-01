---
name: appsec-audit
description: |
  Application security audit focused on URL and input trust boundaries, SSRF-style risks,
  redirects, metadata endpoints, allowlists, and evidence-backed findings.
when_to_use: |
  Use when reviewing code that accepts URLs, fetches remote resources, follows redirects,
  proxies requests, imports external data, parses user-controlled input, or touches
  network egress controls.
---

# AppSec Audit

Use this skill to audit application code for URL and input trust boundary risks. Focus on
evidence-backed findings, not speculative concerns.

## Operating boundary

This skill consumes one bounded request and emits one typed evidence packet. It does not create a
`team-execution` plugin, worker runtime, or isolation mechanism.

There are two execution modes:

- `consume-external-evidence` validates evidence produced by an explicitly identified reviewer.
  Record `host_independence_performed` as `false`; importing a result is not proof that
  Antigravity created an independent reviewer.
- `originate-independent-reviewer` may start an independent reviewer only when the current
  sanitized Fleet Core capability receipt reports `agy.agent.execution` as `passed`. Any other
  state fails closed before review. Prose, fixtures, requested flags, and model role-play are not
  capability evidence.

For the reviewer-origin mode, resolve the reviewer model and effort from the current Fleet Core
policy. Use `plugins/fleet-core/scripts/fleet_commons/models.json`,
`plugins/fleet-core/scripts/fleet_commons/tier_resolver.py`, and
`plugins/fleet-core/scripts/fleet_commons/effort_rider.py`; do not embed a model name or invent a
second effort policy here.

## Closed audit contract

The following machine-readable contract is authoritative. Every object is closed: reject missing
fields, additional fields, wrong types, blank identifiers, duplicate identifiers, and values
outside the listed enums.

<!-- appsec-audit-contract-v1 -->
```json
{
  "schema": "antigravity.appsec-audit-contract.v1",
  "request": {
    "schema": "antigravity.appsec-audit-request.v1",
    "required_fields": [
      "schema",
      "request_id",
      "subject_producer_id",
      "scope_paths",
      "focus_categories",
      "execution_mode",
      "reviewer"
    ],
    "reviewer_required_fields": ["reviewer_id", "identity_source"],
    "execution_modes": [
      "consume-external-evidence",
      "originate-independent-reviewer"
    ],
    "identity_sources": ["external", "antigravity-host"],
    "categories": [
      "ssrf",
      "redirect",
      "input-validation",
      "allowlist",
      "metadata-endpoint",
      "other"
    ]
  },
  "evidence_packet": {
    "schema": "antigravity.appsec-audit-evidence.v1",
    "required_fields": [
      "schema",
      "request_id",
      "reviewer",
      "verdict",
      "findings",
      "checks",
      "evidence",
      "capability"
    ],
    "reviewer_required_fields": [
      "reviewer_id",
      "identity_source",
      "host_independence_performed"
    ],
    "finding_required_fields": [
      "finding_id",
      "severity",
      "category",
      "location",
      "evidence_ids",
      "impact",
      "fix",
      "validation_check_ids"
    ],
    "check_required_fields": ["check_id", "status", "detail", "evidence_ids"],
    "evidence_required_fields": [
      "evidence_id",
      "path",
      "line_start",
      "line_end",
      "observation"
    ],
    "capability_required_fields": ["receipt_sha256", "agy.agent.execution"],
    "verdicts": ["no-findings", "findings-present"],
    "severities": ["critical", "high", "medium", "low"],
    "check_statuses": ["pass", "failed"]
  }
}
```

The bounded request must satisfy all of these rules:

1. `scope_paths` and `focus_categories` are nonempty lists of unique strings.
2. Every scope path is repository-relative and normalized. Reject absolute paths, `..` traversal,
   URLs, globs, and paths outside the operator-requested boundary.
3. `reviewer.reviewer_id` differs from `subject_producer_id`. A producer cannot certify its own
   work.
4. `consume-external-evidence` requires `reviewer.identity_source=external`.
   `originate-independent-reviewer` requires `reviewer.identity_source=antigravity-host`.

## Review scope

Review:

- User-controlled URLs, hosts, paths, query strings, headers, and webhook destinations.
- HTTP clients, redirect handling, proxy code, file importers, and fetch/download helpers.
- SSRF-style paths to cloud metadata endpoint addresses and internal networks.
- DNS rebinding, scheme confusion, localhost/private-network access, and open redirects.
- Allowlist and blocklist enforcement.
- Input parsing at trust boundaries.

## Process

1. Validate the complete closed request before reading implementation files.
2. For `consume-external-evidence`, consume the externally supplied typed packet. Do not originate
   a reviewer or describe the evidence as host-independent.
3. For `originate-independent-reviewer`, validate the current Fleet Core receipt and require
   `agy.agent.execution=passed` before reviewer creation.
4. Map external inputs and trust boundaries only within `scope_paths`.
5. Trace each input to network, file, shell, database, template, or redirect sinks.
6. Check validation order: parse, canonicalize, validate, then use.
7. Confirm allowlists are positive and exact enough for the risk.
8. Check redirects do not escape the approved destination set.
9. Check cloud metadata endpoint protections and private network restrictions.
10. Produce findings only when code evidence supports the risk.

## SSRF Checklist

- Reject non-HTTP schemes unless explicitly required.
- Reject localhost, loopback, link-local, private, multicast, and unspecified addresses.
- Protect metadata endpoints, including `169.254.169.254` and provider-specific hostnames.
- Re-resolve DNS or pin validated IPs when redirects or retries occur.
- Validate every redirect hop.
- Enforce outbound allowlists at the URL/host layer and, where possible, network egress layer.
- Set conservative timeouts and response size limits.

## Deterministic evidence validation

Validate the complete packet before reporting the audit:

1. The packet `request_id`, reviewer identifier, and reviewer identity source exactly match the
   accepted request.
2. All `finding_id`, `check_id`, and `evidence_id` values are nonempty and unique within their
   collections.
3. Every evidence path is inside one of the request's exact scope paths. Line numbers are positive
   integers and `line_end` is not less than `line_start`.
4. Every finding cites one or more existing `evidence_ids` and one or more existing
   `validation_check_ids`. Every check cites one or more existing `evidence_ids`.
5. Finding categories are included in the request's `focus_categories`. Evidence observations,
   impacts, fixes, check details, and locations are nonempty.
6. `no-findings` requires an empty findings list and every check to be `pass`.
   `findings-present` requires at least one finding. Never turn a failed check into a
   `no-findings` verdict.
7. `consume-external-evidence` requires `capability=null` and
   `host_independence_performed=false`.
8. `originate-independent-reviewer` requires
   `host_independence_performed=true`, a lowercase 64-character receipt SHA-256 digest, and the
   exact capability field `agy.agent.execution=passed`.

Reject a packet that fails any rule. Do not summarize partial or evidence-free output as a
completed audit. If no findings remain after validation, state the reviewed scope and residual test
gaps without claiming the application is secure.
