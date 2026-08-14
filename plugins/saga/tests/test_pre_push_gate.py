"""Unit tests for pre-push gate hook and manifest."""

from __future__ import annotations

import importlib.util
import json
import subprocess as sp
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "tools" / "gate-manifest.json"
HOOK_PATH = REPO_ROOT / "plugins" / "saga" / "hooks" / "pre_push_gate_hook.py"


def _load_hook_module() -> Any:
    """Dynamically import the hook script as a module."""
    spec = importlib.util.spec_from_file_location("pre_push_gate_hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGateManifest:
    """Verify the declarative gate manifest is well-formed and complete."""

    def test_manifest_exists(self) -> None:
        assert MANIFEST_PATH.exists(), f"gate manifest not found: {MANIFEST_PATH}"

    def test_manifest_is_valid_json(self) -> None:
        text = MANIFEST_PATH.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_manifest_has_steps(self) -> None:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        steps = data.get("steps")
        assert isinstance(steps, list) and len(steps) > 0, "manifest must have at least one step"

    def test_manifest_step_ids_are_unique(self) -> None:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        ids = [s.get("id") for s in data["steps"]]
        assert len(ids) == len(set(ids)), f"duplicate step IDs: {ids}"

    def test_every_step_has_command(self) -> None:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for step in data["steps"]:
            assert step.get("command"), f"step {step.get('id')!r} has no command"

    def test_every_step_has_label(self) -> None:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for step in data["steps"]:
            assert step.get("label"), f"step {step.get('id')!r} has no label"

    def test_every_step_has_failure_hint(self) -> None:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for step in data["steps"]:
            assert step.get("failure_hint"), f"step {step.get('id')!r} has no failure_hint"


def _make_payload(command: str, tool_name: str = "Bash") -> str:
    return json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})


class TestPrePushGateHookDetection:
    """Verify command detection helpers."""

    @pytest.fixture
    def hook(self) -> Any:
        return _load_hook_module()

    def test_git_push_is_detected(self, hook: Any) -> None:
        assert hook._push_target("git push origin main")[0]
        assert hook._push_target("git -C /some/path push --force-with-lease")[0]
        assert hook._push_target("git push")[0]
        assert hook._push_target("git add -A ; git push")[0]
        assert hook._push_target("git --no-pager -c user.name=x push")[0]

    def test_non_push_is_not_detected(self, hook: Any) -> None:
        assert not hook._push_target("git commit -m 'fix: something'")[0]
        assert not hook._push_target("git pull origin main")[0]
        assert not hook._push_target("echo 'git push'")[0]

    def test_argument_text_containing_push_does_not_gate(self, hook: Any) -> None:
        for command in (
            "git add docs/push-notes.md",
            "git log --oneline --grep=push",
            "git show HEAD:docs/how-to-push.md",
            "git commit -m 'document the git push gate'",
            "git checkout -b feature/push-gate-fix",
        ):
            assert not hook._push_target(command)[0], f"must not gate: {command}"

    def test_repo_is_resolved_from_the_invocation(self, hook: Any) -> None:
        assert hook._push_target("git -C /tmp/repo push")[1] == "/tmp/repo"
        assert hook._push_target("git --git-dir=/tmp/r/.git push")[1] == "/tmp/r/.git"
        assert hook._push_target("git --work-tree /tmp/wt push")[1] == "/tmp/wt"
        assert hook._push_target("git push origin main")[1] is None

    def test_attached_C_value_extracts_the_target(self, hook: Any) -> None:
        assert hook._push_target("git -C/tmp/repo push") == (True, "/tmp/repo")

    def test_cd_only_counts_in_the_leading_position(self, hook: Any) -> None:
        assert hook._cd_target("cd /tmp/other-repo && git push") == "/tmp/other-repo"
        assert hook._cd_target("git push && cd /other") is None
        assert hook._cd_target("git push ; cd /other") is None

    def test_command_wrappers_do_not_hide_a_push(self, hook: Any) -> None:
        assert hook._push_target("sudo git push origin main")[0]
        assert hook._push_target("command git push")[0]
        assert hook._push_target("nohup git push")[0]

    def test_env_chdir_attached_form_does_not_hide_a_push(self, hook: Any) -> None:
        assert hook._push_target("env --chdir=/repo git push")[0]
        assert hook._push_target("env -i -u GIT_CONFIG --chdir=/repo git push")[0]

    def test_line_continuation_is_joined_before_lexing(self, hook: Any) -> None:
        assert hook._push_target("git push \\\norigin main")[0]

    def test_leading_redirections_do_not_hide_a_push(self, hook: Any) -> None:
        assert hook._push_target("2>&1 git push origin main")[0]
        assert hook._push_target(">log git push")[0]

    def test_submodule_foreach_with_push_body_is_gated(self, hook: Any) -> None:
        assert hook._push_target("git submodule foreach git push")[0]
        assert not hook._push_target("git submodule foreach git status")[0]
        assert not hook._push_target("git submodule update --init")[0]

    def test_submodule_foreach_behind_global_options_is_gated(self, hook: Any) -> None:
        assert hook._push_target("git -C /repo submodule foreach git push")[0]

    def test_wrapper_forms_with_options_do_not_hide_a_push(self, hook: Any) -> None:
        assert hook._push_target("sudo -u root git push")[0]
        assert hook._push_target("sudo -H git push")[0]
        assert hook._push_target("sudo env -i git push")[0]
        assert hook._push_target("command env --chdir=/repo git push")[0]
        assert hook._push_target("sudo command git push")[0]
        assert hook._push_target("command -p git push")[0]

    def test_wrapper_options_do_not_create_false_positives(self, hook: Any) -> None:
        assert not hook._push_target("sudo -u git push")[0]
        assert not hook._push_target("sudo -H git status")[0]
        assert not hook._push_target("sudo make push")[0]

    def test_odd_and_even_trailing_backslash_runs(self, hook: Any) -> None:
        # 1 backslash: continuation. 3 backslashes: escaped backslash + continuation (odd run).
        assert hook._push_target("git push " + "\\" + "\norigin main")[0]
        assert hook._push_target("git push " + "\\\\\\" + "\norigin main")[0]
        # 2 backslashes: literal, no continuation — the second line is still a push segment.
        assert hook._push_target("git push " + "\\\\" + "\norigin main")[0]

    def test_cd_prefix_targets_the_other_repo(self, hook: Any) -> None:
        assert hook._cd_target("cd /tmp/other-repo ; git push") == "/tmp/other-repo"
        assert hook._cd_target("git push origin main") is None

    def test_operators_without_whitespace_still_gate(self, hook: Any) -> None:
        for command in (
            "git push&&echo ok",
            "git add -A&&git push",
            "git commit -m x;git push",
            "git push|cat",
            "git push||echo fail",
        ):
            assert hook._push_target(command)[0], f"must gate: {command}"

    def test_quoted_operator_text_still_does_not_gate(self, hook: Any) -> None:
        assert not hook._push_target("git commit -m 'a && b push'")[0]

    def test_git_dir_target_resolves_to_the_worktree(self, hook: Any, tmp_path: Path) -> None:
        assert hook._as_worktree_dir("/tmp/repo/.git") == "/tmp/repo"
        assert hook._as_worktree_dir("/tmp/repo") == "/tmp/repo"
        assert hook._as_worktree_dir(None) is None

        repo = tmp_path / "r"
        repo.mkdir()
        sp.run(["git", "init", "-q"], cwd=repo, check=True)
        assert hook._find_repo_root(str(repo / ".git")) is not None

    def test_newline_separated_push_still_gates(self, hook: Any) -> None:
        assert hook._push_target("git add -A\ngit push")[0]
        assert hook._push_target("echo ok\ngit push")[0]

    def test_env_option_prefix_still_finds_the_push(self, hook: Any) -> None:
        for command in (
            "env -i git push",
            "env -u GIT_CONFIG git push",
            "env --unset=GIT_CONFIG git push",
            "env FOO=1 git push",
            "GIT_AUTHOR_NAME=x git push",
        ):
            assert hook._push_target(command)[0], f"must gate: {command}"

    def test_unparseable_command_does_not_gate(self, hook: Any) -> None:
        assert not hook._push_target("git push 'unterminated")[0]


