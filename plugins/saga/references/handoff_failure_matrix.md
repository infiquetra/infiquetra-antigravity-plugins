# Handoff Failure Matrix

Saga handoff is a typed local boundary, not visual Markdown inference. The
`saga.handoff-envelope.v1` packet is validated by
`plugins/saga/scripts/handoff_envelope.py`; producing it performs no GitHub, board, merge, or deploy
action.

| Failure | Validator response | Operator action | External effect |
|---|---|---|---|
| Envelope is not an object | Reject with `handoff envelope must be an object` | Rebuild the packet as the closed schema | None |
| Required field is absent or an unknown field is present | Reject the closed field set | Use only the documented v1 fields | None |
| Schema is not `saga.handoff-envelope.v1` | Reject the schema | Regenerate with the current helper | None |
| `artifacts`, `evidence`, `risks`, or `still_unauthorized` is empty or malformed | Reject the named list | Supply at least one non-empty string for each category | None |
| Artifact path is absolute, empty, or escapes with `..` | Reject the repository reference | Use a repository-relative artifact path | None |
| `still_unauthorized` names an unsupported action | Reject the action | Use only `issue-create`, `board-update`, `pr-create`, `merge`, or `deploy` | None |
| Issue artifact ownership is not `mission-control` | Reject ownership | Restore `mission-control` as issue artifact owner | None |
| Source is missing or multiple durable sources are plausible | Refuse to guess | Ask the operator to select the durable source | None |
| Prepared issue or later action lacks separate confirmation | Preserve `still_unauthorized` | Stop at the owning workflow's authority gate | None |

## Required handoff contents

- `artifacts` names the repository-relative durable outputs being transferred.
- `evidence` names the proof already produced; it is not a completion claim by itself.
- `risks` tells the recipient what still needs validation.
- `still_unauthorized` preserves the external-action boundary after handoff.

The receiving workflow must revalidate current repository and remote state. A valid envelope routes
information; it does not grant authority.
