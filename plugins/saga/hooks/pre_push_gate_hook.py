#!/usr/bin/env python3
"""
PreToolUse hook: run the pre-push gate and report by exception.

Fires when the Bash tool runs a `git push` command.  Reads the single-source
gate manifest at ``tools/gate-manifest.json`` (relative to the repo root) and
executes every step in order.  Passes silently on success (report by
exception).  On any failure, prints the step label, its output, and the
failure hint to stderr, then exits 2 (blocking) to prevent the push.

Properties:
  - SILENT ON PASS: no output when every step is green.
  - BLOCKING ON FAILURE: exits 2, which prevents the push.
  - SINGLE SOURCE: adding or removing steps in gate-manifest.json — or
    retuning one via its optional ``timeout_seconds`` — is the only change
    needed to update the gate; this script never diverges.
  - CROSS-REPO-SAFE: degrades silently when the manifest is absent (so the
    hook can be registered globally without breaking repos that lack one).

Exit codes:
  0 — all steps passed (or not a push command / manifest absent).
  2 — one or more steps failed (blocking).
"""

from __future__ import annotations

import json
import shlex
import subprocess  # nosec B404
import sys
from pathlib import Path

_MANIFEST_REL = Path("tools") / "gate-manifest.json"

# Fallback per-step budget when a manifest step declares no ``timeout_seconds``.
# Steps that legitimately need longer say so in the manifest (issue #658).
_DEFAULT_STEP_TIMEOUT = 300


# git's own global options, i.e. the ones that may appear BEFORE the subcommand. Split by
# whether they consume a following token, so the subcommand scan can skip an option's value
# without mistaking it for the subcommand (`git -C /repo push` must not read `/repo` as the
# subcommand). Long `--opt=value` forms are self-contained and need no entry here.
_GIT_GLOBAL_OPTS_WITH_VALUE = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
)
_GIT_GLOBAL_FLAGS = frozenset(
    {
        "-p",
        "-P",
        "--paginate",
        "--no-pager",
        "--no-replace-objects",
        "--bare",
        "--literal-pathspecs",
        "--glob-pathspecs",
        "--noglob-pathspecs",
        "--icase-pathspecs",
        "--no-optional-locks",
    }
)

# Shell operators that end one command and begin another.
_SEGMENT_SEPARATORS = frozenset({"|", "||", "&&", ";", "&", "\n"})

# Command words that only wrap the real head (`sudo git push`, `command git push`). A wrapper is
# skipped together with its own options (`sudo -u root`, `command -p`), and only when the token
# after the wrapper run reads as `git`.
_COMMAND_WRAPPERS = frozenset({"sudo", "command", "nohup"})

# Per-wrapper options that consume the following token. Detection only needs the git HEAD, so
# the walk is deliberately conservative: an unrecognized option stops the walk and the gate
# fails open. Note `-p` takes a value for sudo but is a plain flag for command.
_WRAPPER_VALUE_OPTS = {
    "sudo": frozenset(
        {
            "-u",
            "-g",
            "-C",
            "-D",
            "-R",
            "-T",
            "-h",
            "-p",
            "-r",
            "-t",
            "-U",
            "-P",
            "--user",
            "--group",
            "--chdir",
            "--close-from",
            "--other-user",
            "--host",
            "--prompt",
            "--role",
            "--type",
        }
    ),
    "command": frozenset(),
    "nohup": frozenset(),
}


def _join_continuations(command: str) -> str:
    """Join backslash-newline line continuations into one logical line.

    ``git push \\`` + newline + ``origin main`` is one command in the shell; a raw
    ``splitlines`` cut would read the two fragments as separate segments and lose the push.

    An ODD run of trailing backslashes continues the line (the last one escapes the newline);
    an EVEN run is a literal escaped backslash with no continuation, matching the shell.
    """
    lines = command.splitlines()
    if not lines:
        return command
    joined: list[str] = []
    for line in lines:
        stripped = line.rstrip()
        trailing = len(stripped) - len(stripped.rstrip("\\"))
        if trailing % 2 == 1:
            joined.append(stripped[:-1] + " ")
        else:
            joined.append(line)
    return "\n".join(joined)


def _skip_redirect_prefix(segment: list[str]) -> int:
    """Index past a leading redirection run (``2>&1 git push``, ``>log git push``).

    With ``punctuation_chars=True`` a redirection splits into operator tokens: ``2>&1`` reads
    as ``2``, ``>``, ``&``, ``1``. A redirect operator also consumes its target word (``> log``).
    """
    i = 0
    while i < len(segment):
        token = segment[i]
        if token in {">", ">>", "<", "<<"}:
            i += 1
            if (
                i < len(segment)
                and segment[i] not in {">", ">>", "<", "<<", "&", ">&", "<&"}
                and not segment[i].isdigit()
            ):
                i += 1
            continue
        if token in {"&", ">&", "<&"} or token.isdigit():
            i += 1
            continue
        break
    return i


