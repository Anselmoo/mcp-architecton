from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry as detector_registry


def list_architectures_impl() -> list[dict[str, Any]]:
    """List recognized architectures from catalog if present.

    Returns empty list on any error.
    """
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
            if str(it.get("category", "")).lower() == "architecture":
                out.append(it)
        return out
    except Exception:
        return []


def analyze_architectures_impl(
    code: str | None = None,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Detect architecture styles in a code string or Python files (provide code or files)."""
    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    findings: list[dict[str, Any]] = []

    def _is_arch(entry: dict[str, Any]) -> bool:
        name = str(entry.get("name") or entry.get("pattern") or "").strip().lower()
        if not name:
            return False
        if "architecture" in name:
            return True
        arch_names = {
            "layered architecture",
            "hexagonal architecture",
            "clean architecture",
            "3-tier architecture",
            "three-tier architecture",
            "model-view-controller (mvc)",
            # helpers considered architectural elements
            "repository",
            "service layer",
            "unit of work",
            "message bus",
            "domain events",
            "cqrs",
            "front controller",
        }
        # also accept stripped suffix
        base = name.replace(" architecture", "").strip()
        return name in arch_names or base in {n.replace(" architecture", "") for n in arch_names}

    def _normalize(entry: dict[str, Any]) -> dict[str, Any]:
        out = dict(entry)
        out["name"] = out.get("name") or out.get("pattern")
        return out

    if code is not None:
        try:
            res = analyze_code_for_patterns(code, detector_registry)
        except Exception as exc:  # noqa: BLE001
            findings.append({"source": "<input>", "error": str(exc)})
        else:
            for r in cast("list[dict[str, Any]]", res or []):
                if _is_arch(r):
                    out = _normalize(r)
                    out["source"] = "<input>"
                    findings.append(out)

    if files:
        for f in files:
            p = Path(f)
            try:
                text = p.read_text()
            except Exception as exc:  # noqa: BLE001
                findings.append({"source": str(p), "error": str(exc)})
                continue
            try:
                res = analyze_code_for_patterns(text, detector_registry)
            except Exception as exc:  # noqa: BLE001
                findings.append({"source": str(p), "error": str(exc)})
            else:
                for r in cast("list[dict[str, Any]]", res or []):
                    if _is_arch(r):
                        out = _normalize(r)
                        out["source"] = str(p)
                        findings.append(out)

    return {"findings": findings}


__all__ = ["analyze_architectures_impl", "list_architectures_impl"]
