from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Repository pattern.

    Heuristics:
    - Class name includes 'Repository' or endswith 'Repo'.
    - Methods like add/get/list/remove present.
    - Uses a session/db/collection attribute.
    """
    findings: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and (
            node.name.endswith("Repository") or node.name.endswith("Repo")
        ):
            src = ast.get_source_segment(source, node) or ""
            methods = {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
            has_crud = {"add", "get", "list"} & methods
            uses_session = any(s in src for s in ["session", "db", "collection"])
            if has_crud and uses_session:
                findings.append(
                    {
                        "name": "Repository",
                        "confidence": 0.6,
                        "reason": f"Class {node.name} with CRUD methods and session usage",
                    }
                )

    return findings
