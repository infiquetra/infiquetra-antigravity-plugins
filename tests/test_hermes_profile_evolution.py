from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/hermes-profile-evolution"
SCRIPT = PLUGIN / "scripts/profile_request.py"
CLASSIFIER_FIXTURE = PLUGIN / "conformance/profile-change-classifier.v1.json"
HERMES_FIXTURE = PLUGIN / "conformance/profile-request-cli.v1.json"
PROVENANCE_FIXTURE = PLUGIN / "conformance/provenance.json"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_previous_dont_write_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    request = _load_module("antigravity_profile_request", SCRIPT)
finally:
    sys.dont_write_bytecode = _previous_dont_write_bytecode


class Result:
    def __init__(self, returncode: int = 0, stdout: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout


def _actor(kind: str = "harness", actor_id: str = "antigravity") -> dict[str, str]:
    return {"actor_kind": kind, "actor_id": actor_id, "verification": "claimed"}


def _request(paths: list[str] | None = None, **overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "target": "brokkr",
        "requester": _actor("operator", "operator-conformance"),
        "delegation_chain": [_actor()],
        "intent": "Consider this bounded Antigravity suggestion.",
        "evidence_references": ["docs/proposal.md"],
        "paths": paths or ["profiles/brokkr/SOUL.md"],
        "proposal_id": "proposal-conformance-0001",
        "created_at": "2026-08-01T12:00:00Z",
    }
    value.update(overrides)
    return value


def _fixture() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CLASSIFIER_FIXTURE.read_text()))


def _classification(case_id: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        next(case["expected"] for case in _fixture()["cases"] if case["id"] == case_id),
    )


def _hermes_stdout(case_id: str) -> list[Any]:
    fixture = json.loads(HERMES_FIXTURE.read_text())
    return deepcopy(
        next(
            case["expected"]["stdout_json"]
            for case in fixture["cases"]
            if case["case_id"] == case_id and case["expected"]["outcome"] == "success"
        )
    )


def _json_stream(values: list[Any]) -> bytes:
    return b"\n".join(json.dumps(value).encode() for value in values) + b"\n"


def _classifier_runner(output: dict[str, Any], calls: list | None = None):
    def runner(command, **kwargs):
        if calls is not None:
            calls.append((command, kwargs))
        return Result(stdout=json.dumps(output).encode())

    return runner


def _dialogue_bytes(envelope: dict[str, Any]) -> bytes:
    provider = {"choices": [{"message": {"content": "considered"}}]}
    continuity = {
        "continuity_digest": "c" * 64,
        "proposal_id": envelope["proposal_id"],
        "proposal_revision_digest": envelope["revision_digest"],
        "response_digests": ["d" * 64],
        "target": envelope["target"],
        "updated_at": "2026-08-01T12:01:00Z",
    }
    return json.dumps(provider).encode() + b"\n" + json.dumps(continuity).encode() + b"\n"


def _hermes_runner(calls: list):
    def runner(command, **kwargs):
        calls.append((command, kwargs))
        action = command[2]
        if action == "doctor":
            target = command[-1]
            return Result(
                stdout=json.dumps(
                    {
                        "credential_available": True,
                        "route_registered": True,
                        "service_available": True,
                        "target": target,
                    }
                ).encode()
            )
        if action in {"suggest", "reply", "resume"}:
            envelope = json.loads(kwargs["input"])
            return Result(stdout=_dialogue_bytes(envelope))
        raise AssertionError(f"unexpected action {action}")

    return runner


def test_imported_producer_fixtures_match_provenance() -> None:
    classifier, hermes = request.load_contracts()
    provenance = json.loads(PROVENANCE_FIXTURE.read_text())
    paths = {
        "profile-change-classifier.v1.json": CLASSIFIER_FIXTURE,
        "profile-request-cli.v1.json": HERMES_FIXTURE,
    }

    assert classifier["classifier_schema_version"] == 1
    assert hermes["contracts"]["doctor_fields"] == [
        "credential_available",
        "route_registered",
        "service_available",
        "target",
    ]
    for row in provenance["artifacts"]:
        assert hashlib.sha256(paths[row["artifact"]].read_bytes()).hexdigest() == row["sha256"]


