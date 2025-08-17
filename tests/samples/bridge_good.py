class DrawingAPI:
    def draw_circle(self, x: int, y: int, radius: int) -> str:
        return f"circle({x},{y},{radius})"


class DrawingAPIv2:
    def draw_circle(self, x: int, y: int, radius: int) -> str:
        return f"v2 circle({x},{y},{radius})"


class ShapeAbstraction:
    def __init__(self, impl: DrawingAPI) -> None:
        self.impl = impl

    def draw(self, x: int, y: int, r: int) -> str:
        return self.impl.draw_circle(x, y, r)
