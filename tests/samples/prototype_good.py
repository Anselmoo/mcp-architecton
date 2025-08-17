import copy


class Thing:
    def __init__(self, n: int) -> None:
        self.n = n

    def clone(self) -> "Thing":
        return copy.copy(self)
