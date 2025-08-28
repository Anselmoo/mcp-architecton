from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CatalogEntry:
    """Lightweight catalog entry type used by generators for hints.

    This mirrors the shape found in data/patterns/catalog.json but is intentionally
    minimal and optional. Generators tolerate None for any field.
    """

    name: str | None = None
    category: str | None = None
    description: str | None = None
    refs: Optional[List[str]] = None
    prompt_hint: str | None = None
    contract: Optional[Dict[str, Any]] = None


__all__ = ["CatalogEntry"]
