import os
from pathlib import Path


def test_no_legacy_claude_terminology():
    """
    Enforces that no files in plugins/todoist/ contain forbidden legacy terms.
    This guarantees compliance with Requirement R8.
    """
    plugin_dir = Path("plugins/todoist")

    # Check if directory exists before scanning
    if not plugin_dir.exists():
        return

    forbidden_terms = ["Claude", "Anthropic", ".claude", "<boltArtifact>"]

    for root, dirs, files in os.walk(plugin_dir):
        # Skip binary files or common ignore directories
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv")]

        for file in files:
            if file == "PORTABILITY.md":
                continue

            file_path = Path(root) / file

            # Read content
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Skip binary files
                continue

            for term in forbidden_terms:
                # Check case-insensitive for some, exact for others
                if term.lower() in ("claude", "anthropic"):
                    assert term.lower() not in content.lower(), (
                        f"Forbidden term '{term}' found in {file_path}"
                    )
                else:
                    assert term not in content, f"Forbidden term '{term}' found in {file_path}"
