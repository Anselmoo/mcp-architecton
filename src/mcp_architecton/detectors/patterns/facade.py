from __future__ import annotations

import ast
from typing import Any


def _calls_multiple_constructors_or_functions(node: ast.AST, source: str) -> bool:
    """
    Return True if body constructs/calls 2+ distinct names or functions.

    Very lightweight: count distinct Name() constructor calls and function calls.
    """
    names: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                names.add(n.func.id)
            elif isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
                # allow SubA().a() pattern: count SubA constructor call separately
                pass
    return len(names) >= 2


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Detect Facade: a simplified interface orchestrating multiple subsystems.

    Heuristics:
    - Class with a public method calling 2+ distinct functions/constructors.
    - Or a top-level function doing the same.
    """
    results: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and not m.name.startswith("_"):
                    if _calls_multiple_constructors_or_functions(m, source):
                        results.append(
                            {
                                "name": "Facade",
                                "confidence": 0.6,
                                "reason": f"Class {node.name}.{m.name} orchestrates multiple calls",
                            },
                        )
                        break
        elif isinstance(node, ast.FunctionDef):
            if _calls_multiple_constructors_or_functions(node, source):
                results.append(
                    {
                        "name": "Facade",
                        "confidence": 0.55,
                        "reason": f"Function {node.name} orchestrates multiple calls",
                    },
                )

    return results
