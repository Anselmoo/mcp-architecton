from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect State pattern: Context delegates to self.state.* methods."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_state_attr = False
        delegates = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                if "self.state" in text:
                    has_state_attr = True
            if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                text = ast.get_source_segment(source, m) or ""
                if "self.state." in text:
                    delegates = True
        if has_state_attr and delegates:
            findings.append(
                {
                    "name": "State",
                    "confidence": 0.65,
                    "reason": f"Class {cls.name} delegates operations to current state",
                }
            )
    return findings
