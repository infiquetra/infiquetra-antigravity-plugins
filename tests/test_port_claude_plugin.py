import pytest
from pathlib import Path
import json
import sys

# Add scripts directory to path to import the script
repo_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(repo_root))
from scripts.port_claude_plugin import port_plugin

@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock the home directory to prevent host filesystem leakage to ~/.claude and ~/.gemini"""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    
    # Create the mocked dirs
    (home_dir / ".claude").mkdir()
    (home_dir / ".gemini").mkdir()
    
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    return home_dir

@pytest.fixture
def source_plugin_dir(tmp_path):
    source_dir = tmp_path / "source_plugins" / "test_plugin"
    source_dir.mkdir(parents=True)
    
    # Add a loose python script
    (source_dir / "helper.py").write_text("print('hello')\n")
    return source_dir

def test_port_plugin_happy_path(source_plugin_dir, tmp_path, mock_home):
    dest_dir = tmp_path / "dest_plugins" / "test_plugin"
    
    is_success, errors = port_plugin(source_plugin_dir, dest_dir)
    
    assert is_success is True
    assert len(errors) == 0
    assert dest_dir.exists()
    
    # Check plugin.json created
    plugin_json = dest_dir / "plugin.json"
    assert plugin_json.exists()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "test_plugin"
    
    # Check src/ consolidation
    src_dir = dest_dir / "src"
    assert src_dir.exists()
    assert (src_dir / "helper.py").exists()
    assert not (dest_dir / "helper.py").exists()

def test_syntax_translation(source_plugin_dir, tmp_path, mock_home):
    (source_plugin_dir / "instructions.md").write_text(
        "Task reviewer(review the code)\n"
        "Ask @reviewer to confirm.\n"
        "Go to ~/.claude/logs and .claude/config\n"
        "Already has @agent subagent applied.\n"
    )
    
    dest_dir = tmp_path / "dest_plugins" / "test_plugin"
    is_success, errors = port_plugin(source_plugin_dir, dest_dir)
    
    assert is_success is True
    
    content = (dest_dir / "instructions.md").read_text()
    assert "Use the @reviewer subagent to: review the code" in content
    assert "Ask @reviewer subagent to confirm." in content
    assert "Already has @agent subagent applied." in content # Should not double append
    assert "~/.gemini/logs" in content
    assert ".gemini/config" in content
