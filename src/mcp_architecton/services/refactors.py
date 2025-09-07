from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def list_refactorings_impl() -> list[dict[str, Any]]:
    """List refactoring techniques from the catalog, if present.

    Returns empty list on any error. Each item may include name, url, and prompt_hint.
    """
    catalog_path = Path(__file__).resolve().parents[3] / "data" / "patterns" / "catalog.json"
    try:
        if not catalog_path.exists():
            return []
        raw = json.loads(catalog_path.read_text())
        if not isinstance(raw, dict):
            return []
        data: dict[str, Any] = cast("dict[str, Any]", raw)
        items_raw = data.get("refactorings", [])
        items: list[dict[str, Any]] = [
            cast("dict[str, Any]", it) for it in items_raw if isinstance(it, dict)
        ]
        out: list[dict[str, Any]] = []
        for it in items:
            name = f"{it.get('name', '')}"
            url = f"{it.get('url', '')}"
            hint = it.get("prompt_hint")
            entry: dict[str, Any] = {"name": name, "url": url}
            if isinstance(hint, str) and hint.strip():
                entry["prompt_hint"] = hint.strip()
            out.append(entry)
        return out
    except Exception:
        return []


__all__ = ["list_refactorings_impl"]
