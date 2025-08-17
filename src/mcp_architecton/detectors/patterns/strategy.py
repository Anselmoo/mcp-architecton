from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Strategy: class storing a strategy and calling it later."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        strat_attr: str | None = None
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                # crude heuristic to find self.<x> = strategy
                for node in ast.walk(m):
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if (
                                isinstance(t, ast.Attribute)
                                and isinstance(t.value, ast.Name)
                                and t.value.id == "self"
                            ):
                                strat_attr = t.attr
        if not strat_attr:
            continue

        # look for call: self.<attr>(...)
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if f"self.{strat_attr}(" in text:
                    results.append(
                        {
                            "name": "Strategy",
                            "confidence": 0.65,
                            "reason": f"Class {cls.name} invokes strategy via self.{strat_attr}(...)",
                        }
                    )
                    break
    return results
