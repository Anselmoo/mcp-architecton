from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Singleton: class with __new__ storing a single _instance."""
    results: list[dict[str, Any]] = []
    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        # Accept common aliases used for the instance holder
        instance_names = {"_instance", "_inst", "instance"}
        has_instance_attr = any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in instance_names for t in n.targets)
            for n in cls.body
        )
        has_new = any(isinstance(m, ast.FunctionDef) and m.name == "__new__" for m in cls.body)
        if has_instance_attr and has_new:
            results.append(
                {
                    "name": "Singleton",
                    "confidence": 0.7,
                    "reason": f"Class {cls.name} defines instance holder and __new__",
                }
            )
    return results
