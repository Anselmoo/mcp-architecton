from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Publish-Subscribe pattern.

    Heuristics: class or module with subscribe/unsubscribe and publish/emit that iterates listeners.
    """
    findings: list[dict[str, Any]] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            names = {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
            if names & {"subscribe", "unsubscribe", "publish", "emit"}:
                # check publish/emit iterates subscribers
                for m in node.body:
                    if isinstance(m, ast.FunctionDef) and m.name in {"publish", "emit"}:
                        text = ast.get_source_segment(source, m) or ""
                        if any(
                            tok in text
                            for tok in [
                                "for",
                                ".append",
                                ".remove",
                                "listeners",
                                "subscribers",
                            ]
                        ):
                            findings.append(
                                {
                                    "name": "Publish-Subscribe",
                                    "confidence": 0.6,
                                    "reason": (
                                        f"Class {node.name} exposes subscribe/unsubscribe and "
                                        "publish"
                                    ),
                                },
                            )
                            break
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            # module-level list of listeners and functions
            pass
    return findings
