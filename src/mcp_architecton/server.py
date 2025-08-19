from __future__ import annotations

import difflib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

# Per user requirement: import directly from fastmcp
from fastmcp import FastMCP  # type: ignore[import-not-found]

from mcp_architecton.analysis.advice_loader import build_advice_maps
from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.analysis.enforcement import ranked_enforcement_targets
from mcp_architecton.detectors import registry as detector_registry

# Implementor snippets are optional; keep the server resilient if not present.
NAME_ALIASES: dict[str, str] = {}
try:  # pragma: no cover - optional dependency
    from mcp_architecton.snippets import NAME_ALIASES as _IMPL_ALIASES  # type: ignore
    from mcp_architecton.snippets import get_snippet  # type: ignore

    NAME_ALIASES.update(_IMPL_ALIASES)
except Exception:  # pragma: no cover

    def get_snippet(_name: str) -> str | None:  # type: ignore
        return None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_PATTERN_ALIASES: dict[str, str] = NAME_ALIASES
_ARCH_ALIASES: dict[str, str] = NAME_ALIASES


# Lazy caches for dynamically built advice maps
_pattern_refactor_advice_cache: dict[str, str] | None = None
_architecture_refactor_advice_cache: dict[str, str] | None = None


def _pattern_advice() -> dict[str, str]:
    """Get dynamic pattern advice map, building it on first use."""
    global _pattern_refactor_advice_cache, _architecture_refactor_advice_cache
    if _pattern_refactor_advice_cache is None or _architecture_refactor_advice_cache is None:
        pmap, amap = build_advice_maps()
        _pattern_refactor_advice_cache = pmap
        _architecture_refactor_advice_cache = amap
    return _pattern_refactor_advice_cache or {}


def _arch_advice() -> dict[str, str]:
    """Get dynamic architecture advice map, building it on first use."""
    global _architecture_refactor_advice_cache
    if _architecture_refactor_advice_cache is None:
        _pattern_advice()
    return _architecture_refactor_advice_cache or {}


# Name kept to match VS Code MCP config and console script
app: FastMCP = FastMCP("mcp-architecton")


def _ranked_enforcement_targets(
    indicators: list[dict[str, Any]], recs: list[str]
) -> list[tuple[str, str, int, list[str]]]:
    return ranked_enforcement_targets(
        indicators,
        recs,
        _pattern_advice(),
        _arch_advice(),
        NAME_ALIASES,
    )


def _thresholded_enforcement(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 3,
) -> dict[str, Any]:
    """Call anti-pattern scanner, rank issues, and return tailored enforcement prompts.

    Returns per source: metrics snapshot, top suggestions with prompts and reasons.
    """
    base = scan_anti_patterns_impl(code=code, files=files)
    if "error" in base:
        return base
    results: list[dict[str, Any]] = []
    raw_entries = base.get("results", [])
    entries_list: list[Any] = cast(list[Any], raw_entries) if isinstance(raw_entries, list) else []
    for entry in entries_list:
        if not isinstance(entry, dict):
            continue
        entry_d = cast(dict[str, Any], entry)
        indicators_val = entry_d.get("indicators", [])
        indicators_list: list[dict[str, Any]] = []
        if isinstance(indicators_val, list):
            for i in cast(list[object], indicators_val):
                if isinstance(i, dict):
                    indicators_list.append(cast(dict[str, Any], i))
        recs_val = entry_d.get("recommendations", [])
        recs_list: list[str] = []
        if isinstance(recs_val, list):
            for x in cast(list[object], recs_val):
                recs_list.append(f"{x}")
        ranked = _ranked_enforcement_targets(indicators_list, recs_list)
        chosen = ranked[: max_suggestions if max_suggestions and max_suggestions > 0 else 3]
        suggestions: list[dict[str, Any]] = []
        for name, category, weight, reasons in chosen:
            prompt = (
                _pattern_advice().get(name) if category == "Pattern" else _arch_advice().get(name)
            )
            if not prompt:
                continue
            suggestions.append(
                {
                    "target": name,
                    "category": category,
                    "weight": weight,
                    "reasons": reasons,
                    "prompt": prompt,
                }
            )
        results.append(
            {
                "source": entry_d.get("source"),
                "metrics": entry_d.get("metrics"),
                "indicators": indicators_list,
                "suggestions": suggestions,
            }
        )
    return {"results": results}


def _canonical_pattern_name(name: str | None) -> str:
    """Return a normalized canonical pattern name using alias map when available."""
    if not name:
        return ""
    key = name.strip().lower()
    return _PATTERN_ALIASES.get(key, key)


def _canonical_arch_name(name: str | None) -> str:
    """Return a normalized canonical architecture name using alias map when available."""
    if not name:
        return ""
    key = name.strip().lower()
    return _ARCH_ALIASES.get(key, key)


def list_patterns_impl() -> list[dict[str, Any]]:
    """List pattern entries from the catalog (non-architectures)."""
    catalog_path = Path(__file__).resolve().parents[2] / "data" / "patterns" / "catalog.json"
    if not catalog_path.exists():
        return []
    try:
        data = json.loads(catalog_path.read_text())
    except Exception:  # noqa: BLE001
        return []
    patterns: list[dict[str, Any]] = data.get("patterns", [])
    return [p for p in patterns if p.get("category") != "Architecture"]


