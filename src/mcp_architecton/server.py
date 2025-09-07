from __future__ import annotations
# ruff: noqa: I001

import logging
from pathlib import Path
import sys
from typing import Any, cast

from fastmcp import FastMCP  # type: ignore[import-not-found]

from mcp_architecton.analysis.advice_loader import build_advice_maps
from mcp_architecton.analysis.enforcement import ranked_enforcement_targets
from mcp_architecton.analysis.typehint_transformer import add_type_hints_to_code
from mcp_architecton.services.architectures import (
    analyze_architectures_impl as svc_analyze_architectures_impl,
    list_architectures_impl as svc_list_architectures_impl,
)
from mcp_architecton.services.metrics import analyze_metrics_impl as svc_analyze_metrics_impl
from mcp_architecton.services.patterns import (
    analyze_patterns_impl as svc_analyze_patterns_impl,
    list_patterns_impl as svc_list_patterns_impl,
)
from mcp_architecton.services.scan import scan_anti_patterns_impl as svc_scan_anti_patterns_impl
from mcp_architecton.services.enforce import (
    enforce_target_impl as svc_enforce_target_impl,
    enforce_ranked_impl as svc_enforce_ranked_impl,
)
from mcp_architecton.services.refactors import (
    list_refactorings_impl as svc_list_refactorings_impl,
)
from mcp_architecton.generators.refactor_generator import (
    introduce_pattern_impl,
    introduce_architecture_impl,
)

from mcp_architecton.snippets.aliases import (
    NAME_ALIASES,
    canonicalize_name,
)

# Configure logging for the server module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


# MCP server symbol (used by clients as the server name)
app: FastMCP = FastMCP("Architecton")


def _ranked_enforcement_targets(
    indicators: list[dict[str, Any]],
    recs: list[str],
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
    entries_list: list[Any] = (
        cast("list[Any]", raw_entries) if isinstance(raw_entries, list) else []
    )
    for entry in entries_list:
        if not isinstance(entry, dict):
            continue
        entry_d = cast("dict[str, Any]", entry)
        indicators_val = entry_d.get("indicators", [])
        indicators_list: list[dict[str, Any]] = []
        if isinstance(indicators_val, list):
            for i in cast("list[object]", indicators_val):
                if isinstance(i, dict):
                    indicators_list.append(cast("dict[str, Any]", i))
        recs_val = entry_d.get("recommendations", [])
        recs_list: list[str] = []
        if isinstance(recs_val, list):
            for x in cast("list[object]", recs_val):
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
                },
            )
        results.append(
            {
                "source": entry_d.get("source"),
                "metrics": entry_d.get("metrics"),
                "indicators": indicators_list,
                "suggestions": suggestions,
            },
        )
    return {"results": results}


def _canonical_pattern_name(name: str | None) -> str:
    """Return a normalized canonical pattern name using alias map when available."""
    return canonicalize_name(name)


def _canonical_arch_name(name: str | None) -> str:
    """Return a normalized canonical architecture name using alias map when available."""
    return canonicalize_name(name)


def list_patterns_impl() -> list[dict[str, Any]]:
    return svc_list_patterns_impl()


def analyze_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    return svc_analyze_patterns_impl(code=code, files=files)


