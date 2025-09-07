"""Generators package: pattern and architecture snippet generators.

Exports:
- Generator: callable signature for generators
- BUILTINS: combined mapping of canonical keys to generator callables
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

try:  # pragma: no cover - optional dependency
    from ..snippets.catalog import CatalogEntry  # type: ignore
except Exception:  # pragma: no cover

    class CatalogEntry:  # type: ignore
        pass


from .architectures import ARCH_GENERATORS
from .patterns import PATTERN_GENERATORS

# Public type alias
Generator = Callable[[str, CatalogEntry | None], str | None]

# Merge registries (patterns + architectures)
BUILTINS: dict[str, Generator] = {
    **PATTERN_GENERATORS,
    **ARCH_GENERATORS,
}

__all__ = ["BUILTINS", "Generator"]
