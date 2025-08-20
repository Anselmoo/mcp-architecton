from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry as detector_registry


def list_architectures_impl() -> list[dict[str, Any]]:
    """List recognized software architectures from the catalog."""
    catalog_path = Path(__file__).resolve().parents[2] / "data" / "patterns" / "catalog.json"
    if not catalog_path.exists():
        return []
    try:
        import json

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
