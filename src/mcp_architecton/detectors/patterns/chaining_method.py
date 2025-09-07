from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Chaining Method: multiple methods returning self for fluent API."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        returns_self = 0
        for m in [b for b in cls.body if isinstance(b, ast.FunctionDef) and b.name != "__init__"]:
            text = ast.get_source_segment(source, m) or ""
            if "return self" in text:
                returns_self += 1
        if returns_self >= 2:
            findings.append(
                {
                    "name": "Chaining Method",
                    "confidence": 0.65,
                    "reason": f"Class {cls.name} has {returns_self} methods returning self",
                },
            )
    return findings
