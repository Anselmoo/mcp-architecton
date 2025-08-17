from typing import Protocol

# ruff: noqa: I001


class Strategy(Protocol):
    def __call__(self, x: int, y: int) -> int: ...


def add(x: int, y: int) -> int:
    return x + y


def mul(x: int, y: int) -> int:
    return x * y


class Context:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def compute(self, x: int, y: int) -> int:
        return self.strategy(x, y)
