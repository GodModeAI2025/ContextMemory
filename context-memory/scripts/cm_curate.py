#!/usr/bin/env python3
"""
cm_curate.py — Automatically analyze a codebase and generate Memory Nodes.

Scans project structure, package files, configs, and source code to extract
architecture decisions, dependencies, patterns, and conventions.

Usage:
  python3 cm_curate.py --path /path/to/project [--focus "testing"] [--depth 3]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cm_core import (
    get_workspace, ensure_workspace, generate_id, load_index, save_index,
    load_tree, save_tree, save_node, add_history_entry,
    normalize_tags, content_hash, _now
)

# Directories and files to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", "venv", ".venv", "env", ".env", "dist", "build",
    ".next", ".nuxt", "coverage", ".coverage", ".idea", ".vscode",
    "vendor", "target", "out", "bin", "obj", ".gradle", ".context-memory"
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib", ".dll",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".avi",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".pdf", ".doc", ".docx",
    ".lock", ".map"
}

# Config files to analyze
CONFIG_FILES = {
    "package.json", "tsconfig.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Gemfile",
    "requirements.txt", "Pipfile", "composer.json", "Makefile", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", ".env.example",
    "webpack.config.js", "vite.config.ts", "vite.config.js",
    "tailwind.config.js", "next.config.js", "nuxt.config.ts",
    ".eslintrc.json", ".prettierrc", "jest.config.js", "vitest.config.ts",
    "pytest.ini", "tox.ini", "mypy.ini"
}


def scan_directory(project_path: Path, max_depth: int = 3) -> dict:
    """Scan project directory and collect file structure info."""
    result = {
        "files": [],
        "dirs": [],
        "configs": [],
        "source_files": [],
        "test_files": [],
        "total_files": 0,
        "languages": {}
    }
    
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React JSX", ".tsx": "React TSX", ".rb": "Ruby",
        ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".swift": "Swift",
        ".php": "PHP", ".scala": "Scala", ".r": "R", ".jl": "Julia",
        ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart"
    }

    for root, dirs, files in os.walk(project_path):
        # Calculate depth
        rel_depth = len(Path(root).relative_to(project_path).parts)
        if rel_depth > max_depth:
            dirs.clear()
            continue

        # Filter directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for d in dirs:
            result["dirs"].append(str(Path(root, d).relative_to(project_path)))

        for f in files:
            ext = Path(f).suffix.lower()
            if ext in SKIP_EXTENSIONS:
                continue

            rel_path = str(Path(root, f).relative_to(project_path))
            result["total_files"] += 1

            if f in CONFIG_FILES or f.startswith(".") and ext in {".json", ".yml", ".yaml", ".toml"}:
                result["configs"].append(rel_path)

            if ext in lang_map:
                lang = lang_map[ext]
                result["languages"][lang] = result["languages"].get(lang, 0) + 1
                result["source_files"].append(rel_path)

            # Detect test files
            if any(x in f.lower() for x in ["test", "spec", "_test", ".test"]) or \
               any(x in rel_path.lower() for x in ["/tests/", "/test/", "/__tests__/", "/spec/"]):
                result["test_files"].append(rel_path)

            result["files"].append(rel_path)

    return result


def analyze_package_json(project_path: Path) -> dict:
    """Extract info from package.json."""
    pkg_path = project_path / "package.json"
    if not pkg_path.exists():
        return {}
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        return {
            "name": pkg.get("name", "unknown"),
            "version": pkg.get("version"),
            "description": pkg.get("description"),
            "main": pkg.get("main"),
            "scripts": pkg.get("scripts", {}),
            "dependencies": list(pkg.get("dependencies", {}).keys()),
            "devDependencies": list(pkg.get("devDependencies", {}).keys()),
            "type": pkg.get("type"),
            "engines": pkg.get("engines")
        }
    except (json.JSONDecodeError, OSError):
        return {}


def analyze_pyproject(project_path: Path) -> dict:
    """Extract info from pyproject.toml or requirements.txt."""
    result = {}
    
    req_path = project_path / "requirements.txt"
    if req_path.exists():
        try:
            lines = req_path.read_text(encoding="utf-8").strip().split("\n")
            deps = [l.strip().split("==")[0].split(">=")[0].split("<=")[0]
                    for l in lines if l.strip() and not l.startswith("#") and not l.startswith("-")]
            result["dependencies"] = deps
        except OSError:
            pass
    
    pyproj_path = project_path / "pyproject.toml"
    if pyproj_path.exists():
        try:
            content = pyproj_path.read_text(encoding="utf-8")
            name_match = re.search(r'name\s*=\s*"(.+?)"', content)
            if name_match:
                result["name"] = name_match.group(1)
            version_match = re.search(r'version\s*=\s*"(.+?)"', content)
            if version_match:
                result["version"] = version_match.group(1)
        except OSError:
            pass
    
    return result


def generate_nodes(project_path: Path, scan: dict, focus: str = None) -> list:
    """Generate memory node data from scan results."""
    nodes = []
    
    # 1. Architecture overview
    lang_summary = ", ".join(f"{lang} ({count})" for lang, count in
                            sorted(scan["languages"].items(), key=lambda x: -x[1])[:5])
    
    top_dirs = [d for d in scan["dirs"] if "/" not in d][:15]
    
    nodes.append({
        "type": "architecture",
        "title": f"Project Structure Overview",
        "tags": "structure,overview,architecture",
        "relevance": "high",
        "content": (
            f"**Project:** {project_path.name}\n"
            f"**Total files:** {scan['total_files']}\n"
            f"**Languages:** {lang_summary or 'none detected'}\n"
            f"**Top-level directories:** {', '.join(top_dirs) if top_dirs else 'flat structure'}\n"
            f"**Config files found:** {len(scan['configs'])}\n"
            f"**Test files:** {len(scan['test_files'])}"
        )
    })

    # 2. Dependencies
    pkg = analyze_package_json(project_path)
    py = analyze_pyproject(project_path)
    
    if pkg:
        deps = pkg.get("dependencies", [])
        dev_deps = pkg.get("devDependencies", [])
        nodes.append({
            "type": "dependency",
            "title": f"Node.js Dependencies",
            "tags": "dependencies,npm,nodejs," + ",".join(deps[:5]),
            "relevance": "high",
            "content": (
                f"**Package:** {pkg.get('name', '?')} v{pkg.get('version', '?')}\n"
                f"**Type:** {pkg.get('type', 'commonjs')}\n\n"
                f"**Dependencies ({len(deps)}):** {', '.join(deps) if deps else 'none'}\n\n"
                f"**Dev Dependencies ({len(dev_deps)}):** {', '.join(dev_deps) if dev_deps else 'none'}\n\n"
                f"**Scripts:** {json.dumps(pkg.get('scripts', {}), indent=2)}"
            )
        })
    
    if py.get("dependencies"):
        nodes.append({
            "type": "dependency",
            "title": f"Python Dependencies",
            "tags": "dependencies,pip,python," + ",".join(py["dependencies"][:5]),
            "relevance": "high",
            "content": (
                f"**Package:** {py.get('name', '?')} v{py.get('version', '?')}\n\n"
                f"**Dependencies ({len(py['dependencies'])}):** {', '.join(py['dependencies'])}"
            )
        })

    # 3. Configuration patterns
    if scan["configs"]:
        config_summary = "\n".join(f"- `{c}`" for c in scan["configs"][:20])
        nodes.append({
            "type": "config",
            "title": "Configuration Files",
            "tags": "config,setup,tooling",
            "relevance": "medium",
            "content": f"**Configuration files found:**\n\n{config_summary}"
        })

    # 4. Testing setup
    if scan["test_files"]:
        test_summary = "\n".join(f"- `{t}`" for t in scan["test_files"][:15])
        # Detect test framework
        frameworks = []
        configs = [c.lower() for c in scan["configs"]]
        if any("jest" in c for c in configs):
            frameworks.append("Jest")
        if any("vitest" in c for c in configs):
            frameworks.append("Vitest")
        if any("pytest" in c for c in configs) or "pytest.ini" in [Path(c).name for c in scan["configs"]]:
            frameworks.append("Pytest")
        
        nodes.append({
            "type": "convention",
            "title": "Testing Setup",
            "tags": "testing,tests,quality," + ",".join(f.lower() for f in frameworks),
            "relevance": "medium",
            "content": (
                f"**Test framework(s):** {', '.join(frameworks) if frameworks else 'unknown'}\n"
                f"**Test files ({len(scan['test_files'])}):**\n\n{test_summary}"
            )
        })

    # 5. Docker/deployment if present
    docker_files = [c for c in scan["configs"] if "docker" in c.lower() or c == "Dockerfile"]
    if docker_files:
        nodes.append({
            "type": "workflow",
            "title": "Docker/Deployment Setup",
            "tags": "docker,deployment,devops,container",
            "relevance": "medium",
            "content": f"**Docker files found:**\n\n" + "\n".join(f"- `{d}`" for d in docker_files)
        })

    # Filter by focus if specified
    if focus:
        focus_lower = focus.lower()
        nodes = [n for n in nodes if focus_lower in n["title"].lower() or
                 focus_lower in n["tags"] or focus_lower in n["content"].lower()]
        if not nodes:
            # If focus didn't match any generated nodes, return all
            print(f"⚠️  Focus '{focus}' didn't match specific nodes, showing all.")
            return generate_nodes(project_path, scan, focus=None)

    return nodes


def main():
    parser = argparse.ArgumentParser(description="Auto-curate project knowledge")
    parser.add_argument("--path", required=True, help="Path to project directory")
    parser.add_argument("--project-name", "-n", default=None, help="Project name")
    parser.add_argument("--focus", default=None, help="Focus area (e.g., 'testing', 'config')")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Max scan depth")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added")
    parser.add_argument("--base-path", default=None, help="Base storage path")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(f"❌ Not a directory: {project_path}")
        sys.exit(1)

    project_name = args.project_name or project_path.name
    ws = get_workspace(project_name, args.base_path)
    ensure_workspace(ws)

    print(f"🔍 Scanning: {project_path} (depth: {args.depth})")
    scan = scan_directory(project_path, args.depth)
    print(f"   Found {scan['total_files']} files, {len(scan['languages'])} language(s)\n")

    nodes_data = generate_nodes(project_path, scan, args.focus)

    if not nodes_data:
        print("📭 No knowledge extracted. The project might be empty or unrecognized.")
        return

    if args.dry_run:
        print(f"🔎 Would add {len(nodes_data)} node(s):\n")
        for nd in nodes_data:
            print(f"   [{nd['type']}] {nd['title']}")
            print(f"   Tags: {nd['tags']}")
            print()
        return

    # Add nodes
    index = load_index(ws)
    tree = load_tree(ws)
    added = []

    for nd in nodes_data:
        node_id = generate_id(nd["type"], ws)
        tags = normalize_tags(nd["tags"])
        
        node_md = (
            f"# {nd['title']}\n\n"
            f"**Type:** {nd['type']} | **Relevance:** {nd['relevance']} | **Status:** active\n"
            f"**Tags:** {', '.join(tags)}\n"
            f"**Created:** {_now()} | **Source:** auto-curated\n\n"
            f"---\n\n{nd['content']}\n"
        )
        save_node(ws, node_id, node_md)
        
        index.setdefault("nodes", {})[node_id] = {
            "title": nd["title"],
            "type": nd["type"],
            "tags": tags,
            "relevance": nd["relevance"],
            "status": "active",
            "created": _now(),
            "updated": _now(),
            "parent": None,
            "hash": content_hash(nd["content"]),
            "source": "auto-curated"
        }
        
        tree.setdefault("root_children", []).append({"id": node_id, "children": []})
        added.append((node_id, nd["title"]))

    save_index(ws, index)
    save_tree(ws, tree)
    
    for nid, title in added:
        add_history_entry(ws, "curate", nid, f"Auto-curated: {title}")

    print(f"✅ Curated {len(added)} node(s) for '{project_name}':\n")
    for nid, title in added:
        print(f"   📝 {nid}: {title}")
    print(f"\n   Workspace: {ws}")


if __name__ == "__main__":
    main()
