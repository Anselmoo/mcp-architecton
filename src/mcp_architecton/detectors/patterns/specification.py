from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Detect Specification pattern signals.

    Heuristics: classes with is_satisfied_by and boolean combinators (__and__/__or__/__invert__).
    """
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        methods = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        if "is_satisfied_by" in methods and (
            methods & {"__and__", "__or__", "__invert__", "and_", "or_", "not_"}
        ):
            findings.append(
                {
                    "name": "Specification",
                    "confidence": 0.65,
                    "reason": f"Class {cls.name} defines is_satisfied_by and boolean combinators",
                },
            )
    return findings
