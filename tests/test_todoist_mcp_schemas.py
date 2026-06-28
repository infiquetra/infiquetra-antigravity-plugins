import json
from pathlib import Path


def test_plugin_json_structure():
    plugin_file = Path("plugins/todoist/plugin.json")
    assert plugin_file.exists(), "plugin.json must exist"

    with plugin_file.open() as f:
        data = json.load(f)

    assert "name" in data
    assert "version" in data
    assert "tools" in data

    tools = data["tools"]
    assert len(tools) > 0

    for tool in tools:
        assert "env" in tool
        assert "TODOIST_TOKEN" in tool["env"]
        assert "vault-helper" not in str(tool).lower()
