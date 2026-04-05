#!/usr/bin/env python3
"""
cm_cleanup.py — Find and manage outdated or stale Memory Nodes.

Usage:
  python3 cm_cleanup.py [--older-than 30] [--status outdated] [--auto-mark]
"""

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import get_workspace, load_index, save_index, add_history_entry, _now


def main():
    parser = argparse.ArgumentParser(description="Find stale Memory Nodes")
    parser.add_argument("--older-than", type=int, default=30, help="Days since last update")
    parser.add_argument("--status", default=None, help="Filter by status")
    parser.add_argument("--auto-mark", action="store_true", help="Mark stale nodes as outdated")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    index = load_index(ws)
    nodes = index.get("nodes", {})

    if not nodes:
        print("📭 No nodes to check.")
        return

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=args.older_than)
    stale = []
    by_status = {"active": 0, "outdated": 0, "superseded": 0}

    for nid, meta in nodes.items():
        status = meta.get("status", "active")
        by_status[status] = by_status.get(status, 0) + 1

        if args.status and status != args.status:
            continue

        updated = meta.get("updated", meta.get("created", ""))
        if updated:
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated_dt < cutoff:
                    days_old = (now - updated_dt).days
                    stale.append({
                        "id": nid,
                        "title": meta.get("title", "?"),
                        "type": meta.get("type", "?"),
                        "status": status,
                        "days_old": days_old,
                        "updated": updated
                    })
            except (ValueError, TypeError):
                pass

    print(f"\n📊 Node Status Overview:")
    print(f"   Active: {by_status.get('active', 0)} | Outdated: {by_status.get('outdated', 0)} | Superseded: {by_status.get('superseded', 0)}")
    print(f"   Total: {len(nodes)}\n")

    if not stale:
        print(f"✅ No stale nodes (older than {args.older_than} days).")
        return

    stale.sort(key=lambda x: x["days_old"], reverse=True)
    print(f"⚠️  {len(stale)} node(s) not updated in {args.older_than}+ days:\n")

    for s in stale:
        status_icon = "🟢" if s["status"] == "active" else "🟡" if s["status"] == "outdated" else "❌"
        print(f"   {status_icon} [{s['id']}] {s['title']}")
        print(f"      Type: {s['type']} | {s['days_old']} days old | Last updated: {s['updated']}")

    if args.auto_mark:
        marked = 0
        for s in stale:
            if s["status"] == "active":
                nodes[s["id"]]["status"] = "outdated"
                nodes[s["id"]]["updated"] = _now()
                add_history_entry(ws, "auto-mark-outdated", s["id"], f"Auto-marked after {s['days_old']} days")
                marked += 1
        if marked:
            save_index(ws, index)
            print(f"\n   🔄 Auto-marked {marked} active node(s) as 'outdated'.")
    else:
        print(f"\n   Tip: Use --auto-mark to mark active stale nodes as 'outdated'.")
        print(f"   Or use cm_update.py --id <ID> --status outdated to mark individually.")


if __name__ == "__main__":
    main()
