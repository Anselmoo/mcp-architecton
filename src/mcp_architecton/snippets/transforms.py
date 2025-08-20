"""Generic source-to-source transforms using AST-family tools.

This module provides safe, idempotent codemods that can run before
snippet scaffolds are appended. The goal is to reorganize code using
syntax-aware transforms rather than brittle text appends.

Design principles:
- Prefer LibCST (Concrete Syntax Tree) when available; it preserves
  formatting and comments. Fall back gracefully to no-op.
- Idempotent: running a transform multiple times should result in the
  same code after the first successful application.
- Minimal and generic: avoid domain-specific solvers. Transforms should
  be broadly applicable and leave code behavior unchanged unless the
  pattern requires light reorganization.

API: Export BUILTIN_TRANSFORMS mapping consumed by api.register_transformer.

Optional tool integrations used when available (best-effort, graceful fallback):
- libcst (primary, already used)
- RedBaron (fallback when libcst fails/unavailable)
- tree_sitter / ast-grep-py (detectors stubs for future heuristics; currently no-op)
"""

from __future__ import annotations

from typing import Any, Callable, TypedDict

import libcst as cst
from libcst import parse_module
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor
from redbaron import RedBaron

# Note: Additional tools like tree-sitter / ast-grep-py can be integrated here later.


def _libcst_available() -> bool:
    # libcst is required by the project; keep helper for symmetry
    return True


def _redbaron_available() -> bool:
    return True


def _ensure_future_annotations(source: str) -> str | None:
    """Ensure 'from __future__ import annotations' exists at file top.

    Uses a simple string check for existence; uses LibCST only to place
    the import after the module docstring if present. Idempotent.
    """
    if "from __future__ import annotations" in source:
        return None
    if not _libcst_available():
        # Try RedBaron to insert after module docstring if present
        if _redbaron_available():
            try:
                rb = RedBaron(source)  # type: ignore[operator]
                # Find module docstring (first node is a string)
                has_docstring = False
                try:
                    first = rb[0]  # type: ignore[index]
                    has_docstring = getattr(first, "type", "") == "string"
                except Exception:
                    has_docstring = False
                if has_docstring:
                    rb.insert(1, "from __future__ import annotations\n")  # type: ignore[call-arg]
                else:
                    rb.insert(0, "from __future__ import annotations\n")  # type: ignore[call-arg]
                return str(rb)
            except Exception:
                # best-effort textual insert at file start
                return "from __future__ import annotations\n" + source
        # best-effort textual insert at file start
        return "from __future__ import annotations\n" + source

    try:
        mod = parse_module(source)
    except Exception:
        return None

    future_import = cst.SimpleStatementLine(
        [
            cst.ImportFrom(
                module=cst.Name("__future__"),
                names=[cst.ImportAlias(name=cst.Name("annotations"))],
            )
        ]
    )

    body = list(mod.body)
    insert_at = 0
    if body and isinstance(body[0], cst.SimpleStatementLine):
        first = body[0]
        if (
            len(first.body) == 1
            and isinstance(first.body[0], cst.Expr)
            and isinstance(first.body[0].value, cst.SimpleString)
        ):
            insert_at = 1

    new_body = body[:insert_at] + [future_import] + body[insert_at:]
    new_mod = mod.with_changes(body=new_body)
    return new_mod.code


def _normalize_future_annotations(source: str) -> str | None:
    """De-duplicate 'from __future__ import annotations' and move it to the top.

    Text-based and conservative: only handles exact-match lines to avoid
    over-editing. If LibCST is available, places the kept import after the
    module docstring. Returns None if no changes.
    """
    lines = source.splitlines(True)
    target = "from __future__ import annotations"
    idxs = [i for i, ln in enumerate(lines) if ln.strip() == target]
    if not idxs:
        return None
    # Remove all occurrences
    new_lines = [ln for ln in lines if ln.strip() != target]
    # Compute insertion index using LibCST if possible
    insert_at = 0
    if _libcst_available():
        try:
            mod = parse_module("".join(new_lines))
            body = list(mod.body)
            if body and isinstance(body[0], cst.SimpleStatementLine):
                first = body[0]
                if (
                    len(first.body) == 1
                    and isinstance(first.body[0], cst.Expr)
                    and isinstance(first.body[0].value, cst.SimpleString)
                ):
                    # approximate insertion after docstring line span
                    insert_at = 1
        except (cst.ParserError, AttributeError, IndexError):
            insert_at = 0
    # Insert canonical import line with newline
    canonical = target + "\n"
    new_lines = new_lines[:insert_at] + [canonical] + new_lines[insert_at:]
    new_source = "".join(new_lines)
    return new_source if new_source != source else None


