#!/usr/bin/env python3
"""
cm_delete.py — Delete a Memory Node.

Usage:
  python3 cm_delete.py --id arch-001 [--project-name NAME]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, load_tree, save_tree, load_index, save_index,
    delete_node_file, add_history_entry
)


def _remove_from_tree(children: list, node_id: str) -> bool:
    """Recursively remove a node from the tree. Returns True if found."""
    for i, child in enumerate(children):
        if child.get("id") == node_id:
            # Move orphaned children up to current level
            orphans = child.get("children", [])
            children.pop(i)
            children.extend(orphans)
            return True
        if _remove_from_tree(child.get("children", []), node_id):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Delete a Memory Node")
    parser.add_argument("--id", required=True, help="Node ID to delete")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    parser.add_argument("--keep-children", action="store_true",
                        help="Keep child nodes (re-parent to root)")
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    index = load_index(ws)

    if args.id not in index.get("nodes", {}):
        print(f"❌ Node '{args.id}' not found.")
        sys.exit(1)

    meta = index["nodes"][args.id]
    title = meta.get("title", args.id)

    # Remove from tree
    tree = load_tree(ws)
    _remove_from_tree(tree.get("root_children", []), args.id)
    save_tree(ws, tree)

    # Remove from index
    del index["nodes"][args.id]
    save_index(ws, index)

    # Delete file
    delete_node_file(ws, args.id)

    add_history_entry(ws, "delete", args.id, f"Deleted: {title}")
    print(f"🗑️  Deleted `{args.id}`: {title}")


if __name__ == "__main__":
    main()
