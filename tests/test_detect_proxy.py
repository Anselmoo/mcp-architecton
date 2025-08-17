from __future__ import annotations

from pathlib import Path

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def test_detects_proxy():
    code = (Path(__file__).parent / "samples" / "proxy_good.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert any(r.get("name") == "Proxy" for r in res)
