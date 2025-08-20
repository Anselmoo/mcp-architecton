from __future__ import annotations

from difflib import unified_diff

from mcp_architecton.generators.refactor_generator import (
    introduce_architecture_impl,
    introduce_impl,
    introduce_pattern_impl,
)

# simple helpers mirrored by tests


def _diff(old: str, new: str, path: str) -> str:
    return "".join(
        unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=path,
            tofile=path,
            lineterm="",
        )
    )


def _canonical_pattern_name(name: str | None) -> str:
    if not name:
        return ""
    return str(name).strip().lower()


__all__ = [
    "_diff",
    "_canonical_pattern_name",
    "introduce_impl",
    "introduce_pattern_impl",
    "introduce_architecture_impl",
]
