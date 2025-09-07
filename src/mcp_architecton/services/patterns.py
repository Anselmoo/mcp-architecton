from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry as detector_registry


def list_patterns_impl() -> list[dict[str, Any]]:
    """List design patterns (non-architecture) from catalog if present.

    Returns empty list on any error.
    """
    # Catalog default path relative to project root
    catalog_path = Path(__file__).resolve().parents[3] / "data" / "patterns" / "catalog.json"
    try:
        if not catalog_path.exists():
            return []
        data = json.loads(catalog_path.read_text())
        items = (
            cast("list[dict[str, Any]]", data.get("patterns", [])) if isinstance(data, dict) else []
        )
        out: list[dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            # Exclude Architecture category
            if str(it.get("category", "")).lower() == "architecture":
                continue
            out.append(it)
        return out
    except Exception:
        return []


def analyze_patterns_impl(
    code: str | None = None, files: list[str] | None = None,
) -> dict[str, Any]:
    """Detect design patterns in a code string or Python files (provide code or files).

    Returns: {"findings": [...]} with 'source' on each finding. If neither input is provided,
    returns {"error": "Provide 'code' or 'files'"}.
    """
    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    findings: list[dict[str, Any]] = []

    if code is not None:
        try:
            res = analyze_code_for_patterns(code, detector_registry)
        except Exception as exc:  # noqa: BLE001
            findings.append({"source": "<input>", "error": str(exc)})
        else:
            for r in cast("list[dict[str, Any]]", res or []):
                out = dict(r)
                # Normalize key 'name' -> 'pattern' if needed
                if "pattern" not in out and "name" in out:
                    out["pattern"] = out.get("name")
                out["source"] = "<input>"
                findings.append(out)

    if files:
        for f in files:
            p = Path(f)
            try:
                text = p.read_text()
            except Exception as exc:  # noqa: BLE001
                # Still return a record with source
                findings.append({"source": str(p), "error": str(exc)})
                continue
            try:
                res = analyze_code_for_patterns(text, detector_registry)
            except Exception as exc:  # noqa: BLE001
                findings.append({"source": str(p), "error": str(exc)})
            else:
                for r in cast("list[dict[str, Any]]", res or []):
                    out = dict(r)
                    if "pattern" not in out and "name" in out:
                        out["pattern"] = out.get("name")
                    out["source"] = str(p)
                    findings.append(out)

    return {"findings": findings}


__all__ = ["analyze_patterns_impl", "list_patterns_impl"]
