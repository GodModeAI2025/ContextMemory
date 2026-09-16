#!/usr/bin/env python3
"""
cm_cleanup.py — Find and manage outdated or stale Memory Nodes.

Usage:
  python3 cm_cleanup.py [--older-than 30] [--status outdated] [--auto-mark]

Besides nodes not updated for N days, active nodes whose temporal
`valid_until` lies in the past are reported as expired.
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
    expired = []
    by_status = {"active": 0, "outdated": 0, "superseded": 0}

    for nid, meta in nodes.items():
        status = meta.get("status", "active")
        by_status[status] = by_status.get(status, 0) + 1

        if args.status and status != args.status:
            continue

        valid_until = _parse_date((meta.get("temporal") or {}).get("valid_until", ""))
        if status == "active" and valid_until and valid_until < now:
            expired.append({
                "id": nid,
                "title": meta.get("title", "?"),
                "type": meta.get("type", "?"),
                "status": status,
                "valid_until": meta["temporal"]["valid_until"]
            })

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

    if expired:
        print(f"⏳ {len(expired)} active node(s) past their valid_until date:\n")
        for e in expired:
            print(f"   🟠 [{e['id']}] {e['title']}")
            print(f"      Type: {e['type']} | Valid until: {e['valid_until']}")
        print()

    if not stale and not expired:
        print(f"✅ No stale nodes (older than {args.older_than} days).")
        return

    stale.sort(key=lambda x: x["days_old"], reverse=True)
    if stale:
        print(f"⚠️  {len(stale)} node(s) not updated in {args.older_than}+ days:\n")

    for s in stale:
        status_icon = "🟢" if s["status"] == "active" else "🟡" if s["status"] == "outdated" else "❌"
        print(f"   {status_icon} [{s['id']}] {s['title']}")
        print(f"      Type: {s['type']} | {s['days_old']} days old | Last updated: {s['updated']}")

    if args.auto_mark:
        marked = 0
        for e in expired:
            if nodes[e["id"]].get("status") == "active":
                nodes[e["id"]]["status"] = "outdated"
                nodes[e["id"]]["updated"] = _now()
                add_history_entry(ws, "auto-mark-outdated", e["id"], f"Expired: valid_until {e['valid_until']}")
                marked += 1
        for s in stale:
            if nodes[s["id"]].get("status") == "active":
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


def _parse_date(value: str):
    """Parse an ISO 8601 date or datetime; naive values are treated as UTC."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


if __name__ == "__main__":
    main()
