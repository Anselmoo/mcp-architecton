from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Front Controller.

    Signals:
    - A class or module-level router mapping (dict of route->handler).
    - A single entry function/method (handle/dispatch) that looks up a handler and calls it.
    """
    findings: list[dict[str, Any]] = []

    has_route_map = False
    route_map_name = None
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Dict):
                # look for dict of callables
                if any(isinstance(k, ast.Constant) for k in node.value.keys or []):
                    if any(
                        isinstance(v, ast.Name | ast.Attribute) for v in node.value.values or []
                    ):
                        has_route_map = True
                        if node.targets and isinstance(node.targets[0], ast.Name):
                            route_map_name = node.targets[0].id
        elif isinstance(node, ast.ClassDef):
            # detect instance route maps set in __init__
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and m.name == "__init__":
                    src = ast.get_source_segment(source, m) or ""
                    if "self.routes" in src and "{" in src and "}" in src:
                        has_route_map = True

    def is_dispatch(fn: ast.FunctionDef) -> bool:
        if fn.name in {"handle", "dispatch", "route", "process_request"}:
            src = ast.get_source_segment(source, fn) or ""
            if (route_map_name and route_map_name in src) or ".routes" in src or ".get(" in src:
                return True
        return False

    dispatchers = 0
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef) and is_dispatch(node):
            dispatchers += 1
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and is_dispatch(m):
                    dispatchers += 1

    if has_route_map and dispatchers:
        findings.append(
            {
                "name": "Front Controller",
                "confidence": 0.65,
                "reason": (f"Routing table '{route_map_name}' with {dispatchers} dispatcher(s)"),
            }
        )

    return findings
