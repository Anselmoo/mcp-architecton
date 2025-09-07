from __future__ import annotations

import ast
from typing import Any

LAYER_NAMES = {
    "presentation",
    "ui",
    "application",
    "service",
    "domain",
    "infrastructure",
    "persistence",
    "data",
}
ROLE_NAMES = {"Service", "Repository", "Controller"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect classic Layered Architecture signals.

    Signals:
    - Mentions of common layer module/attribute names.
    - Classes named with role suffixes (Service/Repository/Controller).
    - Methods wiring across roles (e.g., Controller -> Service -> Repository).
    """
    findings: list[dict[str, Any]] = []

    src = source
    layer_hits = {name for name in LAYER_NAMES if name in src}

    role_classes: dict[str, str] = {}  # class -> role
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            for role in ROLE_NAMES:
                if node.name.endswith(role):
                    role_classes[node.name] = role

    wiring = 0
    # very naive: look for Controller calling Service method and Service calling Repository
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            role = role_classes.get(node.name)
            if role == "Controller":
                for m in node.body:
                    if isinstance(m, ast.FunctionDef):
                        msrc = ast.get_source_segment(source, m) or ""
                        if ".Service(" in msrc or ".service" in msrc or "self.service." in msrc:
                            wiring += 1
            if role == "Service":
                for m in node.body:
                    if isinstance(m, ast.FunctionDef):
                        msrc = ast.get_source_segment(source, m) or ""
                        if (
                            ".Repository(" in msrc
                            or ".repository" in msrc
                            or "self.repository." in msrc
                        ):
                            wiring += 1

    score = 0
    score += 1 if layer_hits else 0
    score += 1 if role_classes else 0
    score += 1 if wiring else 0

    if score >= 2:
        findings.append(
            {
                "name": "Layered Architecture",
                "confidence": 0.6 + 0.1 * (score - 2),
                "reason": (
                    "Layers "
                    f"{sorted(layer_hits)} with roles {sorted(role_classes.values())} "
                    f"and wiring={wiring}"
                ),
            },
        )

    return findings
