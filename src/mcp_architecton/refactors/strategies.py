"""Refactor strategies using multi-AST tools with safe, idempotent edits.

Contract:
- Strategy = callable: (source: str) -> str | None, idempotent. Return None for no change.
- transform_code(name, source):
    1) Normalize name to a canonical key
    2) Run key-specific strategy (if any)
    3) Run generic transforms from snippets.transforms

Backends used (best-effort):
- LibCST (primary, preserves formatting)
- Parso (syntax probing)
- astroid (semantic probing) [optional]
- tree-sitter (fast parsing) [optional]
- ast-grep-py (pattern matching) [optional]
- RedBaron (fallback CST) [optional]

All imports are optional; failures fall back to no-ops. This module aims to
produce minimally invasive but concrete edits to unblock scaffolding.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

try:  # LibCST is required in project deps
    import libcst as cst
    from libcst import parse_module
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    cst = None  # type: ignore
    parse_module = None  # type: ignore

try:  # Optional helpers (not strictly required at runtime)
    import parso  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    parso = None  # type: ignore

try:
    import astroid  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    astroid = None  # type: ignore

try:
    from redbaron import RedBaron  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    RedBaron = None  # type: ignore

try:
    from tree_sitter import Language, Parser  # type: ignore
    from tree_sitter_languages import get_language  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    Language = None  # type: ignore
    Parser = None  # type: ignore
    get_language = None  # type: ignore

try:
    from ast_grep_py import AstGrep  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    AstGrep = None  # type: ignore

try:
    # Generic transforms from snippets
    from mcp_architecton.snippets.transforms import transform_generic
except (ImportError, ModuleNotFoundError):  # pragma: no cover

    def transform_generic(source: str) -> Optional[str]:  # type: ignore
        return None


try:  # alias normalization
    from mcp_architecton.snippets.aliases import NAME_ALIASES as _IMPL_ALIASES  # type: ignore
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    _aliases: Dict[str, str] = {}
else:
    _aliases = dict(_IMPL_ALIASES)


Strategy = Callable[[str], Optional[str]]


def _canon(name: str) -> str:
    k = (name or "").strip().lower()
    return _aliases.get(k, k)


def _append_snippet_marker(text: str, marker_key: str, body: str) -> str:
    marker = f"# --- mcp-architecton strategy: {marker_key} ---"
    if marker in text:
        return text
    return text.rstrip() + "\n\n" + marker + "\n" + body.rstrip() + "\n# --- end strategy ---\n"


def _safe_libcst_insert_class(source: str, class_code: str) -> Optional[str]:
    if not cst or not parse_module:
        return None
    try:
        mod = parse_module(source)
        # Quick presence check: if class with same name exists, no-op
        class_name = class_code.split()[1].split("(")[0].strip()

        class Finder(cst.CSTVisitor):
            def __init__(self) -> None:
                self.found = False

            def visit_ClassDef(self, node: cst.ClassDef) -> None:  # type: ignore[override]
                if node.name.value == class_name:  # type: ignore[attr-defined]
                    self.found = True

        v = Finder()
        mod.visit(v)
        if v.found:
            return None

        # Append class at module end preserving formatting
        new_body = list(mod.body) + [cst.parse_statement(class_code)]
        new_mod = mod.with_changes(body=new_body)
        return new_mod.code
    except (cst.ParserError, SyntaxError, ValueError):
        return None


def _safe_libcst_insert_function(source: str, func_code: str) -> Optional[str]:
    if not cst or not parse_module:
        return None
    try:
        mod = parse_module(source)
        func_name = func_code.split()[1].split("(")[0].strip()

        class Finder(cst.CSTVisitor):
            def __init__(self) -> None:
                self.found = False

            def visit_FunctionDef(self, node: cst.FunctionDef) -> None:  # type: ignore[override]
                if node.name.value == func_name:  # type: ignore[attr-defined]
                    self.found = True

        v = Finder()
        mod.visit(v)
        if v.found:
            return None

        new_body = list(mod.body) + [cst.parse_statement(func_code)]
        new_mod = mod.with_changes(body=new_body)
        return new_mod.code
    except (cst.ParserError, SyntaxError, ValueError):
        return None


# --- Concrete strategies ---


def _strategy_singleton(source: str) -> Optional[str]:
    """Ensure a minimal Singleton class exists or is correctly shaped.

    Conservative: if any class named 'Singleton' exists, do nothing.
    Otherwise, append a minimal, idempotent class with __new__.
    """
    snippet = (
        "class Singleton:\n"
        "    _instance = None\n\n"
        "    def __new__(cls, *args, **kwargs):  # pragma: no cover - scaffold\n"
        "        if cls._instance is None:\n"
        "            cls._instance = super().__new__(cls)\n"
        "        return cls._instance\n"
    )
    out = _safe_libcst_insert_class(source, snippet)
    if isinstance(out, str):
        return out
    # fallback marker append
    return _append_snippet_marker(source, "singleton", snippet)


def _strategy_facade_function(source: str) -> Optional[str]:
    snippet = (
        "def facade_function(*args, **kwargs):  # pragma: no cover - scaffold\n"
        '    """A thin facade function orchestrating multiple collaborators."""\n'
        "    # TODO: call into subsystems and aggregate results\n"
        "    raise NotImplementedError\n"
    )
    out = _safe_libcst_insert_function(source, snippet)
    if isinstance(out, str):
        return out
    return _append_snippet_marker(source, "facade_function", snippet)


def _strategy_observer(source: str) -> Optional[str]:
    snippet = (
        "class Observable:\n"
        "    def __init__(self) -> None:\n"
        "        self._subs: dict[str, list] = {}\n\n"
        "    def subscribe(self, event: str, handler) -> None:\n"
        "        self._subs.setdefault(event, []).append(handler)\n\n"
        "    def notify(self, event: str, payload):  # pragma: no cover - scaffold\n"
        "        for h in self._subs.get(event, []):\n"
        "            h(payload)\n"
    )
    out = _safe_libcst_insert_class(source, snippet)
    if isinstance(out, str):
        return out
    return _append_snippet_marker(source, "observer", snippet)


def _strategy_strategy(source: str) -> Optional[str]:
    # Provide Strategy/Context minimal scaffold only if absent
    snippet = (
        "from abc import ABC, abstractmethod\n\n"
        "class Strategy(ABC):\n"
        "    @abstractmethod\n"
        "    def execute(self, data):  # pragma: no cover - scaffold\n"
        "        raise NotImplementedError\n\n"
        "class Context:\n"
        "    def __init__(self, strategy: Strategy) -> None:\n"
        "        self._strategy = strategy\n\n"
        "    def process(self, data):\n"
        "        return self._strategy.execute(data)\n"
    )
    out = _safe_libcst_insert_class(source, "class Strategy(ABC):\n    pass\n")
    if isinstance(out, str):
        # The quick check inserted a placeholder; now replace with full snippet via marker append
        return _append_snippet_marker(out, "strategy", snippet)
    return _append_snippet_marker(source, "strategy", snippet)


# Registry and API


_STRATEGIES: Dict[str, Strategy] = {
    "singleton": _strategy_singleton,
    "facade_function": _strategy_facade_function,
    "observer": _strategy_observer,
    "strategy": _strategy_strategy,
}


def register_strategy(key: str, fn: Strategy) -> None:
    _STRATEGIES[_canon(key)] = fn


def transform_code(name: str, source: str) -> Optional[str]:
    key = _canon(name)
    # Key-specific first
    fn = _STRATEGIES.get(key)
    if fn:
        try:
            out = fn(source)
            if isinstance(out, str) and out != source:
                return out
        except (TypeError, ValueError, AttributeError):
            pass
    # Generic transforms as fallback
    try:
        gout = transform_generic(source)
        if isinstance(gout, str) and gout != source:
            return gout
    except (TypeError, ValueError, AttributeError):
        pass
    return None


__all__ = ["Strategy", "register_strategy", "transform_code"]
