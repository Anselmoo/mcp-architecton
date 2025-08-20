from __future__ import annotations

import ast
from typing import Any

import astroid  # type: ignore


def analyze_code_for_patterns(source: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all registered detectors against the source and collect findings."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [{"name": "ParseError", "confidence": 0.0, "reason": str(exc)}]

    # Best-effort: parse using astroid for richer inference; detectors still receive stdlib AST
    # Warm astroid to ensure consistent behavior (ignore errors)
    try:  # pragma: no cover - optional
        astroid.parse(source)  # type: ignore[attr-defined]
    except Exception:
        pass

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


# Optional utilities for callers that want richer context
def astroid_summary(source: str) -> dict[str, Any]:
    """Return a light summary using astroid when available (names, functions).

    Purely optional helper. Does not affect detectors.
    """
    try:  # pragma: no cover - optional
        mod: Any = astroid.parse(source)  # type: ignore[attr-defined]
        try:
            body: list[Any] = list(mod.body)  # type: ignore[attr-defined]
        except Exception:
            body = []
        names = sorted([str(getattr(n, "name", "")) for n in body if hasattr(n, "name")])
        funcs = [
            str(getattr(n, "name", ""))
            for n in body
            if n.__class__.__name__ in {"FunctionDef", "AsyncFunctionDef"}
        ]
        return {"names": names, "functions": funcs}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


__all__ = ["analyze_code_for_patterns", "astroid_summary"]
