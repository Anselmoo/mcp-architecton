from __future__ import annotations

from pathlib import Path
from typing import Any, cast


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
