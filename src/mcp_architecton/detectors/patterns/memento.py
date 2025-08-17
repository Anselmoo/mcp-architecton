from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Memento: save/restore of object state."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_save = False
        has_restore = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name in {"save", "get_memento"}:
                text = ast.get_source_segment(source, m) or ""
                if any(tok in text for tok in ["__dict__", "copy.copy", "copy.deepcopy", "dict("]):
                    has_save = True
            if isinstance(m, ast.FunctionDef) and m.name in {"restore", "set_memento"}:
                text = ast.get_source_segment(source, m) or ""
                if any(tok in text for tok in ["__dict__.update", "setattr(", "for k, v in"]):
                    has_restore = True
        if has_save and has_restore:
            findings.append(
                {
                    "name": "Memento",
                    "confidence": 0.65,
                    "reason": f"Class {cls.name} provides save/restore state methods",
                }
            )
    return findings