def _segments(command: str) -> list[list[str]]:
    """Split a shell command into token lists, one per pipeline/list segment.

    Quoting is honored, so the tokens of ``git commit -m 'git push now'`` carry the message as
    ONE token -- that is what makes subcommand identification possible at all, and it is the fix
    for #663 fault (b).

    ``punctuation_chars=True`` is load-bearing and NOT interchangeable with ``shlex.split``.
    Plain ``split`` only separates an operator that already has whitespace around it, so
    ``git push&&echo ok`` tokenizes as ``['git', 'push&&echo', 'ok']`` -- the subcommand reads as
    ``push&&echo``, never equals ``push``, and a **real push silently bypasses the gate**. That is
    a false negative on a safety gate, strictly worse than the over-firing this change set out to
    fix. Caught in review on #670 before merge.

    Newlines are separators too, and shlex will NOT do that for us: ``\\n`` is ordinary
    whitespace to the lexer, so ``git add -A\\ngit push`` tokenizes to one flat run and the
    segment's subcommand reads as ``add`` -- a second-line push bypasses the gate. Lines are
    therefore split before lexing. Caught in review on #670.

    A backslash-newline is a shell line continuation, not a separator: ``git push \\`` + newline
    joins into one logical line, and a plain ``splitlines`` cut would drop the trailing ``push``
    argument span mid-word. Continuations are joined before lexing.

    An unparseable command (unbalanced quotes) yields no segments, so the caller degrades to not
    gating rather than guessing.
    """
    segments: list[list[str]] = []
    for line in _join_continuations(command).splitlines():
        if not line.strip():
            continue
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            return []
        current: list[str] = []
        for token in tokens:
            if token in _SEGMENT_SEPARATORS:
                segments.append(current)
                current = []
            else:
                current.append(token)
        segments.append(current)
    return [s for s in segments if s]


def _git_invocations(command: str) -> list[list[str]]:
    """Every ``git`` invocation in the command, as its own token list.

    A segment's git call is its FIRST token (``git push``), or the token after an environment
    prefix (``VAR=value git push``, ``env -i git push``). ``echo 'git push'`` yields nothing
    because ``git`` is inside a quoted token, not a command head.

    The ``env`` walk handles ``env``'s own OPTIONS, not just assignments: ``env -i git push`` and
    ``env -u GIT_CONFIG git push`` are real pushes that the assignment-only walk skipped straight
    past, finding no git invocation and letting the push through. Caught in review on #670.
    """
    found: list[list[str]] = []
    for segment in _segments(command):
        start = _skip_redirect_prefix(segment)
        head = start + _skip_wrapper_and_env(segment[start:])
        if head < len(segment) and Path(segment[head]).name == "git":
            found.append(segment[head:])
    return found


# ``env`` options that consume the following token. ``-u``/``--unset`` name a variable to drop.
_ENV_OPTS_WITH_VALUE = frozenset({"-u", "--unset", "-S", "--split-string", "-C", "--chdir"})
_ENV_FLAGS = frozenset({"-i", "--ignore-environment", "-", "-0", "--null", "-v", "--debug"})


def _skip_wrapper_and_env(segment: list[str]) -> int:
    """Index of the command head, past wrapper words, wrapper options, and env prefixes.

    ``sudo -u root git push``, ``sudo env -i git push``, and ``command env --chdir=/repo git
    push`` are real pushes whose git head sits behind a wrapper word plus that wrapper's own
    options. The walk repeats so stacked forms (``sudo command git push``) resolve too, and
    stops at the first non-wrapper token so an unrecognized option fails the gate open rather
    than guessing past the real command word.
    """
    i = _skip_env_prefix(segment)
    while i < len(segment):
        if segment[i] not in _COMMAND_WRAPPERS:
            break
        wrapper = segment[i]
        value_opts = _WRAPPER_VALUE_OPTS.get(wrapper, frozenset())
        i += 1
        while i < len(segment):
            opt = segment[i]
            if opt in value_opts:
                i += 2
                continue
            if opt.startswith("--") and "=" not in opt and opt not in value_opts:
                i += 1
                continue
            if opt.startswith("-") and opt != "-" and "=" not in opt:
                i += 1
                continue
            break
        i += _skip_env_prefix(segment[i:])
    return i


