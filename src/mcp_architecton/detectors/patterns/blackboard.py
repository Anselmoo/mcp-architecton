from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Blackboard pattern (very heuristic).

    Signals:
    - A central blackboard dict or class attribute collecting facts/solutions
    - Multiple knowledge sources writing to it via .append / key assignment
    """
    findings: list[dict[str, Any]] = []

    has_blackboard = False
    writers = 0

    src_module = source
    if "blackboard" in src_module and ("={" in src_module or "= {}" in src_module):
        has_blackboard = True

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            cls_src = ast.get_source_segment(source, node) or ""
            if "blackboard" in cls_src and ("={" in cls_src or "= {}" in cls_src):
                has_blackboard = True

    # writers: look for ".append(" or "[key] =" to blackboard
    if has_blackboard:
        for token in src_module.split():
            if ".append(" in token or "]=" in token:
                writers += 1

    if has_blackboard and writers >= 2:
        findings.append(
            {
                "name": "Blackboard",
                "confidence": 0.4,
                "reason": "Central blackboard with multiple writers",
            },
        )

    return findings
