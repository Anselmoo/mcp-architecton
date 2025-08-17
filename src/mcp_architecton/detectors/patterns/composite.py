from __future__ import annotations

import ast
from typing import Any

CHILDREN = {"children", "nodes", "elements", "items"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Composite: manages a list of children and iterates to call child ops."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_children = None
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                for name in CHILDREN:
                    if f"self.{name}" in text:
                        has_children = name
                        break
        if not has_children:
            continue
        iterates = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                for node in ast.walk(m):
                    if isinstance(node, ast.For):
                        if (
                            isinstance(node.iter, ast.Attribute)
                            and isinstance(node.iter.value, ast.Name)
                            and node.iter.value.id == "self"
                            and node.iter.attr == has_children
                        ):
                            iterates = True
                            break
                    # also detect list comps or generator expressions over self.children
                    if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
                        it = node.generators[0].iter if node.generators else None
                        if (
                            isinstance(it, ast.Attribute)
                            and isinstance(it.value, ast.Name)
                            and it.value.id == "self"
                            and it.attr == has_children
                        ):
                            iterates = True
                            break
                if iterates:
                    break
        if iterates:
            results.append(
                {
                    "name": "Composite",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} iterates self.{has_children} and calls child ops",
                }
            )
    return results
