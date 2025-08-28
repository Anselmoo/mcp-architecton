"""
Boilerplate Scaffold: Strategy (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=existing API/clients; outputs=same observable behavior
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=38; defs=4) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Extract algorithm interface; inject at seam; no public API change
Cross-ref Pattern: https://refactoring.guru/design-patterns/strategy, https://github.com/faif/python-patterns/tree/master/patterns/behavioral/strategy.py
Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques, https://refactoring.com/catalog/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, cast


class Strategy(ABC):
    """Abstract strategy defining the algorithm interface."""

    @abstractmethod
    def execute(self, data: Any) -> Any:  # pragma: no cover - scaffold
        raise NotImplementedError


class ConcreteStrategyA(Strategy):
    def execute(self, data: Any) -> Any:
        # Example: transform to upper-case string representation
        return str(data).upper()


class ConcreteStrategyB(Strategy):
    def execute(self, data: Any) -> Any:
        # Example: reverse string representation
        s = str(data)
        return s[::-1]


class Context:
    """Holds a strategy and delegates work to it."""

    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def process(self, data: Any) -> Any:
        return self._strategy.execute(data)


"""
Boilerplate Scaffold: Adapter (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=Stable Target interface; client calls unchanged; outputs=Same behavior via Adaptee; no observable changes
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=56; defs=4) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Stabilize client API with an adapter; delegate to existing impl; keep diff tiny
Cross-ref Pattern: https://refactoring.guru/design-patterns/adapter, https://github.com/faif/python-patterns/tree/master/patterns/structural/adapter.py
Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques, https://refactoring.com/catalog/
"""


class Target:
    def request(self) -> str:  # pragma: no cover - scaffold
        return "target"


class Adaptee:
    def specific_request(self) -> str:
        return "adaptee"


class Adapter(Target):
    def __init__(self, adaptee: Adaptee) -> None:
        self._adaptee = adaptee

    def request(self) -> str:
        return self._adaptee.specific_request()


"""
Boilerplate Scaffold: Factory Method (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=existing API/clients; outputs=same observable behavior
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=88; defs=7) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Create via factory; avoid direct constructors in clients; preserve call sites
Cross-ref Pattern: https://refactoring.guru/design-patterns/factory-method, https://github.com/faif/python-patterns/tree/master/patterns/creational/factory.py
Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques, https://refactoring.com/catalog/
"""


class ProductA: ...


class ProductB: ...


def create_product(kind: str):  # pragma: no cover - scaffold
    if kind == "A":
        return ProductA()
    elif kind == "B":
        return ProductB()
    raise ValueError(f"Unknown kind: {kind}")


# --- Strategy wiring to non_pythonic_large.giant_switch equivalents ---


def _load_non_pythonic_module():
    """Load examples/non_pythonic_large.py without requiring a package import.

    Keeps this file standalone/runnable from repo root.
    """
    import importlib.util
    import pathlib
    import sys

    mod_name = "non_pythonic_large"
    if mod_name in sys.modules:
        return sys.modules[mod_name]

    path = pathlib.Path(__file__).with_name("non_pythonic_large.py")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError("Cannot load non_pythonic_large module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


class CallableStrategy(Strategy):
    """Strategy wrapper over a simple callable(data) -> Any."""

    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self._fn = fn

    def execute(self, data: Any) -> Any:
        return self._fn(data)


def _get_callable(mod: Any, name: str) -> Callable[[Any], Any]:
    fn = getattr(mod, name, None)
    if not callable(fn):  # pragma: no cover - defensive
        raise AttributeError(f"Missing callable: {name}")
    return cast(Callable[[Any], Any], fn)


# --- Strategy Registry (optional, for extensibility) ---
_STRATEGY_FACTORIES: Dict[str, Callable[[], Strategy]] = {}


def register_strategy_factory(mode: str, factory: Callable[[], Strategy]) -> None:
    _STRATEGY_FACTORIES[mode] = factory


def _register_builtin_modes() -> None:
    def _factory_A() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_001"))

    def _factory_B() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_010"))

    def _factory_C() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_020"))

    def _factory_D() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_030"))

    def _factory_E() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_040"))

    def _factory_F() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_050"))

    def _factory_G() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_017"))

    def _factory_default() -> Strategy:
        mod = _load_non_pythonic_module()
        return CallableStrategy(_get_callable(mod, "repeated_block_025"))

    register_strategy_factory("A", _factory_A)
    register_strategy_factory("B", _factory_B)
    register_strategy_factory("C", _factory_C)
    register_strategy_factory("D", _factory_D)
    register_strategy_factory("E", _factory_E)
    register_strategy_factory("F", _factory_F)
    register_strategy_factory("G", _factory_G)
    register_strategy_factory("default", _factory_default)


_register_builtin_modes()


def create_strategy_for_mode(mode: str) -> Strategy:
    """Factory returning a Strategy matching the original giant_switch mapping.

    Mapping mirrors examples/non_pythonic_large.giant_switch:
    - A -> repeated_block_001
    - B -> repeated_block_010
    - C -> repeated_block_020
    - D -> repeated_block_030
    - E -> repeated_block_040
    - F -> repeated_block_050
    - G -> repeated_block_017
    - default -> repeated_block_025
    """
    # Prefer registry if present; fallback to static mapping for safety.
    factory = _STRATEGY_FACTORIES.get(mode) or _STRATEGY_FACTORIES.get("default")
    if factory is not None:
        return factory()

    mod = _load_non_pythonic_module()

    mapping: Dict[str, Callable[[Any], Any]] = {
        "A": _get_callable(mod, "repeated_block_001"),
        "B": _get_callable(mod, "repeated_block_010"),
        "C": _get_callable(mod, "repeated_block_020"),
        "D": _get_callable(mod, "repeated_block_030"),
        "E": _get_callable(mod, "repeated_block_040"),
        "F": _get_callable(mod, "repeated_block_050"),
        "G": _get_callable(mod, "repeated_block_017"),
    }
    fn = mapping.get(mode, _get_callable(mod, "repeated_block_025"))
    return CallableStrategy(fn)


def giant_switch_via_strategy(value: Any, mode: str) -> Any:
    """Replicate non_pythonic_large.giant_switch behavior using Strategy.

    This is a drop-in alternative that leaves the original code untouched.
    """
    ctx = Context(create_strategy_for_mode(mode))
    return ctx.process(value)


def get_context_for_mode(mode: str) -> Context:
    """Build a Context using a registered Strategy (or fallback mapping)."""
    return Context(create_strategy_for_mode(mode))
