from __future__ import annotations

import ast
from typing import Any

TIERS = {"Controller", "Service", "Repository"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect 3-Tier Architecture (Controller-Service-Repository) wiring."""
    findings: list[dict[str, Any]] = []

    classes = {n.name: n for n in getattr(tree, "body", []) if isinstance(n, ast.ClassDef)}
    roles: dict[str, str] = {}
    for name, _cls in classes.items():
        for role in TIERS:
            if name.endswith(role):
                roles[name] = role

    wiring = 0
    for name, cls in classes.items():
        role = roles.get(name)
        if not role:
            continue
        for m in cls.body:
            if isinstance(m, ast.FunctionDef):
                src = ast.get_source_segment(source, m) or ""
                if role == "Controller" and (
                    "Service(" in src or ".service" in src or "self.service." in src
                ):
                    wiring += 1
                if role == "Service" and (
                    "Repository(" in src or ".repository" in src or "self.repository." in src
                ):
                    wiring += 1

    score = 0
    score += 1 if roles else 0
    score += 1 if wiring else 0

    if score >= 2:
        findings.append(
            {
                "name": "3-Tier Architecture",
                "confidence": 0.65,
                "reason": f"Roles {sorted(roles.values())} with wiring steps={wiring}",
            }
        )

    return findings
