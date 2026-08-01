# Fleet Doctor Evidence Sources

Saga's doctor consumes only the canonical Fleet Core capability catalog and a
validated `antigravity.capabilities.v1` receipt.

| evidence | canonical owner | Saga use |
|---|---|---|
| capability definitions and consumer rules | `plugins/fleet-core/references/antigravity-capability-probes.yaml` | identify known capability IDs |
| receipt validation and privacy limits | `plugins/fleet-core/scripts/fleet_commons/antigravity_capabilities.py` | reject malformed or unsafe evidence |
| consumer evaluation | `plugins/saga/scripts/host_capability_gate.py` | preserve Fleet Core's verdict |
| declared requirement diagnosis | `plugins/saga/scripts/fleet_doctor.py` | block required non-passing states |

The doctor never treats command help, a flag, narration, or a fixture as proof
that the current host executed an agent, selected an effort, or provided
isolation. Host observation is a separate passive Fleet Core operation.
