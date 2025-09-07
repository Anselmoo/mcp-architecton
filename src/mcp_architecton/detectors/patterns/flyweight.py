from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Detect Flyweight: module-level cache reused in a factory function.

    Heuristic: find a module-level dict and a function that checks membership
    and returns cached values or creates & stores new ones.
    """
    results: list[dict[str, Any]] = []

    dict_names: set[str] = set()
    for n in getattr(tree, "body", []):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
            if n.targets and isinstance(n.targets[0], ast.Name):
                dict_names.add(n.targets[0].id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.Dict):
            target = n.target
            if isinstance(target, ast.Name):
                dict_names.add(target.id)
    if not dict_names:
        return results

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef):
            src = ast.get_source_segment(source, node) or ""
            if any(name in src for name in dict_names) and (
                " in " in src and "[" in src and "]" in src and "return " in src
            ):
                results.append(
                    {
                        "name": "Flyweight",
                        "confidence": 0.55,
                        "reason": f"Function {node.name} appears to use a cache for instances",
                    },
                )
                break
    return results
