"""Public API for snippet implementors (code generator style).

This package exposes a small surface that the MCP server imports:

- NAME_ALIASES: common name aliases -> canonical keys
- get_snippet(name): return scaffold code as a string (or None)
- register_generator(fn, keys?): allow external registration of generators

Implementation details live in submodules to avoid a large __init__.py.
"""

from __future__ import annotations

from .aliases import NAME_ALIASES
from .api import get_snippet, register_generator, transform_code

__all__ = [
    "NAME_ALIASES",
    "get_snippet",
    "register_generator",
    "transform_code",
]
