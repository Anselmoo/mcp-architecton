from __future__ import annotations

from mcp_architecton.services import scan as scan_service


def test_scan_service_basic() -> None:
    # Provide a tiny code snippet exercising several heuristics
    sample = """\nimport math\n\nGLOBAL_STATE = {}\n\n\ndef big_function():\n    total = 0\n    for i in range(10):\n        total += i * 2\n    return total\n"""
    result = scan_service.scan_anti_patterns_impl(code=sample)
    assert isinstance(result, dict)
    assert "results" in result
    assert result["results"][0]["indicators"] is not None
