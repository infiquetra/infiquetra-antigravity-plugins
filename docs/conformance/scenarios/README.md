# Saga Conformance Scenarios

The first conformance fixture is `reference-lifecycle`. It is a deterministic index over existing
contract tests, not a transcript replay or model benchmark.

Each scenario records:

- the originating requirement identifiers;
- a minimized repository fixture or synthetic test-builder input;
- one exact pytest validator;
- the observable semantic result; and
- an explicit statement that raw discovery material is not committed.

The fixture covers capability probing, required and optional behavior, host-contract linting,
transition settlement, retry and resume, deliberation receipts, artifact promotion, promoted-content
sanitization, canonical conflict handling, and external-action authority. Its failure set also covers
stale narration, unavailable capability evidence, active Claude-only APIs, mismatched receipts,
missing strategies, and unauthorized mutation attempts.

Raw Antigravity transcripts, histories, and brain artifacts used to discover future scenarios belong
only under the ignored `.conformance-local/` root. A maintainer manually reduces the behavior into
the closed scenario contract; the repository verifier accepts no raw-session input.

Run the deterministic fixture with:

```bash
python3 scripts/saga_conformance.py verify --fixture reference-lifecycle
```

Baseline artifacts under `docs/conformance/baselines/reference-lifecycle/` are sanitized semantic
summaries for the same fixture. Their manifest binds the fixture, requirements contract, Claude and
Codex source snapshots, artifact identities, and operator approval. Any changed binding invalidates
reuse. Issue #22 owns the later live Antigravity comparison and quality sign-off.
