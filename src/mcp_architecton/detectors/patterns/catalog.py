from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Detect Catalog: general dispatcher calling specialized methods.

    Heuristics:
    - A class method or function builds a dict mapping keys to callables and dispatches via it
    - Or a method uses if/elif chain on a parameter to call different internal methods
    """
    findings: list[dict[str, Any]] = []

    def dispatch_via_dict(fn: ast.FunctionDef) -> bool:
        # look for {...: self.<method>, ...}[key](...)
        src = ast.get_source_segment(source, fn) or ""
        return "}[" in src and "](" in src and "self." in src and "{" in src

    def dispatch_via_if(fn: ast.FunctionDef) -> bool:
        if not fn.args.args:
            return False
        p0 = fn.args.args[0].arg
        text = ast.get_source_segment(source, fn) or ""
        return f"if {p0} ==" in text or f"elif {p0} ==" in text or f"match {p0}:" in text

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    if dispatch_via_dict(m) or dispatch_via_if(m):
                        findings.append(
                            {
                                "name": "Catalog",
                                "confidence": 0.6,
                                "reason": f"{node.name}.{m.name} dispatches to specialized methods",
                            },
                        )
                        break
        elif isinstance(node, ast.FunctionDef):
            if dispatch_via_dict(node) or dispatch_via_if(node):
                findings.append(
                    {
                        "name": "Catalog",
                        "confidence": 0.55,
                        "reason": f"Function {node.name} dispatches via catalog mapping",
                    },
                )
    return findings
