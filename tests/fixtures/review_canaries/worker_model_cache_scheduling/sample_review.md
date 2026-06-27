# Sample Review

| priority | claim/gap | evidence | fix |
|----------|-----------|----------|-----|
| P0 | `Unit` carries no file-path data, making plugin-dir segmentation unbuildable. | docs/plans/worker-model-cache-scheduling.md:42 | Add `Unit.files`. |
| P1 | Row cardinality is undefined because the plan says one resident worker but emits one row per unit. | docs/plans/worker-model-cache-scheduling.md:88 | Define one row per segment. |
| P1 | `depends_on` remains unit-level, but scheduling needs segment-level dependency derivation. | docs/plans/worker-model-cache-scheduling.md:114 | Derive segment dependencies before scheduling. |
