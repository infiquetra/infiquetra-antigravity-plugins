# Troubleshoot the Antigravity adapter

Start by checking the installed manifest and running the read-only doctor:

```bash
printf '%s' '{"target":"brokkr"}' \
  | python3 "$PROFILE_ADAPTER" doctor
```

| Symptom | Meaning | Action |
|---|---|---|
| Exit `2` and request requires a Team Mimir root | The `request` action did not receive `--team-mimir-root`. | Pass the explicit checkout root before `request`. |
| Exit `2` and a target mismatch | The requested target differs from the classifier's profile owner. | Correct the target or split the request. |
| Ordinary result with `hermes_contacted: false` | Every path is ordinary repository work. | Continue normal repository review. |
| Doctor fails | Hermes route, credentials, service, or response contract is unavailable. | Repair the external Hermes setup and rerun doctor. |
| A direct edit was not intercepted | This plugin has no supported hook. | Invoke the command or skill before editing governed paths. |
| Status rejects input | The object has extra fields or invalid proposal, revision, or target values. | Copy the canonical identifiers exactly. |
| Contract or provenance failure | Imported producer fixtures do not match their pinned sources. | Update through a reviewed producer-compatibility change; do not bypass validation. |

Errors do not echo request content and are not placed in a retry queue. Retry
only after correcting the local input or restoring the producer boundary.

For custody and activation failures, use the
[Team Mimir operator hub](https://github.com/infiquetra/team-mimir/tree/main/docs/team/profile-evolution).
For dialogue failures, use the
[Hermes producer troubleshooting guide](https://github.com/infiquetra/infiquetra-hermes-plugins/blob/main/docs/profile-evolution/troubleshooting.md).
