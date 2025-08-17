from __future__ import annotations

import ast
from typing import Any

MODEL_HINTS = {"Model", "Entity"}
VIEW_HINTS = {"View", "Template", "Renderer"}
CONTROLLER_HINTS = {"Controller", "Presenter"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    roles: dict[str, str] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            name = node.name
            if any(name.endswith(x) for x in MODEL_HINTS):
                roles[name] = "Model"
            if any(name.endswith(x) for x in VIEW_HINTS):
                roles[name] = "View"
            if any(name.endswith(x) for x in CONTROLLER_HINTS):
                roles[name] = "Controller"

    controller_wires = 0
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and roles.get(node.name) == "Controller":
            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    src = ast.get_source_segment(source, m) or ""
                    # Controller uses model and passes to view
                    uses_model = "Model(" in src or "self.model" in src
                    uses_view = "View(" in src or "self.view" in src or "render(" in src
                    if uses_model and uses_view:
                        controller_wires += 1

    score = 0
    score += 1 if any(r == "Model" for r in roles.values()) else 0
    score += 1 if any(r == "View" for r in roles.values()) or "render(" in source else 0
    score += 1 if any(r == "Controller" for r in roles.values()) else 0
    score += 1 if controller_wires else 0

    if score >= 3:
        findings.append(
            {
                "name": "Model-View-Controller (MVC)",
                "confidence": 0.6 + 0.1 * (score - 3),
                "reason": (
                    "Roles present "
                    f"{sorted(set(roles.values()))}, controller wiring={controller_wires}"
                ),
            }
        )

    return findings
