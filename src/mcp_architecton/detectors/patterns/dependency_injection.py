from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Dependency Injection.

    Heuristics:
    - Class __init__ takes one or more non-self parameters.
    - Assignments in __init__: self.<attr> = <param>
    - Other methods reference self.<attr> or call methods on it.
    """
    findings: list[dict[str, Any]] = []

    class_infos: list[
        tuple[str, set[str], bool]
    ] = []  # (class_name, injected_attrs, used_elsewhere)

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            injected_attrs: set[str] = set()
            used_elsewhere = False
            init_params: set[str] = set()
            methods: list[ast.FunctionDef] = []

            for m in node.body:
                if isinstance(m, ast.FunctionDef):
                    methods.append(m)
                    if m.name == "__init__":
                        # Collect non-self parameters
                        for arg in m.args.args[1:]:
                            init_params.add(arg.arg)
                        # Find self.<attr> = <param>
                        for stmt in ast.walk(m):
                            if isinstance(stmt, ast.Assign):
                                for tgt in stmt.targets:
                                    if (
                                        isinstance(tgt, ast.Attribute)
                                        and isinstance(tgt.value, ast.Name)
                                        and tgt.value.id == "self"
                                    ):
                                        if (
                                            isinstance(stmt.value, ast.Name)
                                            and stmt.value.id in init_params
                                        ):
                                            injected_attrs.add(tgt.attr)
            # Check other methods using injected attrs
            for m in methods:
                if m.name == "__init__":
                    continue
                src_m = ast.get_source_segment(source, m) or ""
                for attr in injected_attrs:
                    if f"self.{attr}." in src_m or f"self.{attr}(" in src_m:
                        used_elsewhere = True
                        break
                if used_elsewhere:
                    break

            if injected_attrs and used_elsewhere:
                class_infos.append((node.name, injected_attrs, used_elsewhere))

    if class_infos:
        findings.append(
            {
                "name": "Dependency Injection",
                "confidence": 0.6,
                "reason": f"Classes with injected dependencies: {', '.join(n for n, _, _ in class_infos)}",
            },
        )

    return findings
