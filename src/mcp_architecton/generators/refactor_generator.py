from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any, Callable, Optional

import astroid  # type: ignore
import libcst as cst  # type: ignore
import parso  # type: ignore
from ast_grep_py import SgRoot
from jinja2 import Template  # type: ignore
from redbaron import RedBaron  # type: ignore
from tree_sitter import Parser  # type: ignore
from tree_sitter_languages import get_language  # type: ignore

from .architectures import ARCH_GENERATORS
from .patterns import PATTERN_GENERATORS

logger = logging.getLogger(__name__)


# Optional: alias map if snippets package is present
try:  # pragma: no cover - optional
    from mcp_architecton.snippets.aliases import NAME_ALIASES as snippet_aliases  # type: ignore
except Exception:  # pragma: no cover
    snippet_aliases: dict[str, str] = {}


Generator = Callable[[str, Optional[Any]], str | None]


def _canon(name: str | None) -> str:
    if not name:
        return ""
    raw = name.strip().lower()
    return snippet_aliases.get(raw, raw)


def _select_generator(name: str) -> tuple[str, str, Generator] | None:
    """Return (category, canonical_name, generator)."""
    canon = _canon(name)
    gen = PATTERN_GENERATORS.get(canon)
    if gen:
        return ("Pattern", canon, gen)
    gen = ARCH_GENERATORS.get(canon)
    if gen:
        return ("Architecture", canon, gen)
    return None


def _render_template(snippet: str, context: dict[str, Any]) -> str:
    try:
        return Template(snippet).render(**context)
    except Exception:  # pragma: no cover - fallback to raw
        return snippet


def _top_level_defs(code: str) -> set[str]:
    names: set[str] = set()
    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                names.add(node.name)
    except SyntaxError:
        pass
    return names


def _astgrep_has_name(code: str, name: str) -> bool:
    """Heuristic presence check using ast-grep's Python API (SgRoot).

    Matches top-level function_definition or class_definition whose 'name' field equals `name`.
    Avoids language-agnostic brace patterns and relies on node kinds/fields.
    """
    try:
        root = SgRoot(code, "python").root()
        # Top-level functions
        for fn in root.find_all(kind="function_definition"):
            nm = fn.field("name")
            parent = fn.parent()
            if nm and nm.text() == name and parent and parent.kind() == "module":
                return True
        # Top-level classes
        for cls in root.find_all(kind="class_definition"):
            nm = cls.field("name")
            parent = cls.parent()
            if nm and nm.text() == name and parent and parent.kind() == "module":
                return True
        return False
    except Exception:
        # Fall back gracefully if ast-grep is unavailable or parsing fails
        return False


def _validate_parsers(code: str) -> list[str]:
    """Run a gauntlet of parsers to validate the scaffold; return warnings (empty if OK)."""
    warnings: list[str] = []
    # Python AST
    try:
        ast.parse(code)
    except SyntaxError as exc:
        warnings.append(f"ast.parse failed: {exc}")

    # parso
    try:
        parso.parse(code)  # type: ignore[misc]
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"parso.parse failed: {exc}")

    # libcst
    try:
        cst.parse_module(code)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"libcst.parse_module failed: {exc}")

    # astroid
    try:
        astroid.parse(code)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"astroid.parse failed: {exc}")

    # redbaron
    try:
        RedBaron(code)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"RedBaron failed: {exc}")

    # tree-sitter
    try:
        lang = get_language("python")  # type: ignore[no-untyped-call]
        parser = Parser()  # type: ignore[call-arg]
        parser.set_language(lang)  # type: ignore[attr-defined]
        tree = parser.parse(code.encode("utf-8"))  # type: ignore[attr-defined]
        if tree.root_node.has_error:
            warnings.append("tree-sitter reports syntax errors")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"tree-sitter failed: {exc}")

    return warnings


@dataclass
class IntroduceResult:
    status: str
    category: str
    name: str
    target: str
    dry_run: bool
    created: bool
    appended: bool
    written_to: Optional[str]
    diff: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "category": self.category,
            "name": self.name,
            "target": self.target,
            "dry_run": self.dry_run,
            "created": self.created,
            "appended": self.appended,
            "written_to": self.written_to,
            "diff": self.diff,
            "warnings": self.warnings,
        }


def _write_or_diff(old: str, new: str, path: Path, dry_run: bool) -> tuple[str, bool]:
    """Return (diff, wrote)."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = "".join(
        unified_diff(old_lines, new_lines, fromfile=str(path), tofile=str(path), lineterm="")
    )
    wrote = False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new)
        wrote = True
    return (diff, wrote)


def introduce_impl(
    *, name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    """Generic introduce helper used by services.enforce and tools.

    Selects the generator by name (pattern or architecture), composes code, validates,
    and appends or creates the module.
    """
    sel = _select_generator(name)
    if not sel:
        return {"status": "error", "error": f"Unknown name: {name}", "name": name}
    category, canon, gen = sel

    try:
        snippet_raw = gen(module_path, None)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"generator failed: {exc}", "name": canon}
    if not snippet_raw:
        return {"status": "error", "error": "no snippet available", "name": canon}

    # Allow light templating if a generator uses placeholders
    snippet = _render_template(snippet_raw, {"name": canon, "module_path": module_path})

    # Duplicate guard: if all top-level names from snippet already exist in target, noop
    target_path = Path(out_path or module_path)
    exists = target_path.exists()
    old_text = target_path.read_text() if exists else ""
    snippet_names = _top_level_defs(snippet)
    target_names = _top_level_defs(old_text)
    duplicate = snippet_names and snippet_names.issubset(target_names)
    if not duplicate:
        # Fallback to ast-grep heuristic if AST set check says no-dup
        duplicate = any(_astgrep_has_name(old_text, n) for n in snippet_names)
    if duplicate:
        return {
            "status": "noop",
            "category": category,
            "name": canon,
            "target": str(target_path),
            "dry_run": dry_run,
            "created": not exists,
            "appended": False,
            "written_to": None,
            "diff": "",
            "warnings": [],
            "reason": "definitions already present",
        }

    # Compose final text
    new_text = snippet if not exists else (old_text.rstrip() + "\n\n" + snippet + "\n")

    # Validate with multiple parsers for resilience
    warnings = _validate_parsers(new_text)

    diff, wrote = _write_or_diff(old_text, new_text, target_path, dry_run)

    result = IntroduceResult(
        status="ok",
        category=category,
        name=canon,
        target=str(target_path),
        dry_run=dry_run,
        created=not exists,
        appended=exists,
        written_to=str(target_path) if wrote else None,
        diff=diff,
        warnings=warnings,
    )
    return result.to_dict()


def introduce_pattern_impl(
    *, name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    sel = _select_generator(name)
    if not sel:
        return {"status": "error", "error": f"Unknown pattern: {name}", "name": name}
    category, canon, _ = sel
    if category != "Pattern":
        return {"status": "error", "error": f"Not a pattern: {name}", "name": name}
    return introduce_impl(name=canon, module_path=module_path, dry_run=dry_run, out_path=out_path)


def introduce_architecture_impl(
    *, name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    sel = _select_generator(name)
    if not sel:
        return {"status": "error", "error": f"Unknown architecture: {name}", "name": name}
    category, canon, _ = sel
    if category != "Architecture":
        return {"status": "error", "error": f"Not an architecture: {name}", "name": name}
    return introduce_impl(name=canon, module_path=module_path, dry_run=dry_run, out_path=out_path)


__all__ = [
    "introduce_impl",
    "introduce_pattern_impl",
    "introduce_architecture_impl",
]