def analyze_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze code or files and return design pattern findings.

    Uses AST-based detectors via analyze_code_for_patterns.
    """
    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    texts: list[tuple[str, str]] = []
    if code:
        texts.append(("<input>", code))
    if files:
        for f in files:
            p = Path(f)
            try:
                texts.append((str(p), p.read_text()))
            except Exception as exc:  # noqa: BLE001
                texts.append((str(p), f"<read-error: {exc}>"))

    findings: list[dict[str, Any]] = []
    for label, text in texts:
        try:
            results = analyze_code_for_patterns(text, detector_registry)
        except Exception as exc:  # noqa: BLE001
            findings.append({"source": label, "error": str(exc)})
            continue
        for r in results:
            r["source"] = label
            findings.append(r)

    return {"findings": findings}


def analyze_metrics_impl(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    """Compute code metrics (CC/MI/LOC) using radon and include Ruff results.

    Accepts either a code string or a list of file paths.
    Returns a dict with per-source metrics and linter analyses.
    """
    try:
        from radon.complexity import cc_visit  # type: ignore
        from radon.metrics import mi_visit  # type: ignore
        from radon.raw import analyze as raw_analyze  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"error": f"radon not available: {exc}"}

    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    texts: list[tuple[str, str]] = []
    if code:
        texts.append(("<input>", code))
    if files:
        for f in files:
            p = Path(f)
            try:
                texts.append((str(p), p.read_text()))
            except Exception as exc:  # noqa: BLE001
                texts.append((str(p), f"<read-error: {exc}>"))

    results: list[dict[str, Any]] = []
    for label, text in texts:
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            cc: list[dict[str, Any]] = []
            for obj in cc_objs:
                cc.append(
                    {
                        "name": getattr(obj, "name", ""),
                        "type": getattr(obj, "kind", ""),
                        "complexity": getattr(obj, "complexity", None),
                        "lineno": getattr(obj, "lineno", None),
                    }
                )

            mi: Any = mi_visit(text, multi=True)  # type: ignore[misc]
            raw_val = raw_analyze(text)  # type: ignore[misc]
            raw = cast(Any, raw_val)
            results.append(
                {
                    "source": label,
                    "cyclomatic_complexity": cc,
                    "maintainability_index": mi,
                    "raw": {
                        "loc": getattr(raw, "loc", None),
                        "lloc": getattr(raw, "lloc", None),
                        "sloc": getattr(raw, "sloc", None),
                        "comments": getattr(raw, "comments", None),
                        "multi": getattr(raw, "multi", None),
                    },
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"source": label, "error": str(exc)})

    # Ruff analysis (aggregated per file)
    ruff_exe = shutil.which("ruff")
    ruff_out: dict[str, Any] = {"error": "ruff CLI not available in PATH"}
    if ruff_exe:
        tmp_dir: str | None = None
        targets: list[str] = []
        try:
            if code:
                tmp_dir = tempfile.mkdtemp(prefix="ruff_")
                p = Path(tmp_dir) / "input.py"
                p.write_text(code)
                targets.append(str(p))
            if files:
                for f in files:
                    try:
                        if Path(f).is_file():
                            targets.append(f)
                    except Exception:
                        pass
            if targets:
                proc = subprocess.run(
                    [ruff_exe, "check", "--format", "json", *targets],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode in (0, 1):  # 1 indicates lint findings
                    try:
                        data = json.loads(proc.stdout or "[]")
                        # Aggregate by file path and rule code
                        agg: dict[str, dict[str, int]] = {}
                        items_list: list[dict[str, Any]] = (
                            cast(list[dict[str, Any]], data) if isinstance(data, list) else []
                        )
                        for item in items_list:
                            try:
                                fpath = str(item.get("filename", ""))
                                code_key = str(item.get("code", ""))
                                if fpath and code_key:
                                    counts_for_file = agg.setdefault(fpath, {})
                                    counts_for_file[code_key] = counts_for_file.get(code_key, 0) + 1
                            except Exception:
                                continue
                        ruff_out = {
                            "results": [
                                {"file": fp, "counts": counts} for fp, counts in sorted(agg.items())
                            ]
                        }
                    except Exception as exc:  # noqa: BLE001
                        ruff_out = {"error": f"ruff parse error: {exc}"}
                else:
                    ruff_out = {"error": proc.stderr.strip() or "ruff failed"}
        finally:
            if tmp_dir:
                try:
                    shutil.rmtree(tmp_dir)
                except Exception:
                    pass

    return {"results": results, "ruff": ruff_out}


def list_architectures_impl() -> list[dict[str, Any]]:
    """List recognized software architectures from the catalog."""
    catalog_path = Path(__file__).resolve().parents[2] / "data" / "patterns" / "catalog.json"
    if not catalog_path.exists():
        return []
    try:
        data = json.loads(catalog_path.read_text())
    except Exception:  # noqa: BLE001
        return []
    patterns: list[dict[str, Any]] = data.get("patterns", [])
    return [p for p in patterns if p.get("category") == "Architecture"]


def analyze_architectures_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Detect architecture styles in a code string or Python files (provide code or files)."""
    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    # Build name set from catalog; fallback to heuristic names
    arch_entries = list_architectures_impl()
    arch_names: set[str] = {str(e.get("name", "")) for e in arch_entries if e.get("name")}
    if not arch_names:
        arch_names = {
            "Layered Architecture",
            "Hexagonal Architecture",
            "Clean Architecture",
            "3-Tier Architecture",
            "Repository",
            "Service Layer",
            "Unit of Work",
            "Message Bus",
            "Domain Events",
            "CQRS",
            "Front Controller",
            "Model-View-Controller (MVC)",
        }

    texts: list[tuple[str, str]] = []
    if code:
        texts.append(("<input>", code))
    if files:
        for f in files:
            p = Path(f)
            try:
                texts.append((str(p), p.read_text()))
            except Exception as exc:  # noqa: BLE001
                texts.append((str(p), f"<read-error: {exc}>"))

    findings: list[dict[str, Any]] = []
    for label, text in texts:
        try:
            all_results = analyze_code_for_patterns(text, detector_registry)
        except Exception as exc:  # noqa: BLE001
            findings.append({"source": label, "error": str(exc)})
            continue
        for r in all_results:
            name = str(r.get("name", ""))
            if name in arch_names:
                r["source"] = label
                findings.append(r)

    return {"findings": findings}


