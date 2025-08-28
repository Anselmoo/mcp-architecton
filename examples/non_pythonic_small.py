"""
Anti-pythonic small example (~50 LOC).

Intentionally includes:
- God Object smell
- Singleton misuse
- Facade-like function
- Mutable default args
- Globals, deep nesting, magic numbers, duplicate logic

These patterns are consistent across medium/large examples.
"""

# ruff: noqa

STATE = {"counter": 0, "errors": []}  # global mutable state


class BadSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):  # naive singleton
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = {"retries": 3, "timeout": 1}


class GodManager:  # God Object doing too much
    def __init__(self):
        self.single = BadSingleton()

    def compute(self, items=None, cache={}):  # mutable default arg
        if items is None:
            items = []
        total = 0
        for i in range(5):  # deep-ish nesting and magic numbers
            if i % 2 == 0:
                if i in cache:
                    total += cache[i]
                else:
                    cache[i] = i * 2
                    total += cache[i]
            else:
                try:
                    total += i // 1
                except Exception as e:  # pragma: no cover
                    STATE["errors"].append(e)
        STATE["counter"] += total
        return total


def facade_process(text, n):  # facade-like orchestration function
    mgr = GodManager()
    a = mgr.compute([1, 2, 3])
    b = mgr.compute([3, 2, 1])
    if n == 1:
        return text.upper() + str(a)
    elif n == 2:
        return text.lower() + str(b)
    elif n == 3:
        return text[::-1] + str(a + b)
    else:
        return f"{text}:{a}:{b}:{STATE['counter']}"


__all__ = [
    "BadSingleton",
    "GodManager",
    "facade_process",
    "STATE",
]
