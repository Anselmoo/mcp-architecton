from __future__ import annotations

from pathlib import Path

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def test_detects_abstract_factory():
    code = (Path(__file__).parent / "samples" / "abstract_factory_good.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert any(r.get("name") == "Abstract Factory" for r in res)
