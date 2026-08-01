# Cross-Runtime Reconciliation

Repository documents are Saga's durable authority. Runtime state is an advisory
projection of those documents and may never overwrite, supersede, or silently
advance canonical lifecycle truth.

Every projection carries:

- a logical projection and runtime identity;
- the repository-relative canonical reference;
- the SHA-256 digest of the canonical bytes it observed;
- a sanitized receipt digest;
- advisory facts; and
- the literal authority value `advisory`.

`scripts/reconcile_controller.py` reads the canonical file immediately before
evaluation. `scripts/reconcile.py` accepts a projection only when its reference
and digest match. A stale projection, a different canonical reference, a
duplicate projection identity, or any claim of canonical authority is rejected.

The reconciliation receipt records both accepted and rejected projections. It
does not write lifecycle state. A lifecycle consumer may use accepted facts only
through its own obligation and transition-receipt contract.

No runtime-specific state directory is inferred. Callers supply explicit typed
receipts, which keeps host-local brain and coordination state in a staging role.
