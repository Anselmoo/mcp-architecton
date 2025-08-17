class ProductA:
    pass


class ProductB:
    pass


def create(kind: str):
    if kind == "a":
        return ProductA()
    else:
        return ProductB()