def introduce_pattern_impl(
    name: str,
    module_path: str,
    dry_run: bool = False,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Create/append a scaffold for the named pattern into module_path with transforms and diff.

    If module_path is a directory, apply transform/scaffold across all Python files under it
    (recursively), optionally writing results to an out_path directory (mirrored structure).
    Aggregates diffs for all changed files.
    """
    name_norm = _canonical_pattern_name(name)
    p = Path(module_path)
    target = Path(out_path) if out_path else p
    base_parent = target if p.is_dir() else (target.parent if out_path else p.parent)
    if not base_parent.exists():
        return {"error": f"Parent directory does not exist: {base_parent}"}

    try:
        from mcp_architecton.snippets import transform_code  # type: ignore
        from mcp_architecton.snippets.transforms import (  # type: ignore
            apply_plan,
            plan_refactor,
        )
    except Exception:
        transform_code = None  # type: ignore[assignment]
        plan_refactor = None  # type: ignore[assignment]
        apply_plan = None  # type: ignore[assignment]

    try:
        # Directory-wide mode
        if p.is_dir() or (out_path and target.is_dir()):
            changed: list[dict[str, str]] = []
            src_root = p if p.is_dir() else (target if target.is_dir() else p)
            dst_root = Path(out_path) if out_path else src_root
            for src in sorted(src_root.rglob("*.py")):
                rel = src.relative_to(src_root)
                dst = dst_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                original = src.read_text()
                planned: str | None = None
                if plan_refactor and apply_plan:
                    try:
                        plan = plan_refactor(original, goals=[name_norm])  # type: ignore[misc]
                        planned = apply_plan(original, plan)  # type: ignore[misc]
                    except Exception:
                        planned = None
                rewritten: str | None = (
                    transform_code(name_norm, planned or original) if transform_code else planned
                )  # type: ignore[call-arg]
                post = rewritten or original
                if post != original:
                    if not dry_run:
                        dst.write_text(post)
                    diff = "".join(
                        difflib.unified_diff(
                            original.splitlines(keepends=True),
                            post.splitlines(keepends=True),
                            fromfile=str(src),
                            tofile=str(dst),
                        )
                    )
                    changed.append({"path": str(dst), "diff": diff})
            if not changed:
                # If no transforms occurred, create a new scaffold module in dst_root
                snippet = get_snippet(name_norm)
                if snippet:
                    new_file = (Path(out_path) if out_path else src_root) / f"{name_norm}.py"
                    if not dry_run:
                        new_file.parent.mkdir(parents=True, exist_ok=True)
                        new_file.write_text(snippet)
                    diff = "".join(
                        difflib.unified_diff(
                            [],
                            snippet.splitlines(keepends=True),
                            fromfile=str(new_file),
                            tofile=str(new_file),
                        )
                    )
                    changed.append({"path": str(new_file), "diff": diff})
            return {
                "status": "ok",
                "written": str(target),
                "mode": "transformed-dir" if changed else "created-new",
                "dry_run": dry_run,
                "changes": changed,
            }

        # Determine an existing FILE path (avoid directories triggering read_text errors)
        existing_path = None
        try:
            if p.exists() and p.is_file():
                existing_path = p
            elif target.exists() and target.is_file():
                existing_path = target
        except Exception:
            existing_path = None
        if existing_path is not None:
            original = existing_path.read_text()
            # Planner pre-pass (As-Is → To-Be)
            if plan_refactor and apply_plan:
                try:
                    plan = plan_refactor(original, goals=[name_norm])  # type: ignore[misc]
                    planned = apply_plan(original, plan)  # type: ignore[misc]
                except Exception:
                    planned = None
            else:
                planned = None
            # Named transform pass
            if transform_code is not None:
                rewritten: str | None = transform_code(name_norm, planned or original)  # type: ignore[call-arg]
            else:
                rewritten = planned
            if isinstance(rewritten, str) and rewritten.strip() and rewritten != original:
                if transform_code is not None:
                    post = cast(str, (transform_code(name_norm, rewritten) or rewritten))  # type: ignore[call-arg]
                else:
                    post = rewritten
                if not dry_run:
                    target.write_text(post)
                diff = "".join(
                    difflib.unified_diff(
                        original.splitlines(keepends=True),
                        post.splitlines(keepends=True),
                        fromfile=str(existing_path),
                        tofile=str(target),
                    )
                )
                return {
                    "status": "ok",
                    "written": str(target),
                    "mode": "transformed" if not out_path else "transformed-new",
                    "dry_run": dry_run,
                    "diff": diff,
                }

        # No transform-only changes; proceed to scaffold path
        snippet = get_snippet(name_norm)
        if snippet is None:
            return {"error": f"Pattern not supported: {name}"}

        if existing_path is not None:
            original = existing_path.read_text()
            updated = original + ("\n\n" if not original.endswith("\n") else "\n") + snippet
            # Planner + transform after append
            if plan_refactor and apply_plan:
                try:
                    plan2 = plan_refactor(updated, goals=[name_norm])  # type: ignore[misc]
                    planned2 = apply_plan(updated, plan2)  # type: ignore[misc]
                except Exception:
                    planned2 = None
            else:
                planned2 = None
            post = (
                (transform_code(name_norm, planned2 or updated) or (planned2 or updated))
                if transform_code
                else (planned2 or updated)
            )  # type: ignore[call-arg]
            if not dry_run:
                target.write_text(post)
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    post.splitlines(keepends=True),
                    fromfile=str(existing_path),
                    tofile=str(target),
                )
            )
            return {
                "status": "ok",
                "written": str(target),
                "mode": "scaffold-appended" if not out_path else "scaffold-appended-new",
                "dry_run": dry_run,
                "diff": diff,
            }
        else:
            # New file creation; normalize using planner + transform
            if plan_refactor and apply_plan:
                try:
                    plan0 = plan_refactor(snippet, goals=[name_norm])  # type: ignore[misc]
                    planned0 = apply_plan(snippet, plan0)  # type: ignore[misc]
                except Exception:
                    planned0 = None
            else:
                planned0 = None
            post = (
                (transform_code(name_norm, planned0 or snippet) or (planned0 or snippet))
                if transform_code
                else (planned0 or snippet)
            )  # type: ignore[call-arg]
            if not dry_run:
                target.write_text(post)
            diff = "".join(
                difflib.unified_diff(
                    [],
                    post.splitlines(keepends=True),
                    fromfile=str(target),
                    tofile=str(target),
                )
            )
            return {
                "status": "ok",
                "written": str(target),
                "mode": "created" if not out_path else "created-new",
                "dry_run": dry_run,
                "diff": diff,
            }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    return {"status": "ok", "written": str(target), "dry_run": dry_run}


def introduce_architecture_impl(
    name: str,
    module_path: str,
    dry_run: bool = False,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Introduce an architecture helper scaffold into the given module path.

    Supports helper snippets like Repository, Unit of Work, Service Layer,
    Message Bus, Domain Events, CQRS, MVC, Hexagonal, etc., if available in
    implementors. Falls back gracefully when snippets aren't present.
    """
    key = name.strip().lower()
    # Normalize common aliases to implementor keys when possible
    arch_aliases: dict[str, str] = {
        "uow": "unit_of_work",
        "unit of work": "unit_of_work",
        "service layer": "service_layer",
        "message bus": "message_bus",
        "domain events": "domain_events",
        "hexagonal": "hexagonal",
        "ports and adapters": "hexagonal",
        "three tier": "three_tier",
        "3 tier": "three_tier",
        "3-tier": "three_tier",
    }
    key = arch_aliases.get(key, key)
    # Let implementors map architecture aliases dynamically
    norm = key

    p = Path(module_path)
    target = Path(out_path) if out_path else p
    base_parent = target if p.is_dir() else (target.parent if out_path else p.parent)
    if not base_parent.exists():
        return {"error": f"Parent directory does not exist: {base_parent}"}

    # Try transform first
    try:
        from mcp_architecton.snippets import transform_code  # type: ignore
    except Exception:
        transform_code = None  # type: ignore[assignment]

    try:
        # Directory-wide mode
        if p.is_dir() or (out_path and target.is_dir()):
            changed: list[dict[str, str]] = []
            src_root = p if p.is_dir() else (target if target.is_dir() else p)
            dst_root = Path(out_path) if out_path else src_root
            for src in sorted(src_root.rglob("*.py")):
                rel = src.relative_to(src_root)
                dst = dst_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                original = src.read_text()
                rewritten: str | None = (
                    transform_code(norm, original) if transform_code is not None else None
                )  # type: ignore[call-arg]
                post = rewritten or original
                if post != original:
                    if not dry_run:
                        dst.write_text(post)
                    diff = "".join(
                        difflib.unified_diff(
                            original.splitlines(keepends=True),
                            post.splitlines(keepends=True),
                            fromfile=str(src),
                            tofile=str(dst),
                        )
                    )
                    changed.append({"path": str(dst), "diff": diff})
            if not changed:
                # If no transforms occurred, create a new scaffold module in dst_root
                snippet = get_snippet(norm)
                if snippet:
                    new_file = (Path(out_path) if out_path else src_root) / f"{norm}.py"
                    if not dry_run:
                        new_file.parent.mkdir(parents=True, exist_ok=True)
                        new_file.write_text(snippet)
                    diff = "".join(
                        difflib.unified_diff(
                            [],
                            snippet.splitlines(keepends=True),
                            fromfile=str(new_file),
                            tofile=str(new_file),
                        )
                    )
                    changed.append({"path": str(new_file), "diff": diff})
            return {
                "status": "ok",
                "written": str(target),
                "mode": "transformed-dir" if changed else "created-new",
                "dry_run": dry_run,
                "changes": changed,
            }

        # Determine an existing FILE path (avoid directories triggering read_text errors)
        existing_path = None
        try:
            if p.exists() and p.is_file():
                existing_path = p
            elif target.exists() and target.is_file():
                existing_path = target
        except Exception:
            existing_path = None

        if existing_path is not None and transform_code is not None:
            original = existing_path.read_text()
            rewritten: str | None = transform_code(norm, original)  # type: ignore[call-arg]
            if isinstance(rewritten, str) and rewritten.strip() and rewritten != original:
                post = cast(str, (transform_code(norm, rewritten) or rewritten))  # type: ignore[call-arg]
                if not dry_run:
                    target.write_text(post)
                diff = "".join(
                    difflib.unified_diff(
                        original.splitlines(keepends=True),
                        post.splitlines(keepends=True),
                        fromfile=str(existing_path),
                        tofile=str(target),
                    )
                )
                return {
                    "status": "ok",
                    "written": str(target),
                    "mode": "transformed" if not out_path else "transformed-new",
                    "dry_run": dry_run,
                    "diff": diff,
                }

        snippet = get_snippet(norm)
        if snippet is None:
            return {"error": f"Architecture not supported: {name}"}

        if existing_path is not None:
            original = existing_path.read_text()
            updated = original + ("\n\n" if not original.endswith("\n") else "\n") + snippet
            post = cast(str, (transform_code(norm, updated) or updated))  # type: ignore[call-arg]
            if not dry_run:
                target.write_text(post)
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    post.splitlines(keepends=True),
                    fromfile=str(existing_path),
                    tofile=str(target),
                )
            )
            return {
                "status": "ok",
                "written": str(target),
                "mode": "scaffold-appended" if not out_path else "scaffold-appended-new",
                "dry_run": dry_run,
                "diff": diff,
            }
        else:
            post = cast(str, (transform_code(norm, snippet) or snippet))  # type: ignore[call-arg]
            if not dry_run:
                target.write_text(post)
            diff = "".join(
                difflib.unified_diff(
                    [],
                    post.splitlines(keepends=True),
                    fromfile=str(target),
                    tofile=str(target),
                )
            )
            return {
                "status": "ok",
                "written": str(target),
                "mode": "created" if not out_path else "created-new",
                "dry_run": dry_run,
                "diff": diff,
            }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    return {"status": "ok", "written": str(target), "dry_run": dry_run}


