from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Abstract Factory by multiple create_* methods constructing different products."""
    results: list[dict[str, Any]] = []

    module_classes = {n.name for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)}

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        create_methods: dict[str, set[str]] = {}
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name.startswith("create_"):
                src = ast.get_source_segment(source, m) or ""
                returns: set[str] = set()
                for name in module_classes:
                    if f"return {name}(" in src:
                        returns.add(name)
                if returns:
                    create_methods[m.name] = returns
        product_set: set[str] = set()
        for s in create_methods.values():
            product_set |= s
        if len(create_methods) >= 2 and len(product_set) >= 2:
            results.append(
                {
                    "name": "Abstract Factory",
                    "confidence": 0.65,
                    "reason": (
                        f"Class '{cls.name}' provides multiple factories for {sorted(product_set)}"
                    ),
                },
            )
    return results
