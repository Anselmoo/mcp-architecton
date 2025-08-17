from __future__ import annotations

import ast
from typing import Any

ALIASES = {"request", "execute", "run", "handle"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Adapter: class translating method names to adaptee's API."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        adaptee_attr: str | None = None
        # find self.<adaptee> assignment in __init__
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
                                adaptee_attr = t.attr
        if not adaptee_attr:
            continue
        delegate_count = 0
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if f"self.{adaptee_attr}." in text:
                    delegate_count += 1
        if delegate_count >= 1:
            results.append(
                {
                    "name": "Adapter",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} delegates to adaptee via self.{adaptee_attr}",
                }
            )
    return results
