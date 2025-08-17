from __future__ import annotations


class A:
    def accept(self, visitor: Visitor) -> None:
        visitor.visit_A(self)


class B:
    def accept(self, visitor: Visitor) -> None:
        visitor.visit_B(self)


class Visitor:
    def visit_A(self, a: A) -> None:
        pass

    def visit_B(self, b: B) -> None:
        pass
