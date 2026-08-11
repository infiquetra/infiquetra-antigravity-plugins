# Portability

This is an Antigravity-native consumer of two producer-owned contracts:

- Team Mimir classifier schema version 1, source commit
  `9440dc744afc6553927fbde7f979ad433e0d1378` and fixture SHA-256
  `04a73d33bec429081606b58851b53053059f2b90a9511f94d6ab26bbcaa34bfc`.
- Hermes profile-request command schema version 1, source commit
  `435b3660e86c41819462bc2b918d49c07a8497a6` and fixture SHA-256
  `31bb58621853cf42814c15df68dde37db2d992bb675f012ff69ba37b66e01f72`.

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

For exact host commands and exit behavior, see the [usage guide](docs/usage.md). The
[architecture guide](docs/architecture.md) shows why the command and target checkout use separate
roots and where producer authority begins.
