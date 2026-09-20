#!/usr/bin/env python3
"""
cm_search.py — Agentic Search across the Context Tree.

Multi-level search:
  1. Quick: exact/fuzzy match on tags, titles, types
  2. Deep: full-text search in node content
  3. Assembly: combine and rank results

Ranking is time-aware: newer knowledge outweighs older knowledge of the same
quality, the content date breaks ties, and where two hits contradict each other
the older one is listed below the newer one instead of being dropped.

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
    content_date, content_year, recency_factor, sort_key_recency,
    VALID_TYPES
)


def _temporal_fields(meta: dict) -> dict:
    """Ranking fields derived from the node's content date."""
    dated, field = content_date(meta)
    return {
        "content_date": dated.date().isoformat() if dated else None,
        "content_date_field": field,
        "content_timestamp": dated.timestamp() if dated else None,
        "content_year": dated.year if dated else None,
        "recency": round(recency_factor(meta), 3)
    }


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

        # Recency: newer knowledge outweighs older knowledge of the same quality.
        temporal = _temporal_fields(meta)
        score *= temporal["recency"]

        if score > 0:
            results.append({
                "id": nid,
                "title": meta.get("title"),
                "type": meta.get("type"),
                "relevance": meta.get("relevance"),
                "status": meta.get("status"),
                "tags": meta.get("tags", []),
                "score": round(score, 2),
                "level": "quick",
                **temporal
            })

    return sorted(results, key=sort_key_recency)


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

        # Recency: same weighting as in the quick search.
        temporal = _temporal_fields(meta)
        score *= temporal["recency"]

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
                "snippet": snippet,
                **temporal
            })

    return sorted(results, key=sort_key_recency)


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


def _outranking_pairs(ws: Path, dated: dict) -> dict:
    """Map an outdated node ID to the newer node that outranks it.

    `dated` maps every result ID to its content timestamp (or None). A pair
    counts when both nodes are in the result set and a `supersedes`,
    `superseded_by` or `contradicts` relation connects them. For `contradicts`
    (symmetric) the content date decides: the younger statement wins, the older
    one stays in the results but is listed below it.
    """
    relations_file = ws / "relations.json"
    if not relations_file.exists():
        return {}

    try:
        from cm_relate import load_relations
    except ImportError:
        return {}

    losers = {}
    for edge in load_relations(ws).get("edges", []):
        source, target, relation = edge.get("from"), edge.get("to"), edge.get("relation")
        if source not in dated or target not in dated:
            continue
        if relation == "supersedes":
            losers[target] = source
        elif relation == "superseded_by":
            losers[source] = target
        elif relation == "contradicts":
            losers.setdefault(_older_of(source, target, dated), _newer_of(source, target, dated))
    losers.pop(None, None)
    return {loser: winner for loser, winner in losers.items() if loser != winner and winner}


def _older_of(a: str, b: str, dated: dict):
    """The node with the older content date; None if that cannot be decided."""
    ts_a, ts_b = dated.get(a), dated.get(b)
    if ts_a is None or ts_b is None or ts_a == ts_b:
        return None
    return a if ts_a < ts_b else b


def _newer_of(a: str, b: str, dated: dict):
    older = _older_of(a, b, dated)
    if older is None:
        return None
    return b if older == a else a


def assemble_results(quick_results: list, deep_results: list, limit: int, ws: Path = None) -> list:
    """Combine and deduplicate results from both search levels."""
    seen = set()
    combined = []
    
    for r in quick_results + deep_results:
        if r["id"] not in seen:
            seen.add(r["id"])
            combined.append(r)
    
    # Sort by score, content date as tie-breaker (newer first)
    combined.sort(key=sort_key_recency)

    # Contradictions: the older statement stays, but never above the newer one.
    if ws is not None:
        dated = {r["id"]: r.get("content_timestamp") for r in combined}
        losers = _outranking_pairs(ws, dated)
        if losers:
            years = {r["id"]: content_year(r) for r in combined}
            for r in combined:
                if r["id"] in losers:
                    r["outranked_by"] = losers[r["id"]]
            # Reordering is only needed inside a year. Across years the hard
            # rule in sort_key_recency already puts the older node below the
            # newer one — pulling it up behind its winner would lift it back
            # above other, newer nodes.
            same_year = {loser: winner for loser, winner in losers.items()
                         if years.get(loser) is not None and years.get(loser) == years.get(winner)}
            if same_year:
                combined = _demote_outranked(combined, same_year)

    return combined[:limit]


def _demote_outranked(results: list, losers: dict) -> list:
    """Move every outdated node directly behind the node that outranks it."""
    by_id = {r["id"]: r for r in results}
    ordered = []
    placed = set()

    def place(result):
        if result["id"] in placed:
            return
        placed.add(result["id"])
        ordered.append(result)
        # Pull in everything this node outranks, keeping the original order.
        for candidate in results:
            if losers.get(candidate["id"]) == result["id"]:
                place(candidate)

    for result in results:
        if losers.get(result["id"]) in by_id:
            continue  # placed right after its winner
        place(result)

    # Safety net: a cycle in the relations must not drop results.
    for result in results:
        place(result)

    return ordered


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
    results = assemble_results(quick_results, deep_results, args.limit, ws)

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
        if r.get("content_date"):
            print(f"     🕐 {r['content_date']} ({r['content_date_field']}) | recency: {r['recency']}")
        else:
            print(f"     🕐 no date — neutral weighting")
        if r.get("outranked_by"):
            print(f"     ⬇️  outdated: outranked by [{r['outranked_by']}]")
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
