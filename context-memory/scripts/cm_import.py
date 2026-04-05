#!/usr/bin/env python3
"""
cm_import.py — Import Context Memory from JSON backup.

Usage:
  python3 cm_import.py --input backup.json [--project-name NAME] [--merge]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, ensure_workspace, load_index, save_index,
    load_tree, save_tree, save_node, add_history_entry, load_history, save_history,
    _now
)


def main():
    parser = argparse.ArgumentParser(description="Import Context Memory from JSON")
    parser.add_argument("--input", "-i", required=True, help="JSON file to import")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    parser.add_argument("--merge", action="store_true",
                        help="Merge with existing (default: skip if exists)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing workspace entirely")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Failed to read JSON: {e}")
        sys.exit(1)

    if data.get("format") != "context-memory-v1":
        print(f"⚠️  Unknown format: {data.get('format', '?')}. Attempting import anyway.")

    project_name = args.project_name or data.get("tree", {}).get("project", "imported")
    ws = get_workspace(project_name, args.path)

    existing = (ws / "tree.json").exists()
    if existing and not args.merge and not args.overwrite:
        print(f"⚠️  Workspace already exists: {ws}")
        print(f"   Use --merge to add to existing or --overwrite to replace.")
        return

    ensure_workspace(ws)

    imported_nodes = data.get("nodes", {})
    imported_tree = data.get("tree", {})
    imported_history = data.get("history", {})

    if args.overwrite or not existing:
        # Full import
        save_tree(ws, imported_tree)
        
        index = {"nodes": {}}
        for nid, node_data in imported_nodes.items():
            content = node_data.pop("content", "")
            if content:
                save_node(ws, nid, content)
            index["nodes"][nid] = node_data
        save_index(ws, index)
        
        if imported_history:
            save_history(ws, imported_history)
        
        add_history_entry(ws, "import", "*", f"Full import from {input_path.name}")
        print(f"✅ Imported {len(imported_nodes)} nodes → {ws}")

    elif args.merge:
        # Merge with existing
        index = load_index(ws)
        tree = load_tree(ws)
        added = 0
        skipped = 0

        for nid, node_data in imported_nodes.items():
            if nid in index.get("nodes", {}):
                skipped += 1
                continue
            
            content = node_data.pop("content", "")
            if content:
                save_node(ws, nid, content)
            index.setdefault("nodes", {})[nid] = node_data
            tree.setdefault("root_children", []).append({"id": nid, "children": []})
            added += 1

        save_index(ws, index)
        save_tree(ws, tree)
        add_history_entry(ws, "merge-import", "*",
                          f"Merged {added} nodes from {input_path.name} (skipped {skipped})")
        
        print(f"✅ Merged: {added} added, {skipped} skipped (already existed)")

    print(f"   Workspace: {ws}")


if __name__ == "__main__":
    main()
