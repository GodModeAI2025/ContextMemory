#!/usr/bin/env python3
"""
Context Memory Core — Shared data structures, storage, and utilities.
"""

import json
import os
import re
import stat
import sys
import hashlib
import tempfile
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

# Recency weighting: how much a fresh node may gain over an ancient one, and how
# fast that bonus decays. 365 days half-life means knowledge from last year still
# counts, knowledge from 2020 is practically neutral.
RECENCY_BOOST = 0.5
RECENCY_HALF_LIFE_DAYS = 365.0


def make_temporal(source_date: str = "", valid_from: str = "", valid_until: str = "",
                  temporal_confidence: str = "unknown") -> dict:
    """Create a temporal metadata block."""
    return {
        "source_date": source_date,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "temporal_confidence": temporal_confidence
    }


def parse_partial_date(value: str) -> Optional[datetime]:
    """Parse an ISO 8601 date, datetime or partial date (YYYY, YYYY-MM).

    Partial values are anchored at their first moment (2025 → 2025-01-01).
    Naive values are treated as UTC. Unparsable values like "Q1 2025" return None.
    """
    if not value:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}", text):
        text = f"{text}-01-01"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text = f"{text}-01"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def content_date(meta: dict) -> tuple:
    """Return (datetime, field) of the most meaningful date of a node.

    The content date answers "how old is this knowledge?", not "when did I touch
    the file?". Priority therefore: temporal.source_date (when it was published),
    temporal.valid_from (since when it holds), updated, created.
    Returns (None, "") if no field can be parsed — such nodes keep a neutral
    weight instead of dropping out of the ranking.
    """
    temporal = meta.get("temporal") or {}
    for field, value in (
        ("temporal.source_date", temporal.get("source_date", "")),
        ("temporal.valid_from", temporal.get("valid_from", "")),
        ("updated", meta.get("updated", "")),
        ("created", meta.get("created", "")),
    ):
        parsed = parse_partial_date(value)
        if parsed:
            return parsed, field
    return None, ""


def recency_factor(meta: dict, now: Optional[datetime] = None) -> float:
    """Score multiplier between 1.0 and 1 + RECENCY_BOOST based on the content date.

    Newer knowledge outweighs older knowledge; the boost halves every
    RECENCY_HALF_LIFE_DAYS. Nodes without a usable date get the neutral 1.0, so
    they never disappear but also never outrank dated knowledge of equal score.
    A date in the future is capped at "today" and cannot buy extra weight.
    """
    dated, _field = content_date(meta)
    if not dated:
        return 1.0
    now = now or datetime.now(timezone.utc)
    age_days = max(0.0, (now - dated).total_seconds() / 86400.0)
    return 1.0 + RECENCY_BOOST * (0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS))


def sort_key_recency(result: dict) -> tuple:
    """Sort helper: score first, content date as tie-breaker, ID as last resort.

    Used as `sorted(..., key=sort_key_recency)` — the key is already ordered
    ascending, so no `reverse=True` is needed.
    """
    timestamp = result.get("content_timestamp")
    return (-float(result.get("score", 0.0)),
            -(timestamp if timestamp is not None else float("-inf")),
            str(result.get("id", "")))


def get_workspace(project: Optional[str] = None, base: Optional[str] = None) -> Path:
    """Get the workspace directory for a project."""
    root = Path(base) if base else DEFAULT_BASE
    if project:
        safe_name = re.sub(r'[^\w\-.]', '_', project.lower().strip())
        return root / safe_name
    return root / "_default"


def write_text_atomic(path: Path, text: str) -> None:
    """Write a file atomically: temp file in the same directory, then os.replace.

    A crash or full disk mid-write leaves the previous version intact instead of
    a truncated JSON file.
    """
    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            # mkstemp creates 0600; keep the permissions of an existing file.
            if path.exists():
                os.fchmod(fh.fileno(), stat.S_IMODE(path.stat().st_mode))
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def write_json_atomic(path: Path, data: dict) -> None:
    write_text_atomic(path, json.dumps(data, indent=2, ensure_ascii=False))


def load_json(path: Path, default: dict) -> dict:
    """Load a JSON store file; fall back to `default` if missing.

    A corrupt file is copied to `<name>.corrupt-<content-hash>` before falling back,
    so the next save cannot silently overwrite the only copy of the data.
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return default
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        backup = path.with_name(f"{path.name}.corrupt-{hashlib.md5(raw).hexdigest()[:12]}")
        if not backup.exists():
            backup.write_bytes(raw)
        print(f"⚠️  {path.name} is corrupt ({exc}). Backup: {backup}", file=sys.stderr)
        return default


def ensure_workspace(ws: Path) -> None:
    """Ensure workspace directories exist."""
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "nodes").mkdir(exist_ok=True)
    for fname in ["tree.json", "index.json", "history.json"]:
        fpath = ws / fname
        if not fpath.exists():
            if fname == "tree.json":
                write_json_atomic(fpath, {
                    "project": ws.name,
                    "created": _now(),
                    "updated": _now(),
                    "root_children": []
                })
            elif fname == "index.json":
                write_json_atomic(fpath, {"nodes": {}})
            elif fname == "history.json":
                write_json_atomic(fpath, {"entries": []})


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
    return load_json(ws / "tree.json",
                     {"project": ws.name, "created": _now(), "updated": _now(), "root_children": []})


def save_tree(ws: Path, tree: dict) -> None:
    tree["updated"] = _now()
    write_json_atomic(ws / "tree.json", tree)


def load_index(ws: Path) -> dict:
    return load_json(ws / "index.json", {"nodes": {}})


def save_index(ws: Path, index: dict) -> None:
    write_json_atomic(ws / "index.json", index)


def load_history(ws: Path) -> dict:
    return load_json(ws / "history.json", {"entries": []})


def save_history(ws: Path, history: dict) -> None:
    # Keep last 500 entries
    history["entries"] = history["entries"][-500:]
    write_json_atomic(ws / "history.json", history)


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
    write_text_atomic(ws / "nodes" / f"{node_id}.md", content)


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
