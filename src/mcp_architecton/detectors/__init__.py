from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Architecture detectors
from .architecture.clean import detect as detect_arch_clean
from .architecture.cqrs import detect as detect_arch_cqrs
from .architecture.domain_events import detect as detect_arch_domain_events
from .architecture.front_controller import detect as detect_front_controller
from .architecture.hexagonal import detect as detect_arch_hexagonal
from .architecture.layered import detect as detect_arch_layered
from .architecture.message_bus import detect as detect_arch_message_bus
from .architecture.mvc import detect as detect_mvc
from .architecture.repository import detect as detect_arch_repository
from .architecture.service_layer import detect as detect_arch_service_layer
from .architecture.three_tier import detect as detect_arch_three_tier
from .architecture.unit_of_work import detect as detect_arch_uow

# Pattern detectors
from .patterns.abstract_factory import detect as detect_abstract_factory
from .patterns.adapter import detect as detect_adapter
from .patterns.blackboard import detect as detect_blackboard
from .patterns.borg import detect as detect_borg
from .patterns.bridge import detect as detect_bridge
from .patterns.builder import detect as detect_builder
from .patterns.catalog import detect as detect_catalog
from .patterns.chain_of_responsibility import detect as detect_chain_of_responsibility
from .patterns.chaining_method import detect as detect_chaining_method
from .patterns.command import detect as detect_command
from .patterns.composite import detect as detect_composite
from .patterns.decorator import detect as detect_decorator
from .patterns.delegation_pattern import detect as detect_delegation_pattern
from .patterns.dependency_injection import detect as detect_dependency_injection
from .patterns.facade import detect as detect_facade
from .patterns.factory import detect as detect_factory
from .patterns.factory_method import detect as detect_factory_method
from .patterns.flyweight import detect as detect_flyweight
from .patterns.graph_search import detect as detect_graph_search
from .patterns.hsm import detect as detect_hsm
from .patterns.iterator import detect as detect_iterator
from .patterns.lazy_evaluation import detect as detect_lazy_evaluation
from .patterns.mediator import detect as detect_mediator
from .patterns.memento import detect as detect_memento
from .patterns.observer import detect as detect_observer
from .patterns.pool import detect as detect_pool
from .patterns.prototype import detect as detect_prototype
from .patterns.proxy import detect as detect_proxy
from .patterns.publish_subscribe import detect as detect_publish_subscribe
from .patterns.registry import detect as detect_registry
from .patterns.singleton import detect as detect_singleton
from .patterns.specification import detect as detect_specification
from .patterns.state import detect as detect_state
from .patterns.strategy import detect as detect_strategy
from .patterns.template_method import detect as detect_template_method
from .patterns.visitor import detect as detect_visitor

Detector = Callable[[Any, str], list[dict[str, Any]]]

registry: dict[str, Detector] = {
    "Singleton": detect_singleton,
    "Strategy": detect_strategy,
    "Observer": detect_observer,
    "Factory": detect_factory,
    "Factory Method": detect_factory_method,
    "Abstract Factory": detect_abstract_factory,
    "Builder": detect_builder,
    "Prototype": detect_prototype,
    "Borg": detect_borg,
    "Pool": detect_pool,
    "Lazy Evaluation": detect_lazy_evaluation,
    "Bridge": detect_bridge,
    "Composite": detect_composite,
    "Proxy": detect_proxy,
    "Adapter": detect_adapter,
    "Flyweight": detect_flyweight,
    "Front Controller": detect_front_controller,
    "Model-View-Controller (MVC)": detect_mvc,
    "Decorator": detect_decorator,
    "Command": detect_command,
    "Catalog": detect_catalog,
    "Chaining Method": detect_chaining_method,
    "Chain of Responsibility": detect_chain_of_responsibility,
    "Iterator": detect_iterator,
    "Iterator (Alt)": detect_iterator,  # alias for alt implementation
    "Mediator": detect_mediator,
    "Memento": detect_memento,
    "Facade": detect_facade,
    "Publish-Subscribe": detect_publish_subscribe,
    "Registry": detect_registry,
    "Specification": detect_specification,
    "State": detect_state,
    "Template Method": detect_template_method,
    "Template": detect_template_method,  # alias to match reference naming
    "Visitor": detect_visitor,
    "Dependency Injection": detect_dependency_injection,
    "Delegation Pattern": detect_delegation_pattern,
    "Blackboard": detect_blackboard,
    "Graph Search": detect_graph_search,
    "Hierarchical State Machine": detect_hsm,
    "Layered Architecture": detect_arch_layered,
    "Hexagonal Architecture": detect_arch_hexagonal,
    "Clean Architecture": detect_arch_clean,
    "3-Tier Architecture": detect_arch_three_tier,
    "Repository": detect_arch_repository,
    "Service Layer": detect_arch_service_layer,
    "Unit of Work": detect_arch_uow,
    "Message Bus": detect_arch_message_bus,
    "Domain Events": detect_arch_domain_events,
    "CQRS": detect_arch_cqrs,
}
