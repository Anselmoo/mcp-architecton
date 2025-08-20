from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry as detector_registry


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
