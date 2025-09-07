from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Iterator: class implementing __iter__ and __next__."""
    results: list[dict[str, Any]] = []
    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        methods = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        if {"__iter__", "__next__"}.issubset(methods):
            results.append(
                {
                    "name": "Iterator",
                    "confidence": 0.7,
                    "reason": f"Class {cls.name} defines __iter__ and __next__",
                },
            )
    return results
