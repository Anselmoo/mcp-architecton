from __future__ import annotations

from mcp_architecton.server import list_patterns


def test_list_patterns_returns_catalog():
    items = list_patterns()
    assert isinstance(items, list)
    assert any(p.get("name") == "Singleton" for p in items)
