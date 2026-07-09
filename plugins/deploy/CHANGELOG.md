# Changelog

## [1.0.4] - 2026-07-05

- `release-orchestrator` agent: add validated `effort: high` and `model: gemini-3.1-pro` frontmatter fields, consuming the fleet effort convention (#363) — release coordination warrants deliberate reasoning.

## [1.0.3] - 2026-07-05

- Reformat CHANGELOG headings to the fleet's canonical grammar (bracketed version, hyphen-minus date) as part of the release-surface single-source generator work (#429).

## [1.0.0] - 2026-05-29

- Add Infiquetra tag-promotion deploy commands and deploy-state skill.
- Add release orchestrator guidance for rollback, hotfix, status, and release notes.
- Add deterministic helpers for tag naming, deployment status drift, and release-note preview.
- Preserve VECU deploy safety mechanics source-neutrally: version inference, hotfix refs, rollback tags, existing-tag rejection, dry-run protection, and unhealthy snapshot quarantine.
