from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from mcp_architecton.analysis.advice_loader import build_advice_maps
from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.analysis.enforcement import ranked_enforcement_targets
from mcp_architecton.detectors import registry as detector_registry
from mcp_architecton.generators.refactor_generator import introduce_impl
from mcp_architecton.services.scan import scan_anti_patterns_impl
from mcp_architecton.snippets.aliases import NAME_ALIASES as _impl_aliases_src


def _canon(name: str) -> str:
    raw = (name or "").strip().lower()
    return _impl_aliases_src.get(raw, raw)


def _iter_py_files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        pp = Path(p)
        if any(ch in p for ch in "*?[]"):
            # glob pattern
            for m in pp.parent.glob(pp.name):
                if m.is_file() and m.suffix == ".py":
                    out.append(m)
        elif pp.is_dir():
            out.extend([f for f in pp.rglob("*.py") if f.is_file()])
        elif pp.is_file() and pp.suffix == ".py":
            out.append(pp)
    # dedupe
    seen: set[str] = set()
    uniq: list[Path] = []
    for f in out:
        s = str(f.resolve())
        if s not in seen:
            seen.add(s)
            uniq.append(f)
    return uniq


def _simplify(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _files_matching_target(files: list[Path], target_name: str) -> list[Path]:
    wanted = (target_name or "").strip().lower()
    wanted_s = _simplify(wanted)
    hits: list[Path] = []
    for f in files:
        try:
            text = f.read_text()
        except Exception:
            continue
        try:
            results = analyze_code_for_patterns(text, detector_registry)
        except Exception:
            results = []
        for r in results:
            rname = str(r.get("name", "")).strip().lower()
            r_s = _simplify(rname)
            # Accept direct match, simplified match, or match after stripping common suffixes
            base_arch = rname.replace(" architecture", "").strip()
            base_s = _simplify(base_arch)
            if rname == wanted or r_s == wanted_s or base_s == wanted_s:
                hits.append(f)
                break
    return hits


def enforce_target_impl(
    *,
    name: str,
    paths: list[str],
    scope: str = "hits",  # "hits" | "all"
    dry_run: bool = True,
    out_dir: str | None = None,
    max_files: int | None = None,
) -> dict[str, Any]:
    """Enforce a specific pattern/architecture across given paths.

    - Normalizes the name with aliases
    - Scopes to detector hits by default
    - Applies introduce_impl per-file (diffs aggregated)
    """
    if not paths:
        return {"status": "error", "error": "Provide non-empty 'paths'"}

    canon = _canon(name)
    _, arch_map = build_advice_maps()
    category = "Architecture" if canon in arch_map else "Pattern"

    all_files = _iter_py_files(paths)
    if not all_files:
        return {"status": "ok", "category": category, "changes": []}

    selected = _files_matching_target(all_files, canon) if scope == "hits" else list(all_files)
    if max_files is not None and max_files > 0:
        selected = selected[:max_files]

    changes: list[dict[str, Any]] = []
    for f in selected:
        out_path_arg: str | None = None
        if out_dir:
            out_path_arg = str(Path(out_dir) / f.name)
        res = introduce_impl(name=canon, module_path=str(f), dry_run=dry_run, out_path=out_path_arg)
        if "target" not in res:
            res["target"] = str(f)
        res["category"] = category
        changes.append(res)

    result: dict[str, Any] = {
        "status": "ok",
        "category": category,
        "name": canon,
        "scope": scope,
        "dry_run": dry_run,
        "paths": paths,
        "changes": changes,
    }
    if not changes:
        result["reason"] = (
            "no files matched scope or detector hits; try scope='all' or verify target name"
        )
    return result


def enforce_ranked_impl(
    *,
    paths: list[str],
    top_n: int = 3,
    scope: str = "hits",
    dry_run: bool = True,
    out_dir: str | None = None,
) -> dict[str, Any]:
    """Scan for anti-pattern indicators, rank targets, and enforce top-N."""
    if not paths:
        return {"status": "error", "error": "Provide non-empty 'paths'"}

    files = _iter_py_files(paths)

    scan_res = scan_anti_patterns_impl(files=[str(f) for f in files])
    indicators: list[dict[str, Any]] = []
    recs: list[str] = []
    results_any = scan_res.get("results", [])
    if isinstance(results_any, list):
        for entry in cast("list[object]", results_any):
            if not isinstance(entry, dict):
                continue
            ed = cast("dict[str, Any]", entry)
            if isinstance(ed.get("indicators"), list):
                indicators.extend(cast("list[dict[str, Any]]", ed["indicators"]))
            if isinstance(ed.get("recommendations"), list):
                recs.extend([str(x) for x in cast("list[Any]", ed["recommendations"])])

    pat_map, arch_map = build_advice_maps()
    ranked = ranked_enforcement_targets(indicators, recs, pat_map, arch_map, _impl_aliases_src)
    chosen = ranked[: top_n if top_n and top_n > 0 else 3]

    applied: list[dict[str, Any]] = []
    for tgt_name, _category, weight, reasons in chosen:
        res = enforce_target_impl(
            name=tgt_name,
            paths=paths,
            scope=scope,
            dry_run=dry_run,
            out_dir=out_dir,
        )
        res["weight"] = weight
        res["reasons"] = reasons
        applied.append(res)

    return {
        "status": "ok",
        "paths": paths,
        "top_n": top_n,
        "dry_run": dry_run,
        "scope": scope,
        "applied": applied,
    }


__all__ = ["enforce_ranked_impl", "enforce_target_impl"]
