#!/usr/bin/env python3
"""
cm_relate.py — Knowledge Graph Relations between Memory Nodes.

Adds typed, directional edges between nodes to create a true Knowledge Graph.
Supports relation types like: depends_on, caused_by, implements, supersedes, etc.

Usage:
  python3 cm_relate.py --from arch-001 --to dep-001 --relation depends_on
  python3 cm_relate.py --from bug-001 --to les-001 --relation caused_by --note "Fix in v2.3"
  python3 cm_relate.py --show arch-001          # Show all relations for a node
  python3 cm_relate.py --graph                   # Show full knowledge graph
  python3 cm_relate.py --path arch-001 bug-001   # Find connection path
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, ensure_workspace, load_index, add_history_entry, _now
)

# ─── Relation Types ──────────────────────────────────────────────────

RELATION_TYPES = {
    # Structural
    "depends_on":    {"label": "hängt ab von",      "icon": "🔗", "reverse": "required_by"},
    "required_by":   {"label": "benötigt von",       "icon": "🔗", "reverse": "depends_on"},
    "part_of":       {"label": "ist Teil von",       "icon": "🧩", "reverse": "contains"},
    "contains":      {"label": "enthält",            "icon": "🧩", "reverse": "part_of"},
    
    # Causal
    "caused_by":     {"label": "verursacht durch",   "icon": "⚡", "reverse": "causes"},
    "causes":        {"label": "verursacht",         "icon": "⚡", "reverse": "caused_by"},
    "fixed_by":      {"label": "behoben durch",      "icon": "🔧", "reverse": "fixes"},
    "fixes":         {"label": "behebt",             "icon": "🔧", "reverse": "fixed_by"},
    
    # Semantic
    "implements":    {"label": "implementiert",      "icon": "⚙️", "reverse": "implemented_by"},
    "implemented_by":{"label": "implementiert durch", "icon": "⚙️", "reverse": "implements"},
    "supersedes":    {"label": "ersetzt",            "icon": "🔄", "reverse": "superseded_by"},
    "superseded_by": {"label": "ersetzt durch",      "icon": "🔄", "reverse": "supersedes"},
    "related_to":    {"label": "verwandt mit",       "icon": "↔️", "reverse": "related_to"},
    
    # Knowledge
    "documents":     {"label": "dokumentiert",       "icon": "📝", "reverse": "documented_by"},
    "documented_by": {"label": "dokumentiert durch",  "icon": "📝", "reverse": "documents"},
    "validates":     {"label": "validiert",          "icon": "✅", "reverse": "validated_by"},
    "validated_by":  {"label": "validiert durch",    "icon": "✅", "reverse": "validates"},
    "contradicts":   {"label": "widerspricht",       "icon": "⚠️", "reverse": "contradicts"},
    "extends":       {"label": "erweitert",          "icon": "➕", "reverse": "extended_by"},
    "extended_by":   {"label": "erweitert durch",    "icon": "➕", "reverse": "extends"},
    
    # Workflow
    "precedes":      {"label": "kommt vor",          "icon": "⏩", "reverse": "follows"},
    "follows":       {"label": "folgt auf",          "icon": "⏩", "reverse": "precedes"},
    "blocks":        {"label": "blockiert",          "icon": "🚫", "reverse": "blocked_by"},
    "blocked_by":    {"label": "blockiert durch",    "icon": "🚫", "reverse": "blocks"},
}


# ─── Relations Storage ───────────────────────────────────────────────

def _relations_path(ws: Path) -> Path:
    return ws / "relations.json"


def load_relations(ws: Path) -> dict:
    """Load the relations graph."""
    rpath = _relations_path(ws)
    if rpath.exists():
        try:
            return json.loads(rpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"edges": [], "meta": {"created": _now(), "updated": _now()}}


def save_relations(ws: Path, relations: dict) -> None:
    relations["meta"]["updated"] = _now()
    _relations_path(ws).write_text(
        json.dumps(relations, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ─── Core Operations ────────────────────────────────────────────────

def add_relation(ws: Path, from_id: str, to_id: str, relation: str,
                 note: str = "", bidirectional: bool = False) -> dict:
    """Add a directed relation between two nodes."""
    index = load_index(ws)
    nodes = index.get("nodes", {})
    
    if from_id not in nodes:
        return {"error": f"Node '{from_id}' not found"}
    if to_id not in nodes:
        return {"error": f"Node '{to_id}' not found"}
    if relation not in RELATION_TYPES:
        return {"error": f"Unknown relation '{relation}'. Valid: {', '.join(sorted(RELATION_TYPES.keys()))}"}
    if from_id == to_id:
        return {"error": "Cannot relate a node to itself"}
    
    relations = load_relations(ws)
    
    # Check for duplicate
    for edge in relations["edges"]:
        if edge["from"] == from_id and edge["to"] == to_id and edge["relation"] == relation:
            return {"error": f"Relation already exists: {from_id} --{relation}--> {to_id}"}
    
    # Add forward edge
    edge = {
        "from": from_id,
        "to": to_id,
        "relation": relation,
        "note": note,
        "created": _now()
    }
    relations["edges"].append(edge)
    
    # Add reverse edge if bidirectional or symmetric
    reverse = RELATION_TYPES[relation].get("reverse")
    if bidirectional and reverse and reverse != relation:
        reverse_edge = {
            "from": to_id,
            "to": from_id,
            "relation": reverse,
            "note": note,
            "created": _now()
        }
        # Don't add if reverse already exists
        exists = any(
            e["from"] == to_id and e["to"] == from_id and e["relation"] == reverse
            for e in relations["edges"]
        )
        if not exists:
            relations["edges"].append(reverse_edge)
    
    save_relations(ws, relations)
    add_history_entry(ws, "relate", from_id, f"{from_id} --{relation}--> {to_id}: {note}")
    
    return {"success": True, "edge": edge}


def remove_relation(ws: Path, from_id: str, to_id: str, relation: str = None) -> int:
    """Remove relation(s) between two nodes. If relation is None, remove all."""
    relations = load_relations(ws)
    original_count = len(relations["edges"])
    
    relations["edges"] = [
        e for e in relations["edges"]
        if not (
            e["from"] == from_id and e["to"] == to_id and
            (relation is None or e["relation"] == relation)
        )
    ]
    
    removed = original_count - len(relations["edges"])
    if removed > 0:
        save_relations(ws, relations)
        add_history_entry(ws, "unrelate", from_id,
                          f"Removed {removed} relation(s) {from_id} --> {to_id}")
    return removed


def get_node_relations(ws: Path, node_id: str) -> dict:
    """Get all relations for a specific node (incoming and outgoing)."""
    relations = load_relations(ws)
    index = load_index(ws)
    
    outgoing = []
    incoming = []
    
    for edge in relations["edges"]:
        if edge["from"] == node_id:
            target_meta = index.get("nodes", {}).get(edge["to"], {})
            outgoing.append({
                **edge,
                "target_title": target_meta.get("title", edge["to"]),
                "target_type": target_meta.get("type", "?")
            })
        elif edge["to"] == node_id:
            source_meta = index.get("nodes", {}).get(edge["from"], {})
            incoming.append({
                **edge,
                "source_title": source_meta.get("title", edge["from"]),
                "source_type": source_meta.get("type", "?")
            })
    
    return {"outgoing": outgoing, "incoming": incoming}


def find_path(ws: Path, from_id: str, to_id: str, max_depth: int = 6) -> list:
    """Find shortest path between two nodes using BFS."""
    relations = load_relations(ws)
    
    # Build adjacency list
    adj = {}
    for edge in relations["edges"]:
        adj.setdefault(edge["from"], []).append((edge["to"], edge["relation"]))
        # Also traverse reverse direction
        reverse = RELATION_TYPES.get(edge["relation"], {}).get("reverse")
        if reverse:
            adj.setdefault(edge["to"], []).append((edge["from"], f"~{edge['relation']}"))
    
    # BFS
    queue = deque([(from_id, [(from_id, None)])])
    visited = {from_id}
    
    while queue:
        current, path = queue.popleft()
        if len(path) > max_depth:
            continue
        
        for neighbor, rel in adj.get(current, []):
            if neighbor == to_id:
                return path + [(to_id, rel)]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [(neighbor, rel)]))
    
    return []  # No path found


def get_related_context(ws: Path, node_id: str, depth: int = 2) -> list:
    """Get all related nodes within N hops — useful for context assembly."""
    relations = load_relations(ws)
    index = load_index(ws)
    
    visited = set()
    result = []
    queue = deque([(node_id, 0)])
    
    while queue:
        current, d = queue.popleft()
        if current in visited or d > depth:
            continue
        visited.add(current)
        
        if current != node_id:
            meta = index.get("nodes", {}).get(current, {})
            result.append({
                "id": current,
                "title": meta.get("title", current),
                "type": meta.get("type", "?"),
                "relevance": meta.get("relevance", "?"),
                "distance": d
            })
        
        for edge in relations["edges"]:
            if edge["from"] == current and edge["to"] not in visited:
                queue.append((edge["to"], d + 1))
            elif edge["to"] == current and edge["from"] not in visited:
                queue.append((edge["from"], d + 1))
    
    return sorted(result, key=lambda x: (x["distance"], x["id"]))


def print_graph(ws: Path, index: dict):
    """Print the full knowledge graph as ASCII art."""
    relations = load_relations(ws)
    edges = relations.get("edges", [])
    
    if not edges:
        print("📭 No relations defined yet.")
        print("   Use: cm_relate.py --from <ID> --to <ID> --relation <TYPE>")
        return
    
    # Group by from-node
    by_source = {}
    for edge in edges:
        by_source.setdefault(edge["from"], []).append(edge)
    
    # Find all nodes involved
    all_nodes = set()
    for edge in edges:
        all_nodes.add(edge["from"])
        all_nodes.add(edge["to"])
    
    # Find root nodes (nodes that are sources but not targets, or all if circular)
    targets = {e["to"] for e in edges}
    roots = all_nodes - targets
    if not roots:
        roots = all_nodes  # Circular — show all
    
    print(f"\n🕸️  Knowledge Graph ({len(all_nodes)} nodes, {len(edges)} relations)\n")
    
    printed = set()
    
    def print_node(nid, depth=0):
        if nid in printed and depth > 0:
            return
        printed.add(nid)
        
        meta = index.get("nodes", {}).get(nid, {})
        indent = "   " * depth
        title = meta.get("title", nid)
        ntype = meta.get("type", "?")
        
        print(f"{indent}📌 [{nid}] {title} ({ntype})")
        
        for edge in by_source.get(nid, []):
            rel_info = RELATION_TYPES.get(edge["relation"], {})
            icon = rel_info.get("icon", "→")
            label = rel_info.get("label", edge["relation"])
            target_meta = index.get("nodes", {}).get(edge["to"], {})
            target_title = target_meta.get("title", edge["to"])
            note = f' — "{edge["note"]}"' if edge.get("note") else ""
            
            if edge["to"] in printed:
                print(f"{indent}   {icon} ──{label}──→ [{edge['to']}] {target_title} (↩️){note}")
            else:
                print(f"{indent}   {icon} ──{label}──→ [{edge['to']}] {target_title}{note}")
                print_node(edge["to"], depth + 1)
    
    for root in sorted(roots):
        print_node(root)
        print()


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Manage Knowledge Graph Relations")
    
    # Add relation
    parser.add_argument("--from", dest="from_id", help="Source node ID")
    parser.add_argument("--to", dest="to_id", help="Target node ID")
    parser.add_argument("--relation", "-r", choices=list(RELATION_TYPES.keys()),
                        help="Relation type")
    parser.add_argument("--note", default="", help="Optional note about this relation")
    parser.add_argument("--bidirectional", "-b", action="store_true",
                        help="Add reverse relation too")
    
    # Query
    parser.add_argument("--show", "-s", help="Show relations for a node")
    parser.add_argument("--graph", "-g", action="store_true", help="Show full graph")
    parser.add_argument("--path", nargs=2, metavar=("FROM", "TO"),
                        help="Find path between two nodes")
    parser.add_argument("--context", help="Get related context for a node")
    parser.add_argument("--context-depth", type=int, default=2,
                        help="Depth for context traversal")
    
    # Remove
    parser.add_argument("--remove", action="store_true",
                        help="Remove relation (use with --from, --to)")
    
    # List types
    parser.add_argument("--types", action="store_true", help="List all relation types")
    
    # Common
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--base-path", "-p", default=None)
    
    args = parser.parse_args()
    ws = get_workspace(args.project_name, args.base_path)
    ensure_workspace(ws)
    index = load_index(ws)

    # List relation types
    if args.types:
        print("\n📋 Available relation types:\n")
        for name, info in sorted(RELATION_TYPES.items()):
            print(f"   {info['icon']} {name:20s} {info['label']:25s} (reverse: {info['reverse']})")
        return

    # Show full graph
    if args.graph:
        print_graph(ws, index)
        return

    # Show relations for a node
    if args.show:
        node_id = args.show
        meta = index.get("nodes", {}).get(node_id, {})
        if not meta:
            print(f"❌ Node '{node_id}' not found.")
            return
        
        rels = get_node_relations(ws, node_id)
        print(f"\n🔗 Relations for [{node_id}] {meta.get('title', '?')}:\n")
        
        if rels["outgoing"]:
            print("   Outgoing:")
            for r in rels["outgoing"]:
                info = RELATION_TYPES.get(r["relation"], {})
                note = f'  — "{r["note"]}"' if r.get("note") else ""
                print(f"   {info.get('icon', '→')} ──{info.get('label', r['relation'])}──→ "
                      f"[{r['to']}] {r['target_title']}{note}")
        
        if rels["incoming"]:
            print("   Incoming:")
            for r in rels["incoming"]:
                info = RELATION_TYPES.get(r["relation"], {})
                note = f'  — "{r["note"]}"' if r.get("note") else ""
                print(f"   {info.get('icon', '←')} ←──{info.get('label', r['relation'])}── "
                      f"[{r['from']}] {r['source_title']}{note}")
        
        if not rels["outgoing"] and not rels["incoming"]:
            print("   (keine Relationen)")
        return

    # Find path
    if args.path:
        from_id, to_id = args.path
        path = find_path(ws, from_id, to_id)
        if path:
            print(f"\n🛤️  Path from [{from_id}] to [{to_id}] ({len(path)-1} hops):\n")
            for i, (nid, rel) in enumerate(path):
                meta = index.get("nodes", {}).get(nid, {})
                title = meta.get("title", nid)
                if i == 0:
                    print(f"   📌 [{nid}] {title}")
                else:
                    info = RELATION_TYPES.get(rel.lstrip("~"), {})
                    icon = info.get("icon", "→")
                    label = info.get("label", rel)
                    direction = "↑" if rel.startswith("~") else "↓"
                    print(f"   {direction} {icon} {label}")
                    print(f"   📌 [{nid}] {title}")
        else:
            print(f"❌ No path found between [{from_id}] and [{to_id}].")
        return

    # Get related context
    if args.context:
        related = get_related_context(ws, args.context, args.context_depth)
        meta = index.get("nodes", {}).get(args.context, {})
        print(f"\n🌐 Context für [{args.context}] {meta.get('title', '?')} "
              f"(depth: {args.context_depth}):\n")
        if related:
            for r in related:
                dist_bar = "●" * r["distance"] + "○" * (args.context_depth - r["distance"])
                print(f"   {dist_bar} [{r['id']}] {r['title']} ({r['type']})")
        else:
            print("   (keine verbundenen Nodes)")
        return

    # Remove relation
    if args.remove:
        if not args.from_id or not args.to_id:
            print("❌ --remove requires --from and --to")
            return
        removed = remove_relation(ws, args.from_id, args.to_id, args.relation)
        print(f"🗑️  {removed} relation(s) removed.")
        return

    # Add relation
    if args.from_id and args.to_id and args.relation:
        result = add_relation(ws, args.from_id, args.to_id, args.relation,
                              args.note, args.bidirectional)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            info = RELATION_TYPES[args.relation]
            from_title = index.get("nodes", {}).get(args.from_id, {}).get("title", args.from_id)
            to_title = index.get("nodes", {}).get(args.to_id, {}).get("title", args.to_id)
            print(f"✅ {info['icon']} [{args.from_id}] {from_title}")
            print(f"   ──{info['label']}──→")
            print(f"   [{args.to_id}] {to_title}")
            if args.note:
                print(f'   Note: "{args.note}"')
            if args.bidirectional:
                rev = RELATION_TYPES.get(info.get("reverse", ""), {})
                print(f"   + Reverse: {rev.get('icon', '↔')} {rev.get('label', '?')}")
        return

    # No valid action
    parser.print_help()


if __name__ == "__main__":
    main()