class TestPrePushGateHookExitBehavior:
    """Verify that the hook exits correctly based on push detection and step results."""

    @pytest.fixture
    def hook(self) -> Any:
        return _load_hook_module()

    def test_non_bash_tool_exits_0(self, hook: Any) -> None:
        payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "foo.py"}})
        with patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.read.return_value = payload
            with pytest.raises(SystemExit) as exc_info:
                hook.main()
        assert exc_info.value.code == 0

    def test_non_push_bash_command_exits_0(self, hook: Any) -> None:
        payload = _make_payload("git commit -m 'fix: oops'")
        with patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.read.return_value = payload
            with pytest.raises(SystemExit) as exc_info:
                hook.main()
        assert exc_info.value.code == 0

    def test_missing_manifest_exits_0(self, hook: Any, tmp_path: Path) -> None:
        payload = _make_payload("git push origin main")
        with (
            patch.object(sys, "stdin") as mock_stdin,
            patch.object(hook, "_find_repo_root", return_value=tmp_path),
        ):
            mock_stdin.read.return_value = payload
            with pytest.raises(SystemExit) as exc_info:
                hook.main()
        assert exc_info.value.code == 0

    def test_failing_step_exits_2_and_reports(
        self, hook: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        manifest = {
            "steps": [
                {
                    "id": "always-fail",
                    "label": "always fail",
                    "command": [sys.executable, "-c", "import sys; sys.exit(1)"],
                    "failure_hint": "Fix the thing.",
                }
            ]
        }
        (tmp_path / "tools").mkdir()
        (tmp_path / "tools" / "gate-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        payload = _make_payload("git push origin main")

        with (
            patch.object(sys, "stdin") as mock_stdin,
            patch.object(hook, "_find_repo_root", return_value=tmp_path),
        ):
            mock_stdin.read.return_value = payload
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "always fail" in captured.err
        assert "Fix the thing." in captured.err
        assert "blocked" in captured.err
