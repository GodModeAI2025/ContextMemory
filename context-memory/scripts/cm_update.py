#!/usr/bin/env python3
"""
cm_update.py — Update an existing Memory Node.

Usage:
  python3 cm_update.py --id arch-001 [--title "New Title"] [--content "New content"]
    [--tags "new,tags"] [--relevance high] [--status outdated]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, load_index, save_index, load_node, save_node,
    add_history_entry, normalize_tags, content_hash,
    VALID_RELEVANCE, VALID_STATUS, _now
)


def main():
    parser = argparse.ArgumentParser(description="Update a Memory Node")
    parser.add_argument("--id", required=True, help="Node ID to update")
    parser.add_argument("--title", default=None)
    parser.add_argument("--content", "-c", default=None)
    parser.add_argument("--content-file", "-f", default=None)
    parser.add_argument("--tags", default=None, help="Comma-separated tags (replaces existing)")
    parser.add_argument("--add-tags", default=None, help="Tags to add (keeps existing)")
    parser.add_argument("--relevance", "-r", default=None, choices=VALID_RELEVANCE)
    parser.add_argument("--status", "-s", default=None, choices=VALID_STATUS)
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    index = load_index(ws)

    if args.id not in index.get("nodes", {}):
        print(f"❌ Node '{args.id}' not found.")
        sys.exit(1)

    meta = index["nodes"][args.id]
    changes = []

    # Update metadata
    if args.title:
        meta["title"] = args.title
        changes.append(f"title → '{args.title}'")

    if args.tags is not None:
        meta["tags"] = normalize_tags(args.tags)
        changes.append(f"tags → {meta['tags']}")

    if args.add_tags:
        new_tags = set(meta.get("tags", [])) | set(normalize_tags(args.add_tags))
        meta["tags"] = sorted(new_tags)
        changes.append(f"added tags: {args.add_tags}")

    if args.relevance:
        meta["relevance"] = args.relevance
        changes.append(f"relevance → {args.relevance}")

    if args.status:
        meta["status"] = args.status
        changes.append(f"status → {args.status}")

    # Update content
    content = args.content
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")

    if content:
        existing = load_node(ws, args.id)
        if existing:
            # Preserve the header, replace content after ---
            parts = existing.split("---", 2)
            if len(parts) >= 3:
                # Rebuild header with updated metadata
                header = parts[0]
                # Update title in header if changed
                if args.title:
                    import re
                    header = re.sub(r'^# .+$', f'# {args.title}', header, flags=re.MULTILINE)
                new_md = f"{header}---\n\n{content}\n"
            else:
                new_md = f"# {meta['title']}\n\n**Updated:** {_now()}\n\n---\n\n{content}\n"
        else:
            new_md = f"# {meta['title']}\n\n**Updated:** {_now()}\n\n---\n\n{content}\n"
        
        save_node(ws, args.id, new_md)
        meta["hash"] = content_hash(content)
        changes.append("content updated")

    meta["updated"] = _now()
    save_index(ws, index)
    add_history_entry(ws, "update", args.id, "; ".join(changes))

    print(f"✅ Updated `{args.id}`: {meta['title']}")
    for c in changes:
        print(f"   • {c}")


if __name__ == "__main__":
    main()