@pytest.mark.parametrize(
    "case_id",
    [
        "ordinary-repository",
        "target-owned",
        "custodian-owned-runtime",
        "external-source-custody",
        "unknown-path",
        "prohibited-secret-file",
        "prohibited-private-runtime",
        "mixed-target-and-ordinary",
        "mixed-target-and-external",
        "cross-target-aggregation",
    ],
)
def test_real_classifier_boundary_consumes_every_pinned_fixture_case(case_id: str) -> None:
    case = next(row for row in _fixture()["cases"] if row["id"] == case_id)
    calls: list = []

    output = request.classify_paths(
        case["paths"],
        team_mimir_root=Path("/team-mimir"),
        runner=_classifier_runner(case["expected"], calls),
    )

    assert output == case["expected"]
    command = calls[0][0]
    assert command[1] == "/team-mimir/scripts/classify_profile_change.py"
    assert command[-len(case["paths"]) :] == case["paths"]
    assert "--schema-version" in command and "--format" in command


def test_documented_installed_plugin_command_targets_separate_team_mimir_checkout(
    tmp_path: Path,
) -> None:
    team_mimir = tmp_path / "team-mimir"
    classifier_dir = team_mimir / "scripts"
    classifier_dir.mkdir(parents=True)
    classifier_log = tmp_path / "classifier.json"
    classification = _classification("target-owned")
    classifier = classifier_dir / "classify_profile_change.py"
    classifier.write_text(
        "\n".join(
            (
                "#!/usr/bin/env python3",
                "import json, os, sys",
                "with open(os.environ['CLASSIFIER_LOG'], 'w') as stream:",
                "    json.dump(sys.argv[1:], stream)",
                f"print({json.dumps(json.dumps(classification))})",
            )
        )
        + "\n"
    )

    home = tmp_path / "home"
    install = home / ".gemini/config/plugins/hermes-profile-evolution"
    install.parent.mkdir(parents=True)
    install.symlink_to(PLUGIN, target_is_directory=True)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    hermes_log = tmp_path / "hermes.jsonl"
    hermes = fake_bin / "hermes"
    hermes.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys

payload = sys.stdin.buffer.read()
with open(os.environ["HERMES_LOG"], "a") as stream:
    stream.write(json.dumps({"argv": sys.argv[1:], "stdin": payload.decode()}) + "\\n")
action = sys.argv[2]
if action == "doctor":
    print(json.dumps({
        "credential_available": True,
        "route_registered": True,
        "service_available": True,
        "target": sys.argv[-1],
    }))
elif action == "suggest":
    envelope = json.loads(payload)
    print(json.dumps({"choices": [{"message": {"content": "considered"}}]}))
    print(json.dumps({
        "continuity_digest": "c" * 64,
        "proposal_id": envelope["proposal_id"],
        "proposal_revision_digest": envelope["revision_digest"],
        "response_digests": ["d" * 64],
        "target": envelope["target"],
        "updated_at": "2026-08-01T12:01:00Z",
    }))
else:
    raise SystemExit(9)
"""
    )
    hermes.chmod(0o755)

    native_command = (PLUGIN / "commands/hermes-profile-evolution.md").read_text()
    assert 'TEAM_MIMIR_ROOT="${TEAM_MIMIR_ROOT:-$PWD}"' in native_command
    assert (
        'HERMES_PROFILE_EVOLUTION_PLUGIN_ROOT="${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/hermes-profile-evolution}"'
        in native_command
    )
    assert '--team-mimir-root "$TEAM_MIMIR_ROOT" request' in native_command
    assert not (team_mimir / "plugins").exists()

    shell = """
