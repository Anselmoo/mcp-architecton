from __future__ import annotations

import ast
from typing import Any


def detect(tree: ast.AST, source: str) -> list[dict[str, Any]]:
    """Detect Graph Search (heuristic and broad).

    Signals:
    - Functions named bfs/dfs/dijkstra/a_star or similar
    - Usage of queue or stack constructs (list as stack, deque)
    """
    findings: list[dict[str, Any]] = []

    lowered = source.lower()
    names = {"bfs", "dfs", "dijkstra", "a_star", "a*", "bellman_ford"}
    if any(n in lowered for n in names) and (
        "queue" in lowered or "stack" in lowered or "deque" in lowered
    ):
        findings.append(
            {
                "name": "Graph Search",
                "confidence": 0.35,
                "reason": "Search algorithm names with queue/stack usage",
            }
        )

    return findings
