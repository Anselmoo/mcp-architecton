from __future__ import annotations

import ast
from typing import Any


def analyze_code_for_patterns(source: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all registered detectors against the source and collect findings."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [{"name": "ParseError", "confidence": 0.0, "reason": str(exc)}]

    findings: list[dict[str, Any]] = []
    for name, detector in registry.items():
        try:
            res = detector(tree, source)
            if res:
                findings.extend(res)
        except Exception as exc:  # noqa: BLE001
            findings.append(
                {
                    "name": name,
                    "confidence": 0.0,
                    "reason": f"detector-error: {exc}",
                }
            )
    return findings
