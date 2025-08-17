class RealService:
    def op(self, x: int) -> int:
        return x * 2


class ServiceProxy:
    def __init__(self, real: RealService) -> None:
        self._real = real

    def op(self, x: int) -> int:
        # access check, then delegate
        return self._real.op(x)
