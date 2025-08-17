from __future__ import annotations

from pathlib import Path

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def test_detect_singleton_good():
    code = Path("tests/samples/singleton_good.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert any(r["name"] == "Singleton" for r in res)


def test_detect_singleton_bad():
    code = Path("tests/samples/singleton_bad.py").read_text()
    res = analyze_code_for_patterns(code, registry)
    assert not any(r["name"] == "Singleton" for r in res)
