from __future__ import annotations

from typing import Callable, Optional

try:  # pragma: no cover - optional import for type
    import libcst as cst  # type: ignore
    from libcst import parse_module  # type: ignore
except Exception:  # pragma: no cover
    cst = None  # type: ignore
    parse_module = None  # type: ignore

Strategy = Callable[[str], Optional[str]]

_STRATEGIES: dict[str, Strategy] = {}


def _canon(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().lower()


def register_strategy(name: str, fn: Strategy) -> None:
    _STRATEGIES[_canon(name)] = fn


def _append_snippet_marker(text: str, key: str, body: str) -> str:
    key_c = _canon(key)
    marker_start = f"# --- mcp-architecton strategy: {key_c} ---"
    marker_end = "# --- end strategy ---"
    if marker_start in text:
        return text
    prefix = (text.rstrip() + "\n\n") if text else ""
    return f"{prefix}{marker_start}\n{body}\n{marker_end}\n"


def _safe_libcst_insert_class(source: str, class_src: str) -> Optional[str]:
    if not cst or not parse_module:  # pragma: no cover - environment without libcst
        return None
    try:
        # parse to ensure input is syntactically valid
        parse_module(source)
        # naive append at end as a SimpleStatementLine for safety
        new_src = source.rstrip() + "\n\n" + class_src + "\n"
        # ensure it parses
        parse_module(new_src)
        return new_src
    except Exception:  # pragma: no cover - keep safe
        return None


def _safe_libcst_insert_function(source: str, func_src: str) -> Optional[str]:
    if not cst or not parse_module:  # pragma: no cover
        return None
    try:
        new_src = source.rstrip() + "\n\n" + func_src + "\n"
        parse_module(new_src)
        return new_src
    except Exception:  # pragma: no cover
        return None


# Built-in minimal strategies using simple scaffolds; integrate with generators later if needed.


def _singleton_strategy(src: str) -> Optional[str]:
    body = (
        "class Singleton:\n"
        "    _instance = None\n\n"
        "    def __new__(cls, *args, **kwargs):\n"
        "        if cls._instance is None:\n"
        "            cls._instance = super().__new__(cls)\n"
        "        return cls._instance\n"
    )
    appended = _append_snippet_marker(src, "singleton", body)
    return None if appended == src else appended


def _observer_strategy(src: str) -> Optional[str]:
    body = (
        "class Observable:\n"
        "    def __init__(self) -> None:\n"
        "        self._subs = {}\n\n"
        "    def subscribe(self, event, handler):\n"
        "        self._subs.setdefault(event, []).append(handler)\n\n"
        "    def notify(self, event, payload):\n"
        "        for h in self._subs.get(event, []):\n"
        "            h(payload)\n"
    )
    out = _append_snippet_marker(src, "observer", body)
    return None if out == src else out


def _facade_function_strategy(src: str) -> Optional[str]:
    body = (
        "def facade_function(*args, **kwargs):\n"
        '    """A thin facade function orchestrating multiple collaborators."""\n'
        "    raise NotImplementedError\n"
    )
    out = _append_snippet_marker(src, "facade_function", body)
    return None if out == src else out


def _strategy_strategy(src: str) -> Optional[str]:
    body = (
        "from abc import ABC, abstractmethod\n\n"
        "class Strategy(ABC):\n"
        "    @abstractmethod\n"
        "    def execute(self, data):\n"
        "        raise NotImplementedError\n\n"
        "class Context:\n"
        "    def __init__(self, strategy: Strategy):\n"
        "        self._strategy = strategy\n"
    )
    out = _append_snippet_marker(src, "strategy", body)
    return None if out == src else out


# register minimal built-ins
register_strategy("singleton", _singleton_strategy)
register_strategy("observer", _observer_strategy)
register_strategy("facade_function", _facade_function_strategy)
register_strategy("strategy", _strategy_strategy)


def transform_code(name: str, source: str) -> Optional[str]:
    """Transform code using a registered strategy by name.

    Returns None if no change is needed or strategy not found.
    """
    key = _canon(name)
    fn = _STRATEGIES.get(key)
    if not fn:
        # generic fallback: no-op
        return None
    try:
        result = fn(source)
        if result is None or result == source:
            return None
        return result
    except Exception:
        # Swallow and fallback to None
        return None
