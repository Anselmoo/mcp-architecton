from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Message Bus pattern.

    Heuristics:
    - A dict of handlers keyed by event/command types
    - A function/class dispatching publish/handle that routes to handlers
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()
    has_bus = "messagebus" in lowered or "message_bus" in lowered or "bus =" in lowered
    has_handlers_map = ("handlers = {" in lowered) or ("handler_map" in lowered)
    has_publish = (
        "def publish(" in lowered or "def handle(" in lowered or "def dispatch(" in lowered
    )

    if (has_bus or has_handlers_map) and has_publish:
        findings.append(
            {
                "name": "Message Bus",
                "confidence": 0.45,
                "reason": "Handlers map with publish/dispatch entrypoint",
            },
        )

    return findings
