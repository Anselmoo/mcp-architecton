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