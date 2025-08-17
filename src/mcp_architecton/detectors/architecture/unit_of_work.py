from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Unit of Work pattern.

    Heuristics:
    - Class named UnitOfWork or endswith Uow provides context manager methods
    - Has begin/commit/rollback and manages a session
    """
    findings: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and (
            node.name.lower() == "unitofwork" or node.name.lower().endswith("uow")
        ):
            methods = {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
            cm_ok = "__enter__" in methods and "__exit__" in methods
            tx_ok = {"begin", "commit", "rollback"} & methods
            src = ast.get_source_segment(source, node) or ""
            manages_session = any(s in src for s in ["session", "engine", "connection"])
            if cm_ok and manages_session and tx_ok:
                findings.append(
                    {
                        "name": "Unit of Work",
                        "confidence": 0.6,
                        "reason": f"{node.name} manages session and transaction lifecycle",
                    }
                )

    return findings
