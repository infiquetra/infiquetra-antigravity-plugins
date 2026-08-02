# Portability

This is an Antigravity-native consumer of two producer-owned contracts:

- Team Mimir classifier schema version 1, source commit
  `9440dc744afc6553927fbde7f979ad433e0d1378` and fixture SHA-256
  `04a73d33bec429081606b58851b53053059f2b90a9511f94d6ab26bbcaa34bfc`.
- Hermes profile-request command schema version 1, source commit
  `292c62eb4dbff9a2b0d2683501a1cd00ed119f7b` and fixture SHA-256
  `b651eff9ac155758719f0fee59ad7dcf22fc6a81f11f27bc1668da0720eaf61c`.

Antigravity supplies a root manifest, command, and skill. The Python adapter translates only
between bounded Antigravity standard input and the producer command lines. It verifies fixture
provenance, executes the real classifier, preserves canonical Hermes standard input, and validates
closed response shapes before returning them.

Executable location and classification scope are independent. The command resolves the adapter
from `${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/hermes-profile-evolution}`, matching this
repository's native symlink installation pattern, and passes the Team Mimir checkout through the
explicit `--team-mimir-root` argument. No absolute machine or source-checkout path is embedded.

Unsupported features are explicit: there is no hook, hard enforcement, direct profile mutation,
credential or host configuration, live installation, offline queue, copied classifier, invented
doctor field, or Saga semantic-port ledger.
