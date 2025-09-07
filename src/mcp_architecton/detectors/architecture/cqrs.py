from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect CQRS (Command Query Responsibility Segregation).

    Heuristics:
    - Presence of both command and query handlers (e.g., handle_command/handle_query).
    - Commands mutate via UoW/repository; queries read via a view/get_*.
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()

    # Textual hints
    has_commands_text = ("command" in lowered) and (
        "handle_" in lowered or "def handle(" in lowered
    )
    has_queries_text = ("query" in lowered) and ("handle_" in lowered or "get_" in lowered)

    # AST inspection for handler names
    has_command_handler = False
    has_query_handler = False
    mutates_state = False
    reads_view = False

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef):
            name = node.name.lower()
            if "command" in name:
                has_command_handler = True
                src_fn = ast.get_source_segment(source, node) or ""
                if ("uow" in src_fn and ".add(" in src_fn) or (
                    "repo" in src_fn and ".add(" in src_fn
                ):
                    mutates_state = True
            if "query" in name:
                has_query_handler = True
                src_fn = ast.get_source_segment(source, node) or ""
                if ("view." in src_fn and ".get_" in src_fn) or (
                    "return" in src_fn and "get_" in src_fn
                ):
                    reads_view = True

    if (has_commands_text or has_command_handler) and (has_queries_text or has_query_handler):
        confidence = 0.4
        if has_command_handler and has_query_handler:
            confidence += 0.1
        if mutates_state:
            confidence += 0.05
        if reads_view:
            confidence += 0.05
        findings.append(
            {
                "name": "CQRS",
                "confidence": min(confidence, 0.7),
                "reason": "Detected command and query handlers separation",
            },
        )

    return findings
