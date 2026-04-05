#!/usr/bin/env python3
"""
cm_stats.py — Show Context Memory statistics.

Usage:
  python3 cm_stats.py [--project-name NAME]
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import get_workspace, load_tree, load_index, load_history


def main():
    parser = argparse.ArgumentParser(description="Show workspace statistics")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    if not (ws / "tree.json").exists():
        print("❌ No workspace found.")
        sys.exit(1)

    tree = load_tree(ws)
    index = load_index(ws)
    history = load_history(ws)
    nodes = index.get("nodes", {})

    # Basic stats
    print(f"\n📊 Context Memory Statistics")
    print(f"   Project: {tree.get('project', ws.name)}")
    print(f"   Created: {tree.get('created', '?')}")
    print(f"   Updated: {tree.get('updated', '?')}")
    print(f"   Path: {ws}\n")

    print(f"   📝 Total nodes: {len(nodes)}")
    
    # Type distribution
    types = Counter(m.get("type", "unknown") for m in nodes.values())
    if types:
        print(f"\n   📋 By Type:")
        for t, c in types.most_common():
            bar = "█" * c
            print(f"      {t:15s} {bar} {c}")

    # Relevance distribution
    relevance = Counter(m.get("relevance", "medium") for m in nodes.values())
    if relevance:
        icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
        print(f"\n   🎯 By Relevance:")
        for r in ["critical", "high", "medium", "low"]:
            c = relevance.get(r, 0)
            if c > 0:
                print(f"      {icons.get(r, '•')} {r:10s} {'█' * c} {c}")

    # Status distribution
    status = Counter(m.get("status", "active") for m in nodes.values())
    if status:
        print(f"\n   📌 By Status:")
        for s, c in status.most_common():
            print(f"      {s:12s} {c}")

    # Source distribution
    sources = Counter(m.get("source", "manual") for m in nodes.values())
    if sources:
        print(f"\n   🔧 By Source:")
        for s, c in sources.most_common():
            print(f"      {s:15s} {c}")

    # Tag cloud (top 15)
    all_tags = []
    for m in nodes.values():
        all_tags.extend(m.get("tags", []))
    tag_counts = Counter(all_tags)
    if tag_counts:
        top_tags = tag_counts.most_common(15)
        print(f"\n   🏷️  Top Tags:")
        print(f"      {', '.join(f'{t}({c})' for t, c in top_tags)}")

    # History stats
    entries = history.get("entries", [])
    if entries:
        actions = Counter(e.get("action", "?") for e in entries)
        print(f"\n   📜 History: {len(entries)} entries")
        print(f"      " + " | ".join(f"{a}: {c}" for a, c in actions.most_common()))

    # Disk usage
    nodes_dir = ws / "nodes"
    if nodes_dir.exists():
        total_size = sum(f.stat().st_size for f in nodes_dir.iterdir() if f.is_file())
        print(f"\n   💾 Disk: {total_size / 1024:.1f} KB in node files")

    print()


if __name__ == "__main__":
    main()
