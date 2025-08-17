from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Registry: track subclasses via __init_subclass__ or class-level list."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_init_subclass = any(
            isinstance(m, ast.FunctionDef) and m.name == "__init_subclass__" for m in cls.body
        )
        has_registry_attr = any(
            isinstance(m, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id in {"REGISTRY", "registry", "_registry"}
                for t in m.targets
            )
            for m in cls.body
        )
        if has_init_subclass and has_registry_attr:
            findings.append(
                {
                    "name": "Registry",
                    "confidence": 0.65,
                    "reason": (
                        f"Class {cls.name} defines __init_subclass__ and a registry container"
                    ),
                }
            )
    return findings