TEAM_MIMIR_ROOT="${TEAM_MIMIR_ROOT:-$PWD}"
HERMES_PROFILE_EVOLUTION_PLUGIN_ROOT="${AGY_PLUGIN_ROOT:-$HOME/.gemini/config/plugins/hermes-profile-evolution}"
python3 "$HERMES_PROFILE_EVOLUTION_PLUGIN_ROOT/scripts/profile_request.py" \\
  --team-mimir-root "$TEAM_MIMIR_ROOT" request
"""
    environment = {
        **os.environ,
        "CLASSIFIER_LOG": str(classifier_log),
        "HERMES_LOG": str(hermes_log),
        "HOME": str(home),
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
    }
    completed = subprocess.run(
        ["bash", "-c", shell],
        cwd=team_mimir,
        env=environment,
        input=request._canonical_json(_request()),
        capture_output=True,
        check=False,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr.decode()
    classifier_arguments = json.loads(classifier_log.read_text())
    assert classifier_arguments[:2] == ["--root", str(team_mimir)]
    assert classifier_arguments[-1] == "profiles/brokkr/SOUL.md"
    hermes_calls = [json.loads(line) for line in hermes_log.read_text().splitlines()]
    assert hermes_calls[0] == {
        "argv": ["profile-request", "doctor", "--target", "brokkr"],
        "stdin": "",
    }
    assert hermes_calls[1]["argv"] == ["profile-request", "suggest"]
    expected_envelope = request.build_envelope(_request(), classification)
    assert hermes_calls[1]["stdin"] == request._canonical_json(expected_envelope).decode()


def test_ordinary_request_proceeds_without_target_or_hermes() -> None:
    def forbidden_hermes(*args, **kwargs):
        raise AssertionError("ordinary work must not contact Hermes")

    output = request.route_request(
        {"paths": ["docs/team/README.md"]},
        team_mimir_root=Path("/team-mimir"),
        classifier_runner=_classifier_runner(_classification("ordinary-repository")),
        hermes_runner=forbidden_hermes,
    )

    decoded = json.loads(output)
    assert decoded["outcome"] == "ordinary_repository"
    assert decoded["hermes_contacted"] is False


@pytest.mark.parametrize(
    ("paths", "case_id"),
    [
        (["profiles/brokkr/SOUL.md"], "target-owned"),
        (["profiles/brokkr/SOUL.md", "docs/team/README.md"], "mixed-target-and-ordinary"),
        (
            ["profiles/brokkr/SOUL.md", "plugins/profile-evolution/plugin.py"],
            "mixed-target-and-external",
        ),
    ],
)
def test_profile_owned_and_single_target_mixed_requests_use_canonical_standard_input(
    paths: list[str], case_id: str
) -> None:
    calls: list = []
    output = request.route_request(
        _request(paths),
        team_mimir_root=Path("/team-mimir"),
        classifier_runner=_classifier_runner(_classification(case_id)),
        hermes_runner=_hermes_runner(calls),
    )

    assert json.loads(output.splitlines()[0]) == {
        "choices": [{"message": {"content": "considered"}}]
    }
    assert calls[0][0] == ["hermes", "profile-request", "doctor", "--target", "brokkr"]
    assert calls[1][0] == ["hermes", "profile-request", "suggest"]
    envelope = json.loads(calls[1][1]["input"])
    assert set(envelope) == set(request.ENVELOPE_FIELDS)
    assert envelope["target"] == "brokkr"
    assert "paths" not in envelope


@pytest.mark.parametrize(
    ("case_id", "match"),
    [
        ("cross-target-aggregation", "one target-addressed"),
        ("external-source-custody", "one target-addressed"),
        ("unknown-path", "one target-addressed"),
        ("prohibited-secret-file", "prohibited material"),
    ],
)
def test_unsupported_or_unsafe_classifier_results_stop_without_hermes(
    case_id: str, match: str
) -> None:
    case = next(row for row in _fixture()["cases"] if row["id"] == case_id)

    with pytest.raises(request.RequestError, match=match):
        request.route_request(
            _request(case["paths"]),
            team_mimir_root=Path("/team-mimir"),
            classifier_runner=_classifier_runner(case["expected"]),
            hermes_runner=lambda *args, **kwargs: pytest.fail("Hermes must not be called"),
        )


def test_classifier_drift_nonzero_and_timeout_fail_without_echoing_input() -> None:
    drifted = deepcopy(_classification("target-owned"))
    drifted["owner"] = "attacker-provided-private-value"
    with pytest.raises(request.RequestError, match="drifted") as drift:
        request.classify_paths(
            ["profiles/brokkr/SOUL.md"],
            team_mimir_root=Path("/team-mimir"),
            runner=_classifier_runner(drifted),
        )
    assert "attacker-provided-private-value" not in str(drift.value)

    with pytest.raises(request.RequestError, match="classifier failed"):
        request.classify_paths(
            ["profiles/brokkr/SOUL.md"],
            team_mimir_root=Path("/team-mimir"),
            runner=lambda *args, **kwargs: Result(3, b"private"),
        )
    with pytest.raises(request.RequestError, match="timed out"):
        request.classify_paths(
            ["profiles/brokkr/SOUL.md"],
            team_mimir_root=Path("/team-mimir"),
            runner=lambda *args, **kwargs: (_ for _ in ()).throw(
                subprocess.TimeoutExpired("classifier", 20)
            ),
        )


def test_fixture_digest_drift_fails_closed_without_modifying_imported_bytes(
    tmp_path: Path, monkeypatch
) -> None:
    classifier = tmp_path / "profile-change-classifier.v1.json"
    hermes = tmp_path / "profile-request-cli.v1.json"
    provenance = tmp_path / "provenance.json"
    classifier.write_bytes(CLASSIFIER_FIXTURE.read_bytes() + b"\n")
    hermes.write_bytes(HERMES_FIXTURE.read_bytes())
    provenance.write_bytes(PROVENANCE_FIXTURE.read_bytes())
    monkeypatch.setattr(request, "CLASSIFIER_FIXTURE", classifier)
    monkeypatch.setattr(request, "HERMES_FIXTURE", hermes)
    monkeypatch.setattr(request, "PROVENANCE_FIXTURE", provenance)
    request.load_contracts.cache_clear()
    try:
        with pytest.raises(request.RequestError, match="digest drifted"):
            request.load_contracts()
    finally:
        request.load_contracts.cache_clear()


@pytest.mark.parametrize(
    "value",
    [
        b"{not-json",
        json.dumps(_request(target="A")).encode(),
        json.dumps(_request(intent="token=abcdefghijklmnop")).encode(),
    ],
)
def test_malformed_invalid_target_and_secret_input_are_rejected(value: bytes) -> None:
    if value == b"{not-json":
        with pytest.raises(request.RequestError, match="valid JSON"):
            request._parse_one_json(value)
        return
    parsed = json.loads(value)
    with pytest.raises(request.RequestError):
        request.route_request(
            parsed,
            team_mimir_root=Path("/team-mimir"),
            classifier_runner=_classifier_runner(_classification("target-owned")),
            hermes_runner=lambda *args, **kwargs: pytest.fail("Hermes must not be called"),
        )


def test_oversized_input_is_rejected_before_json_parsing() -> None:
    with pytest.raises(request.RequestError, match="exceeds"):
        request._read_input(io.BytesIO(b"x" * (request.MAX_INPUT_BYTES + 1)))


def test_invented_doctor_fields_service_failure_and_unexpected_output_are_rejected() -> None:
    envelope = request.build_envelope(_request(), _classification("target-owned"))

    def invented_doctor(command, **kwargs):
        return Result(
            stdout=json.dumps(
                {
                    "target": "brokkr",
                    "route_registered": True,
                    "credential_available": True,
                    "service_available": True,
                    "status": "ok",
                    "schema_version": 1,
                }
            ).encode()
        )

    with pytest.raises(request.RequestError, match="incompatible"):
        request.dialogue("suggest", envelope, runner=invented_doctor)
    with pytest.raises(request.RequestError, match="failed"):
        request.dialogue(
            "suggest", envelope, runner=lambda *args, **kwargs: Result(1, b"private service error")
        )

    calls = 0

    def unexpected(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Result(
                stdout=b'{"credential_available":true,"route_registered":true,'
                b'"service_available":true,"target":"brokkr"}'
            )
        return Result(stdout=b'{"unexpected":"private response"}\n')

    with pytest.raises(request.RequestError, match="unexpected dialogue") as error:
        request.dialogue("suggest", envelope, runner=unexpected)
    assert "private response" not in str(error.value)


def test_reply_resume_status_and_census_use_exact_producer_grammar() -> None:
    envelope = request.build_envelope(_request(), _classification("target-owned"))
    calls: list = []
    runner = _hermes_runner(calls)
    request.dialogue("reply", envelope, message="Please clarify.", runner=runner)
    request.dialogue("resume", envelope, runner=runner)

    assert calls[1][0] == [
        "hermes",
        "profile-request",
        "reply",
        "--message",
        "Please clarify.",
    ]
    assert calls[3][0] == ["hermes", "profile-request", "resume"]
    assert calls[1][1]["input"] == request._canonical_json(envelope)

    status_calls: list = []

    def status_runner(command, **kwargs):
        status_calls.append((command, kwargs))
        if command[2] == "doctor":
            return _hermes_runner([])(command, **kwargs)
        return Result(
            stdout=json.dumps(
                {
                    "deadline": "2026-08-08T12:00:00Z",
                    "evidence_verification": "verified",
                    "proposal_revision_digest": envelope["revision_digest"],
                    "public_evidence_digest": "e" * 64,
                    "result": "adopted",
                    "target": "brokkr",
                }
            ).encode()
        )

    request.status(
        {
            "proposal_id": envelope["proposal_id"],
            "revision": envelope["revision_digest"],
            "target": "brokkr",
        },
        runner=status_runner,
    )
    assert status_calls[1][0] == [
        "hermes",
        "profile-request",
        "status",
        "--proposal-id",
        envelope["proposal_id"],
        "--revision",
        envelope["revision_digest"],
        "--target",
        "brokkr",
    ]

    census_calls: list = []
    census_fixture = next(
        case["expected"]["stdout_json"][0]
        for case in json.loads(HERMES_FIXTURE.read_text())["cases"]
        if case["case_id"] == "census"
    )

    def census_runner(command, **kwargs):
        census_calls.append((command, kwargs))
        return Result(stdout=json.dumps(census_fixture).encode())

    request.census(b'{"schema_version":1,"targets":[]}', runner=census_runner)
    assert census_calls[0][0] == ["hermes", "profile-request", "census"]
    assert census_calls[0][1]["input"] == b'{"schema_version":1,"targets":[]}'


@pytest.mark.parametrize(
    "case_id",
    ["suggest", "reply", "resume", "reply-message-at-minimum", "reply-message-at-maximum"],
)
def test_every_pinned_dialogue_success_shape_rejects_adversarial_mutations(
    case_id: str,
) -> None:
    values = _hermes_stdout(case_id)
    envelope = json.loads(HERMES_FIXTURE.read_text())["proposal_envelope"]
    request._validate_dialogue_output(_json_stream(values), envelope)

    mutations: list[list[Any]] = []
    for index, field in ((0, "choices"), *[(1, key) for key in values[1]]):
        mutated = deepcopy(values)
        mutated[index].pop(field)
        mutations.append(mutated)
    mutated = deepcopy(values)
    mutated[0]["private"] = "token=abcdefghijklmnop"
    mutations.append(mutated)
    mutated = deepcopy(values)
    mutated[1]["private"] = "token=abcdefghijklmnop"
    mutations.append(mutated)

    replacements = [
        ((0, "choices"), "not-a-list"),
        ((0, "choices"), []),
        ((0, "choices"), [{"message": {"content": "considered"}, "extra": True}]),
        ((0, "choices"), [{"message": {}}]),
        ((0, "choices"), [{"message": {"content": 7}}]),
        ((0, "choices"), [{"message": {"content": "   "}}]),
        ((0, "choices"), [{"message": {"content": "token=abcdefghijklmnop"}}]),
        ((1, "proposal_id"), "short"),
        ((1, "proposal_revision_digest"), "z" * 64),
        ((1, "target"), "A"),
        ((1, "response_digests"), "not-a-list"),
        ((1, "response_digests"), []),
        ((1, "response_digests"), ["z" * 64]),
        ((1, "continuity_digest"), "z" * 64),
        ((1, "updated_at"), "not-a-timestamp"),
    ]
    for (index, field), replacement in replacements:
        mutated = deepcopy(values)
        mutated[index][field] = replacement
        mutations.append(mutated)

    for mutated in mutations:
        with pytest.raises(request.RequestError, match="unexpected dialogue") as error:
            request._validate_dialogue_output(_json_stream(mutated), envelope)
        assert "abcdefghijklmnop" not in str(error.value)


def test_standard_chat_metadata_is_removed_to_the_producer_projection() -> None:
    values = _hermes_stdout("suggest")
    envelope = json.loads(HERMES_FIXTURE.read_text())["proposal_envelope"]
    values[0].update(
        {
            "created": 1,
            "id": "chatcmpl-public",
            "model": "provider-model",
            "object": "chat.completion",
            "usage": {"total_tokens": 3},
        }
    )
    values[0]["choices"][0].update({"finish_reason": "stop", "index": 0})
    values[0]["choices"][0]["message"]["role"] = "assistant"

    projected = request._validate_dialogue_output(_json_stream(values), envelope)

    assert request._parse_json_stream(projected) == _hermes_stdout("suggest")


def test_adapter_timeout_does_not_preempt_the_producer_transport() -> None:
    assert request.SUBPROCESS_TIMEOUT_SECONDS == 45
    assert request.SUBPROCESS_TIMEOUT_SECONDS > 30


def test_pinned_status_success_shape_rejects_adversarial_mutations() -> None:
    values = _hermes_stdout("status")
    expected = values[0]
    target = expected["target"]
    revision = expected["proposal_revision_digest"]
    request._validate_status_output(_json_stream(values), target, revision)

    mutations: list[list[Any]] = []
    for field in expected:
        mutated = deepcopy(values)
        mutated[0].pop(field)
        mutations.append(mutated)
    mutated = deepcopy(values)
    mutated[0]["private"] = "token=abcdefghijklmnop"
    mutations.append(mutated)
    for field, replacement in {
        "deadline": "not-a-timestamp",
        "evidence_verification": "invented",
        "proposal_revision_digest": "z" * 64,
        "public_evidence_digest": "z" * 64,
        "result": "invented",
        "target": "A",
    }.items():
        mutated = deepcopy(values)
        mutated[0][field] = replacement
        mutations.append(mutated)

    for mutated in mutations:
        with pytest.raises(request.RequestError, match="unexpected status") as error:
            request._validate_status_output(_json_stream(mutated), target, revision)
        assert "abcdefghijklmnop" not in str(error.value)


def test_pinned_census_success_shape_rejects_adversarial_mutations() -> None:
    values = _hermes_stdout("census")
    expected = values[0][0]
    request._validate_census_output(_json_stream(values))

    mutations: list[list[Any]] = [[{}], [[]]]
    for field in expected:
        mutated = deepcopy(values)
        mutated[0][0].pop(field)
        mutations.append(mutated)
    mutated = deepcopy(values)
    mutated[0][0]["private"] = "token=abcdefghijklmnop"
    mutations.append(mutated)
    for field, replacement in {
        "census_id": "short",
        "commit_state": "invented",
        "drift_state": "invented",
        "evidence_verification": "invented",
        "observed_at": "not-a-timestamp",
        "public_evidence_digest": "z" * 64,
        "record_type": "invented",
        "recovery_state": "invented",
        "result": "invented",
        "schema_version": 2,
        "target": "A",
    }.items():
        mutated = deepcopy(values)
        mutated[0][0][field] = replacement
        mutations.append(mutated)
    duplicate = deepcopy(values)
    duplicate[0].append(deepcopy(duplicate[0][0]))
    mutations.append(duplicate)

    for mutated in mutations:
        with pytest.raises(request.RequestError, match="unexpected census") as error:
            request._validate_census_output(_json_stream(mutated))
        assert "abcdefghijklmnop" not in str(error.value)


def test_reply_uses_producer_limit_and_rejects_secret_message() -> None:
    envelope = request.build_envelope(_request(), _classification("target-owned"))
    limit = json.loads(HERMES_FIXTURE.read_text())["contracts"]["limits"]["reply_message"]
    with pytest.raises(request.RequestError, match="too large"):
        request.dialogue("reply", envelope, message="x" * (limit["max_characters"] + 1))
    with pytest.raises(request.RequestError, match="secret-bearing"):
        request.dialogue("reply", envelope, message="token=abcdefghijklmnop")


def test_adapter_contains_no_classifier_copy_or_hook_claim() -> None:
    script = SCRIPT.read_text()
    command = (PLUGIN / "commands/hermes-profile-evolution.md").read_text()
    skill = (PLUGIN / "skills/hermes-profile-evolution/SKILL.md").read_text()

    assert "def _classify_one" not in script
    assert "config.projection.yml" not in script
    assert "classify_profile_change.py" in script
    assert "no supported hook contract" in skill.lower()
    assert "live chat dialogue, not queue" in command.lower()
    assert not (PLUGIN / "hooks").exists()


def test_cli_main_dispatches_native_request_and_dialogue_actions(monkeypatch, capsys) -> None:
    envelope = request.build_envelope(_request(), _classification("target-owned"))
    monkeypatch.setattr(request, "_read_input", lambda: json.dumps(envelope).encode())
    monkeypatch.setattr(
        request,
        "route_request",
        lambda value, **kwargs: b'{"outcome":"ordinary"}\n',
    )
    assert request.main(["--team-mimir-root", "/team-mimir", "request"]) == 0
    assert json.loads(capsys.readouterr().out) == {"outcome": "ordinary"}
    assert request.main(["request"]) == 2
    assert "explicit Team Mimir repository root" in capsys.readouterr().err

    calls: list[tuple[str, object]] = []

    def fake_dialogue(action, value, **kwargs):
        calls.append((action, value))
        return b'{"ok":true}\n'

    monkeypatch.setattr(request, "dialogue", fake_dialogue)
    assert request.main(["resume"]) == 0
    assert calls == [("resume", envelope)]
    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_cli_main_reports_bounded_errors_without_input(monkeypatch, capsys) -> None:
    private_value = "token=abcdefghijklmnop"
    monkeypatch.setattr(
        request,
        "_read_input",
        lambda: json.dumps({"target": "brokkr", "intent": private_value}).encode(),
    )
    monkeypatch.setattr(
        request,
        "route_request",
        lambda value, **kwargs: (_ for _ in ()).throw(
            request.RequestError("request is secret-bearing")
        ),
    )

    assert request.main(["--team-mimir-root", "/team-mimir", "request"]) == 2
    captured = capsys.readouterr()
    assert "request is secret-bearing" in captured.err
    assert private_value not in captured.err
