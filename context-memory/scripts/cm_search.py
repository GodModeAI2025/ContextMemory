#!/usr/bin/env python3
"""
cm_search.py — Agentic Search across the Context Tree.

Multi-level search:
  1. Quick: exact/fuzzy match on tags, titles, types
  2. Deep: full-text search in node content
  3. Assembly: combine and rank results

Usage:
  python3 cm_search.py --query "authentication" [--type architecture] [--limit 5]
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, ensure_workspace, load_index, load_node,
    VALID_TYPES
)


def quick_search(index: dict, query_words: set, node_type: str = None) -> list:
    """Level 1: Fast search on metadata (tags, title, type)."""
    results = []
    for nid, meta in index.get("nodes", {}).items():
        if meta.get("status") == "superseded":
            continue
        if node_type and meta.get("type") != node_type:
            continue

        score = 0.0
        title_lower = meta.get("title", "").lower()
        tags = set(meta.get("tags", []))

        # Exact tag match (highest weight)
        tag_matches = query_words & tags
        score += len(tag_matches) * 3.0

        # Title word match
        title_words = set(title_lower.split())
        title_matches = query_words & title_words
        score += len(title_matches) * 2.0

        # Partial tag match (substring)
        for qw in query_words:
            for tag in tags:
                if qw in tag or tag in qw:
                    if qw not in tag_matches and tag not in tag_matches:
                        score += 1.0

        # Partial title match (substring)
        for qw in query_words:
            if qw in title_lower and qw not in title_matches:
                score += 0.5

        # Relevance boost
        relevance_boost = {"critical": 1.5, "high": 1.0, "medium": 0.5, "low": 0.0}
        score *= (1 + relevance_boost.get(meta.get("relevance", "medium"), 0) * 0.2)

        if score > 0:
            results.append({
                "id": nid,
                "title": meta.get("title"),
                "type": meta.get("type"),
                "relevance": meta.get("relevance"),
                "status": meta.get("status"),
                "tags": meta.get("tags", []),
                "score": round(score, 2),
                "level": "quick"
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def deep_search(ws: Path, index: dict, query_words: set, exclude_ids: set, node_type: str = None) -> list:
    """Level 2: Full-text search in node content."""
    results = []
    for nid, meta in index.get("nodes", {}).items():
        if nid in exclude_ids:
            continue
        if meta.get("status") == "superseded":
            continue
        if node_type and meta.get("type") != node_type:
            continue

        content = load_node(ws, nid)
        if not content:
            continue

        content_lower = content.lower()
        score = 0.0

        for qw in query_words:
            count = content_lower.count(qw)
            if count > 0:
                # Diminishing returns for repeated matches
                score += min(count, 5) * 0.5

        # Phrase match bonus (consecutive words)
        query_phrase = " ".join(sorted(query_words))
        if len(query_words) > 1:
            for i in range(len(query_words)):
                for j in range(i + 1, len(query_words)):
                    pair = list(query_words)[i] + " " + list(query_words)[j]
                    if pair in content_lower:
                        score += 2.0

        if score > 0:
            # Extract a snippet around the first match
            snippet = _extract_snippet(content, query_words)
            results.append({
                "id": nid,
                "title": meta.get("title"),
                "type": meta.get("type"),
                "relevance": meta.get("relevance"),
                "status": meta.get("status"),
                "tags": meta.get("tags", []),
                "score": round(score, 2),
                "level": "deep",
                "snippet": snippet
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def _extract_snippet(content: str, query_words: set, context_chars: int = 120) -> str:
    """Extract a text snippet around the first query word match."""
    content_lower = content.lower()
    best_pos = len(content)
    
    for qw in query_words:
        pos = content_lower.find(qw)
        if 0 <= pos < best_pos:
            best_pos = pos

    if best_pos >= len(content):
        return content[:200].strip() + "..."

    start = max(0, best_pos - context_chars // 2)
    end = min(len(content), best_pos + context_chars)
    snippet = content[start:end].strip()
    
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    
    # Remove markdown headers for cleaner display
    snippet = re.sub(r'#{1,6}\s+', '', snippet)
    return snippet


def assemble_results(quick_results: list, deep_results: list, limit: int) -> list:
    """Combine and deduplicate results from both search levels."""
    seen = set()
    combined = []
    
    for r in quick_results + deep_results:
        if r["id"] not in seen:
            seen.add(r["id"])
            combined.append(r)
    
    # Sort by score (quick results naturally score higher)
    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:limit]


def main():
    parser = argparse.ArgumentParser(description="Search the Context Tree")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--type", "-t", default=None, choices=VALID_TYPES, help="Filter by type")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    parser.add_argument("--deep-only", action="store_true", help="Skip quick search")
    parser.add_argument("--project-name", "-n", default=None)
    parser.add_argument("--path", "-p", default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--with-relations", "-R", action="store_true",
                        help="Show related nodes for each result")
    args = parser.parse_args()

    ws = get_workspace(args.project_name, args.path)
    if not (ws / "index.json").exists():
        print("❌ No workspace found. Run cm_init.py first.")
        sys.exit(1)

    index = load_index(ws)
    total_nodes = len(index.get("nodes", {}))
    
    if total_nodes == 0:
        print("📭 Context Tree is empty. Add knowledge with cm_add.py or cm_curate.py.")
        return

    # Prepare query words
    query_words = set(
        re.sub(r'[^\w]', ' ', args.query.lower()).split()
    )
    query_words -= {"der", "die", "das", "und", "oder", "in", "von", "zu", "für",
                     "the", "and", "or", "in", "of", "to", "for", "is", "a", "an",
                     "wie", "was", "wo", "wer", "how", "what", "where", "who"}

    if not query_words:
        print("❌ Query too generic. Please use more specific terms.")
        return

    if args.verbose:
        print(f"🔍 Searching {total_nodes} nodes for: {', '.join(query_words)}")
        if args.type:
            print(f"   Filter: type={args.type}")

    # Level 1: Quick search
    quick_results = [] if args.deep_only else quick_search(index, query_words, args.type)
    
    if args.verbose and quick_results:
        print(f"   Quick search: {len(quick_results)} result(s)")

    # Level 2: Deep search (if quick didn't find enough)
    quick_ids = {r["id"] for r in quick_results}
    deep_results = []
    if len(quick_results) < args.limit:
        deep_results = deep_search(ws, index, query_words, quick_ids, args.type)
        if args.verbose and deep_results:
            print(f"   Deep search: {len(deep_results)} additional result(s)")

    # Assemble
    results = assemble_results(quick_results, deep_results, args.limit)

    if not results:
        print(f"📭 No results for '{args.query}'.")
        print(f"   Try broader terms or check available types with cm_tree.py.")
        return

    # Load relations if requested
    relations_data = None
    if args.with_relations:
        try:
            from cm_relate import get_node_relations, RELATION_TYPES
            relations_data = True
        except ImportError:
            relations_data = None

    print(f"\n🔍 {len(results)} result(s) for '{args.query}':\n")
    for i, r in enumerate(results, 1):
        icon = {"quick": "⚡", "deep": "🔎"}.get(r["level"], "•")
        rel_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(r["relevance"], "•")
        
        print(f"  {i}. {icon} [{r['id']}] {r['title']}")
        print(f"     {rel_icon} {r['type']} | {r['relevance']} | score: {r['score']}")
        if r.get("tags"):
            print(f"     🏷️  {', '.join(r['tags'])}")
        if r.get("snippet"):
            print(f"     📝 {r['snippet']}")
        
        # Show relations for this result
        if relations_data:
            rels = get_node_relations(ws, r["id"])
            all_rels = rels["outgoing"] + rels["incoming"]
            if all_rels:
                print(f"     🕸️  Relations:")
                for rel in all_rels[:5]:
                    rinfo = RELATION_TYPES.get(rel["relation"], {})
                    if "target_title" in rel:
                        print(f"        {rinfo.get('icon', '→')} ──{rinfo.get('label', rel['relation'])}──→ [{rel['to']}] {rel['target_title']}")
                    else:
                        print(f"        {rinfo.get('icon', '←')} ←──{rinfo.get('label', rel['relation'])}── [{rel['from']}] {rel['source_title']}")
                if len(all_rels) > 5:
                    print(f"        ... +{len(all_rels) - 5} more")
        print()


if __name__ == "__main__":
    main()
