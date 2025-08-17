from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Prototype: clone method returning a shallow/deep copy."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name in {"clone", "copy"}:
                text = ast.get_source_segment(source, m) or ""
                if "copy.copy(" in text or "copy.deepcopy(" in text:
                    results.append(
                        {
                            "name": "Prototype",
                            "confidence": 0.65,
                            "reason": f"Class {cls.name} defines {m.name} using copy module",
                        }
                    )
                    break
    return results