def analyze_metrics_impl(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    return svc_analyze_metrics_impl(code=code, files=files)


def list_architectures_impl() -> list[dict[str, Any]]:
    return svc_list_architectures_impl()


def analyze_architectures_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    return svc_analyze_architectures_impl(code=code, files=files)


def suggest_pattern_refactor_impl(code: str) -> dict[str, Any]:
    """Suggest refactors toward canonical implementations for detected patterns."""
    findings = svc_analyze_patterns_impl(code=code).get("findings", [])
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
    # If empty, offer a lightweight generic suggestion using advice defaults
    if not suggestions:
        # Provide top 3 generic pattern prompts if available
        pats = list(_pattern_advice().items())[:3]
        suggestions = [{"pattern": k, "advice": v} for k, v in pats]
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
    if not suggestions:
        archs = list(_arch_advice().items())[:3]
        suggestions = [{"architecture": k, "advice": v} for k, v in archs]
    return {"suggestions": suggestions}


def scan_anti_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    return svc_scan_anti_patterns_impl(code=code, files=files)


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
        res = svc_analyze_patterns_impl(code=text)
        for r in cast("list[dict[str, Any]]", res.get("findings", [])):
            r["source"] = r.get("source") or str(f)
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
                        },
                    )
                mi: Any = mi_visit(text, multi=True)  # type: ignore[misc]
                raw_val = raw_analyze(text)  # type: ignore[misc]
                raw = cast("Any", raw_val)
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
                    },
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
        code=code,
        files=files,
        max_suggestions=max_suggestions,
    )

    # Summaries
    pat_findings_raw = pat.get("findings", [])
    pat_findings: list[dict[str, Any]] = []
    if isinstance(pat_findings_raw, list):
        for obj in cast("list[object]", pat_findings_raw):
            if isinstance(obj, dict):
                pat_findings.append(cast("dict[str, Any]", obj))
    detected_patterns: list[str] = sorted(
        {str(f.get("name", "")) for f in pat_findings if f.get("name")},
    )

    arch_findings_raw = arch.get("findings", [])
    arch_findings: list[dict[str, Any]] = []
    if isinstance(arch_findings_raw, list):
        for obj in cast("list[object]", arch_findings_raw):
            if isinstance(obj, dict):
                arch_findings.append(cast("dict[str, Any]", obj))
    detected_architectures: list[str] = sorted(
        {str(f.get("name", "")) for f in arch_findings if f.get("name")},
    )

    # Aggregate Ruff counts across files from metrics
    ruff_summary: dict[str, int] = {}
    ruff_metrics = cast("dict[str, Any]", metrics_res.get("ruff", {}))
    results_any = ruff_metrics.get("results", [])
    if isinstance(results_any, list):
        for entry in cast("list[object]", results_any):
            if isinstance(entry, dict):
                ed = cast("dict[str, Any]", entry)
                counts_any = ed.get("counts", {})
                counts_dict = (
                    cast("dict[str, Any]", counts_any) if isinstance(counts_any, dict) else {}
                )
                for code_key, cnt in counts_dict.items():
                    try:
                        ruff_summary[str(code_key)] = ruff_summary.get(str(code_key), 0) + int(cnt)
                    except (ValueError, TypeError):
                        # Skip non-numeric counts
                        pass

    # Anti-pattern indicators snapshot (first source if present)
    anti_indicators: list[dict[str, Any]] = []
    if isinstance(enforce.get("results"), list):
        enforced_list = cast("list[object]", enforce.get("results", []))
        if enforced_list and isinstance(enforced_list[0], dict):
            first = cast("dict[str, Any]", enforced_list[0])
            anti_indicators = cast("list[dict[str, Any]]", first.get("indicators", []))

    # Proposal suggestions
    suggestions: list[dict[str, Any]] = []
    if isinstance(enforce.get("results"), list):
        all_sug: list[dict[str, Any]] = []
        for entry in cast("list[object]", enforce.get("results", [])):
            if isinstance(entry, dict):
                ed = cast("dict[str, Any]", entry)
                sug_any = ed.get("suggestions", [])
                if isinstance(sug_any, list):
                    for s in cast("list[object]", sug_any):
                        if isinstance(s, dict):
                            all_sug.append(cast("dict[str, Any]", s))
        # dedupe by target keeping highest weight
        best: dict[str, dict[str, Any]] = {}
        for s in all_sug:
            t = str(s.get("target", ""))
            cur = best.get(t)
            if not cur or int(s.get("weight", 0)) > int(cur.get("weight", 0)):
                best[t] = s
        suggestions = sorted(
            best.values(),
            key=lambda x: (-int(x.get("weight", 0)), str(x.get("target", ""))),
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
        code=code,
        files=files,
        max_suggestions=max_suggestions,
    )
    if "error" in base:
        return base
    proposal = cast("dict[str, Any]", base.get("proposal", {}))
    suggestions_raw = proposal.get("suggestions", [])
    suggestions: list[dict[str, Any]] = []
    if isinstance(suggestions_raw, list):
        for s in cast("list[object]", suggestions_raw):
            if isinstance(s, dict):
                sd = cast("dict[str, Any]", s)
                if str(sd.get("category", "")) == "Pattern":
                    suggestions.append(sd)
    summary = cast("dict[str, Any]", base.get("summary", {}))
    return {
        "summary": {
            "patterns_detected": summary.get("patterns_detected", []),
            "ruff_rule_counts": summary.get("ruff_rule_counts", {}),
            "anti_indicators": summary.get("anti_indicators", []),
        },
        "proposal": {
            "suggestions": suggestions[
                : max_suggestions if max_suggestions and max_suggestions > 0 else 5
            ],
        },
        "raw": base.get("raw", {}),
    }


# (canonical implementation defined above)


@app.tool(name="list-patterns")
def tool_list_patterns() -> list[dict[str, Any]]:
    """List available design patterns with metadata from the catalog."""
    return list_patterns_impl()


@app.tool(name="list-refactorings")
def tool_list_refactorings() -> list[dict[str, Any]]:
    """List refactoring techniques with URLs and prompt hints (if available)."""
    return svc_list_refactorings_impl()


