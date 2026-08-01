---
name: fleet-doctor
description: Diagnose Saga requirements from a sanitized Fleet Core capability receipt before dispatch.
---

# `/fleet-doctor`

Use the `fleet-doctor` skill. This command is read-only: it consumes a current
sanitized capability receipt and reports whether the caller's declared required
capabilities pass.

It does not observe the host, invoke a model, refresh credentials, install a
plugin, or mutate Saga state. A required capability in `failed`, `unknown`, or
`unavailable` state blocks dispatch. An optional capability may make a report
degraded, but cannot satisfy a required capability.
