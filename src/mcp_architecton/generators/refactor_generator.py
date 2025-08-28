from __future__ import annotations

import ast
import json
import logging
import py_compile
import tempfile
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any, Callable, Optional, cast

import astroid
import libcst as cst
import parso
from ast_grep_py import SgRoot
from jinja2 import Template
from redbaron import RedBaron
from tree_sitter import Parser
from tree_sitter_languages import get_language

from mcp_architecton.snippets.aliases import canonicalize_name  # type: ignore

from .architectures import ARCH_GENERATORS
from .patterns import PATTERN_GENERATORS

logger = logging.getLogger(__name__)


Generator = Callable[[str, Optional[Any]], str | None]


def _canon(name: str | None) -> str:
    if not name:
        return ""
    return canonicalize_name(name)


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


def _load_catalog_entry(name: str, category: str) -> Optional[dict[str, Any]]:
    """Best-effort loader for catalog.json entries.

    Matches by case-insensitive name; returns dict with optional refs/description.
    Works in editable installs by resolving the repo root relative to this file.
    """
    try:

        def _norm(s: str) -> str:
            # lower, replace underscores/hyphens with spaces, collapse whitespace
            import re

            s2 = s.lower().replace("_", " ").replace("-", " ")
            return re.sub(r"\s+", " ", s2).strip()

        root = Path(__file__).resolve().parents[3]
        catalog_path = root / "data" / "patterns" / "catalog.json"
        if not catalog_path.exists():
            return None

        data_loaded: Any = json.loads(catalog_path.read_text())
        if not isinstance(data_loaded, dict):
            return None
        data_map: dict[str, Any] = cast(dict[str, Any], data_loaded)
        patterns_any: Any = data_map.get("patterns")
        if not isinstance(patterns_any, list):
            return None
        patterns_val: list[dict[str, Any]] = [
            cast(dict[str, Any], it) for it in patterns_any if isinstance(it, dict)
        ]

        # Normalize name and allow a few common aliases from generator keys to catalog names
        nl = _norm(name)
        aliases: dict[str, str] = {
            # architectures
            "clean": "clean architecture",
            "layered": "layered architecture",
            "three tier": "3 tier",
            "three_tier": "3 tier",
            "mvc": "mvc",
            "hexagonal": "hexagonal architecture",
            "microservices": "microservices",
            "event driven": "event driven architecture",
            "event_driven": "event driven architecture",
            # creational synonyms
            "factory method": "factory method",
        }
        nl = aliases.get(nl, nl)
        cat_filter = (category or "").strip().lower()
        # Don't over-constrain on generic buckets; catalog uses style-specific categories
        enforce_cat = cat_filter not in {"", "pattern", "architecture"}

        for it_any in patterns_val:
            it_name = str(it_any.get("name") or "").strip().lower()
            it_cat = str(it_any.get("category") or "").strip().lower()
            if _norm(it_name) == nl and (not enforce_cat or it_cat == cat_filter):
                # Typed enough for our usage
                return it_any
        return None
    except Exception:  # pragma: no cover - non-fatal
        return None


def _resolve_refactoring_refs(limit: int = 3) -> list[str]:
    """Return a prioritized list of refactoring reference links from catalog or fallback."""
    refs: list[str] = []
    try:
        root = Path(__file__).resolve().parents[3]
        catalog_path = root / "data" / "patterns" / "catalog.json"
        if catalog_path.exists():
            raw = catalog_path.read_text()
            data_obj: Any = json.loads(raw)
            data: dict[str, Any]
            if isinstance(data_obj, dict):
                data = cast(dict[str, Any], data_obj)
            else:
                data = {}
            # 1) General refactoring entry
            patterns_any: Any = data.get("patterns") or []
            patterns_list: list[dict[str, Any]] = [
                cast(dict[str, Any], it) for it in patterns_any if isinstance(it, dict)
            ]
            for it in patterns_list:
                cat_val = str(it.get("category", ""))
                if cat_val.strip().lower() == "refactoring":
                    refs_any: Any = it.get("refs", [])
                    refs_list: list[str] = [str(x) for x in refs_any if isinstance(x, str)]
                    for s in refs_list:
                        if s and s not in refs:
                            refs.append(s)
            # 2) Optional explicit techniques list if present
            techniques_any: Any = data.get("refactorings") or []
            techniques_list: list[dict[str, Any]] = [
                cast(dict[str, Any], t) for t in techniques_any if isinstance(t, dict)
            ]
            for tech in techniques_list:
                url_val = str(tech.get("url", ""))
                if url_val and url_val not in refs:
                    refs.append(url_val)
    except Exception:  # pragma: no cover - non-fatal
        pass
    # Fallbacks appended last
    fallbacks = [
        "https://refactoring.guru/refactoring/techniques",
        "https://refactoring.com/catalog/",
    ]
    for fb in fallbacks:
        if fb not in refs:
            refs.append(fb)
    return refs[: max(1, limit)]


def _resolve_refactoring_general_ref() -> str:
    """Backward-compat: first ref from _resolve_refactoring_refs."""
    return _resolve_refactoring_refs(limit=1)[0]


