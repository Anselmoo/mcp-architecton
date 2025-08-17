from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Decorator: a wrapper class delegating to a contained component.

    Heuristic: class with __init__(..., component) saving to self.<attr> and a
    method that calls self.<attr>.<method>(...).
    """
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        wrapped_attr: str | None = None
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                for st in m.body:
                    if isinstance(st, ast.Assign):
                        for t in st.targets:
                            if (
                                isinstance(t, ast.Attribute)
                                and isinstance(t.value, ast.Name)
                                and t.value.id == "self"
                            ):
                                wrapped_attr = t.attr
        if not wrapped_attr:
            continue

        delegates = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if f"self.{wrapped_attr}." in text:
                    delegates = True
                    break
        if delegates:
            results.append(
                {
                    "name": "Decorator",
                    "confidence": 0.65,
                    "reason": f"Class {cls.name} delegates to wrapped component via self.{wrapped_attr}",
                }
            )
    return results