def suggest_pattern_refactor_impl(code: str) -> dict[str, Any]:
    """Suggest refactors toward canonical implementations for detected patterns."""
    findings = analyze_code_for_patterns(code, detector_registry)
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for f in findings:
        raw_name = str(f.get("name", ""))
        canon = _canonical_pattern_name(raw_name)
        if not canon:
            continue
        if canon in seen:
            continue
        seen.add(canon)
        advice = _pattern_advice().get(canon, None)
        if advice:
            suggestions.append({"pattern": canon, "advice": advice})
    return {"suggestions": suggestions}


def suggest_architecture_refactor_impl(code: str) -> dict[str, Any]:
    """Suggest refactors for detected architecture styles."""
    findings = analyze_architectures_impl(code=code).get("findings", [])
    suggestions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for f in findings:
        raw_name = str(f.get("name", ""))
        canon = _canonical_arch_name(raw_name)
        if not canon or canon in seen:
            continue
        seen.add(canon)
        advice = _arch_advice().get(canon, None)
        if advice:
            suggestions.append({"architecture": canon, "advice": advice})
    return {"suggestions": suggestions}


def scan_anti_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Scan for anti-pattern indicators and map to pattern/architecture recommendations.

    Returns per-source: metrics (CC/MI/LOC), indicators, and suggested patterns/architectures.
    """
    try:
        from radon.complexity import cc_visit  # type: ignore
        from radon.metrics import mi_visit  # type: ignore
        from radon.raw import analyze as raw_analyze  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"error": f"radon not available: {exc}"}

    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    texts: list[tuple[str, str]] = []
    if code:
        texts.append(("<input>", code))
    if files:
        for f in files:
            p = Path(f)
            try:
                texts.append((str(p), p.read_text()))
            except Exception as exc:  # noqa: BLE001
                texts.append((str(p), f"<read-error: {exc}>"))

    def _indicators_for_text(text: str) -> tuple[list[dict[str, Any]], list[str]]:
        ind: list[dict[str, Any]] = []
        recs: list[str] = []
        # Cyclomatic complexity
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            hi_cc = [o for o in cc_objs if getattr(o, "complexity", 0) >= 10]
            if hi_cc:
                ind.append({"type": "high_cc", "count": len(hi_cc)})
                recs.append("Strategy or Template Method to split complex logic")
        except Exception:
            pass

        # Maintainability index (single score)
        try:
            mi_val = mi_visit(text, multi=False)  # type: ignore[misc]
            try:
                if float(mi_val) < 50.0:
                    ind.append({"type": "low_mi", "mi": mi_val})
                    recs.append("Refactor to smaller functions; apply Strategy/Facade")
            except Exception:
                pass
        except Exception:
            pass

        # Raw metrics
        try:
            raw_val = raw_analyze(text)  # type: ignore[misc]
            raw_any = cast(Any, raw_val)
            loc = getattr(raw_any, "loc", 0)
            if isinstance(loc, int) and loc > 1000:
                ind.append({"type": "large_file", "loc": loc})
                recs.append("Split module by responsibility; consider Layered/MVC separation")
        except Exception:
            pass

        # Heuristic anti-signals
        if "global " in text or "from typing import Any" in text:
            ind.append({"type": "global_or_any_usage"})
            recs.append("Introduce DI/Facade; reduce global state and Any")
        if "eval(" in text or "exec(" in text:
            ind.append({"type": "dynamic_eval"})
            recs.append("Avoid eval/exec; use Strategy/Factory")
        if "print(" in text and ("logging" not in text):
            ind.append({"type": "print_logging"})
            recs.append("Use logging; keep IO at edges (Hexagonal)")

        # Very large functions (simple heuristic)
        for block in text.split("\n\n"):
            lines = block.splitlines()
            if len(lines) > 80 and any(line.strip().startswith("def ") for line in lines[:3]):
                ind.append({"type": "very_large_function", "lines": len(lines)})
                recs.append("Extract methods (Template Method) or strategies")
                break

        # Map duplicate recommendations once
        uniq_recs: list[str] = []
        seen_local: set[str] = set()
        for r in recs:
            if r not in seen_local:
                seen_local.add(r)
                uniq_recs.append(r)
        return ind, uniq_recs

    results: list[dict[str, Any]] = []
    for label, text in texts:
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            cc: list[dict[str, Any]] = []
            for obj in cc_objs:
                cc.append(
                    {
                        "name": getattr(obj, "name", ""),
                        "type": getattr(obj, "kind", ""),
                        "complexity": getattr(obj, "complexity", None),
                        "lineno": getattr(obj, "lineno", None),
                    }
                )
            mi: Any = mi_visit(text, multi=True)  # type: ignore[misc]
            raw_val = raw_analyze(text)  # type: ignore[misc]
            indicators, recommendations = _indicators_for_text(text)
            results.append(
                {
                    "source": label,
                    "metrics": {
                        "cyclomatic_complexity": cc,
                        "maintainability_index": mi,
                        "raw": {
                            "loc": getattr(cast(Any, raw_val), "loc", None),
                            "lloc": getattr(cast(Any, raw_val), "lloc", None),
                            "sloc": getattr(cast(Any, raw_val), "sloc", None),
                            "comments": getattr(cast(Any, raw_val), "comments", None),
                            "multi": getattr(cast(Any, raw_val), "multi", None),
                        },
                    },
                    "indicators": indicators,
                    "recommendations": recommendations,
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"source": label, "error": str(exc)})

    return {"results": results}


def analyze_paths_impl(paths: list[str], include_metrics: bool = False) -> dict[str, Any]:
    """Analyze one or more paths (files/dirs/globs) for patterns/architectures.

    - paths: file paths, directory paths, or glob patterns
    - include_metrics: if True, include radon metrics per file
    """
    if not paths:
        return {"error": "Provide non-empty 'paths'"}

    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if any(ch in p for ch in "*?[]"):
            # glob pattern
            for m in pp.parent.glob(pp.name):
                if m.is_file() and m.suffix == ".py":
                    files.append(m)
        elif pp.is_dir():
            for f in pp.rglob("*.py"):
                if f.is_file():
                    files.append(f)
        elif pp.is_file() and pp.suffix == ".py":
            files.append(pp)

    unique_files: list[Path] = []
    seen: set[str] = set()
    for f in files:
        s = str(f.resolve())
        if s not in seen:
            seen.add(s)
            unique_files.append(f)

    findings: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []

    # Optional radon imports
    if include_metrics:
        try:
            from radon.complexity import cc_visit  # type: ignore
            from radon.metrics import mi_visit  # type: ignore
            from radon.raw import analyze as raw_analyze  # type: ignore
        except Exception as exc:  # noqa: BLE001
            return {"error": f"radon not available: {exc}"}

    for f in unique_files:
        try:
            text = f.read_text()
        except Exception as exc:  # noqa: BLE001
            findings.append({"source": str(f), "error": f"<read-error: {exc}>"})
            continue
        for r in analyze_code_for_patterns(text, detector_registry):
            r["source"] = str(f)
            findings.append(r)

        if include_metrics:
            try:
                cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
                cc: list[dict[str, Any]] = []
                for obj in cc_objs:
                    cc.append(
                        {
                            "name": getattr(obj, "name", ""),
                            "type": getattr(obj, "kind", ""),
                            "complexity": getattr(obj, "complexity", None),
                            "lineno": getattr(obj, "lineno", None),
                        }
                    )
                mi: Any = mi_visit(text, multi=True)  # type: ignore[misc]
                raw_val = raw_analyze(text)  # type: ignore[misc]
                raw = cast(Any, raw_val)
                metrics.append(
                    {
                        "source": str(f),
                        "cyclomatic_complexity": cc,
                        "maintainability_index": mi,
                        "raw": {
                            "loc": getattr(raw, "loc", None),
                            "lloc": getattr(raw, "lloc", None),
                            "sloc": getattr(raw, "sloc", None),
                            "comments": getattr(raw, "comments", None),
                            "multi": getattr(raw, "multi", None),
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001
                metrics.append({"source": str(f), "error": str(exc)})

    result: dict[str, Any] = {"findings": findings}
    if include_metrics:
        result["metrics"] = metrics
    return result


def propose_architecture_impl(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Produce a unified architecture and pattern proposal.

    Runs pattern/architecture detectors, Radon metrics, Ruff, and
    enforcement ranking to generate prioritized suggestions with prompts.
    """
    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    # Collect core analyses with graceful failure for optional tools
    pat: dict[str, Any] = analyze_patterns_impl(code=code, files=files)
    arch: dict[str, Any] = analyze_architectures_impl(code=code, files=files)
    metrics_res: dict[str, Any] = analyze_metrics_impl(code=code, files=files)
    enforce: dict[str, Any] = _thresholded_enforcement(
        code=code, files=files, max_suggestions=max_suggestions
    )

    # Summaries
    pat_findings_raw = pat.get("findings", [])
    pat_findings: list[dict[str, Any]] = []
    if isinstance(pat_findings_raw, list):
        for obj in cast(list[object], pat_findings_raw):
            if isinstance(obj, dict):
                pat_findings.append(cast(dict[str, Any], obj))
    detected_patterns: list[str] = sorted(
        {str(f.get("name", "")) for f in pat_findings if f.get("name")}
    )

    arch_findings_raw = arch.get("findings", [])
    arch_findings: list[dict[str, Any]] = []
    if isinstance(arch_findings_raw, list):
        for obj in cast(list[object], arch_findings_raw):
            if isinstance(obj, dict):
                arch_findings.append(cast(dict[str, Any], obj))
    detected_architectures: list[str] = sorted(
        {str(f.get("name", "")) for f in arch_findings if f.get("name")}
    )

    # Aggregate Ruff counts across files from metrics
    ruff_summary: dict[str, int] = {}
    ruff_metrics = cast(dict[str, Any], metrics_res.get("ruff", {}))
    results_any = ruff_metrics.get("results", [])
    if isinstance(results_any, list):
        for entry in cast(list[object], results_any):
            if isinstance(entry, dict):
                ed = cast(dict[str, Any], entry)
                counts_any = ed.get("counts", {})
                counts_dict = (
                    cast(dict[str, Any], counts_any) if isinstance(counts_any, dict) else {}
                )
                for code_key, cnt in counts_dict.items():
                    try:
                        ruff_summary[str(code_key)] = ruff_summary.get(str(code_key), 0) + int(cnt)
                    except Exception:
                        pass

    # Anti-pattern indicators snapshot (first source if present)
    anti_indicators: list[dict[str, Any]] = []
    if isinstance(enforce.get("results"), list):
        enforced_list = cast(list[object], enforce.get("results", []))
        if enforced_list and isinstance(enforced_list[0], dict):
            first = cast(dict[str, Any], enforced_list[0])
            anti_indicators = cast(list[dict[str, Any]], first.get("indicators", []))

    # Proposal suggestions
    suggestions: list[dict[str, Any]] = []
    if isinstance(enforce.get("results"), list):
        all_sug: list[dict[str, Any]] = []
        for entry in cast(list[object], enforce.get("results", [])):
            if isinstance(entry, dict):
                ed = cast(dict[str, Any], entry)
                sug_any = ed.get("suggestions", [])
                if isinstance(sug_any, list):
                    for s in cast(list[object], sug_any):
                        if isinstance(s, dict):
                            all_sug.append(cast(dict[str, Any], s))
        # dedupe by target keeping highest weight
        best: dict[str, dict[str, Any]] = {}
        for s in all_sug:
            t = str(s.get("target", ""))
            cur = best.get(t)
            if not cur or int(s.get("weight", 0)) > int(cur.get("weight", 0)):
                best[t] = s
        suggestions = sorted(
            best.values(), key=lambda x: (-int(x.get("weight", 0)), str(x.get("target", "")))
        )
        if max_suggestions and max_suggestions > 0:
            suggestions = suggestions[:max_suggestions]

    return {
        "summary": {
            "patterns_detected": detected_patterns,
            "architectures_detected": detected_architectures,
            "ruff_rule_counts": ruff_summary,
            "anti_indicators": anti_indicators,
        },
        "proposal": {
            "suggestions": suggestions,
        },
        "raw": {
            "patterns": pat,
            "architectures": arch,
            "metrics": metrics_res,
            "ruff": ruff_metrics,
        },
    }


