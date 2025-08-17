class Leaf:
    def operation(self) -> str:
        return "leaf"


class Composite:
    def __init__(self) -> None:
        self.children: list[Leaf] = []

    def add(self, node: Leaf) -> None:
        self.children.append(node)

    def remove(self, node: Leaf) -> None:
        self.children.remove(node)

    def operation(self) -> str:
        return ",".join(child.operation() for child in self.children)
