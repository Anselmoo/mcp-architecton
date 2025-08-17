from __future__ import annotations

from pathlib import Path

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def test_detects_chain_of_responsibility():
    code = (Path(__file__).parent / "samples" / "chain_of_responsibility_good.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert any(r.get("name") == "Chain of Responsibility" for r in res)
