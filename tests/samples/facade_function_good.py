class SubX:
    def x(self) -> str:
        return "X"


class SubY:
    def y(self) -> str:
        return "Y"


def helper() -> str:
    return "H"


def do_all() -> str:
    return SubX().x() + SubY().y() + helper()
