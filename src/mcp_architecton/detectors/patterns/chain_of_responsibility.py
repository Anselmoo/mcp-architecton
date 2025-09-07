from __future__ import annotations

import ast
from typing import Any

HANDLER_NAMES = {"set_next", "next", "successor"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Chain of Responsibility: handlers linked and call next.handle."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_link = False
        delegates_next = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef):
                if m.name in HANDLER_NAMES or m.name == "__init__":
                    text = ast.get_source_segment(source, m) or ""
                    if "self.next" in text or "self.successor" in text:
                        has_link = True
                text = ast.get_source_segment(source, m) or ""
                if ".handle(" in text and ("self.next" in text or "self.successor" in text):
                    delegates_next = True
        if has_link and delegates_next:
            results.append(
                {
                    "name": "Chain of Responsibility",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} links handlers and delegates to next",
                },
            )
    return results