def _skip_env_prefix(segment: list[str]) -> int:
    """Index of the real command head, past any ``VAR=value`` / ``env ...`` prefix."""
    i = 0
    while i < len(segment):
        token = segment[i]
        if token == "env":
            i += 1
            # Walk env's own options and assignments until the command word.
            while i < len(segment):
                opt = segment[i]
                if opt in _ENV_OPTS_WITH_VALUE:
                    i += 2
                    continue
                if any(
                    opt.startswith(name + "=")
                    for name in _ENV_OPTS_WITH_VALUE
                    if name.startswith("--")
                ):
                    i += 1
                    continue
                if opt in _ENV_FLAGS or opt.startswith("--unset="):
                    i += 1
                    continue
                if "=" in opt and not opt.startswith("-"):
                    i += 1
                    continue
                break
            continue
        if "=" in token and not token.startswith("-"):
            i += 1
            continue
        break
    return i


def _git_subcommand(invocation: list[str]) -> tuple[str | None, str | None]:
    """Return ``(subcommand, target_path)`` for one ``git`` token list.

    Walks git's global options -- skipping an option's value where it takes one -- and returns
    the first non-option token as the SUBCOMMAND. This is the fix for #663 fault (b): the old
    regex matched the word ``push`` anywhere in the argument span, so ``git add
    docs/push-notes.md``, ``git log --grep=push``, and ``git commit -m "... push ..."`` all ran
    the full gate suite. A token list knows the difference between a subcommand and an argument.

    ``target_path`` is ``-C <path>`` / ``--git-dir=<path>`` / ``--work-tree=<path>`` when given
    -- #663 fault (a): resolving the repo from the invocation rather than the session cwd is what
    lets a push aimed elsewhere reach that repo's manifest, or fall through the cross-repo exit.
    """
    target: str | None = None
    i = 1  # token 0 is `git`
    while i < len(invocation):
        token = invocation[i]
        if not token.startswith("-"):
            return token, target
        name, sep, value = token.partition("=")
        if sep and name in _GIT_GLOBAL_OPTS_WITH_VALUE:
            if name in ("--git-dir", "--work-tree"):
                target = value
            i += 1
            continue
        if token in _GIT_GLOBAL_OPTS_WITH_VALUE:
            if i + 1 < len(invocation):
                if token in ("-C", "--git-dir", "--work-tree"):
                    target = invocation[i + 1]
                i += 2
                continue
            return None, target
        if token.startswith("-C") and len(token) > 2 and not token.startswith("--"):
            # Attached short-option value: ``git -C/path push``.
            target = token[2:]
            i += 1
            continue
        if token in _GIT_GLOBAL_FLAGS:
            i += 1
            continue
        # An unrecognized option before the subcommand: skip it rather than guess it is the
        # subcommand. Unknown never reads as `push`, so the gate stays off by default.
        i += 1
    return None, target


def _nested_foreach_pushes(invocation: list[str]) -> bool:
    """A ``git submodule foreach <body>`` runs the body once per submodule.

    An unquoted body like ``git submodule foreach git push`` tokenizes the inner invocation in
    the same segment; each submodule then receives a real push the outer-subcommand read would
    otherwise miss. The subcommand is located via ``_git_subcommand`` so global options before
    it (``git -C /repo submodule foreach ...``) do not hide the nested push.
    """
    subcommand, _ = _git_subcommand(invocation)
    if subcommand != "submodule":
        return False
    try:
        idx = invocation.index("submodule")
    except ValueError:
        return False
    if idx + 1 >= len(invocation) or invocation[idx + 1] != "foreach":
        return False
    body = invocation[idx + 2 :]
    i = 0
    while i < len(body):
        if Path(body[i]).name == "git":
            inner_subcommand, _ = _git_subcommand(body[i:])
            if inner_subcommand == "push":
                return True
        i += 1
    return False


def _push_target(command: str) -> tuple[bool, str | None]:
    """``(is_push, target_path)`` for the whole command.

    True when ANY segment's git invocation has ``push`` as its actual subcommand. A compound
    like ``git add -A && git push`` is still a push.
    """
    for invocation in _git_invocations(command):
        subcommand, target = _git_subcommand(invocation)
        if subcommand == "push":
            return True, target
        if _nested_foreach_pushes(invocation):
            return True, None
    return False, None


def _cd_target(command: str) -> str | None:
    """Path from a LEADING ``cd <path> &&`` prefix, if any.

    #663 fault (a) observed live: ``cd <other-repo> && git push`` resolved to the SESSION repo,
    so this repo's ~5500-test suite ran against a push aimed elsewhere and blocked it on 17
    unrelated failures. The missing-manifest cross-repo exit could not save it, because the
    session repo does have a manifest.

    Only the leading position counts: ``git push && cd /other`` is a push from the session repo,
    and reading the trailing ``cd`` would run the gate against ``/other``'s manifest (or skip it
    entirely when ``/other`` has none).
    """
    segments = _segments(command)
    if not segments:
        return None
    first = segments[0]
    start = _skip_redirect_prefix(first)
    head = start + _skip_wrapper_and_env(first[start:])
    if head + 1 < len(first) and first[head] == "cd" and first[head + 1] not in _SEGMENT_SEPARATORS:
        return first[head + 1]
    return None


