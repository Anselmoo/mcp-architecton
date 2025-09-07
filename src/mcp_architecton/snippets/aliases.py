from __future__ import annotations

# Single source of truth for alias mappings used by generators/services.
# Keys are normalized lowercase display names; values are canonical generator keys.

# Architectures (styles + helper building blocks)
ARCHITECTURE_ALIASES: dict[str, str] = {
    # Styles
    "hexagonal architecture": "hexagonal",
    "layered architecture": "layered",
    "clean architecture": "clean",
    "3-tier architecture": "three_tier",
    "three-tier architecture": "three_tier",
    "3 tier": "three_tier",
    "3-tier": "three_tier",
    "three tier": "three_tier",
    "model-view-controller (mvc)": "mvc",
    "mvc": "mvc",
    # Helpers
    "service layer": "service_layer",
    "unit of work": "unit_of_work",
    "message bus": "message_bus",
    "domain events": "domain_events",
    "repository": "repository",
    "cqrs": "cqrs",
}

# Patterns (include common spellings/synonyms)
PATTERN_ALIASES: dict[str, str] = {
    "abstract factory": "abstract_factory",
    "factory method": "factory_method",
    "factory-method": "factory_method",
    "adapter": "adapter",
    "bridge": "bridge",
    "builder": "builder",
    "chain of responsibility": "chain_of_responsibility",
    "composite": "composite",
    "decorator": "decorator",
    "facade": "facade",
    "facade function": "facade_function",
    "flyweight": "flyweight",
    "iterator": "iterator",
    "mediator": "mediator",
    "memento": "memento",
    "observer": "observer",
    "prototype": "prototype",
    "proxy": "proxy",
    "singleton": "singleton",
    "state": "state",
    "strategy": "strategy",
    "template method": "template_method",
    "visitor": "visitor",
    # misc patterns included in repo
    "blackboard": "blackboard",
    "borg": "borg",
    "catalog": "catalog",
    "chaining method": "chaining_method",
    "command": "command",
    "graph search": "graph_search",
    "hsm": "hsm",
    "lazy evaluation": "lazy_evaluation",
    "pool": "pool",
    "publish-subscribe": "publish_subscribe",
    "publish subscribe": "publish_subscribe",
    "pubsub": "publish_subscribe",
    "registry": "registry",
    "specification": "specification",
}

# Refactoring techniques (light set; can expand as catalog grows)
REFACTOR_ALIASES: dict[str, str] = {
    "strangler fig": "strangler_fig",
    "branch by abstraction": "branch_by_abstraction",
    "extract method": "extract_method",
    "inline variable": "inline_variable",
    "introduce parameter object": "introduce_parameter_object",
    "replace conditional with polymorphism": "replace_conditional_with_polymorphism",
}

# Backward-compatible combined map
NAME_ALIASES: dict[str, str] = {
    **ARCHITECTURE_ALIASES,
    **PATTERN_ALIASES,
    **REFACTOR_ALIASES,
}


def _norm(name: str | None) -> str:
    return (name or "").strip().lower()


def canonicalize_architecture_name(name: str | None) -> str:
    return ARCHITECTURE_ALIASES.get(_norm(name), _norm(name))


def canonicalize_pattern_name(name: str | None) -> str:
    return PATTERN_ALIASES.get(_norm(name), _norm(name))


def canonicalize_refactor_name(name: str | None) -> str:
    return REFACTOR_ALIASES.get(_norm(name), _norm(name))


def canonicalize_name(name: str | None) -> str:
    return NAME_ALIASES.get(_norm(name), _norm(name))


__all__ = [
    "ARCHITECTURE_ALIASES",
    "NAME_ALIASES",
    "PATTERN_ALIASES",
    "REFACTOR_ALIASES",
    "canonicalize_architecture_name",
    "canonicalize_name",
    "canonicalize_pattern_name",
    "canonicalize_refactor_name",
]
