from __future__ import annotations

# Default, concise refactor prompts for patterns and architectures.

PATTERN_REFACTOR_ADVICE_DEFAULTS: dict[str, str] = {
    "Abstract Factory": "Group related factories behind an interface to create families of objects.",
    "Adapter": "Wrap incompatible interfaces with an adapter class; convert expected methods and types.",
    "Blackboard": "Use a shared board with knowledge sources writing/reading until goal achieved.",
    "Borg": "Share state via a class-level __dict__ shared by instances; prefer explicit DI when possible.",
    "Bridge": "Split abstraction from implementation; define interface and inject concrete implementor.",
    "Builder": "Extract construction steps to a builder; assemble complex objects step by step.",
    "Catalog": "Centralize metadata/constructors for product types; validate registrations.",
    "Chain of Responsibility": "Create handler objects with next links; pass requests until one handles it.",
    "Chaining Method": "Return self and keep methods side-effect free to enable fluent chaining.",
    "Command": "Encapsulate actions into command objects with execute/undo; queue or log them.",
    "Composite": "Model part-whole trees with a common interface; composites forward to children.",
    "Decorator": "Wrap an object to add behavior without subclassing; honor the same interface.",
    "Delegation Pattern": "Forward work to a helper object instead of inheritance; pass through APIs.",
    "Dependency Injection": "Inject dependencies via constructor or setters; avoid globals and locators.",
    "Facade": "Provide a simple API over subsystems; keep orchestration in the facade.",
    "Factory": "Centralize object creation in a function/factory; hide concrete classes from callers.",
    "Factory Method": "Defer object creation to overridable factory methods in subclasses.",
    "Flyweight": "Share immutable state across many instances; externalize varying state.",
    "Graph Search": "Isolate traversal strategy; separate graph abstraction from search algorithm.",
    "Hierarchical State Machine (HSM)": (
        "Model nested states with explicit enter/exit and parent/child transitions; "
        "consider State objects for each level."
    ),
    "Iterator": "Expose a simple iterator to traverse collections without exposing internals.",
    "Lazy Evaluation": "Defer expensive work until first use; cache results; invalidate when inputs change.",
    "Mediator": "Extract complex object interactions to a mediator; colleagues talk via mediator only.",
    "Memento": "Capture state snapshots in value objects; provide restore points without exposing internals.",
    "Observer": "Let observers subscribe to subjects; notify on state changes; keep observers decoupled.",
    "Pool": "Maintain a pool of reusable objects; hand out, validate, and return to the pool.",
    "Prototype": "Clone prototypes instead of creating from scratch; customize after copy.",
    "Proxy": "Interpose a proxy to control access, add caching, or lazy load the real subject.",
    "Publish-Subscribe": "Publish events to a bus; subscribers handle asynchronously; avoid direct coupling.",
    "Registry": "Keep a typed registry for lookups; avoid global mutable dicts; provide clear lifecycle.",
    "Singleton": (
        "Control instance via __new__/class attr; provide get_instance; "
        "keep it stateless where possible."
    ),
    "Specification": "Encapsulate predicates; combine with and/or/not; keep domain rules testable.",
    "State": "Represent states as classes; delegate behavior to current state; transition explicitly.",
    "Strategy": "Extract algorithms behind a common interface; inject the chosen strategy at runtime.",
    "Template Method": "Put the algorithm skeleton in a base class; call hook steps implemented by subclasses.",
    "Visitor": "Move cross-cutting operations to a visitor; add accept() to elements; double-dispatch.",
}

ARCHITECTURE_REFACTOR_ADVICE_DEFAULTS: dict[str, str] = {
    "Clean Architecture": (
        "Organize concentric layers; entities and use-cases core; frameworks at the outer rings."
    ),
    "CQRS": "Split write commands from read queries; consider separate models and stores for scale.",
    "Domain Events": "Model domain events; publish after state changes; handle asynchronously where feasible.",
    "Front Controller": "Route requests through a single controller; apply cross-cutting concerns centrally.",
    "Hexagonal Architecture": (
        "Introduce ports (interfaces) and adapters; push IO to edges; "
        "drive the domain via use cases."
    ),
    "Layered Architecture": (
        "Separate presentation, application, domain, and infrastructure; "
        "depend inward; define clear boundaries."
    ),
    "Message Bus": (
        "Send commands/events over a bus; handlers are decoupled; "
        "support retries and dead-letter queues."
    ),
    "MVC": "Split Model, View, Controller; keep controllers thin; avoid business logic in views.",
    "Repository": "Abstract data persistence behind repositories; return aggregates; keep domain pure.",
    "Service Layer": (
        "Expose application services orchestrating use-cases; "
        "keep domain logic in entities/value objects."
    ),
    "Three-Tier Architecture": (
        "Separate presentation, logic, and data tiers; enforce strict dependencies and contracts."
    ),
    "Unit of Work": "Track changes to aggregates; commit as a single transaction; provide rollback.",
}