def _build_boilerplate_header(
    name: str,
    category: str,
    refs: list[str] | None,
    contract: dict[str, str] | None = None,
    tools: list[str] | None = None,
    complexity: dict[str, int | str] | None = None,
    extra_refactor_refs: list[str] | None = None,
    prompt_hint: str | None = None,
) -> str:
    """Compact guidance header enforcing stepwise integration and guardrails.

    Output is a short module docstring (< ~12 lines) with steps, optional
    Contract (inputs/outputs), and cross-references.
    """
    title = f"Boilerplate Scaffold: {name.replace('_', ' ').title()} ({category})"
    steps = [
        "1) Map roles to your code (Target/Adapter/etc.)",
        "2) Extract/define the client-facing interface (keep API stable)",
        "3) Implement adapter and delegate to existing impl",
        "4) Wire via a small seam; avoid broad rewrites",
        "5) Run unit tests and ruff; commit minimal diffs",
    ]

    pattern_refs = refs or []
    refactoring_refs = extra_refactor_refs or _resolve_refactoring_refs(limit=2)

    contract_inputs = (contract or {}).get("inputs") or "Public inputs unchanged"
    contract_outputs = (contract or {}).get("outputs") or "Behavior unchanged"
    tools_line = ", ".join(
        tools
        or [
            "ast",
            "parso",
            "libcst",
            "astroid",
            "RedBaron",
            "tree-sitter",
            "py_compile",
        ]
    )
    tools_short = "ast/libcst/py_compile"

    # Optional simple complexity hint
    level = str((complexity or {}).get("level") or "").lower()
    loc = (complexity or {}).get("loc")
    defs = (complexity or {}).get("defs")
    if level not in {"low", "medium", "high"}:
        level = ""

    lines: list[str] = []
    lines.append(title)
    lines.extend(steps)
    lines.append(f"Contract: inputs={contract_inputs}; outputs={contract_outputs}")
    lines.append(f"Validation: {tools_line}")
    if level:
        lines.append(
            f"Complexity: {level} (LOC={loc or '?'}; defs={defs or '?'}) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction"
        )
    # Minimal prompt hint to guide LLM-assisted edits (catalog-sourced if available)
    ph = (
        prompt_hint
        or f"Keep public API stable, propose minimal seam, limit diff; validate with tests + {tools_short}"
    )
    lines.append(f"Prompt: {ph}")
    if pattern_refs:
        pr = ", ".join(pattern_refs[:2])
        lines.append(f"Cross-ref Pattern: {pr}")
    if refactoring_refs:
        # Show up to two concise refs
        first_two = ", ".join(refactoring_refs[:2])
        lines.append(f"Cross-ref Refactoring: {first_two}")

    # Convert to a compact docstring
    body = "\n".join(lines)
    return f'"""\n{body}\n"""'


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

    # py_compile as an additional safety check
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "_snippet_check.py"
            tmp.write_text(code)
            py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"py_compile failed: {exc}")

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
        # Load catalog entry to pass into generator (for refs/description) and header
        entry = _load_catalog_entry(canon, category)
        snippet_raw = gen(module_path, entry)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"generator failed: {exc}", "name": canon}
    if not snippet_raw:
        return {"status": "error", "error": "no snippet available", "name": canon}

    # Allow light templating if a generator uses placeholders
    snippet = _render_template(snippet_raw, {"name": canon, "module_path": module_path})

    # Prepend a compact boilerplate header with integration guidance, contract, refs, tools, and complexity hint
    refs: list[str] = []
    prompt_hint: str | None = None
    if isinstance(entry, dict):
        refs = entry.get("refs", []) or []
        ph = entry.get("prompt_hint")
        if isinstance(ph, str) and ph.strip():
            prompt_hint = ph.strip()
    # Generators can optionally supply contract via catalog entry; fallback to a generic one
    contract = {"inputs": "existing API/clients", "outputs": "same observable behavior"}
    if isinstance(entry, dict):
        entry_contract_any = entry.get("contract")
        if isinstance(entry_contract_any, dict):
            entry_contract = cast(dict[str, Any], entry_contract_any)
            ci_any = entry_contract.get("inputs")
            co_any = entry_contract.get("outputs")
            if isinstance(ci_any, str) and ci_any.strip():
                contract["inputs"] = ci_any.strip()
            if isinstance(co_any, str) and co_any.strip():
                contract["outputs"] = co_any.strip()
    # Simple complexity heuristic based on existing module (if any)
    target_path = Path(out_path or module_path)
    exists = target_path.exists()
    old_text = target_path.read_text() if exists else ""
    loc_count = (old_text or snippet).count("\n") + 1
    defs_count = len(_top_level_defs(old_text)) if old_text else len(_top_level_defs(snippet))
    if loc_count >= 800 or defs_count >= 40:
        level = "high"
    elif loc_count >= 300 or defs_count >= 15:
        level = "medium"
    else:
        level = "low"
    complexity = {"level": level, "loc": loc_count, "defs": defs_count}
    tools = ["ast", "parso", "libcst", "astroid", "RedBaron", "tree-sitter", "py_compile"]
    refactor_refs = _resolve_refactoring_refs(limit=2)
    header = _build_boilerplate_header(
        canon,
        category,
        refs,
        contract,
        tools=tools,
        complexity=complexity,
        extra_refactor_refs=refactor_refs,
        prompt_hint=prompt_hint,
    )
    snippet = header + "\n\n" + snippet

    # Duplicate guard: if all top-level names from snippet already exist in target, noop
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
