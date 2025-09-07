from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Delegation Pattern.

    Heuristics:
    - Methods forwarding to an attribute: self.<delegate>.<method>(...)
    - At least two different methods forward to the same attribute.
    """
    findings: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            forwards: dict[str, set[str]] = {}
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and m.name != "__init__":
                    src = ast.get_source_segment(source, m) or ""
                    # naive parse: look for self.<x>.
                    for token in {t for t in src.split() if t.startswith("self.") and "." in t}:
                        if token.count(".") >= 2:  # self.attr.method
                            attr = token.split(".")[1]
                            forwards.setdefault(attr, set()).add(m.name)
            # consider delegation if any attribute is used by >=2 methods
            if any(len(v) >= 2 for v in forwards.values()):
                findings.append(
                    {
                        "name": "Delegation Pattern",
                        "confidence": 0.55,
                        "reason": f"Class {node.name} forwards multiple methods to a delegate",
                    },
                )

    return findings
