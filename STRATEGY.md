# Strategy — Infiquetra Antigravity Plugins

> Living direction anchor for `infiquetra-antigravity-plugins`.
> Last updated: 2026-06-17.

---

## Target Problem

Building software with agentic AI assistants is powerful but chaotic.
Without structured workflows, agents lose context between sessions,
skip lifecycle gates, produce inconsistent artifacts, and can't
coordinate multi-step work across repositories.

Infiquetra needs a cohesive plugin ecosystem for Google Antigravity
that provides:

1. **Lifecycle discipline** — a saga-based state machine that tracks
   work from idea through spec, plan, implementation, review, QA,
   deploy, and retro, with durable artifacts at each phase.
2. **SDLC automation** — issue creation, board management, label
   taxonomy, flow metrics, and milestone tracking via GitHub's
   Projects v2 API.
3. **Deployment orchestration** — tag-promotion workflows, release
   notes, hotfix paths, and deployment state tracking.
4. **Infrastructure operations** — home-lab cluster management,
   Ansible preflight, monitoring guards, and inventory validation.
5. **Quality coordination** — multi-agent consensus workflows,
   structured review cycles, and adversarial verification.

---

## Approach

**Plugin-per-domain architecture.** Each plugin is a self-contained
bundle of skills, scripts, agents, and configuration. Plugins are
installed via symlink into `~/.gemini/config/plugins/` and loaded
natively by Antigravity at session start.

**Antigravity-native orchestration.** All skills use Antigravity's
native tools (`define_subagent`, `invoke_subagent`, `send_message`,
`schedule`) rather than platform-specific abstractions. Skills are
SKILL.md instruction files with YAML frontmatter, read by the agent
at invocation time.

**Parity with Claude plugins.** The saga, mission-control, and deploy
plugins are ported from `infiquetra-claude-plugins` with thoughtful
adaptation — not mechanical regex. Path references use `.gemini/`,
orchestration uses native subagent tools, and command stubs follow
the Antigravity skill directory pattern.

**Marketplace validation.** All plugins conform to the
`ANTIGRAVITY.md` plugin specification and validate against the
marketplace schema via `marketplace/validator/validate.py`.

**Quality gates.** Every change passes pytest, ruff, mypy, and bandit
before merge. Test coverage targets 80% floor, 100% on critical
paths.

---

## Who It's For

- **Jeff (operator)** — the primary user, running Antigravity sessions
  for Infiquetra engineering work across multiple repositories.
- **Future Infiquetra contributors** — anyone using the Antigravity
  plugin ecosystem for structured agentic development.
- **Marketplace consumers** — developers discovering and installing
  individual plugins from the Infiquetra marketplace registry.

---

## Key Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Plugin validation | 100% pass | `marketplace/validator/validate.py` |
| CI pipeline | Green on every PR | pytest + ruff + mypy + bandit |
| Claude parity | Feature-complete for saga, MC, deploy | Byte-level diff analysis |
| Lifecycle coverage | All 12 saga phases have skills | Skill directory count |
| Test coverage | ≥80% on plugin scripts | `uv run pytest --cov` |

---

## Active Tracks

| Track | Plugin | Status | Focus |
|-------|--------|--------|-------|
| Saga Lifecycle | `saga` | Active | 17 lifecycle skills, saga state machine, docs system |
| SDLC Management | `mission-control` | Active | Issue contracts, board ops, flow metrics, labels |
| Deployment | `deploy` | Stable | Tag-promotion, release notes, hotfix workflow |
| Home Lab Ops | `home-lab-ops` | Stable | Ansible preflight, Proxmox ops, monitoring, vault |
| Multi-Agent | `multi-agent-consensus` | Stable | Consensus protocol, parallel workers + reviewers |
| Task Management | `todoist` | Experimental | Todoist MCP integration |
| Network Ops | `unifi` | Experimental | UniFi controller monitoring |
| Marketplace | `marketplace/` | Active | Registry, validator, install tooling |

---

## Non-Goals

- **Runtime framework**: Plugins are instruction files and scripts,
  not a runtime SDK. Antigravity provides the runtime.
- **Cross-platform portability**: These plugins target Google
  Antigravity specifically. The Claude equivalents live in
  `infiquetra-claude-plugins`.
- **Plugin hosting service**: The marketplace is a local registry
  and validator, not a hosted service.