def propose_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Produce a unified pattern-focused proposal.

    Reuses propose_architecture and filters suggestions to Patterns only.
    """
    base: dict[str, Any] = propose_architecture_impl(
        code=code, files=files, max_suggestions=max_suggestions
    )
    if "error" in base:
        return base
    proposal = cast(dict[str, Any], base.get("proposal", {}))
    suggestions_raw = proposal.get("suggestions", [])
    suggestions: list[dict[str, Any]] = []
    if isinstance(suggestions_raw, list):
        for s in cast(list[object], suggestions_raw):
            if isinstance(s, dict):
                sd = cast(dict[str, Any], s)
                if str(sd.get("category", "")) == "Pattern":
                    suggestions.append(sd)
    summary = cast(dict[str, Any], base.get("summary", {}))
    return {
        "summary": {
            "patterns_detected": summary.get("patterns_detected", []),
            "ruff_rule_counts": summary.get("ruff_rule_counts", {}),
            "anti_indicators": summary.get("anti_indicators", []),
        },
        "proposal": {
            "suggestions": suggestions[
                : max_suggestions if max_suggestions and max_suggestions > 0 else 5
            ]
        },
        "raw": base.get("raw", {}),
    }


# (canonical implementation defined above)


@app.tool(name="list-patterns")
def tool_list_patterns() -> list[dict[str, Any]]:
    """List available design patterns with metadata from the catalog."""
    return list_patterns_impl()


def list_patterns() -> list[dict[str, Any]]:
    return list_patterns_impl()


@app.tool(name="analyze-patterns")
def tool_analyze_patterns(
    code: str | None = None, files: list[str] | None = None
) -> dict[str, Any]:
    """Detect design patterns in a code string or Python files (provide code or files)."""
    return analyze_patterns_impl(code=code, files=files)


def analyze_patterns(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    return analyze_patterns_impl(code=code, files=files)


@app.tool(name="analyze-metrics")
def tool_analyze_metrics(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    """Compute Radon metrics (CC/MI/LOC) and aggregate Ruff issues for code or files."""
    return analyze_metrics_impl(code=code, files=files)


def analyze_metrics(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    return analyze_metrics_impl(code=code, files=files)


@app.tool(name="list-architectures")
def tool_list_architectures() -> list[dict[str, Any]]:
    """List recognized software architectures from the catalog."""
    return list_architectures_impl()


def list_architectures() -> list[dict[str, Any]]:
    return list_architectures_impl()


@app.tool(name="analyze-architectures")
def tool_analyze_architectures(
    code: str | None = None, files: list[str] | None = None
) -> dict[str, Any]:
    """Detect architecture styles in a code string or Python files (provide code or files)."""
    return analyze_architectures_impl(code=code, files=files)


def analyze_architectures(
    code: str | None = None, files: list[str] | None = None
) -> dict[str, Any]:
    return analyze_architectures_impl(code=code, files=files)


@app.tool(name="introduce-pattern")
def tool_introduce_pattern(
    name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    """Create/append a scaffold for the named pattern into module_path.

    Optional: dry_run (no writes) and out_path to write to a different file (e.g., refactor-as-new).
    """
    return introduce_pattern_impl(
        name=name, module_path=module_path, dry_run=dry_run, out_path=out_path
    )


def introduce_pattern(
    name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    return introduce_pattern_impl(
        name=name, module_path=module_path, dry_run=dry_run, out_path=out_path
    )


@app.tool(name="introduce-architecture")
def tool_introduce_architecture(
    name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    """Create/append a scaffold for the named architecture helper into module_path.

    Optional: dry_run (no writes) and out_path to write to a different file.
    """
    return introduce_architecture_impl(
        name=name, module_path=module_path, dry_run=dry_run, out_path=out_path
    )


def introduce_architecture(
    name: str, module_path: str, dry_run: bool = False, out_path: str | None = None
) -> dict[str, Any]:
    return introduce_architecture_impl(
        name=name, module_path=module_path, dry_run=dry_run, out_path=out_path
    )


@app.tool(name="suggest-refactor-patterns")
def tool_suggest_refactor_patterns(code: str) -> dict[str, Any]:
    """Suggest refactors for detected patterns (alias of suggest_refactor)."""
    return suggest_pattern_refactor_impl(code)


def suggest_refactor_patterns(code: str) -> dict[str, Any]:
    return suggest_pattern_refactor_impl(code)


@app.tool(name="suggest-architecture-refactor")
def tool_suggest_architecture_refactor(code: str) -> dict[str, Any]:
    """Suggest architectural refactors based on detected architecture styles."""
    return suggest_architecture_refactor_impl(code)


def suggest_architecture_refactor(code: str) -> dict[str, Any]:
    return suggest_architecture_refactor_impl(code)


@app.tool(name="scan-anti-patterns")
def tool_scan_anti_patterns(
    code: str | None = None, files: list[str] | None = None
) -> dict[str, Any]:
    """Scan for anti-pattern indicators and map to pattern/architecture recommendations."""
    return scan_anti_patterns_impl(code=code, files=files)


def scan_anti_patterns(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    return scan_anti_patterns_impl(code=code, files=files)


@app.tool(name="analyze-paths")
def tool_analyze_paths(paths: list[str], include_metrics: bool = False) -> dict[str, Any]:
    """Analyze Python files under paths (files/dirs/globs) for patterns; optionally include metrics."""
    return analyze_paths_impl(paths=paths, include_metrics=include_metrics)


def analyze_paths(paths: list[str], include_metrics: bool = False) -> dict[str, Any]:
    return analyze_paths_impl(paths=paths, include_metrics=include_metrics)


@app.tool(name="propose-architecture")
def tool_propose_architecture(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 5
) -> dict[str, Any]:
    """Build a prioritized proposal (patterns + architectures) using detectors, metrics, Ruff, and enforcement."""
    return propose_architecture_impl(code=code, files=files, max_suggestions=max_suggestions)


def propose_architecture(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 5
) -> dict[str, Any]:
    return propose_architecture_impl(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="propose-patterns")
def tool_propose_patterns(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 5
) -> dict[str, Any]:
    """Produce a pattern-focused proposal filtered from the unified proposal."""
    return propose_patterns_impl(code=code, files=files, max_suggestions=max_suggestions)


def propose_patterns(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 5
) -> dict[str, Any]:
    return propose_patterns_impl(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="thresholded-enforcement")
def tool_thresholded_enforcement(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 3
) -> dict[str, Any]:
    """Rank anti-pattern indicators and return top enforcement prompts with reasons."""
    return _thresholded_enforcement(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="scan-anti-architectures")
def tool_scan_anti_architectures(
    code: str | None = None, files: list[str] | None = None, max_suggestions: int = 5
) -> dict[str, Any]:
    """Scan like thresholded_enforcement but return only architecture suggestions per source."""
    base: dict[str, Any] = _thresholded_enforcement(
        code=code, files=files, max_suggestions=max_suggestions
    )
    if "error" in base:
        return base
    results_out: list[dict[str, Any]] = []
    raw_results = base.get("results", [])
    if isinstance(raw_results, list):
        for entry in cast(list[object], raw_results):
            if not isinstance(entry, dict):
                continue
            ed = cast(dict[str, Any], entry)
            arch_sug: list[dict[str, Any]] = []
            sug_raw = ed.get("suggestions", [])
            if isinstance(sug_raw, list):
                for s in cast(list[object], sug_raw):
                    if isinstance(s, dict):
                        sd = cast(dict[str, Any], s)
                        if str(sd.get("category", "")) == "Architecture":
                            arch_sug.append(sd)
            results_out.append(
                {
                    "source": ed.get("source"),
                    "metrics": ed.get("metrics"),
                    "indicators": ed.get("indicators"),
                    "suggestions": arch_sug[
                        : max_suggestions if max_suggestions and max_suggestions > 0 else 5
                    ],
                }
            )
    return {"results": results_out}


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Run the FastMCP server
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
