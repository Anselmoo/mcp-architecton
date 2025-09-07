from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Proxy: class holding a real subject and delegating calls."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        real_attr: str | None = None
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
                                real_attr = t.attr
        if not real_attr:
            continue
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if f"self.{real_attr}." in text:
                    results.append(
                        {
                            "name": "Proxy",
                            "confidence": 0.65,
                            "reason": f"Class {cls.name} delegates to real subject via self.{real_attr}",
                        },
                    )
                    break
    return results
