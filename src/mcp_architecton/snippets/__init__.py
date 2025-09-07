"""Optional snippets package for generator aliasing and canned templates.

This minimal implementation ensures imports resolve even if no external
snippets are provided. Downstream code can override these by installing
an alternate snippets package/module on PYTHONPATH.
"""

from __future__ import annotations

from .aliases import NAME_ALIASES


def get_snippet(name: str) -> str | None:
    """Return a canned snippet string for a given canonical name, if any.

    Minimal default returns None so generators fall back to programmatic output.
    """
    _ = name  # no default snippets bundled
    return None


__all__ = ["NAME_ALIASES", "get_snippet"]
