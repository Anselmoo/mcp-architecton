from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Object Pool: acquire/release from internal pool/list."""
    findings: list[dict[str, Any]] = []

    for cls in [n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)]:
        has_pool_attr = False
        has_acquire = False
        has_release = False
        for m in cls.body:
            if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                text = ast.get_source_segment(source, m) or ""
                if any(tok in text for tok in ["self.pool =", "self._pool =", "self.objects ="]):
                    has_pool_attr = True
            if isinstance(m, ast.FunctionDef) and m.name in {"acquire", "get"}:
                has_acquire = True
            if isinstance(m, ast.FunctionDef) and m.name in {"release", "put"}:
                has_release = True
        if has_pool_attr and has_acquire and has_release:
            findings.append(
                {
                    "name": "Pool",
                    "confidence": 0.6,
                    "reason": f"Class {cls.name} exposes acquire/release with internal pool",
                },
            )
    return findings
