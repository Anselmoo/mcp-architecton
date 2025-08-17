from __future__ import annotations

from pathlib import Path

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def test_detects_three_tier_architecture():
    code = (Path(__file__).parent / "samples" / "architecture_three_tier_good.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert any(r.get("name") == "3-Tier Architecture" for r in res)
