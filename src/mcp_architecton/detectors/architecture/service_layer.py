from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Service Layer pattern.

    Heuristics:
    - Module-level function or class method that accepts a `uow` (unit of work) argument
      and orchestrates domain ops within a `with uow as ...:` block, calling commit.
    - Alternatively, naming hints like 'service' / 'usecase' alongside uow/repository mentions.
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()
    has_service_names = any(s in lowered for s in ["service", "usecase", "use_case"])
    mentions_uow_or_repo = any(s in lowered for s in ["uow", "unitofwork", "repository"])

    def uses_uow(fn: ast.FunctionDef) -> bool:
        # has a parameter named uow
        has_uow_param = any(a.arg == "uow" for a in fn.args.args)
        if not has_uow_param:
            return False
        src_fn = ast.get_source_segment(source, fn) or ""
        if "with uow" in src_fn and ".commit(" in src_fn:
            return True
        # AST pass: look for With using Name 'uow'
        for stmt in ast.walk(fn):
            if isinstance(stmt, ast.With):
                for item in stmt.items:
                    if isinstance(item.context_expr, ast.Name) and item.context_expr.id == "uow":
                        # look for commit call inside
                        body_src = "\n".join(
                            (ast.get_source_segment(source, b) or "") for b in stmt.body
                        )
                        if ".commit(" in body_src:
                            return True
        return False

    # direct name + mentions
    if has_service_names and mentions_uow_or_repo:
        findings.append(
            {
                "name": "Service Layer",
                "confidence": 0.5,
                "reason": "Service/usecase orchestrating repositories or unit of work",
            }
        )
    else:
        # scan for functions orchestrating a uow transaction
        for node in getattr(tree, "body", []):
            if isinstance(node, ast.FunctionDef) and uses_uow(node):
                findings.append(
                    {
                        "name": "Service Layer",
                        "confidence": 0.55,
                        "reason": f"Function {node.name} uses uow context and commits",
                    }
                )
                break

    return findings
