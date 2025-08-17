from __future__ import annotations


class Mediator:
    def __init__(self) -> None:
        self.members: list[Colleague] = []

    def register(self, m: Colleague) -> None:
        self.members.append(m)

    def notify(self, msg: str) -> None:
        for m in self.members:
            m.receive(msg)


class Colleague:
    def __init__(self, mediator: Mediator) -> None:
        self.mediator: Mediator = mediator

    def send(self, msg: str) -> None:
        self.mediator.notify(msg)

    def receive(self, msg: str) -> None:
        pass
