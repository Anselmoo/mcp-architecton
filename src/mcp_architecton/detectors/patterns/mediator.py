from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Mediator: class with register/notify and colleagues calling it."""
    results: list[dict[str, Any]] = []

    mediators: set[str] = set()
    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        method_names = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        if {"register", "notify"}.issubset(method_names):
            mediators.add(cls.name)

    if not mediators:
        return results

    src = source
    for name in mediators:
        # look for "self.<mediator>.notify(" usage in other classes
        if ".notify(" in src and name in src:
            results.append(
                {
                    "name": "Mediator",
                    "confidence": 0.55,
                    "reason": f"Mediator class {name} with register/notify used by colleagues",
                },
            )
            break

    return results
