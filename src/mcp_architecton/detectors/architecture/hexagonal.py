from __future__ import annotations

import ast
from typing import Any

PORT_HINTS = {"Protocol", "ABC", "abstractmethod"}
ADAPTER_HINTS = {"Adapter", "Repository", "Gateway"}


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """
    Heuristic Hexagonal Architecture detector.

    Signals:
    - Presence of typing.Protocol or abc.ABC ports (interfaces) used as type hints or bases.
    - Classes named *Adapter/*Repository/*Gateway implementing those ports.
    - Adapters calling external libs (imported modules) in their methods.
    """
    findings: list[dict[str, Any]] = []

    # collect imports to detect external calls
    imported_modules: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Import):
            for n in node.names:
                imported_modules.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])

    class_bases: dict[str, set[str]] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            bases: set[str] = set()
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.add(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.add(b.attr)
            class_bases[node.name] = bases

    ports = {name for name, bases in class_bases.items() if bases & PORT_HINTS}

    adapter_classes: list[str] = []
    external_calls = 0

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            name = node.name
            looks_like_adapter = any(hint in name for hint in ADAPTER_HINTS)
            implements_port = bool(ports and (name not in ports)) and any(
                b in ports for b in class_bases.get(name, set())
            )
            if looks_like_adapter or implements_port:
                adapter_classes.append(name)
                # count calls to imported modules inside methods
                for m in node.body:
                    if isinstance(m, ast.FunctionDef):
                        for sub in ast.walk(m):
                            if isinstance(sub, ast.Call):
                                func = sub.func
                                if isinstance(func, ast.Attribute) and isinstance(
                                    func.value,
                                    ast.Name,
                                ):
                                    if func.value.id in imported_modules:
                                        external_calls += 1

    score = 0
    score += 1 if ports else 0
    score += 1 if adapter_classes else 0
    score += 1 if external_calls >= 1 else 0

    if score >= 2:
        findings.append(
            {
                "name": "Hexagonal Architecture",
                "confidence": 0.6 + 0.1 * (score - 2),
                "reason": (
                    "Ports "
                    f"{sorted(ports)} with adapters {adapter_classes} and "
                    f"{external_calls} external call(s)"
                ),
            },
        )

    return findings
