from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Visitor: element classes with accept(visitor) calling visit_*."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "accept":
                text = ast.get_source_segment(source, m) or ""
                if ".visit_" in text:
                    results.append(
                        {
                            "name": "Visitor",
                            "confidence": 0.6,
                            "reason": f"Class {cls.name}.accept calls visitor.visit_*",
                        }
                    )
                    break
    return results
