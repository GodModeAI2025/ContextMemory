#!/usr/bin/env python3
"""
cm_add.py — Add a Memory Node to the Context Tree.

Usage:
  python3 cm_add.py --type architecture --title "API Design" --tags "api,rest" \
    --relevance high --content "Details..." [--project-name NAME] [--parent PARENT_ID]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, ensure_workspace, generate_id, load_tree, save_tree,
    load_index, save_index, save_node, add_history_entry,
    normalize_tags, find_similar_nodes, content_hash, make_temporal,
    VALID_TYPES, VALID_RELEVANCE, VALID_CONFIDENCE, _now
)


def main():
    parser = argparse.ArgumentParser(description="Add a Memory Node")
    parser.add_argument("--type", "-t", required=True, choices=VALID_TYPES)
    parser.add_argument("--title", required=True)
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--relevance", "-r", default="medium", choices=VALID_RELEVANCE)
    parser.add_argument("--confidence", default="medium", choices=VALID_CONFIDENCE,
                        help="How certain is this knowledge? (high/medium/low/unknown)")
    parser.add_argument("--content", "-c", required=True, help="Node content (markdown)")
    parser.add_argument("--content-file", "-f", help="Read content from file instead")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--parent", default=None, help="Parent node ID for nesting")
    parser.add_argument("--force", action="store_true", help="Skip duplicate check")
    parser.add_argument("--path", "-p", default=None, help="Base path")
    # Temporal fields
    parser.add_argument("--source-date", default="", help="When was this knowledge created/published? (ISO 8601)")
    parser.add_argument("--valid-from", default="", help="When does this knowledge start being valid?")
    parser.add_argument("--valid-until", default="", help="When does this knowledge expire?")
    parser.add_argument("--temporal-confidence", default="unknown",
                        choices=["explicit", "inferred", "unknown"],
                        help="How certain is the time attribution?")
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    ensure_workspace(ws)

    content = args.content
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")

    # Duplicate check
    if not args.force:
        similar = find_similar_nodes(ws, args.title, content)
        if similar:
            print("⚠️  Similar nodes found:")
            for s in similar:
                print(f"   - {s['id']}: {s['title']} (similarity: {s['similarity']}, match: {s['match']})")
            print(f"\n   Use --force to add anyway, or cm_update.py to update existing node.")
            print(f"   Tip: Consider merging with '{similar[0]['id']}' instead.")
            return

    # Generate ID and save
    node_id = generate_id(args.type, ws)
    tags = normalize_tags(args.tags)
    temporal = make_temporal(args.source_date, args.valid_from, args.valid_until, args.temporal_confidence)
    
    # Temporal display
    time_info = ""
    if args.source_date:
        time_info += f"**Source Date:** {args.source_date}  \n"
    if args.valid_from or args.valid_until:
        vf = args.valid_from or "?"
        vu = args.valid_until or "ongoing"
        time_info += f"**Valid:** {vf} → {vu}  \n"

    # Build markdown content for node file
    node_md = f"""# {args.title}

**Type:** {args.type} | **Relevance:** {args.relevance} | **Confidence:** {args.confidence} | **Status:** active  
**Tags:** {', '.join(tags) if tags else 'none'}  
**Created:** {_now()}  
{time_info}
---

{content}
"""
    save_node(ws, node_id, node_md)

    # Update index
    index = load_index(ws)
    index["nodes"][node_id] = {
        "title": args.title,
        "type": args.type,
        "tags": tags,
        "relevance": args.relevance,
        "confidence": args.confidence,
        "status": "active",
        "created": _now(),
        "updated": _now(),
        "parent": args.parent,
        "hash": content_hash(content),
        "temporal": temporal
    }
    save_index(ws, index)

    # Update tree
    tree = load_tree(ws)
    node_ref = {"id": node_id, "children": []}
    
    if args.parent:
        # Find parent in tree and add as child
        if not _add_to_parent(tree.get("root_children", []), args.parent, node_ref):
            # Parent not found in tree, add to root with warning
            tree.setdefault("root_children", []).append(node_ref)
            print(f"⚠️  Parent '{args.parent}' not found in tree, added to root level.")
    else:
        tree.setdefault("root_children", []).append(node_ref)
    
    save_tree(ws, tree)

    # Log history
    add_history_entry(ws, "add", node_id, f"Added: {args.title} [{args.type}]")

    print(f"✅ Saved as `{node_id}`: {args.title}")
    print(f"   Type: {args.type} | Relevance: {args.relevance} | Confidence: {args.confidence}")
    print(f"   Tags: {', '.join(tags) if tags else 'none'}")
    if args.source_date:
        print(f"   Source date: {args.source_date}")
    if args.parent:
        print(f"   Parent: {args.parent}")
    print(f"   Path: {ws / 'nodes' / f'{node_id}.md'}")


def _add_to_parent(children: list, parent_id: str, node_ref: dict) -> bool:
    """Recursively find parent and add child. Returns True if found."""
    for child in children:
        if child.get("id") == parent_id:
            child.setdefault("children", []).append(node_ref)
            return True
        if _add_to_parent(child.get("children", []), parent_id, node_ref):
            return True
    return False


if __name__ == "__main__":
    main()
