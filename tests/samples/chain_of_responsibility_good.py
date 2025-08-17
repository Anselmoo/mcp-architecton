from __future__ import annotations


class Handler:
    def __init__(self, nxt: Handler | None = None) -> None:
        self.next: Handler | None = nxt

    def handle(self, x: object) -> object:
        if self.next:
            return self.next.handle(x)
        return x
