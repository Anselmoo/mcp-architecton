# Ports & Adapters example
from typing import Protocol


class InputPort(Protocol):
    def run(self, data: str) -> str: ...


class OutputPort(Protocol):
    def send(self, result: str) -> None: ...


class Adapter:
    def __init__(self, output: OutputPort):
        self.output = output

    def process(self, port: InputPort, data: str) -> None:
        res = port.run(data)
        self.output.send(res)
