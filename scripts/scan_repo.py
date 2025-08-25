#!/usr/bin/env python3
"""
Repository anti-pattern scanner runner.

- Walks the current directory (.) for Python files, skipping common folders (venv, .git, .mypy_cache, .ruff_cache, .tox, .svn, __pycache__).
- Calls the MCP server's scan_anti_patterns tool functions directly.
- Prints a compact summary: counts per indicator and top recommendations.

Usage:
  uv run python scripts/scan_repo.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from mcp_architecton.server import scan_anti_patterns, thresholded_enforcement

SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".svn",
    ".hg",
}


def discover_py_files(root: Path) -> list[str]:
    files: list[str] = []
    for p in root.rglob("*.py"):
        try:
            parts = set(p.parts)
            if parts.intersection(SKIP_DIRS):
                continue
            files.append(str(p))
        except Exception:
            continue
    return files


def main() -> int:
    root = Path(".").resolve()
    files = discover_py_files(root)
    if not files:
        print("No Python files found.")
        return 0

    scan = scan_anti_patterns(files=files)
    if "error" in scan:
        print(f"Error: {scan['error']}")
        return 2

    # Aggregate indicators
    indicator_counts: dict[str, int] = {}
    results_val = scan.get("results", [])
    entries: list[Any] = cast(list[Any], results_val) if isinstance(results_val, list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_d = cast(dict[str, Any], entry)
        inds_val = entry_d.get("indicators", [])
        inds_list: list[Any] = cast(list[Any], inds_val) if isinstance(inds_val, list) else []
        for ind in inds_list:
            if isinstance(ind, dict):
                ind_d = cast(dict[str, Any], ind)
                t = f"{ind_d.get('type', 'unknown')}"
                indicator_counts[t] = indicator_counts.get(t, 0) + 1

    # Get thresholded suggestions (top 3 per file)
    enforced = thresholded_enforcement(files=files, max_suggestions=3)

    print("=== Anti-Pattern Indicators (counts across repo) ===")
    for k, v in sorted(indicator_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"- {k}: {v}")

    print("\n=== Top Suggestions (per file) ===")
    enforced_val = enforced.get("results", [])
    res_list: list[Any] = cast(list[Any], enforced_val) if isinstance(enforced_val, list) else []
    for res in res_list:
        if not isinstance(res, dict):
            continue
        res_d = cast(dict[str, Any], res)
        src = f"{res_d.get('source', '<unknown>')}"
        suggs_val = res_d.get("suggestions", [])
        suggs: list[Any] = cast(list[Any], suggs_val) if isinstance(suggs_val, list) else []
        if not suggs:
            continue
        print(f"\n{src}:")
        for s in suggs:
            if not isinstance(s, dict):
                continue
            sd = cast(dict[str, Any], s)
            target = sd.get("target")
            category = sd.get("category")
            weight = sd.get("weight")
            reasons_val = sd.get("reasons", [])
            reasons = (
                ", ".join(cast(list[str], reasons_val)) if isinstance(reasons_val, list) else ""
            )
            prompt = sd.get("prompt")
            print(f"- [{category}] {target} (weight {weight}) -> {reasons}")
            print(f"  Advice: {prompt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
