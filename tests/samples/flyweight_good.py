cache: dict[str, object] = {}


class Thing:
    def __init__(self, name: str) -> None:
        self.name = name


def get_thing(name: str) -> Thing:
    if name in cache:
        return cache[name]  # type: ignore[return-value]
    cache[name] = Thing(name)
    return cache[name]  # type: ignore[return-value]
