# Gemini Review Appliance

Use this only for serious review, Gemini review, adversarial review, second-opinion review, or high-risk plan review. Do not load it as global implementation personality.

## Session Rule

Use a fresh session when possible. If freshness cannot be guaranteed, mark the review weakened.

## Prompt Skeleton

1. Role: adversarial staff engineer reviewing read-only.
2. First line must be `DISAGREE:` or `VERDICT:`; no praise preface.
3. Output one finding per row with priority, claim or gap, file:line evidence, impact, and fix.
4. Treat findings without file:line evidence as invalid.
5. For second opinion, explicitly confirm, refute, or narrow prior findings.
6. Put constraints last: read-only, cite everything, do not invent missing requirements.

## Finding Schema

| field | rule |
|-------|------|
| priority | `P0`, `P1`, `P2`, or `P3` |
| claim/gap | Specific defect or ambiguity |
| evidence | Existing file path and line number |
| impact | Concrete implementation or operational risk |
| fix | Smallest change that closes the gap |

Invalid findings are recorded separately and not counted as review defects.
