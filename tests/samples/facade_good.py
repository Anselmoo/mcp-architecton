class SubA:
    def a(self) -> str:
        return "A"


class SubB:
    def b(self) -> str:
        return "B"


def util() -> str:
    return "U"


class Facade:
    def do(self) -> str:
        return SubA().a() + SubB().b() + util()
