"""Catalog loader for pattern and architecture metadata.

Used to enrich generated scaffolds with docstrings or names when available.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast


class CatalogEntry(TypedDict, total=False):
    name: str
    category: str
    intent: str
    description: str
    refs: list[str]


class Catalog(TypedDict):
    patterns: list[CatalogEntry]


def load_catalog() -> Catalog:
    root = Path(__file__).resolve().parents[3]
    cat = root / "data" / "patterns" / "catalog.json"
    if not cat.exists():
        return {"patterns": []}
    try:
        data = json.loads(cat.read_text())
        pats = cast(list[dict[str, Any]], data.get("patterns", []))
        entries: list[CatalogEntry] = []
        for e in pats:
            entries.append(
                {
                    "name": str(e.get("name", "")),
                    "category": str(e.get("category", "")),
                    "intent": str(e.get("intent", "")),
                    "description": str(e.get("description", "")),
                    "refs": [str(x) for x in cast(list[Any], e.get("refs", []))],
                }
            )
        return {"patterns": entries}
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
        return {"patterns": []}


def find_catalog_entry(name: str) -> CatalogEntry | None:
    """Case-insensitive lookup by name from the catalog with simple aliasing."""
    catalog = load_catalog()["patterns"]
    low = name.strip().lower().replace("_", " ")
    for entry in catalog:
        ename = str(entry.get("name", ""))
        el = ename.lower()
        base = el.replace(" architecture", "")
        if el == low or base == low or low in el:
            return entry
    return None


__all__ = ["CatalogEntry", "Catalog", "load_catalog", "find_catalog_entry"]
