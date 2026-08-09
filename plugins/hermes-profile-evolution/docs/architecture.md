# Antigravity front-door architecture

The Antigravity plugin transports one bounded request across two producer-owned
contracts. It does not reproduce either contract or gain target authority.

![Antigravity front-door architecture](assets/profile-evolution-antigravity-front-door.png)

## Request flow

1. The native command or skill collects intent, target, requester, delegation
   chain, repository-relative paths, and sanitized evidence references.
2. The adapter executes `scripts/classify_profile_change.py` under the explicit
   Team Mimir repository root.
3. Ordinary work returns without contacting Hermes. A supported governed result
   must name exactly one target profile; other dispositions stop.
4. The adapter runs the canonical Hermes doctor and sends the version-1 proposal
   envelope to dialogue, status, or census operations.
5. Hermes owns routing, credentials, dialogue, and the target response.

The plugin root and Team Mimir root are deliberately separate. Installed plugin
code must not be searched for inside the target checkout.

## Authority

The requester is the actor asking for consideration. The delegation chain
records Antigravity as a claimed harness hop. The target is the profile that
owns the proposed behavior, and it may accept, decline, defer, ask questions,
or take no action.

The plugin cannot edit or commit the target, settle a mutation, choose a model
or provider, manage credentials, or queue work. Antigravity exposes no supported
blocking hook for this plugin.

Read the [portability note](../PORTABILITY.md), the
[Team Mimir operator hub](https://github.com/infiquetra/team-mimir/tree/main/docs/team/profile-evolution),
and the [Hermes producer documentation](https://github.com/infiquetra/infiquetra-hermes-plugins/tree/main/docs/profile-evolution)
for the surrounding contracts.
