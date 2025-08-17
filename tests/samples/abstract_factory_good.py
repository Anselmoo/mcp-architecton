class ProductA:
    pass


class ProductB:
    pass


class Factory:
    def create_a(self) -> ProductA:
        return ProductA()

    def create_b(self) -> ProductB:
        return ProductB()
