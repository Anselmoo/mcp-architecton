from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CatalogEntry:
    """Lightweight catalog entry type used by generators for hints.

    This mirrors the shape found in data/patterns/catalog.json but is intentionally
    minimal and optional. Generators tolerate None for any field.
    """

    name: str | None = None
    category: str | None = None
    description: str | None = None
    refs: list[str] | None = None
    prompt_hint: str | None = None
    contract: dict[str, Any] | None = None


__all__ = ["CatalogEntry"]
