"""
Boilerplate Scaffold: Strategy (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=existing API/clients; outputs=same observable behavior
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=38; defs=4) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Extract algorithm interface; inject at seam; no public API change
Cross-ref Pattern: https://refactoring.guru/design-patterns/strategy, https://github.com/faif/python-patterns/tree/master/patterns/behavioral/strategy.py
Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques, https://refactoring.com/catalog/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Strategy(ABC):
    """Abstract strategy defining the algorithm interface."""

    @abstractmethod
    def execute(self, data: Any) -> Any:  # pragma: no cover - scaffold
        raise NotImplementedError


class ConcreteStrategyA(Strategy):
    def execute(self, data: Any) -> Any:
        # Example: transform to upper-case string representation
        return str(data).upper()


class ConcreteStrategyB(Strategy):
    def execute(self, data: Any) -> Any:
        # Example: reverse string representation
        s = str(data)
        return s[::-1]


class Context:
    """Holds a strategy and delegates work to it."""

    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def process(self, data: Any) -> Any:
        return self._strategy.execute(data)

"""
Boilerplate Scaffold: Facade (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=existing API/clients; outputs=same observable behavior
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=53; defs=4) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Introduce a thin facade; do not leak subsystem details; keep client API stable
Cross-ref Pattern: https://refactoring.guru/design-patterns/facade, https://github.com/faif/python-patterns/blob/master/patterns/structural/facade.py
Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques, https://refactoring.com/catalog/
"""

class _SubsystemA:
    def op_a(self) -> str:
        return "A"


class _SubsystemB:
    def op_b(self) -> str:
        return "B"


class Facade:
    """Simplified interface orchestrating multiple subsystems."""

    def __init__(self) -> None:
        self._a = _SubsystemA()
        self._b = _SubsystemB()

    def do(self) -> str:
        # Minimal orchestration example
        return f"{self._a.op_a()}-{self._b.op_b()}"