@app.tool(name="analyze-patterns")
def tool_analyze_patterns(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Detect design patterns in a code string or Python files (provide code or files)."""
    return analyze_patterns_impl(code=code, files=files)


@app.tool(name="analyze-metrics")
def tool_analyze_metrics(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    """Compute Radon metrics (CC/MI/LOC) and aggregate Ruff issues for code or files."""
    return analyze_metrics_impl(code=code, files=files)


@app.tool(name="list-architectures")
def tool_list_architectures() -> list[dict[str, Any]]:
    """List recognized software architectures from the catalog."""
    return list_architectures_impl()


@app.tool(name="analyze-architectures")
def tool_analyze_architectures(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Detect architecture styles in a code string or Python files (provide code or files)."""
    return analyze_architectures_impl(code=code, files=files)


@app.tool(name="introduce-pattern")
def tool_introduce_pattern(
    name: str,
    module_path: str,
    dry_run: bool = False,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Create/append a scaffold for the named pattern into module_path.

    Optional: dry_run (no writes) and out_path to write to a different file (e.g., refactor-as-new).
    """
    return introduce_pattern_impl(
        name=name,
        module_path=module_path,
        dry_run=dry_run,
        out_path=out_path,
    )


@app.tool(name="introduce-architecture")
def tool_introduce_architecture(
    name: str,
    module_path: str,
    dry_run: bool = False,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Create/append a scaffold for the named architecture helper into module_path.

    Optional: dry_run (no writes) and out_path to write to a different file.
    """
    return introduce_architecture_impl(
        name=name,
        module_path=module_path,
        dry_run=dry_run,
        out_path=out_path,
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
    code: str | None = None,
    files: list[str] | None = None,
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
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Build a prioritized proposal (patterns + architectures) using detectors, metrics, Ruff, and enforcement."""
    return propose_architecture_impl(code=code, files=files, max_suggestions=max_suggestions)


def propose_architecture(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    return propose_architecture_impl(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="propose-patterns")
def tool_propose_patterns(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Produce a pattern-focused proposal filtered from the unified proposal."""
    return propose_patterns_impl(code=code, files=files, max_suggestions=max_suggestions)


def propose_patterns(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    return propose_patterns_impl(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="transform-add-type-hints")
def tool_transform_add_type_hints(code: str) -> dict[str, Any]:
    """Add `Any` type hints to unannotated function params/returns (idempotent)."""
    changed, out = add_type_hints_to_code(code)
    return {"changed": changed, "result": out}


@app.tool(name="thresholded-enforcement")
def tool_thresholded_enforcement(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 3,
) -> dict[str, Any]:
    """Rank anti-pattern indicators and return top enforcement prompts with reasons."""
    return _thresholded_enforcement(code=code, files=files, max_suggestions=max_suggestions)


@app.tool(name="enforce-target")
def tool_enforce_target(
    name: str,
    paths: list[str],
    scope: str = "hits",
    dry_run: bool = True,
    out_dir: str | None = None,
    max_files: int | None = None,
) -> dict[str, Any]:
    """Enforce a specific pattern/architecture across paths (per-file introduce with diffs)."""
    return svc_enforce_target_impl(
        name=name,
        paths=paths,
        scope=scope,
        dry_run=dry_run,
        out_dir=out_dir,
        max_files=max_files,
    )


@app.tool(name="enforce-ranked")
def tool_enforce_ranked(
    paths: list[str],
    top_n: int = 3,
    scope: str = "hits",
    dry_run: bool = True,
    out_dir: str | None = None,
) -> dict[str, Any]:
    """Run indicator scan, rank targets, and enforce the top-N suggestions across paths."""
    return svc_enforce_ranked_impl(
        paths=paths,
        top_n=top_n,
        scope=scope,
        dry_run=dry_run,
        out_dir=out_dir,
    )


@app.tool(name="scan-anti-architectures")
def tool_scan_anti_architectures(
    code: str | None = None,
    files: list[str] | None = None,
    max_suggestions: int = 5,
) -> dict[str, Any]:
    """Scan like thresholded_enforcement but return only architecture suggestions per source."""
    base: dict[str, Any] = _thresholded_enforcement(
        code=code,
        files=files,
        max_suggestions=max_suggestions,
    )
    if "error" in base:
        return base
    results_out: list[dict[str, Any]] = []
    raw_results = base.get("results", [])
    if isinstance(raw_results, list):
        for entry in cast("list[object]", raw_results):
            if not isinstance(entry, dict):
                continue
            ed = cast("dict[str, Any]", entry)
            arch_sug: list[dict[str, Any]] = []
            sug_raw = ed.get("suggestions", [])
            if isinstance(sug_raw, list):
                for s in cast("list[object]", sug_raw):
                    if isinstance(s, dict):
                        sd = cast("dict[str, Any]", s)
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
                },
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
