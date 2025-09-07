from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Hierarchical State Machine (HSM) (heuristic).

    Signals:
    - Presence of a State base class and nested substates
    - Methods like enter/exit/handle and transitions pointing to parent/child
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()
    has_state = "class state" in lowered or "class base_state" in lowered
    has_enter_exit = "def enter(" in lowered and "def exit(" in lowered
    mentions_parent_child = "parent" in lowered and "child" in lowered

    if has_state and has_enter_exit and mentions_parent_child:
        findings.append(
            {
                "name": "Hierarchical State Machine (HSM)",
                "confidence": 0.35,
                "reason": "State base with enter/exit and parent/child references",
            },
        )

    return findings
