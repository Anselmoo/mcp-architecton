from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Detect Domain Events pattern.

    Heuristics:
    - Event classes ending with 'Event' or dataclasses decorated with @dataclass
    - Emission via publish/emit or appended to an events list on aggregate/entities
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()
    has_event_classes = "class" in lowered and "event" in lowered
    mentions_emit_publish = "emit(" in lowered or "publish(" in lowered
    mentions_events_list = ".events.append(" in lowered or "events = [" in lowered

    if has_event_classes and (mentions_emit_publish or mentions_events_list):
        findings.append(
            {
                "name": "Domain Events",
                "confidence": 0.45,
                "reason": "Event classes with emit/publish or aggregate events list",
            },
        )

    return findings
