#!/usr/bin/env python3
"""
Context Memory Core — Shared data structures, storage, and utilities.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Default base directory
DEFAULT_BASE = Path.home() / ".context-memory"

# Node types
VALID_TYPES = [
    "architecture", "pattern", "decision", "lesson", "config",
    "api", "dependency", "workflow", "bug", "convention"
]

VALID_RELEVANCE = ["critical", "high", "medium", "low"]
VALID_CONFIDENCE = ["high", "medium", "low", "unknown"]
VALID_STATUS = ["active", "outdated", "superseded"]
VALID_TEMPORAL_CONFIDENCE = ["explicit", "inferred", "unknown"]


def make_temporal(source_date: str = "", valid_from: str = "", valid_until: str = "",
                  temporal_confidence: str = "unknown") -> dict:
    """Create a temporal metadata block."""
    return {
        "source_date": source_date,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "temporal_confidence": temporal_confidence
    }


def get_workspace(project: Optional[str] = None, base: Optional[str] = None) -> Path:
    """Get the workspace directory for a project."""
    root = Path(base) if base else DEFAULT_BASE
    if project:
        safe_name = re.sub(r'[^\w\-.]', '_', project.lower().strip())
        return root / safe_name
    return root / "_default"


def ensure_workspace(ws: Path) -> None:
    """Ensure workspace directories exist."""
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "nodes").mkdir(exist_ok=True)
    for fname in ["tree.json", "index.json", "history.json"]:
        fpath = ws / fname
        if not fpath.exists():
            if fname == "tree.json":
                fpath.write_text(json.dumps({
                    "project": ws.name,
                    "created": _now(),
                    "updated": _now(),
                    "root_children": []
                }, indent=2, ensure_ascii=False), encoding="utf-8")
            elif fname == "index.json":
                fpath.write_text(json.dumps({"nodes": {}}, indent=2, ensure_ascii=False), encoding="utf-8")
            elif fname == "history.json":
                fpath.write_text(json.dumps({"entries": []}, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generate_id(node_type: str, ws: Path, index: dict = None) -> str:
    """Generate a unique node ID like arch-001.
    
    Pass an in-memory index dict for batch operations to avoid
    reading stale data from disk.
    """
    prefix_map = {
        "architecture": "arch", "pattern": "pat", "decision": "dec",
        "lesson": "les", "config": "cfg", "api": "api",
        "dependency": "dep", "workflow": "wf", "bug": "bug",
        "convention": "conv"
    }
    prefix = prefix_map.get(node_type, node_type[:4])
    if index is None:
        index = load_index(ws)
    existing = [nid for nid in index.get("nodes", {}) if nid.startswith(prefix + "-")]
    nums = []
    for nid in existing:
        parts = nid.split("-", 1)
        if len(parts) == 2:
            try:
                nums.append(int(parts[1]))
            except ValueError:
                pass
    next_num = max(nums, default=0) + 1
    return f"{prefix}-{next_num:03d}"


def load_tree(ws: Path) -> dict:
    try:
        return json.loads((ws / "tree.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"project": ws.name, "created": _now(), "updated": _now(), "root_children": []}


def save_tree(ws: Path, tree: dict) -> None:
    tree["updated"] = _now()
    (ws / "tree.json").write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8")


def load_index(ws: Path) -> dict:
    try:
        return json.loads((ws / "index.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"nodes": {}}


def save_index(ws: Path, index: dict) -> None:
    (ws / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def load_history(ws: Path) -> dict:
    try:
        return json.loads((ws / "history.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": []}


def save_history(ws: Path, history: dict) -> None:
    # Keep last 500 entries
    history["entries"] = history["entries"][-500:]
    (ws / "history.json").write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def add_history_entry(ws: Path, action: str, node_id: str, details: str = "") -> None:
    history = load_history(ws)
    history["entries"].append({
        "timestamp": _now(),
        "action": action,
        "node_id": node_id,
        "details": details
    })
    save_history(ws, history)


def load_node(ws: Path, node_id: str) -> Optional[str]:
    """Load a node's markdown content."""
    node_path = ws / "nodes" / f"{node_id}.md"
    if node_path.exists():
        return node_path.read_text(encoding="utf-8")
    return None


def save_node(ws: Path, node_id: str, content: str) -> None:
    """Save a node's markdown content."""
    (ws / "nodes" / f"{node_id}.md").write_text(content, encoding="utf-8")


def delete_node_file(ws: Path, node_id: str) -> bool:
    """Delete a node file. Returns True if deleted."""
    node_path = ws / "nodes" / f"{node_id}.md"
    if node_path.exists():
        node_path.unlink()
        return True
    return False


def normalize_tags(tags: str) -> list:
    """Normalize a comma-separated tag string into a clean list."""
    if not tags:
        return []
    return sorted(set(
        re.sub(r'[^\w\-]', '', t.strip().lower())
        for t in tags.split(",") if t.strip()
    ))


def content_hash(content: str) -> str:
    """Generate a short hash for duplicate detection."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]


def find_similar_nodes(ws: Path, title: str, content: str, threshold: float = 0.6) -> list:
    """Find nodes with similar titles or content (simple word overlap)."""
    index = load_index(ws)
    title_words = set(title.lower().split())
    content_words = set(content.lower().split()[:50])  # First 50 words
    
    similar = []
    for nid, meta in index.get("nodes", {}).items():
        if meta.get("status") == "superseded":
            continue
        existing_title_words = set(meta.get("title", "").lower().split())
        existing_tags = set(meta.get("tags", []))
        
        # Title similarity
        if title_words and existing_title_words:
            overlap = len(title_words & existing_title_words) / max(len(title_words), len(existing_title_words))
            if overlap >= threshold:
                similar.append({"id": nid, "title": meta.get("title"), "similarity": round(overlap, 2), "match": "title"})
                continue
        
        # Tag overlap
        content_as_tags = set(normalize_tags(",".join(content_words)))
        tag_overlap = len(content_as_tags & existing_tags)
        if tag_overlap >= 3:
            similar.append({"id": nid, "title": meta.get("title"), "similarity": tag_overlap / 10, "match": "tags"})
    
    return sorted(similar, key=lambda x: x["similarity"], reverse=True)[:5]


def list_projects(base: Optional[str] = None) -> list:
    """List all projects in the base directory."""
    root = Path(base) if base else DEFAULT_BASE
    if not root.exists():
        return []
    projects = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / "tree.json").exists():
            tree = load_tree(d)
            index = load_index(d)
            projects.append({
                "name": d.name,
                "path": str(d),
                "created": tree.get("created", "unknown"),
                "updated": tree.get("updated", "unknown"),
                "node_count": len(index.get("nodes", {}))
            })
    return projects
