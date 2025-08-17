from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Observer: Subject with attach/detach/notify managing observers."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        method_names = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        if {"attach", "detach", "notify"}.issubset(method_names):
            # also check for observers attribute usage
            src = "\n".join(
                ast.get_source_segment(source, m) or ""
                for m in cls.body
                if isinstance(m, ast.FunctionDef)
            )
            if "observers" in src:
                results.append(
                    {
                        "name": "Observer",
                        "confidence": 0.7,
                        "reason": f"Class {cls.name} manages observers with attach/detach/notify",
                    }
                )
    return results
