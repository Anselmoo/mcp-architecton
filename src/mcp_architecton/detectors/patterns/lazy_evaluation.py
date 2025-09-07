from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Lazy Evaluation: cached_property or lru_cache or manual lazy @property."""
    findings: list[dict[str, Any]] = []

    # decorator-based
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    for dec in m.decorator_list:
                        if isinstance(dec, ast.Name) and dec.id in {"cached_property", "property"}:
                            # simple @property considered, but increase confidence if it caches
                            text = ast.get_source_segment(source, m) or ""
                            if "hasattr(self," in text and "setattr(self," in text:
                                findings.append(
                                    {
                                        "name": "Lazy Evaluation",
                                        "confidence": 0.6,
                                        "reason": (
                                            f"{node.name}.{m.name} lazily caches computed value"
                                        ),
                                    },
                                )
                        if isinstance(dec, ast.Attribute) and dec.attr in {"lru_cache", "cache"}:
                            findings.append(
                                {
                                    "name": "Lazy Evaluation",
                                    "confidence": 0.6,
                                    "reason": f"Uses functools.{dec.attr} for lazy caching",
                                },
                            )
        elif isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Attribute) and dec.attr in {"lru_cache", "cache"}:
                    findings.append(
                        {
                            "name": "Lazy Evaluation",
                            "confidence": 0.6,
                            "reason": f"Function {node.name} uses functools.{dec.attr}",
                        },
                    )
    return findings
