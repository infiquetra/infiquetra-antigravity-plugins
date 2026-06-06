#!/usr/bin/env python3
"""
Port Claude Code Plugins to Antigravity

Automates the migration of legacy Claude plugins (saga, deploy, mission-control)
to the Antigravity architecture.
"""

import sys
import shutil
import json
from pathlib import Path

# Color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
RESET = "\033[0m"

TARGET_PLUGINS = ["saga", "deploy", "mission-control"]

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
                "description": f"Ported {source_dir.name} plugin"
            }
            plugin_json.write_text(json.dumps(plugin_data, indent=2) + "\n")
            
        # 3. Consolidate Python scripts into src/
        src_dir = dest_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        for py_file in dest_dir.glob("*.py"):
            if py_file.is_file():
                shutil.move(str(py_file), str(src_dir / py_file.name))
                
    except Exception as e:
        errors.append(f"Exception during porting: {e}")
        return False, errors
        
    return len(errors) == 0, errors

def main():
    print(f"\n{BOLD}🚀 Port Claude Plugins to Antigravity{RESET}")
    print(f"{'═' * 45}\n")
    
    repo_root = Path(__file__).parent.parent.resolve()
    claude_repo_root = repo_root.parent / "infiquetra-claude-plugins"
    source_plugins_dir = claude_repo_root / "plugins"
    dest_plugins_dir = repo_root / "plugins"
    
    if not source_plugins_dir.exists():
        print(f"{RED}❌ Source plugins directory not found: {source_plugins_dir}{RESET}")
        sys.exit(1)
        
    dest_plugins_dir.mkdir(exist_ok=True)
    
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
