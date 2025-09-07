from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Borg (shared state singleton) implementation."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_shared = False
        assigns_dict = False
        for m in cls.body:
            if isinstance(m, ast.Assign):
                for t in m.targets:
                    if isinstance(t, ast.Name) and t.id in {
                        "__shared_state",
                        "_shared_state",
                        "shared_state",
                    }:
                        has_shared = True
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                if "self.__dict__ =" in text and "shared_state" in text:
                    assigns_dict = True
        if has_shared and assigns_dict:
            findings.append(
                {
                    "name": "Borg",
                    "confidence": 0.7,
                    "reason": f"Class {cls.name} assigns __dict__ to shared state",
                },
            )
    return findings
