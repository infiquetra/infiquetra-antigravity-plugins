"""Offline safety and request-contract tests for the restored UniFi clients."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SRC / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


NETWORK = _load("unifi_network_client")
PROTECT = _load("unifi_protect_client")


@pytest.mark.parametrize(
    ("module", "class_name"),
    [
        (NETWORK, "UnifiNetworkClient"),
        (PROTECT, "UnifiProtectClient"),
    ],
)
def test_write_requests_are_dry_run_without_confirmation(
    module: ModuleType, class_name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    client = getattr(module, class_name)(api_key="test-key", host="unifi.test")

    with (
        patch.object(module.requests, "request") as request,
        pytest.raises(SystemExit) as exc_info,
    ):
        client._request(
            "POST",
            "https://unifi.test/api/resource",
            data={"name": "test"},
            confirm=False,
        )

    assert exc_info.value.code == 0
    request.assert_not_called()
    output = json.loads(capsys.readouterr().out)
    assert output["dry_run"] is True


@pytest.mark.parametrize(
    ("module", "class_name"),
    [
        (NETWORK, "UnifiNetworkClient"),
        (PROTECT, "UnifiProtectClient"),
    ],
)
def test_read_requests_use_api_key_and_timeout(module: ModuleType, class_name: str) -> None:
    response = MagicMock(status_code=200, content=b'{"ok": true}')
    response.json.return_value = {"ok": True}
    client = getattr(module, class_name)(api_key="test-key", host="unifi.test")

    with patch.object(module.requests, "request", return_value=response) as request:
        result = client._request("GET", "https://unifi.test/api/resource")

    assert result == {"ok": True}
    assert request.call_args.kwargs["headers"]["X-Api-Key"] == "test-key"
    assert request.call_args.kwargs["timeout"] == 30
