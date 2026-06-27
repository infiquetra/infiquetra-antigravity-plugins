# Harness Escalation Policy

Default to the cheapest path that can prove the work.

| path | use when |
|------|----------|
| inline | Small local change, clear target, low blast radius, narrow checks enough. |
| strict reviewer | Plan, requirements, or code needs adversarial evidence-gated review. |
| high-thinking Gemini | High-risk plan/review where a fresh second opinion can catch non-overlapping defects. |
| multi-agent consensus | Broad parallel work, security/data/infra blast radius, or unresolved reviewer disagreement. |

Every escalated output should state which path was used and why. If Gemini or consensus tooling is unavailable, save the prompt or route local review instead of pretending the heavier gate passed.
