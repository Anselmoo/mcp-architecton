class Legacy:
    def do_it(self, x: int) -> int:
        return x * 2


class Adapter:
    def __init__(self, adaptee: Legacy) -> None:
        self.adaptee = adaptee

    def compute(self, value: int) -> int:
        return self.adaptee.do_it(value)