def _as_worktree_dir(target: str | None) -> str | None:
    """Normalize a targeting path to something usable as a ``cwd``.

    ``--git-dir`` names the **git directory**, not a working tree. Handing ``<repo>/.git`` to
    ``git rev-parse --show-toplevel`` as ``cwd`` returns non-zero, `_find_repo_root` yields
    ``None``, and ``main()`` exits 0 before ever reading the manifest -- so the very form the
    targeting fix claimed to support silently skipped the gate. Caught in review on #670 before
    merge.

    A path whose basename is ``.git`` resolves to its parent; anything else is returned as-is.
    """
    if target is None:
        return None
    path = Path(target)
    if path.name == ".git":
        return str(path.parent or Path("."))
    return target


def _find_repo_root(cwd: str | None) -> Path | None:
    """Return the git repository root, or None if not inside a repo."""
    try:
        result = subprocess.run(  # nosec B603 B607
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=_as_worktree_dir(cwd),
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:  # nosec B110
        pass
    return None


def _run_step(step: dict, cwd: Path) -> tuple[bool, str]:
    """
    Run a single gate step.

    Returns (passed, output) where output is combined stdout+stderr
    (empty string on pass — caller decides whether to surface it).
    """
    cmd: list[str] = step.get("command", [])
    if not cmd:
        return True, ""

    # Per-step budget, from the manifest, defaulting to the historical 300 s (issue
    # #658). The timeout used to be hardcoded here, which broke the SINGLE SOURCE
    # property above: tuning the gate meant editing the hook, not the manifest. It also
    # failed the wrong way — the suite grew past 300 s while still passing, so the gate
    # blocked every push in the repo reporting a timeout rather than a test failure,
    # which reads identically to a real red at the call site.
    timeout_seconds = step.get("timeout_seconds", _DEFAULT_STEP_TIMEOUT)

    try:
        result = subprocess.run(  # nosec B603 B607
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout_seconds} s"
    except Exception as exc:
        return False, str(exc)

    if result.returncode == 0:
        return True, ""

    combined = "\n".join(part for part in (result.stdout.rstrip(), result.stderr.rstrip()) if part)
    return False, combined


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except Exception:
        # Malformed envelope — pass through silently.
        sys.exit(0)

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command: str = tool_input.get("command", "")

    is_push, target = _push_target(command)
    if not is_push:
        sys.exit(0)

    # Resolve the repo from the INVOCATION (`git -C` / `--git-dir` / `--work-tree`), then from a
    # leading `cd <path> &&`, and only then from the session cwd (#663 fault (a)). Resolving from
    # cwd first is what ran this repo's suite against a push aimed at another repo.
    cwd_str = target or _cd_target(command)
    repo_root = _find_repo_root(cwd_str)

    if repo_root is None:
        # Not inside a git repo — degrade silently.
        sys.exit(0)

    manifest_path = repo_root / _MANIFEST_REL
    if not manifest_path.exists():
        # No manifest — degrade silently (cross-repo safety).
        sys.exit(0)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(
            f"[saga/pre-push-gate] Cannot read gate manifest: {exc}",
            file=sys.stderr,
        )
        sys.exit(0)  # Manifest unreadable — degrade silently rather than blocking.

    steps: list[dict] = manifest.get("steps", [])
    if not steps:
        sys.exit(0)

    failures: list[tuple[str, str, str]] = []  # (label, output, hint)

    for step in steps:
        label: str = step.get("label", step.get("id", "unknown"))
        passed, output = _run_step(step, repo_root)
        if not passed:
            hint: str = step.get("failure_hint", "")
            failures.append((label, output, hint))

    if not failures:
        # All green — silent pass (report by exception).
        sys.exit(0)

    # Report failures and block the push.
    print(
        f"[saga/pre-push-gate] {len(failures)} gate step(s) failed — push blocked.\n",
        file=sys.stderr,
    )
    for label, output, hint in failures:
        print(f"  FAIL: {label}", file=sys.stderr)
        if output:
            for line in output.splitlines():
                print(f"    {line}", file=sys.stderr)
        if hint:
            print(f"    Hint: {hint}", file=sys.stderr)
        print(file=sys.stderr)

    sys.exit(2)


if __name__ == "__main__":
    main()
