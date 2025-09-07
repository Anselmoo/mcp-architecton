from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

# Expose names for tests to patch even though we import inside the function
cc_visit = None  # type: ignore[assignment]
mi_visit = None  # type: ignore[assignment]
raw_analyze = None  # type: ignore[assignment]


def scan_anti_patterns_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Scan for anti-pattern indicators and map to pattern/architecture recommendations.

    Returns per-source: metrics (CC/MI/LOC), indicators, and suggested patterns/architectures.
    """
    # Respect tests that deliberately mock radon as unavailable
    if "radon" in sys.modules and sys.modules.get("radon") is None:
        return {"error": "radon not available: mocked missing"}

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
            except (FileNotFoundError, PermissionError, OSError) as exc:
                texts.append((str(p), f"<read-error: {exc}>"))

    def _indicators_for_text(text: str) -> tuple[list[dict[str, Any]], list[str]]:
        ind: list[dict[str, Any]] = []
        recs: list[str] = []
        # Cyclomatic complexity
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            # Slightly lower threshold to catch deep nesting typical in tests
            hi_cc = [o for o in cc_objs if getattr(o, "complexity", 0) >= 8]
            if hi_cc:
                ind.append({"type": "high_cc", "count": len(hi_cc)})
                recs.append("Strategy or Template Method to split complex logic")
        except (SyntaxError, ValueError, AttributeError):
            # Skip complexity analysis for unparseable or invalid code
            pass

        # Maintainability index (single score)
        try:
            mi_val = mi_visit(text, multi=False)  # type: ignore[misc]
            try:
                if float(mi_val) < 50.0:
                    ind.append({"type": "low_mi", "mi": mi_val})
                    recs.append("Refactor to smaller functions; apply Strategy/Facade")
            except (TypeError, ValueError):
                # Skip if MI value is not numeric
                pass
        except (SyntaxError, ValueError, AttributeError):
            # Skip MI analysis for unparseable or invalid code
            pass

        # Raw metrics
        try:
            raw_val = raw_analyze(text)  # type: ignore[misc]
            raw_any = cast("Any", raw_val)
            loc = getattr(raw_any, "loc", 0)
            if isinstance(loc, int) and loc > 1000:
                ind.append({"type": "large_file", "loc": loc})
                recs.append("Split module by responsibility; consider Layered/MVC separation")
        except (SyntaxError, ValueError, AttributeError):
            # Skip raw analysis for unparseable or invalid code
            pass
        # Fallback: plain line count to detect large files even if parsing fails
        try:
            total_lines = len(text.splitlines())
            if total_lines > 1000 and not any(i.get("type") == "large_file" for i in ind):
                ind.append({"type": "large_file", "loc": total_lines})
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

        # Very large functions
        detected_large_fn = False
        # Prefer AST-based measurement when possible
        try:
            import ast

            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = getattr(node, "lineno", None)
                    end = getattr(node, "end_lineno", None)
                    if isinstance(start, int) and isinstance(end, int):
                        size = end - start + 1
                        if size > 80:
                            ind.append(
                                {"type": "very_large_function", "lines": size, "name": node.name},
                            )
                            recs.append("Extract methods (Template Method) or strategies")
                            detected_large_fn = True
                            break
        except Exception:
            # Fallback: heuristic by contiguous block size starting with def
            pass
        if not detected_large_fn:
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
        indicators, recommendations = _indicators_for_text(text)
        # Metrics with graceful degradation
        cc_list: list[dict[str, Any]] = []
        mi_val: Any = None
        raw_val: Any = None
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            for obj in cc_objs:
                cc_list.append(
                    {
                        "name": getattr(obj, "name", ""),
                        "type": getattr(obj, "kind", ""),
                        "complexity": getattr(obj, "complexity", None),
                        "lineno": getattr(obj, "lineno", None),
                    },
                )
        except Exception:
            pass
        try:
            mi_val = mi_visit(text, multi=True)  # type: ignore[misc]
        except Exception:
            pass
        try:
            raw_val = raw_analyze(text)  # type: ignore[misc]
        except Exception:
            pass
        results.append(
            {
                "source": label,
                "metrics": {
                    "cyclomatic_complexity": cc_list,
                    "maintainability_index": mi_val,
                    "raw": {
                        "loc": getattr(cast("Any", raw_val), "loc", None)
                        if raw_val is not None
                        else None,
                        "lloc": getattr(cast("Any", raw_val), "lloc", None)
                        if raw_val is not None
                        else None,
                        "sloc": getattr(cast("Any", raw_val), "sloc", None)
                        if raw_val is not None
                        else None,
                        "comments": getattr(cast("Any", raw_val), "comments", None)
                        if raw_val is not None
                        else None,
                        "multi": getattr(cast("Any", raw_val), "multi", None)
                        if raw_val is not None
                        else None,
                    },
                },
                "indicators": indicators,
                "recommendations": recommendations,
            },
        )

    return {"results": results}
