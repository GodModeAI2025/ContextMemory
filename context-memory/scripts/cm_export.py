#!/usr/bin/env python3
"""
cm_export.py — Export Context Memory in multiple formats.

Formats:
  markdown  — Human-readable Markdown document
  json      — Full backup as JSON (for import)
  jsonld    — JSON-LD Knowledge Graph with schema.org context
  mermaid   — Mermaid diagram for visual graph rendering
  chunks    — Embedding-optimized text chunks for RAG pipelines
  all       — All formats at once

Usage:
  python3 cm_export.py --format markdown --output knowledge.md
  python3 cm_export.py --format jsonld --output graph.json
  python3 cm_export.py --format mermaid --output graph.mermaid
  python3 cm_export.py --format chunks --output chunks.jsonl
  python3 cm_export.py --format all --output-dir ./export/
  python3 cm_export.py --validate  # Run quality check without exporting
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import get_workspace, load_tree, load_index, load_node, load_history, _now

# Try loading relations
def _load_relations_safe(ws):
    try:
        rpath = ws / "relations.json"
        if rpath.exists():
            return json.loads(rpath.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"edges": []}


# ─── Quality Validation ──────────────────────────────────────────────

def validate_workspace(ws: Path) -> dict:
    """Run quality checks on the entire workspace. Returns score and issues."""
    index = load_index(ws)
    relations = _load_relations_safe(ws)
    nodes = index.get("nodes", {})
    edges = relations.get("edges", [])
    
    issues = []
    checks_passed = 0
    checks_total = 0
    
    # 1. Every node has a title and content
    checks_total += 1
    missing_content = []
    for nid, meta in nodes.items():
        content = load_node(ws, nid)
        if not content or len(content.strip()) < 20:
            missing_content.append(nid)
    if missing_content:
        issues.append(f"Nodes with missing/empty content: {', '.join(missing_content)}")
    else:
        checks_passed += 1
    
    # 2. No orphan relation references
    checks_total += 1
    node_ids = set(nodes.keys())
    orphan_edges = []
    for edge in edges:
        if edge.get("from") not in node_ids:
            orphan_edges.append(f"{edge['from']} (source)")
        if edge.get("to") not in node_ids:
            orphan_edges.append(f"{edge['to']} (target)")
    if orphan_edges:
        issues.append(f"Orphan relation references: {', '.join(orphan_edges)}")
    else:
        checks_passed += 1
    
    # 3. No duplicate titles
    checks_total += 1
    titles = {}
    for nid, meta in nodes.items():
        t = meta.get("title", "")
        titles.setdefault(t, []).append(nid)
    dupes = {t: ids for t, ids in titles.items() if len(ids) > 1}
    if dupes:
        dupe_strs = [f"'{t}': {ids}" for t, ids in dupes.items()]
        issues.append(f"Duplicate titles: {'; '.join(dupe_strs)}")
    else:
        checks_passed += 1
    
    # 4. Every node has tags
    checks_total += 1
    no_tags = [nid for nid, m in nodes.items() if not m.get("tags")]
    if no_tags:
        issues.append(f"Nodes without tags: {', '.join(no_tags)}")
    else:
        checks_passed += 1
    
    # 5. Confidence field present
    checks_total += 1
    no_conf = [nid for nid, m in nodes.items() if not m.get("confidence")]
    if no_conf:
        issues.append(f"Nodes without confidence: {', '.join(no_conf)} (defaulting to 'medium')")
    else:
        checks_passed += 1
    
    # 6. Temporal data present on at least some nodes
    checks_total += 1
    has_temporal = sum(1 for m in nodes.values()
                       if m.get("temporal", {}).get("source_date"))
    if has_temporal == 0 and len(nodes) > 0:
        issues.append("No nodes have temporal data (source_date). Consider adding time context.")
    else:
        checks_passed += 1
    
    # 7. Active nodes exist
    checks_total += 1
    active = sum(1 for m in nodes.values() if m.get("status") == "active")
    if active == 0 and len(nodes) > 0:
        issues.append("No active nodes — all are outdated or superseded.")
    else:
        checks_passed += 1
    
    # 8. Relations exist if >3 nodes
    checks_total += 1
    if len(nodes) > 3 and len(edges) == 0:
        issues.append("No relations defined. Consider connecting your knowledge nodes.")
    else:
        checks_passed += 1
    
    score = round((checks_passed / checks_total) * 100) if checks_total > 0 else 0
    
    return {
        "score": score,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "issues": issues,
        "stats": {
            "total_nodes": len(nodes),
            "active_nodes": active,
            "total_relations": len(edges),
            "nodes_with_temporal": has_temporal,
            "nodes_with_confidence": len(nodes) - len(no_conf)
        }
    }


# ─── Markdown Export ─────────────────────────────────────────────────

def export_markdown(ws: Path, output: Path):
    """Export as a readable Markdown document."""
    tree = load_tree(ws)
    index = load_index(ws)
    relations = _load_relations_safe(ws)
    nodes = index.get("nodes", {})
    validation = validate_workspace(ws)

    lines = [
        f"# Context Memory: {tree.get('project', ws.name)}",
        f"",
        f"*Exported: {_now()} | {len(nodes)} nodes | "
        f"Quality: {validation['score']}/100*",
        f"",
        "---",
        ""
    ]

    by_type = {}
    for nid, meta in sorted(nodes.items()):
        t = meta.get("type", "other")
        by_type.setdefault(t, []).append((nid, meta))

    type_titles = {
        "architecture": "Architecture", "pattern": "Patterns",
        "decision": "Decisions", "lesson": "Lessons Learned",
        "config": "Configuration", "api": "APIs",
        "dependency": "Dependencies", "workflow": "Workflows",
        "bug": "Bugs & Fixes", "convention": "Conventions"
    }

    for t, items in sorted(by_type.items()):
        lines.append(f"## {type_titles.get(t, t.title())}")
        lines.append("")
        for nid, meta in items:
            status = meta.get("status", "active")
            if status == "superseded":
                continue
            content = load_node(ws, nid)
            body = _extract_body(content) if content else "(content missing)"
            
            status_mark = " ⚠️" if status == "outdated" else ""
            conf = meta.get("confidence", "medium")
            temporal = meta.get("temporal", {})
            
            lines.append(f"### [{nid}] {meta.get('title', '?')}{status_mark}")
            meta_line = f"*{meta.get('relevance', '?')} | confidence: {conf}"
            meta_line += f" | Tags: {', '.join(meta.get('tags', []))}*"
            lines.append(meta_line)
            
            if temporal.get("source_date"):
                time_parts = []
                if temporal.get("source_date"):
                    time_parts.append(f"Source: {temporal['source_date']}")
                if temporal.get("valid_from") or temporal.get("valid_until"):
                    vf = temporal.get("valid_from", "?")
                    vu = temporal.get("valid_until", "ongoing")
                    time_parts.append(f"Valid: {vf} → {vu}")
                lines.append(f"*🕐 {' | '.join(time_parts)}*")
            
            lines.append("")
            lines.append(body)
            lines.append("")
            lines.append("---")
            lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Exported {len(nodes)} nodes as Markdown → {output}")


# ─── JSON Backup Export ──────────────────────────────────────────────

def export_json(ws: Path, output: Path):
    """Export as JSON for backup/transfer."""
    tree = load_tree(ws)
    index = load_index(ws)
    history = load_history(ws)
    relations = _load_relations_safe(ws)

    nodes_with_content = {}
    for nid in index.get("nodes", {}):
        content = load_node(ws, nid)
        nodes_with_content[nid] = {
            **index["nodes"][nid],
            "content": content or ""
        }

    export_data = {
        "format": "context-memory-v2",
        "tree": tree,
        "nodes": nodes_with_content,
        "relations": relations,
        "history": history
    }

    output.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Exported {len(nodes_with_content)} nodes as JSON → {output}")


# ─── JSON-LD Knowledge Graph Export ──────────────────────────────────

def export_jsonld(ws: Path, output: Path):
    """Export as JSON-LD Knowledge Graph with schema.org context."""
    tree = load_tree(ws)
    index = load_index(ws)
    relations = _load_relations_safe(ws)
    validation = validate_workspace(ws)
    nodes = index.get("nodes", {})
    edges = relations.get("edges", [])

    # Build clusters from types
    clusters = {}
    for nid, meta in nodes.items():
        t = meta.get("type", "other")
        if t not in clusters:
            clusters[t] = {"id": t, "label": t.title(), "concepts": []}
        clusters[t]["concepts"].append(nid)

    # Build JSON-LD nodes
    ld_nodes = []
    for nid, meta in nodes.items():
        content = load_node(ws, nid)
        body = _extract_body(content) if content else ""
        
        # Extract statements (non-empty lines from body)
        statements = [l.strip().lstrip("- ").lstrip("* ")
                      for l in body.split("\n")
                      if l.strip() and not l.startswith("#") and not l.startswith("**")][:5]
        
        temporal = meta.get("temporal", {})
        
        ld_nodes.append({
            "id": nid,
            "label": meta.get("title", nid),
            "type": meta.get("type", "unknown"),
            "cluster": meta.get("type", "unknown"),
            "confidence": meta.get("confidence", "medium"),
            "relevance_level": meta.get("relevance", "medium"),
            "definition": meta.get("title", ""),
            "relevance": f"Tagged: {', '.join(meta.get('tags', []))}",
            "status": meta.get("status", "active"),
            "statements": statements,
            "temporal": {
                "source_date": temporal.get("source_date", ""),
                "source_period": temporal.get("source_date", ""),
                "valid_from": temporal.get("valid_from", ""),
                "valid_until": temporal.get("valid_until", ""),
                "distillation_date": meta.get("created", ""),
                "temporal_confidence": temporal.get("temporal_confidence", "unknown")
            }
        })

    # Build JSON-LD edges
    ld_edges = []
    for edge in edges:
        ld_edges.append({
            "source": edge.get("from", ""),
            "target": edge.get("to", ""),
            "type": edge.get("relation", "related_to"),
            "label": edge.get("note", ""),
            "weight": 1.0,
            "confidence": "high",
            "temporal": {
                "valid_from": "",
                "valid_until": ""
            }
        })

    # Build embedding chunks
    chunks = _build_chunks(ws, index)

    jsonld = {
        "@context": {
            "@vocab": "https://schema.org/",
            "cm": "https://context-memory.dev/v2/",
            "nodes": "cm:nodes",
            "edges": "cm:edges",
            "chunks": "cm:chunks",
            "confidence": "cm:confidence",
            "temporal": "cm:temporal",
            "cluster": "cm:cluster",
            "weight": "cm:weight"
        },
        "metadata": {
            "title": tree.get("project", ws.name),
            "distillation_date": _now(),
            "distiller_version": "2.0",
            "language": "auto",
            "quality_score": validation["score"],
            "concept_count": len(nodes),
            "relationship_count": len(edges),
            "cluster_count": len(clusters)
        },
        "clusters": list(clusters.values()),
        "nodes": ld_nodes,
        "edges": ld_edges,
        "chunks": chunks
    }

    output.write_text(json.dumps(jsonld, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Exported JSON-LD Knowledge Graph → {output}")
    print(f"   {len(ld_nodes)} nodes, {len(ld_edges)} edges, {len(chunks)} chunks")


# ─── Mermaid Diagram Export ──────────────────────────────────────────

def export_mermaid(ws: Path, output: Path):
    """Export as Mermaid diagram for visual rendering."""
    index = load_index(ws)
    relations = _load_relations_safe(ws)
    nodes = index.get("nodes", {})
    edges = relations.get("edges", [])

    lines = ["graph LR"]

    # Style classes for node types
    type_styles = {
        "architecture": ":::arch", "pattern": ":::pat", "decision": ":::dec",
        "lesson": ":::les", "config": ":::cfg", "api": ":::api",
        "dependency": ":::dep", "workflow": ":::wf", "bug": ":::bug",
        "convention": ":::conv"
    }

    # Add nodes
    for nid, meta in nodes.items():
        if meta.get("status") == "superseded":
            continue
        label = meta.get("title", nid)
        # Sanitize for Mermaid (no special chars)
        safe_label = label.replace('"', "'").replace("[", "(").replace("]", ")")
        safe_id = nid.replace("-", "_")
        style = type_styles.get(meta.get("type", ""), "")
        lines.append(f'    {safe_id}["{safe_label}"]{style}')

    # Edge type to Mermaid arrow
    arrow_map = {
        "depends_on": "-->", "required_by": "-->",
        "caused_by": "-.->", "causes": "-.->",
        "fixed_by": "==>", "fixes": "==>",
        "implements": "-->", "implemented_by": "-->",
        "supersedes": "-->", "superseded_by": "-->",
        "related_to": "---",
        "documents": "-->", "documented_by": "-->",
        "validates": "-->", "validated_by": "-->",
        "contradicts": "---",
        "extends": "-->", "extended_by": "-->",
        "precedes": "-->", "follows": "-->",
        "blocks": "-->", "blocked_by": "-->",
        "part_of": "-->", "contains": "-->",
    }

    # Add edges
    for edge in edges:
        src = edge.get("from", "").replace("-", "_")
        tgt = edge.get("to", "").replace("-", "_")
        rel = edge.get("relation", "related_to")
        arrow = arrow_map.get(rel, "-->")
        label = rel.replace("_", " ")
        
        if src in [n.replace("-", "_") for n in nodes] and \
           tgt in [n.replace("-", "_") for n in nodes]:
            lines.append(f'    {src} {arrow}|"{label}"| {tgt}')

    # Style definitions
    lines.append("")
    lines.append("    classDef arch fill:#4A90D9,stroke:#2C5F8A,color:#fff")
    lines.append("    classDef dec fill:#E74C3C,stroke:#C0392B,color:#fff")
    lines.append("    classDef les fill:#F39C12,stroke:#D68910,color:#fff")
    lines.append("    classDef pat fill:#27AE60,stroke:#1E8449,color:#fff")
    lines.append("    classDef bug fill:#E74C3C,stroke:#C0392B,color:#fff")
    lines.append("    classDef cfg fill:#8E44AD,stroke:#6C3483,color:#fff")
    lines.append("    classDef api fill:#3498DB,stroke:#2471A3,color:#fff")
    lines.append("    classDef dep fill:#95A5A6,stroke:#717D7E,color:#fff")
    lines.append("    classDef wf fill:#1ABC9C,stroke:#148F77,color:#fff")
    lines.append("    classDef conv fill:#D5DBDB,stroke:#ABB2B9,color:#333")

    content = "\n".join(lines)
    output.write_text(content, encoding="utf-8")
    print(f"✅ Exported Mermaid diagram → {output}")
    print(f"   {len(nodes)} nodes, {len(edges)} edges")
    print(f"   Paste into Obsidian, GitHub, or mermaid.live to render")


# ─── Embedding Chunks Export ─────────────────────────────────────────

def _build_chunks(ws: Path, index: dict) -> list:
    """Build clean embedding-optimized text chunks from all nodes."""
    chunks = []
    nodes = index.get("nodes", {})
    
    for nid, meta in nodes.items():
        if meta.get("status") == "superseded":
            continue
        content = load_node(ws, nid)
        if not content:
            continue
        body = _extract_body(content)
        if not body.strip():
            continue
        
        # Clean: remove markdown syntax, emojis, wikilinks
        clean = body
        clean = re.sub(r'#{1,6}\s+', '', clean)          # Headers
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)   # Bold
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)       # Italic
        clean = re.sub(r'`(.+?)`', r'\1', clean)         # Inline code
        clean = re.sub(r'```[\s\S]*?```', '', clean)      # Code blocks
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)  # Links
        clean = re.sub(r'\[\[(.+?)\]\]', r'\1', clean)   # Wikilinks
        clean = re.sub(r'[🏗️🧩⚖️💡⚙️🔌📦🔄🐛📏🔴🟠🟡⚪✅❌⚠️🔗🔧➕↔️⏩🚫📝]', '', clean)
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        clean = clean.strip()
        
        if len(clean) < 10:
            continue
        
        # Prepend temporal context as natural language
        temporal = meta.get("temporal", {})
        time_prefix = ""
        if temporal.get("source_date"):
            time_prefix = f"As of {temporal['source_date']}: "
        elif temporal.get("valid_from"):
            time_prefix = f"Valid from {temporal['valid_from']}: "
        
        title = meta.get("title", nid)
        chunk_text = f"{time_prefix}{title}. {clean}"
        
        # Estimate tokens (~4 chars per token)
        token_est = len(chunk_text) // 4
        
        chunks.append({
            "id": f"chunk-{nid}",
            "text": chunk_text,
            "concepts": [nid],
            "type": meta.get("type", "unknown"),
            "temporal_scope": temporal.get("source_date", ""),
            "confidence": meta.get("confidence", "medium"),
            "token_estimate": token_est
        })
    
    return chunks


def export_chunks(ws: Path, output: Path):
    """Export embedding-optimized chunks as JSONL."""
    index = load_index(ws)
    chunks = _build_chunks(ws, index)
    
    lines = [json.dumps(c, ensure_ascii=False) for c in chunks]
    output.write_text("\n".join(lines), encoding="utf-8")
    
    total_tokens = sum(c["token_estimate"] for c in chunks)
    print(f"✅ Exported {len(chunks)} embedding chunks → {output}")
    print(f"   Total estimated tokens: ~{total_tokens:,}")
    print(f"   Format: JSONL (one JSON object per line)")
    print(f"   Ready for: LangChain, LlamaIndex, OpenAI Embeddings, Cohere")


# ─── Helpers ─────────────────────────────────────────────────────────

def _extract_body(content: str) -> str:
    """Extract body text after first --- in a node's markdown."""
    lines = content.split("\n")
    in_body = False
    body_lines = []
    for line in lines:
        if line.strip() == "---" and not in_body:
            in_body = True
            continue
        if in_body:
            body_lines.append(line)
    return "\n".join(body_lines).strip()


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Export Context Memory")
    parser.add_argument("--format", "-f",
                        choices=["markdown", "json", "jsonld", "mermaid", "chunks", "all"],
                        help="Export format")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--output-dir", default=None, help="Output directory (for --format all)")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    parser.add_argument("--validate", "-v", action="store_true",
                        help="Run quality validation without exporting")
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    if not (ws / "tree.json").exists():
        print("❌ No workspace found.")
        sys.exit(1)

    # Validation mode
    if args.validate:
        v = validate_workspace(ws)
        print(f"\n🔍 Quality Validation: {v['score']}/100\n")
        print(f"   Checks passed: {v['checks_passed']}/{v['checks_total']}")
        print(f"   Nodes: {v['stats']['total_nodes']} (active: {v['stats']['active_nodes']})")
        print(f"   Relations: {v['stats']['total_relations']}")
        print(f"   With temporal data: {v['stats']['nodes_with_temporal']}")
        print(f"   With confidence: {v['stats']['nodes_with_confidence']}")
        if v["issues"]:
            print(f"\n   ⚠️  Issues:")
            for issue in v["issues"]:
                print(f"      • {issue}")
        else:
            print(f"\n   ✅ No issues found.")
        return

    if not args.format:
        parser.print_help()
        return

    # Export all formats
    if args.format == "all":
        tree = load_tree(ws)
        name = tree.get("project", ws.name)
        out_dir = Path(args.output_dir) if args.output_dir else Path(".")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        export_markdown(ws, out_dir / f"{name}.knowledge.md")
        export_json(ws, out_dir / f"{name}.knowledge.json")
        export_jsonld(ws, out_dir / f"{name}.knowledge.jsonld.json")
        export_mermaid(ws, out_dir / f"{name}.knowledge.mermaid")
        export_chunks(ws, out_dir / f"{name}.knowledge.chunks.jsonl")
        
        v = validate_workspace(ws)
        print(f"\n📊 Quality Score: {v['score']}/100")
        if v["issues"]:
            for issue in v["issues"]:
                print(f"   ⚠️  {issue}")
        return

    # Single format
    if not args.output:
        print("❌ --output required for single format export.")
        sys.exit(1)

    output = Path(args.output)
    
    exporters = {
        "markdown": export_markdown,
        "json": export_json,
        "jsonld": export_jsonld,
        "mermaid": export_mermaid,
        "chunks": export_chunks,
    }
    
    exporters[args.format](ws, output)
    
    # Always show quality score
    v = validate_workspace(ws)
    print(f"   Quality Score: {v['score']}/100")


if __name__ == "__main__":
    main()
