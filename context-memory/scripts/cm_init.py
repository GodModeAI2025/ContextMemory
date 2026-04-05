#!/usr/bin/env python3
"""
cm_init.py — Initialize a Context Memory workspace.

Usage:
  python3 cm_init.py [--project-name NAME] [--path BASE_PATH]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import get_workspace, ensure_workspace, load_tree, list_projects


def main():
    parser = argparse.ArgumentParser(description="Initialize Context Memory workspace")
    parser.add_argument("--project-name", "-n", default=None, help="Project name")
    parser.add_argument("--path", "-p", default=None, help="Base path for storage")
    parser.add_argument("--list", "-l", action="store_true", help="List existing projects")
    args = parser.parse_args()

    if args.list:
        projects = list_projects(args.path)
        if not projects:
            print("No projects found.")
        else:
            print(f"Found {len(projects)} project(s):\n")
            for p in projects:
                print(f"  📁 {p['name']}")
                print(f"     Nodes: {p['node_count']} | Updated: {p['updated']}")
                print(f"     Path: {p['path']}\n")
        return

    ws = get_workspace(args.project_name, args.path)
    
    already_exists = (ws / "tree.json").exists()
    ensure_workspace(ws)
    
    tree = load_tree(ws)
    
    if already_exists:
        print(f"✅ Workspace already exists: {ws}")
        print(f"   Project: {tree.get('project', ws.name)}")
        print(f"   Created: {tree.get('created', 'unknown')}")
    else:
        # Update project name in tree
        if args.project_name:
            tree["project"] = args.project_name
            (ws / "tree.json").write_text(
                json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        print(f"🚀 Workspace created: {ws}")
        print(f"   Project: {tree.get('project', ws.name)}")
    
    print(f"\n   Structure:")
    print(f"   ├── tree.json    (Context Tree)")
    print(f"   ├── nodes/       (Memory Nodes)")
    print(f"   ├── index.json   (Search Index)")
    print(f"   └── history.json (Change History)")


if __name__ == "__main__":
    main()
