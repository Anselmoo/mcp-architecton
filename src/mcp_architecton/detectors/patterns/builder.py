from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Builder: fluent setters and a build() method creating a product."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_build = any(isinstance(m, ast.FunctionDef) and m.name == "build" for m in cls.body)
        returns_self = sum(
            1
            for m in cls.body
            if isinstance(m, ast.FunctionDef)
            and m.name != "__init__"
            and "return self" in (ast.get_source_segment(source, m) or "")
        )
        creates_obj = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "build":
                text = ast.get_source_segment(source, m) or ""
                if "return " in text and "(" in text and ")" in text:
                    creates_obj = True
        if has_build and (returns_self >= 1 or creates_obj):
            results.append(
                {
                    "name": "Builder",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} has fluent setters and a build() method",
                }
            )
    return results
