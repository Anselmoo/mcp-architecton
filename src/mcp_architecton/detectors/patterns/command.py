from __future__ import annotations

import ast
from typing import Any

INVOKE_NAMES = {"execute", "run", "invoke", "do"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Command: a class encapsulating an action via execute/run."""
    results: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        methods = {m.name for m in cls.body if isinstance(m, ast.FunctionDef)}
        if methods & INVOKE_NAMES:
            results.append(
                {
                    "name": "Command",
                    "confidence": 0.55,
                    "reason": (
                        f"Class {cls.name} defines an invoker method {methods & INVOKE_NAMES}"
                    ),
                },
            )
    return results
