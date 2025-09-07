from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect simple Factory functions (alias of Factory Method heuristics)."""
    findings: list[dict[str, Any]] = []

    class_names = {n.name for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)}

    def returns_known_class(fn: ast.FunctionDef) -> bool:
        src = ast.get_source_segment(source, fn) or ""
        return any(f"{cn}(" in src for cn in class_names)

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef) and node.name.lower() in {"factory", "create"}:
            if returns_known_class(node):
                findings.append(
                    {
                        "name": "Factory",
                        "confidence": 0.6,
                        "reason": f"Function {node.name} returns instances of module classes",
                    },
                )
    return findings
