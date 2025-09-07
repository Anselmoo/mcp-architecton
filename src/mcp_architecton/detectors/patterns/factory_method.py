from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Factory Method: function selecting and returning different classes.

    Heuristic: top-level function with if/elif branching that returns instances
    of different classes.
    """
    results: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef):
            returned_classes: set[str] = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Call):
                    func = n.value.func
                    if isinstance(func, ast.Name):
                        returned_classes.add(func.id)
            if len(returned_classes) >= 2:
                results.append(
                    {
                        "name": "Factory Method",
                        "confidence": 0.6,
                        "reason": f"Function {node.name} returns multiple concrete types",
                    },
                )
    return results