def _organize_imports(source: str) -> str | None:
    """Add missing imports required by upcoming scaffolds or transforms.

    Very conservative: ensures 'abc.ABC' and 'abc.abstractmethod' are importable
    if AST detects abstract base classes introduced by prior steps. If LibCST
    is unavailable, no-op.
    """
    if not _libcst_available():
        # RedBaron fallback: ensure abc imports when ABC/abstractmethod used
        if not _redbaron_available():
            return None
        try:
            rb = RedBaron(source)
            code_str = str(rb)
            needs_abc = (" ABC" in code_str or "(ABC" in code_str) and (
                "from abc import ABC" not in code_str
            )
            needs_am = ("abstractmethod" in code_str) and (
                "abstractmethod" not in code_str.split("import ")[-1]
            )
            if not (needs_abc or needs_am):
                return None
            # Build import line
            symbols: list[str] = []
            if needs_abc:
                symbols.append("ABC")
            if needs_am:
                symbols.append("abstractmethod")
            import_line = f"from abc import {', '.join(symbols)}\n"
            # Insert after future import or at top
            inserted = False
            for i, node in enumerate(rb):
                try:
                    text = str(node)
                except (AttributeError, TypeError):  # Node conversion errors
                    continue
                if text.strip().startswith("from __future__ import annotations"):
                    rb.insert(i + 1, import_line)
                    inserted = True
                    break
            if not inserted:
                rb.insert(0, import_line)
            return str(rb)
        except (AttributeError, TypeError, ValueError):  # RedBaron operation errors
            return None

    try:
        mod = parse_module(source)
    except (cst.ParserError, ValueError):  # LibCST parsing errors
        return None

    ctx = CodemodContext()
    # Heuristic: if code references 'ABC' or 'abstractmethod' without import
    code_str = mod.code
    needs_abc = (" ABC" in code_str or "(ABC" in code_str) and "import ABC" not in code_str
    needs_am = (
        "abstractmethod" in code_str and "abstractmethod" not in code_str.split("import ")[-1]
    )
    if needs_abc:
        AddImportsVisitor.add_needed_import(ctx, "abc", "ABC")
    if needs_am:
        AddImportsVisitor.add_needed_import(ctx, "abc", "abstractmethod")
    if not (needs_abc or needs_am):
        return None

    new_mod = AddImportsVisitor(ctx).transform_module(mod)
    return new_mod.code


def transform_generic(source: str) -> str | None:
    """Run a small suite of safe, generic transforms.

    Returns a new source string only if a change was made; otherwise None.
    """
    transformers: list[Callable[[str], str | None]] = [
        _normalize_future_annotations,
        _ensure_future_annotations,
        _organize_imports,
    ]
    current = source
    changed = False
    for fn in transformers:
        out = fn(current)
        if isinstance(out, str) and out != current:
            current = out
            changed = True
    return current if changed else None


# Registry of built-in transforms: '*' makes them run for any requested name
BUILTIN_TRANSFORMS: dict[str, list[Callable[[str], str | None]]] = {
    "*": [transform_generic],
}


# --- As-Is → To-Be planning hooks ---


class PlanStep(TypedDict, total=False):
    kind: str  # e.g., "normalize_future", "add_imports", "extract_symbol"
    details: dict[str, Any]


class RefactorPlan(TypedDict, total=False):
    steps: list[PlanStep]
    notes: list[str]
    risks: list[str]


def plan_refactor(source: str, goals: list[str] | None = None) -> RefactorPlan:
    """Compute a minimal, generic refactor plan from As-Is → To-Be.

    Current stub plans for: future annotations normalization and conservative imports.
    """
    steps: list[PlanStep] = []
    notes: list[str] = []
    risks: list[str] = []

    # Normalize and ensure future annotations where appropriate
    # If the canonical future line appears more than once, plan to normalize
    target = "from __future__ import annotations"
    lines = source.splitlines()
    if sum(1 for ln in lines if ln.strip() == target) > 1:
        steps.append({"kind": "normalize_future", "details": {}})
        notes.append("De-duplicate 'from __future__ import annotations' and move to top.")
    # If it's missing entirely, plan to ensure it
    if not any(ln.strip() == target for ln in lines):
        steps.append({"kind": "ensure_future", "details": {}})
        notes.append("Ensure future annotations import is present.")

    # Very light heuristic for import organization: if 'ABC' / 'abstractmethod' used
    # without obvious import in the file, add an import step.
    code_str = source
    needs_abc = (" ABC" in code_str or "(ABC" in code_str) and (
        "from abc import ABC" not in code_str
    )
    needs_am = ("abstractmethod" in code_str) and (
        "abstractmethod" not in code_str.split("import ")[-1]
    )
    if needs_abc or needs_am:
        steps.append(
            {
                "kind": "add_imports",
                "details": {
                    "symbols": [
                        s for s, ok in [("ABC", needs_abc), ("abstractmethod", needs_am)] if ok
                    ]
                },
            }
        )
        notes.append("Ensure abc imports for ABC/abstractmethod are present.")

    # Respect simple goal hints if provided
    if goals:
        goal_set = {g.strip().lower() for g in goals}
        if "organize_imports" in goal_set and not any(
            s.get("kind") == "add_imports" for s in steps
        ):
            steps.append({"kind": "add_imports", "details": {}})
        if "ensure_future_annotations" in goal_set and not any(
            s.get("kind") in {"normalize_future", "ensure_future"} for s in steps
        ):
            steps.append({"kind": "ensure_future", "details": {}})

    return {"steps": steps, "notes": notes, "risks": risks}


def apply_plan(source: str, plan: RefactorPlan) -> str | None:
    """Apply a plan's steps idempotently. Returns new source or None if no change."""
    if not plan or not plan.get("steps"):
        return None

    # Map plan kinds to underlying functions
    kind_map: dict[str, Callable[[str], str | None]] = {
        "normalize_future": _normalize_future_annotations,
        "ensure_future": _ensure_future_annotations,
        "add_imports": _organize_imports,
    }

    current = source
    changed = False
    for step in plan.get("steps", []):
        fn = kind_map.get(step.get("kind", ""))
        if not fn:
            continue
        try:
            out = fn(current)
        except (TypeError, ValueError, AttributeError):  # Transform function errors
            continue
        if isinstance(out, str) and out != current:
            current = out
            changed = True
    return current if changed else None


__all__ = [
    "transform_generic",
    "BUILTIN_TRANSFORMS",
    "plan_refactor",
    "apply_plan",
]
