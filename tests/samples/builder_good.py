class Product:
    def __init__(self, x: int) -> None:
        self.x = x


class ProductBuilder:
    def __init__(self) -> None:
        self._x = 0

    def with_x(self, x: int) -> "ProductBuilder":
        self._x = x
        return self

    def build(self) -> Product:
        return Product(self._x)
