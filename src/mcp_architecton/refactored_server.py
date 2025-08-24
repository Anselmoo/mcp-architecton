

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
