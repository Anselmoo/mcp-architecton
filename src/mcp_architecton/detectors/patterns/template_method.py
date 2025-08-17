from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Template Method: method orchestrating steps on self."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name in {"process", "template", "run"}:
                # simple heuristic: method orchestrates multiple self.<step>() calls
                _ = ast.get_source_segment(source, m) or ""
                # lightweight: ensure it calls at least two self.<step>()
                count = 0
                for n in ast.walk(m):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                        if isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
                            count += 1
                if count >= 2:
                    results.append(
                        {
                            "name": "Template Method",
                            "confidence": 0.6,
                            "reason": f"Class {cls.name}.{m.name} orchestrates multiple self.* calls",
                        }
                    )
                    break
    return results
