# Reference Service Specification

## Folder contract

| Folder | Required files | Completeness | Depends on |
|---|---|---|---|
| architecture | overview.md, security.md | Boundaries and access model are explicit. | — |
| api | openapi.yaml, endpoint-specifications.md | Every endpoint appears in contract and prose. | architecture |
| operations | runbook.md | Failure, recovery, and ownership are documented. | api |
