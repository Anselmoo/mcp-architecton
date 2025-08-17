from __future__ import annotations

from typing import Any


class Observer:
    def update(self, data: Any) -> None:
        pass


class Subject:
    observers: list[Observer] = []

    def attach(self, obs: Observer) -> None:
        self.observers.append(obs)

    def detach(self, obs: Observer) -> None:
        self.observers.remove(obs)

    def notify(self, data: Any) -> None:
        for o in self.observers:
            o.update(data)
