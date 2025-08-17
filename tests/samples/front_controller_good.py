def home() -> str:
    return "home"


def about() -> str:
    return "about"


class FrontController:
    def __init__(self) -> None:
        self.routes = {"/": home, "/about": about}

    def dispatch(self, path: str) -> str:
        handler = self.routes.get(path)
        if handler:
            return handler()
        return "404"
