# Clean Architecture vocabulary
from dataclasses import dataclass


@dataclass
class Entity:
    id: int


class UseCase:
    def execute(self):
        pass


class Gateway:
    def fetch(self):
        pass
