"""Generators package: pattern and architecture snippet generators.

Exports:
- Generator: callable signature for generators
- BUILTINS: combined mapping of canonical keys to generator callables
"""

from __future__ import annotations

from typing import Callable, Optional

from ..catalog import CatalogEntry
from .architectures import ARCH_GENERATORS
from .patterns import PATTERN_GENERATORS

# Public type alias
Generator = Callable[[str, Optional[CatalogEntry]], str | None]

# Merge registries (patterns + architectures)
BUILTINS: dict[str, Generator] = {
    **PATTERN_GENERATORS,
    **ARCH_GENERATORS,
}

__all__ = ["Generator", "BUILTINS"]

