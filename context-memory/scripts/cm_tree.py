#!/usr/bin/env python3
"""
cm_tree.py — Display the Context Tree.

Usage:
  python3 cm_tree.py [--format visual|compact|detailed] [--project-name NAME]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import get_workspace, load_tree, load_index


TYPE_ICONS = {
    "architecture": "🏗️", "pattern": "🧩", "decision": "⚖️", "lesson": "💡",
    "config": "⚙️", "api": "🔌", "dependency": "📦", "workflow": "🔄",
    "bug": "🐛", "convention": "📏"
}

REL_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}


def print_tree_visual(children: list, index: dict, prefix: str = "", is_last: bool = True):
    """Print a visual tree with box-drawing characters."""
    for i, child in enumerate(children):
        nid = child.get("id", "???")
        meta = index.get("nodes", {}).get(nid, {})
        is_last_child = (i == len(children) - 1)
        
        connector = "└── " if is_last_child else "├── "
        
        type_icon = TYPE_ICONS.get(meta.get("type", ""), "📄")
        rel_icon = REL_ICONS.get(meta.get("relevance", "medium"), "•")
        title = meta.get("title", nid)
        status = meta.get("status", "active")
        
        status_mark = ""
        if status == "outdated":
            status_mark = " ⚠️ OUTDATED"
        elif status == "superseded":
            status_mark = " ❌ SUPERSEDED"
        
        print(f"{prefix}{connector}{type_icon} {nid}: {title} {rel_icon}{status_mark}")
        
        sub_children = child.get("children", [])
        if sub_children:
            new_prefix = prefix + ("    " if is_last_child else "│   ")
            print_tree_visual(sub_children, index, new_prefix, is_last_child)


def print_tree_compact(children: list, index: dict, depth: int = 0):
    """Print a compact list view."""
    for child in children:
        nid = child.get("id", "???")
        meta = index.get("nodes", {}).get(nid, {})
        indent = "  " * depth
        type_short = meta.get("type", "?")[:4]
        title = meta.get("title", nid)
        print(f"{indent}[{nid}] {type_short}: {title}")
        for sub in child.get("children", []):
            print_tree_compact([sub], index, depth + 1)


def print_tree_detailed(children: list, index: dict, ws_path: Path, depth: int = 0):
    """Print detailed view with tags and dates."""
    for child in children:
        nid = child.get("id", "???")
        meta = index.get("nodes", {}).get(nid, {})
        indent = "  " * depth
        
        type_icon = TYPE_ICONS.get(meta.get("type", ""), "📄")
        title = meta.get("title", nid)
        tags = ", ".join(meta.get("tags", []))
        relevance = meta.get("relevance", "?")
        status = meta.get("status", "?")
        updated = meta.get("updated", "?")
        
        print(f"{indent}{type_icon} [{nid}] {title}")
        print(f"{indent}   Relevance: {relevance} | Status: {status} | Updated: {updated}")
        if tags:
            print(f"{indent}   Tags: {tags}")
        print()
        
        for sub in child.get("children", []):
            print_tree_detailed([sub], index, ws_path, depth + 1)


def main():
    parser = argparse.ArgumentParser(description="Display the Context Tree")
    parser.add_argument("--format", "-f", default="visual", choices=["visual", "compact", "detailed"])
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    parser.add_argument("--types", action="store_true", help="Show type distribution")
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    if not (ws / "tree.json").exists():
        print("❌ No workspace found. Run cm_init.py first.")
        sys.exit(1)

    tree = load_tree(ws)
    index = load_index(ws)
    children = tree.get("root_children", [])
    total = len(index.get("nodes", {}))

    print(f"\n🌳 Context Tree: {tree.get('project', ws.name)}")
    print(f"   {total} node(s) | Last updated: {tree.get('updated', '?')}\n")

    if not children:
        print("   (empty — add knowledge with cm_add.py or cm_curate.py)")
        return

    if args.types:
        type_counts = {}
        for meta in index.get("nodes", {}).values():
            t = meta.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        print("   Type distribution:")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            icon = TYPE_ICONS.get(t, "📄")
            bar = "█" * c
            print(f"   {icon} {t:15s} {bar} {c}")
        print()

    if args.format == "visual":
        print_tree_visual(children, index)
    elif args.format == "compact":
        print_tree_compact(children, index)
    elif args.format == "detailed":
        print_tree_detailed(children, index, ws)


if __name__ == "__main__":
    main()
