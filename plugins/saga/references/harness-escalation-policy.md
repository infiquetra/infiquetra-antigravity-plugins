# Harness Escalation Policy

Default to the cheapest path that can prove the work.

| path | use when |
|------|----------|
| inline | Small local change, clear target, low blast radius, narrow checks enough. |
| strict reviewer | Plan, requirements, or code needs adversarial evidence-gated review. |
| capability-gated high-thinking Gemini second opinion | High-risk plan or review where a proven independent agent can catch non-overlapping defects. |
| multi-agent consensus | Broad parallel work, security/data/infra blast radius, or unresolved reviewer disagreement. |

Every escalated output should state which path was used and why. An independent
review receipt is valid only when the current environment proves
`agy.agent.execution=passed`, or when Saga consumes an already-independent typed
receipt with intact provenance. If the required capability is unknown,
unavailable, or failed, save the prompt or route advisory local review and keep
the independent gate unsatisfied.
