import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the plugins directory to sys.path to allow importing the script
plugins_dir = Path(__file__).parent.parent / "plugins"
sys.path.append(str(plugins_dir))

from todoist.src.core.todoist_client import TodoistClient

@patch('todoist.src.core.todoist_client.TodoistAPI')
def test_tasks_list_success(mock_api_class, capsys):
    mock_api = MagicMock()
    mock_api_class.return_value = mock_api
    
    mock_task = MagicMock()
    mock_task.id = "1"
    mock_task.content = "Test Task"
    mock_task.description = ""
    mock_task.project_id = "p1"
    mock_task.section_id = None
    mock_task.parent_id = None
    mock_task.order = 1
    mock_task.priority = 1
    mock_task.is_completed = False
    mock_task.labels = []
    mock_task.created_at = "2023-01-01T00:00:00Z"
    mock_task.creator_id = "user1"
    mock_task.url = "http://todoist.com/task/1"
    mock_task.due = None
    mock_task.duration = None
    
    mock_api.get_tasks.return_value = [mock_task]
    
    client = TodoistClient(token="fake-token")
    client.tasks_list()
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    
    assert output["success"] is True
    assert output["count"] == 1
    assert output["data"][0]["id"] == "1"

@patch('todoist.src.core.todoist_client.TodoistAPI')
def test_tasks_list_error(mock_api_class, capsys):
    mock_api = MagicMock()
    mock_api_class.return_value = mock_api
    mock_api.get_tasks.side_effect = Exception("API Error")
    
    client = TodoistClient(token="fake-token")
    
    with pytest.raises(SystemExit):
        client.tasks_list()
        
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    
    assert output["error"] is True
    assert "API Error" in output["message"]
