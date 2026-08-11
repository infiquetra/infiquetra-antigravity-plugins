# Changelog

## 0.1.2 - 2026-08-10

- Support canonical status responses for immediate `no_change` outcomes that legitimately omit `deadline`.
- Enforce closed allowed status fields (`target`, `proposal_revision_digest`, `result`, `evidence_verification`, `public_evidence_digest`, `deadline`, `commit_state`, `drift_state`, `recovery_state`) while requiring core common status fields.
- Reject unallowed/private status fields, `response_digest`, malformed evidence, and invalid deadline timestamps.

## 0.1.1 - 2026-08-09

- Allow the producer's bounded 30-second network request to finish before the adapter exits.
- Project standard chat-completion responses onto the producer-declared public fields.
- Remove provider-specific response metadata from successful dialogue.

## 0.1.0 - 2026-08-02

- Add Antigravity-native command and skill discovery.
- Call the producer-owned Team Mimir classifier instead of copying custody rules.
- Forward canonical suggestions and dialogue to `hermes profile-request` through bounded standard
  input.
- Fail closed on invalid input, producer drift, service failure, and unexpected output.
- Record the imported producer commits, fixture digests, native surfaces, and unsupported features
  in a compact portability receipt.
