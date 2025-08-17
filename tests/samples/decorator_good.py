class Component:
    def op(self, x: int) -> int:
        return x


class DoubleDecorator:
    def __init__(self, component: Component) -> None:
        self.component = component

    def op(self, x: int) -> int:
        # double the result from the wrapped component
        return 2 * self.component.op(x)
