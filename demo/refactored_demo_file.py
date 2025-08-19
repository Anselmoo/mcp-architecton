from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, TypeAlias, TypeVar

Handler: TypeAlias = Callable[["Request"], "Response"]
JSONBody: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None
H = TypeVar("H", bound=Handler)


@dataclass(slots=True)
class Request:
    method: str
    path: str
    query: Mapping[str, str] = field(default_factory=dict[str, str])
    body: Any = None


@dataclass(slots=True)
class Response:
    status_code: int = 200
    body: JSONBody = None
    headers: Mapping[str, str] = field(default_factory=dict[str, str])

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status_code, "body": self.body, "headers": self.headers}


class Router:
    def __init__(self) -> None:
        self._routes: dict[str, Handler] = {}

    def add(self, path: str, handler: Handler) -> None:
        self._routes[path] = handler

    def resolve(self, path: str) -> Handler | None:
        return self._routes.get(path)


class App:
    def __init__(self) -> None:
        self._router = Router()

    def route(self, path: str) -> Callable[[H], H]:
        def _decorator(fn: H) -> H:
            self._router.add(path, fn)
            return fn

        return _decorator

    def handle(
        self, method: str, path: str, query: Mapping[str, str] | None = None, body: Any = None
    ) -> Response:
        req = Request(method=method.upper(), path=path, query=query or {}, body=body)
        handler = self._router.resolve(req.path)
        if handler is None:
            return Response(status_code=404, body={"error": "not found"})
        return handler(req)


# --- Strategy pattern for Fibonacci computation (domain-specific) ---
class FibStrategy(ABC):
    @abstractmethod
    def compute(self, n: int) -> int:  # pragma: no cover - simple demo
        raise NotImplementedError


class IterativeFib(FibStrategy):
    def compute(self, n: int) -> int:
        if n < 2:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


class MemoizedFib(FibStrategy):
    @staticmethod
    @lru_cache(maxsize=None)
    def _fib(k: int) -> int:
        if k < 2:
            return k
        return MemoizedFib._fib(k - 1) + MemoizedFib._fib(k - 2)

    def compute(self, n: int) -> int:
        return MemoizedFib._fib(n)


def create_app() -> App:
    app = App()

    @app.route("/health")
    def health(req: Request) -> Response:
        # trivial health check
        return Response(200, {"status": "ok", "method": req.method})

    @app.route("/echo")
    def echo(req: Request) -> Response:
        # TODO: refactor: extract validation and normalization of query params into a helper
        msg = req.query.get("q", "").strip()
        if not msg:
            return Response(400, {"error": "missing 'q' query parameter"})
        return Response(200, {"echo": msg})

    @app.route("/compute")
    def compute(req: Request) -> Response:
        # Parse and validate input
        raw_n = req.query.get("n", "10")
        try:
            n = int(raw_n)
        except ValueError:
            return Response(400, {"error": "n must be an integer"})
        if n < 0 or n > 35:
            # keep bounds small to avoid slow demo work
            return Response(400, {"error": "n must be between 0 and 35"})

        # Choose algorithm strategy via query param (default: iterative)
        algo = (req.query.get("algo", "iter") or "iter").lower()
        if algo == "memo":
            strategy: FibStrategy = MemoizedFib()
        else:
            strategy = IterativeFib()

        return Response(200, {"n": n, "fib": strategy.compute(n)})

    return app


# Minimal inline demo (kept out of tests)
if __name__ == "__main__":  # pragma: no cover
    app = create_app()
    print(app.handle("GET", "/health").to_dict())
    print(app.handle("GET", "/echo", {"q": " hello "}).to_dict())
    print(app.handle("GET", "/compute", {"n": "12"}).to_dict())
    print(app.handle("GET", "/missing").to_dict())
