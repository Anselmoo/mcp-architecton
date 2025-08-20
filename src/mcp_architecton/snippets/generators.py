"""Backward-compat shim for generators.

The original monolithic module has been split into the package
`mcp_architecton.snippets.generators`. Import public symbols from there.
"""

from __future__ import annotations

from .generators import BUILTINS, Generator  # re-export

__all__ = ["Generator", "BUILTINS"]
