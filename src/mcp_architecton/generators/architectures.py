from __future__ import annotations

from typing import Callable, Optional

from ..catalog import CatalogEntry

Generator = Callable[[str, Optional[CatalogEntry]], str | None]


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


ARCH_GENERATORS: dict[str, Generator] = {
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
