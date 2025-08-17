from __future__ import annotations

import ast
from typing import Any

CLEAN_TERMS = {"use_case", "usecase", "interactor", "entities", "adapters", "boundaries", "gateway"}
DOMAIN_TERMS = {"entity", "entities", "value_object", "aggregate"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Clean Architecture hints.

    Signals:
    - Presence of use_case/interactor modules/functions/classes.
    - Domain terms present while imports are mostly stdlib/local (no heavy external deps).
    - Adapters layer references.
    """
    findings: list[dict[str, Any]] = []

    src = source.lower()
    clean_hits = {t for t in CLEAN_TERMS if t in src}
    domain_hits = {t for t in DOMAIN_TERMS if t in src}

    external_imports = 0
    std_ok = {
        "typing",
        "dataclasses",
        "abc",
        "pathlib",
        "datetime",
        "uuid",
        "re",
        "collections",
        "math",
        "itertools",
        "functools",
        "json",
    }
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Import):
            for n in node.names:
                mod = n.name.split(".")[0]
                if mod not in std_ok:
                    external_imports += 1
        elif isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module.split(".")[0]
            if mod not in std_ok:
                external_imports += 1

    score = 0
    score += 1 if clean_hits else 0
    score += 1 if domain_hits else 0
    score += 1 if external_imports == 0 else 0

    if score >= 2:
        findings.append(
            {
                "name": "Clean Architecture",
                "confidence": 0.6 + 0.1 * (score - 2),
                "reason": (
                    "Signals "
                    f"{sorted(clean_hits)} / domain {sorted(domain_hits)} / "
                    f"external_imports={external_imports}"
                ),
            }
        )

    return findings
