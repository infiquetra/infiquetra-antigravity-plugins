#!/usr/bin/env python3
"""
Port Claude Code Plugins to Antigravity

Automates the migration of legacy Claude plugins (saga, deploy, mission-control)
to the Antigravity architecture.
"""

import json
import re
import shutil
import sys
from pathlib import Path

# Color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
RESET = "\033[0m"

TARGET_PLUGINS = ["saga", "deploy", "mission-control"]


def rewrite_paths_and_syntax(dest_dir: Path):
    """Translates paths and agent syntaxes in the newly copied files."""
    for filepath in dest_dir.rglob("*"):
        if filepath.is_file() and filepath.suffix in [
            ".py",
            ".md",
            ".json",
            ".txt",
            ".yaml",
            ".yml",
        ]:
            try:
                content = filepath.read_text(encoding="utf-8")
                original_content = content

                # 1. Rewrite paths
                content = content.replace(".claude/", ".gemini/")
                content = content.replace("~/.claude/", "~/.gemini/")

                # 2. Rewrite Task invocations: Task agent(args) -> Use the @agent subagent to: args
                content = re.sub(
                    r"Task ([a-zA-Z0-9_-]+)\((.*?)\)",
                    r"Use the @\1 subagent to: \2",
                    content,
                    flags=re.DOTALL,
                )

                # 3. Rewrite @agent mentions, avoiding double append
                content = re.sub(
                    r"@([a-zA-Z0-9_-]+)(?!\w)(?!\s+subagent)", r"@\1 subagent", content
                )

                if content != original_content:
                    filepath.write_text(content, encoding="utf-8")
            except UnicodeDecodeError:
                pass  # Skip files that aren't utf-8


def port_plugin(source_dir: Path, dest_dir: Path) -> tuple[bool, list[str]]:
    errors = []

    if not source_dir.exists():
        errors.append(f"Source plugin directory not found: {source_dir}")
        return False, errors

    try:
        # 1. Copy the plugin directory
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(source_dir, dest_dir)

        # 2. Create plugin.json
        plugin_json = dest_dir / "plugin.json"
        if not plugin_json.exists():
            plugin_data = {
                "name": source_dir.name,
                "version": "1.0.0",
                "description": f"Ported {source_dir.name} plugin",
            }
            plugin_json.write_text(json.dumps(plugin_data, indent=2) + "\n")

        # 3. Consolidate Python scripts into src/
        src_dir = dest_dir / "src"
        src_dir.mkdir(exist_ok=True)

        for py_file in dest_dir.glob("*.py"):
            if py_file.is_file():
                shutil.move(str(py_file), str(src_dir / py_file.name))

        # 4. Rewrite syntax and paths
        rewrite_paths_and_syntax(dest_dir)

        # 5. Strip out legacy artifact syncing/checkpoint logic
        scaffold_script = src_dir / "scaffold_checkpoint.py"
        if scaffold_script.exists():
            scaffold_script.unlink()

    except Exception as e:
        errors.append(f"Exception during porting: {e}")
        return False, errors

    return True, []


def main():
    repo_root = Path(__file__).resolve().parent.parent
    claude_repo_root = repo_root.parent / "infiquetra-claude-plugins"
    source_plugins_dir = claude_repo_root / "plugins"
    dest_plugins_dir = repo_root / "plugins"

    if not source_plugins_dir.exists():
        print(f"{RED}❌ Source plugins directory not found: {source_plugins_dir}{RESET}")
        sys.exit(1)

    dest_plugins_dir.mkdir(parents=True, exist_ok=True)

    all_success = True
    for plugin_name in TARGET_PLUGINS:
        print(f"Porting {plugin_name}...", end=" ")

        source_dir = source_plugins_dir / plugin_name
        dest_dir = dest_plugins_dir / plugin_name

        is_success, errors = port_plugin(source_dir, dest_dir)

        if is_success:
            print(f"{GREEN}✓{RESET}")
        else:
            print(f"{RED}✗{RESET}")
            for err in errors:
                print(f"  {YELLOW}- {err}{RESET}")
            all_success = False

    if all_success:
        print(f"\n{GREEN}{BOLD}✨ All target plugins ported successfully!{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}⚠️ Some plugins failed to port.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
