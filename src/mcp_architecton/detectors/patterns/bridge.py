from __future__ import annotations

import ast
from typing import Any

IMPL_NAMES = {"implementor", "impl", "driver", "backend"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Bridge: Abstraction has a reference to Implementor and delegates work."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        impl_attr = None
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                for name in IMPL_NAMES:
                    if f"self.{name} =" in text:
                        impl_attr = name
                        break
        if not impl_attr:
            continue
        uses_impl = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if f"self.{impl_attr}." in text:
                    uses_impl = True
                    break
        if uses_impl:
            results.append(
                {
                    "name": "Bridge",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} delegates to implementor via self.{impl_attr}",
                },
            )
    return results
