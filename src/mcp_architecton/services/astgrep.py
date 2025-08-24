from __future__ import annotations
# ruff: noqa: I001

from pathlib import Path
from typing import Any


def astgrep_search_impl(
    pattern: str | None = None,
    rule: str | None = None,
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Search code using ast-grep if available.

    - pattern: structural pattern string (sg query)
    - rule: path to a YAML rule file (optional alternative to pattern)
    - code: code string to search (exclusive with files)
    - files: list of python files to search when code is not provided

    Returns a dict with 'matches': list[dict], items include source and span info.
    If ast-grep is unavailable, returns an 'error' explaining the situation.
    """
    if not pattern and not rule:
        return {"error": "Provide 'pattern' or 'rule'"}

    try:
        # Import inside function to make dependency optional at import time
        from ast_grep_py import PythonSource  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"error": f"ast-grep-py not available: {exc}"}

    matches: list[dict[str, Any]] = []

    def _match_to_dict(m: Any, source_label: str) -> dict[str, Any]:
        try:
            span = m.range
            return {
                "source": source_label,
                "start": {
                    "row": getattr(span.start, "row", None),
                    "column": getattr(span.start, "column", None),
                },
                "end": {
                    "row": getattr(span.end, "row", None),
                    "column": getattr(span.end, "column", None),
                },
                "text": m.matched_text(),
            }
        except Exception:  # noqa: BLE001
            return {"source": source_label}

    try:
        if code is not None:
            src: Any = PythonSource(code)  # type: ignore[misc]
            found: Any = src.find(pattern) if pattern else src.find_yaml(rule or "")  # type: ignore[attr-defined]
            found_list: list[Any] = list(found or [])  # type: ignore[misc]
            for m in found_list:
                matches.append(_match_to_dict(m, "<code>"))
        else:
            file_list: list[Path] = []
            for f in files or []:
                p = Path(f)
                if p.is_file() and p.suffix == ".py":
                    file_list.append(p)
                elif p.is_dir():
                    for ff in p.rglob("*.py"):
                        if ff.is_file():
                            file_list.append(ff)
            seen: set[str] = set()
            uniq: list[Path] = []
            for f in file_list:
                s = str(f.resolve())
                if s not in seen:
                    seen.add(s)
                    uniq.append(f)
            for f in uniq:
                try:
                    text = f.read_text()
                except Exception:  # noqa: BLE001
                    continue
                src: Any = PythonSource(text)  # type: ignore[misc]
                found: Any = src.find(pattern) if pattern else src.find_yaml(rule or "")  # type: ignore[attr-defined]
                found_list: list[Any] = list(found or [])  # type: ignore[misc]
                for m in found_list:
                    matches.append(_match_to_dict(m, str(f)))
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    return {"matches": matches}


__all__ = ["astgrep_search_impl"]
