"""Built-in snippet code generators.

Each generator is a function (name, catalog_entry?) -> code | None
registered via api.register_generator. Generators are simple and avoid
external dependencies.
"""

from __future__ import annotations

from typing import Callable, Optional

from .catalog import CatalogEntry

Generator = Callable[[str, Optional[CatalogEntry]], str | None]


def gen_strategy(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        '''
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
'''
    ).strip()


def gen_singleton(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):  # pragma: no cover - scaffold
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
    ).strip()


def gen_facade(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        '''
class _SubsystemA:
    def op_a(self) -> str:
        return "A"


class _SubsystemB:
    def op_b(self) -> str:
        return "B"


class Facade:
    """Simplified interface orchestrating multiple subsystems."""

    def __init__(self) -> None:
        self._a = _SubsystemA()
        self._b = _SubsystemB()

    def do(self) -> str:
        # Minimal orchestration example
        return f"{self._a.op_a()}-{self._b.op_b()}"
'''
    ).strip()


def gen_facade_function(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        '''
def facade_function(*args, **kwargs):  # pragma: no cover - scaffold
    """A thin facade function orchestrating multiple collaborators."""
    # TODO: call into subsystems and aggregate results
    raise NotImplementedError
'''
    ).strip()


def gen_observer(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations

from typing import Callable, Dict, list


class Observable:
    def __init__(self) -> None:
        self._subs: Dict[str, list[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subs.setdefault(event, []).append(handler)

    def notify(self, event: str, payload) -> None:  # pragma: no cover - scaffold
        for h in self._subs.get(event, []):
            h(payload)
"""
    ).strip()


def gen_command(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Command:  # pragma: no cover - scaffold
    def execute(self) -> None:
        raise NotImplementedError


class Invoker:
    def __init__(self) -> None:
        self._queue: list[Command] = []

    def add(self, cmd: Command) -> None:
        self._queue.append(cmd)

    def run(self) -> None:
        for c in self._queue:
            c.execute()
"""
    ).strip()


def gen_blackboard(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Blackboard:
    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        self._data[key] = value

    def get(self, key: str) -> object | None:
        return self._data.get(key)
"""
    ).strip()


def gen_borg(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        '''
class Borg:
    """Borg pattern: instances share state via shared __dict__."""

    _shared_state: dict[str, object] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class SingletonBorg(Borg):
    """A Borg variant providing a convenient default state."""

    def __init__(self, state: str | None = None) -> None:
        super().__init__()
        self.state = state or getattr(self, "state", "default")

    def __str__(self) -> str:  # pragma: no cover - scaffold
        return str(getattr(self, "state", "default"))
'''
    ).strip()


def gen_catalog(_: str, __: Optional[CatalogEntry]) -> str | None:
    entry = __ or {}
    desc = str(entry.get("intent") or entry.get("description") or "Simple in-memory catalog.")
    refs = entry.get("refs", []) or []
    refs_comment = ("\n# References:\n" + "\n".join(f"# - {r}" for r in refs)) if refs else ""
    return (
        '"""' + desc + refs_comment + '"""\n\n'
        "class Catalog:\n"
        "    def __init__(self) -> None:\n"
        "        self._items: dict[str, object] = {}\n\n"
        "    def add(self, key: str, item: object) -> None:\n"
        '        """Register an item under a key."""\n'
        "        self._items[key] = item\n\n"
        "    def get(self, key: str) -> object | None:\n"
        '        """Retrieve an item by key, or None if missing."""\n'
        "        return self._items.get(key)\n\n"
        "    def remove(self, key: str) -> None:\n"
        '        """Remove an item if it exists."""\n'
        "        self._items.pop(key, None)\n\n"
        "    def keys(self) -> list[str]:\n"
        "        return list(self._items.keys())\n"
    ).strip()


def gen_chaining_method(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Chainable:
    def step(self):
        # do work
        return self
"""
    ).strip()


def gen_delegation_pattern(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Real:
    def op(self) -> str: return "real"


class Delegator:
    def __init__(self, real: Real): self._real = real
    def op(self) -> str: return self._real.op()
"""
    ).strip()


def gen_dependency_injection(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Container:
    def __init__(self): self._deps = {}
    def register(self, key: str, dep): self._deps[key] = dep
    def resolve(self, key: str): return self._deps[key]
"""
    ).strip()


def gen_factory(_: str, __: Optional[CatalogEntry]) -> str | None:
    entry = __ or {}
    desc = str(
        entry.get("intent")
        or entry.get("description")
        or "Factory interface and example implementation."
    )
    refs = entry.get("refs", []) or []
    refs_comment = ("\n# References:\n" + "\n".join(f"# - {r}" for r in refs)) if refs else ""
    return (
        '"""' + desc + refs_comment + '"""\n\n'
        "from __future__ import annotations\n"
        "from typing import Protocol\n\n\n"
        "class Product(Protocol):\n"
        "    def use(self) -> str: ...\n\n\n"
        "class Factory:  # pragma: no cover - scaffold\n"
        "    def create(self, kind: str) -> Product:\n"
        '        """Create a product by kind."""\n'
        "        raise NotImplementedError\n\n\n"
        "class ConcreteA:\n"
        "    def use(self) -> str:\n"
        '        return "A"\n\n\n'
        "class ConcreteB:\n"
        "    def use(self) -> str:\n"
        '        return "B"\n\n\n'
        "class SimpleFactory(Factory):\n"
        "    def create(self, kind: str) -> Product:\n"
        '        if kind == "A":\n'
        "            return ConcreteA()\n"
        '        if kind == "B":\n'
        "            return ConcreteB()\n"
        '        raise ValueError(f"unknown kind: {kind}")\n'
    ).strip()


def gen_graph_search(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
def bfs(start, neighbors):  # pragma: no cover - scaffold
    from collections import deque
    q = deque([start])
    seen = {start}
    while q:
        n = q.popleft()
        yield n
        for m in neighbors(n):
            if m not in seen:
                seen.add(m)
                q.append(m)
"""
    ).strip()


def gen_hsm(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations

from abc import ABC, abstractmethod


class HSMState(ABC):
    @abstractmethod
    def on_event(self, ctx: "HSM", event: str) -> "HSMState":  # pragma: no cover - scaffold
        return self


class HSM:
    def __init__(self, initial: HSMState) -> None:
        self.state = initial

    def dispatch(self, event: str) -> None:  # pragma: no cover - scaffold
        self.state = self.state.on_event(self, event)
"""
    ).strip()


def gen_lazy_evaluation(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Lazy:
    def __init__(self, fn): self._fn, self._val, self._done = fn, None, False
    def value(self):
        if not self._done:
            self._val, self._done = self._fn(), True
        return self._val
"""
    ).strip()


def gen_memento(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Memento:
    def __init__(self, state): self.state = state
"""
    ).strip()


def gen_pool(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Pool:
    def __init__(self): self._objs = []
    def acquire(self): return self._objs.pop() if self._objs else object()
    def release(self, obj): self._objs.append(obj)
"""
    ).strip()


def gen_registry(_: str, __: Optional[CatalogEntry]) -> str | None:
    entry = __ or {}
    desc = str(
        entry.get("intent")
        or entry.get("description")
        or "Simple key->value registry with safe access."
    )
    refs = entry.get("refs", []) or []
    refs_comment = ("\n# References:\n" + "\n".join(f"# - {r}" for r in refs)) if refs else ""
    return (
        '"""' + desc + refs_comment + '"""\n\n'
        "from __future__ import annotations\n"
        "from typing import Generic, TypeVar\n\n"
        'K = TypeVar("K")\n'
        'V = TypeVar("V")\n\n\n'
        "class Registry(Generic[K, V]):\n"
        "    def __init__(self) -> None:\n"
        "        self._reg: dict[K, V] = {}\n\n"
        "    def register(self, key: K, val: V) -> None:\n"
        "        self._reg[key] = val\n\n"
        "    def get(self, key: K) -> V | None:\n"
        "        return self._reg.get(key)\n\n"
        "    def unregister(self, key: K) -> None:\n"
        "        self._reg.pop(key, None)\n\n"
        "    def keys(self) -> list[K]:\n"
        "        return list(self._reg.keys())\n"
    ).strip()


def gen_specification(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Specification:
    def is_satisfied_by(self, candidate) -> bool:  # pragma: no cover - scaffold
        raise NotImplementedError
"""
    ).strip()


def gen_decorator(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from typing import Protocol, runtime_checkable


@runtime_checkable
class Component(Protocol):
    def op(self) -> str: ...


class Concrete(Component):
    def op(self) -> str:
        return "base"


class Decorator(Component):
    def __init__(self, inner: Component) -> None:
        self._inner = inner

    def op(self) -> str:
        return self._inner.op()
"""
    ).strip()


def gen_adapter(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Target:
    def request(self) -> str: return "target"


class Adaptee:
    def specific_request(self) -> str: return "adaptee"


class Adapter(Target):
    def __init__(self, adaptee: Adaptee) -> None:
        self._adaptee = adaptee

    def request(self) -> str:
        return self._adaptee.specific_request()
"""
    ).strip()


def gen_bridge(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from abc import ABC, abstractmethod


class Implementor(ABC):
    @abstractmethod
    def op_impl(self) -> str: ...


class ConcreteImplA(Implementor):
    def op_impl(self) -> str:
        return "A"


class Abstraction:
    def __init__(self, impl: Implementor) -> None:
        self._impl = impl

    def op(self) -> str:
        return f"Abstraction->" + self._impl.op_impl()
"""
    ).strip()


def gen_builder(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Builder:
    def reset(self) -> None: ...
    def step(self) -> None: ...
    def build(self): ...
"""
    ).strip()


def gen_composite(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from typing import Iterable


class Component:
    def op(self) -> str: return ""


class Leaf(Component):
    def op(self) -> str: return "leaf"


class Composite(Component):
    def __init__(self, children: Iterable[Component]):
        self.children = list(children)

    def op(self) -> str:
        return "+".join(c.op() for c in self.children)
"""
    ).strip()


def gen_abstract_factory(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from abc import ABC, abstractmethod


class AbstractFactory(ABC):
    @abstractmethod
    def create(self): ...
"""
    ).strip()


def gen_flyweight(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
# Module-level cache for flyweight instances
_CACHE: dict[str, object] = {}


def get_flyweight(key: str) -> object:  # pragma: no cover - scaffold
    # Return cached instance or create and store a new one.
    if key in _CACHE:
        return _CACHE[key]
    obj = object()
    _CACHE[key] = obj
    return obj
"""
    ).strip()


def gen_iterator(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class IterableCollection:
    def __iter__(self):  # pragma: no cover - scaffold
        yield from []
"""
    ).strip()


def gen_mediator(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations


class Mediator:
    def __init__(self) -> None:
        self.a: ComponentA | None = None
        self.b: ComponentB | None = None

    def notify(self, sender: object, event: str) -> None:  # pragma: no cover - scaffold
        # Simple orchestration example
        if event == "A_done" and self.b is not None:
            self.b.react()


class ComponentA:
    def __init__(self, mediator: Mediator) -> None:
        self.mediator = mediator
        self.mediator.a = self

    def act(self) -> None:
        # do work ... then notify mediator
        self.mediator.notify(self, "A_done")


class ComponentB:
    def __init__(self, mediator: Mediator) -> None:
        self.mediator = mediator
        self.mediator.b = self

    def react(self) -> None:  # pragma: no cover - scaffold
        # respond to A
        pass
"""
    ).strip()


def gen_factory_method(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class ProductA: ...
class ProductB: ...


def create_product(kind: str):  # pragma: no cover - scaffold
    if kind == "A":
        return ProductA()
    elif kind == "B":
        return ProductB()
    raise ValueError(f"Unknown kind: {kind}")
"""
    ).strip()


def gen_prototype(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
import copy


class Prototype:
    def clone(self):
        return copy.deepcopy(self)
"""
    ).strip()


def gen_proxy(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Subject:
    def op(self) -> str: return "real"


class Proxy(Subject):
    def __init__(self, real: Subject) -> None:
        self._real = real

    def op(self) -> str:
        # access control / caching cross-cutting
        return self._real.op()
"""
    ).strip()


def gen_state(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations

from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def handle(self, ctx: Context) -> None:  # pragma: no cover - scaffold
        ...


class Context:
    def __init__(self, state: State) -> None:
        self.state = state

    def request(self) -> None:  # pragma: no cover - scaffold
        self.state.handle(self)


class ConcreteStateA(State):
    def handle(self, ctx: Context) -> None:
        # Transition example A -> B
        ctx.state = ConcreteStateB()


class ConcreteStateB(State):
    def handle(self, ctx: Context) -> None:
        # Transition example B -> A
        ctx.state = ConcreteStateA()
"""
    ).strip()


def gen_template_method(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from abc import ABC, abstractmethod


class AbstractWorkflow(ABC):
    def run(self) -> None:
        self.step_one()
        self.step_two()

    @abstractmethod
    def step_one(self) -> None: ...

    @abstractmethod
    def step_two(self) -> None: ...
"""
    ).strip()


def gen_chain_of_responsibility(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Handler:
    def __init__(self, nxt=None): self._nxt = nxt
    def handle(self, req):
        if self._nxt: self._nxt.handle(req)
"""
    ).strip()


def gen_visitor(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations

from abc import ABC, abstractmethod


class Visitor(ABC):
    @abstractmethod
    def visit_element(self, el: Element) -> None:  # pragma: no cover - scaffold
        ...


class Element(ABC):
    @abstractmethod
    def accept(self, v: Visitor) -> None: ...


class ConcreteElement(Element):
    def accept(self, v: Visitor) -> None:
        v.visit_element(self)
"""
    ).strip()


def gen_front_controller(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class FrontController:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def handle(self, request):  # pragma: no cover - scaffold
        # preprocess and dispatch
        return self.dispatcher.dispatch(request)
"""
    ).strip()


def gen_mvc(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Model:
    def __init__(self): self.state = {}


class View:
    def render(self, model: Model) -> str: return str(model.state)


class Controller:
    def __init__(self, model: Model, view: View):
        self.model, self.view = model, view

    def handle(self, request):  # pragma: no cover - scaffold
        # mutate model and return rendered view
        return self.view.render(self.model)
"""
    ).strip()


def gen_hexagonal(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Port:
    def op(self, *args, **kwargs): ...


class Adapter(Port):
    def __init__(self, service): self.service = service
    def op(self, *args, **kwargs): return self.service(*args, **kwargs)


class ApplicationService:
    def __init__(self, port: Port): self.port = port
    def run(self, *args, **kwargs): return self.port.op(*args, **kwargs)
"""
    ).strip()


def gen_layered(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class PresentationLayer: ...
class ApplicationLayer: ...
class DomainLayer: ...
class InfrastructureLayer: ...
"""
    ).strip()


def gen_clean(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Entities: ...
class UseCases: ...
class InterfaceAdapters: ...
class FrameworksDrivers: ...
"""
    ).strip()


def gen_three_tier(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class PresentationTier: ...
class LogicTier: ...
class DataTier: ...
"""
    ).strip()


def gen_publish_subscribe(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from collections import defaultdict
from typing import Callable, Dict, list


class PubSub:
    def __init__(self) -> None:
        self._subs: Dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, message) -> None:  # pragma: no cover - scaffold
        for h in self._subs.get(topic, []):
            h(message)
"""
    ).strip()


def gen_repository(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def get(self, id_: str) -> Optional[T]:  # pragma: no cover - scaffold
        raise NotImplementedError

    @abstractmethod
    def save(self, id_: str, entity: T) -> None:  # pragma: no cover - scaffold
        raise NotImplementedError


class InMemoryRepository(Repository[T]):
    def __init__(self) -> None:
        self._store: Dict[str, T] = {}

    def get(self, id_: str) -> Optional[T]:
        return self._store.get(id_)

    def save(self, id_: str, entity: T) -> None:
        self._store[id_] = entity
"""
    ).strip()


def gen_uow(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        '''
class UnitOfWork:
    """Transaction boundary and resource lifetime manager."""

    def __enter__(self):  # pragma: no cover - scaffold
        # begin transaction
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - scaffold
        if exc:
            # rollback
            return False
        # commit
        return False
'''
    ).strip()


def gen_service_layer(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class ServiceLayer:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    def perform_action(self, payload):  # pragma: no cover - scaffold
        with self.uow:
            # domain logic calling repo
            entity = self.repo.get(payload.get("id"))
            # mutate entity or create new
            if entity is not None:
                self.repo.save(entity)
"""
    ).strip()


def gen_message_bus(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from collections import defaultdict
from typing import Callable, Dict, list


class MessageBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._handlers[topic].append(handler)

    def publish(self, topic: str, message) -> None:  # pragma: no cover - scaffold
        for h in self._handlers.get(topic, []):
            h(message)
"""
    ).strip()


def gen_domain_events(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
from dataclasses import dataclass
from typing import Callable, DefaultDict, Dict, list, Type
from collections import defaultdict


class DomainEvent:  # pragma: no cover - scaffold
    pass


class EventDispatcher:
    def __init__(self) -> None:
        self._subs: DefaultDict[Type[DomainEvent], list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        self._subs[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        for h in self._subs.get(type(event), []):
            h(event)
"""
    ).strip()


def gen_cqrs(_: str, __: Optional[CatalogEntry]) -> str | None:
    return (
        """
class Command:  # pragma: no cover - scaffold
    pass


class Query:  # pragma: no cover - scaffold
    pass


class CommandHandler:
    def handle(self, cmd: Command):  # pragma: no cover - scaffold
        raise NotImplementedError


class QueryHandler:
    def handle(self, qry: Query):  # pragma: no cover - scaffold
        raise NotImplementedError
"""
    ).strip()


# Registry of built-in generators keyed by canonical snippet key
BUILTINS: dict[str, Generator] = {
    # Patterns (alphabetical)
    "abstract_factory": gen_abstract_factory,
    "adapter": gen_adapter,
    "blackboard": gen_blackboard,
    "borg": gen_borg,
    "bridge": gen_bridge,
    "builder": gen_builder,
    "catalog": gen_catalog,
    "chain_of_responsibility": gen_chain_of_responsibility,
    "chaining_method": gen_chaining_method,
    "command": gen_command,
    "composite": gen_composite,
    "decorator": gen_decorator,
    "delegation_pattern": gen_delegation_pattern,
    "dependency_injection": gen_dependency_injection,
    "facade": gen_facade,
    "facade_function": gen_facade_function,
    "factory": gen_factory,
    "factory_method": gen_factory_method,
    "flyweight": gen_flyweight,
    "front_controller": gen_front_controller,
    "graph_search": gen_graph_search,
    "hsm": gen_hsm,
    "iterator": gen_iterator,
    "lazy_evaluation": gen_lazy_evaluation,
    "mediator": gen_mediator,
    "memento": gen_memento,
    "observer": gen_observer,
    "pool": gen_pool,
    "prototype": gen_prototype,
    "proxy": gen_proxy,
    "publish_subscribe": gen_publish_subscribe,
    "registry": gen_registry,
    "singleton": gen_singleton,
    "specification": gen_specification,
    "state": gen_state,
    "strategy": gen_strategy,
    "template_method": gen_template_method,
    "visitor": gen_visitor,
    # Architecture helpers (alphabetical)
    "cqrs": gen_cqrs,
    "domain_events": gen_domain_events,
    "message_bus": gen_message_bus,
    "repository": gen_repository,
    "service_layer": gen_service_layer,
    "unit_of_work": gen_uow,
    # Architecture styles (alphabetical)
    "clean": gen_clean,
    "hexagonal": gen_hexagonal,
    "layered": gen_layered,
    "mvc": gen_mvc,
    "three_tier": gen_three_tier,
}

__all__ = ["Generator", "BUILTINS"]
