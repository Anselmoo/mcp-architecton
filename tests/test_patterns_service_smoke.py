from __future__ import annotations

from mcp_architecton.services import patterns as patterns_service

SAMPLE_PATTERN = (
    """\nclass Product: ...\n\nclass Creator: ...\n\n def factory():\n    return Product()\n"""
)


def test_patterns_analyze_code() -> None:
    res = patterns_service.analyze_patterns_impl(code=SAMPLE_PATTERN)
    assert isinstance(res, dict)
    assert "findings" in res


def test_patterns_list_catalog() -> None:
    lst = patterns_service.list_patterns_impl()
    assert isinstance(lst, list)
