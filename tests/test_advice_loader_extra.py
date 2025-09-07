from __future__ import annotations

from mcp_architecton.analysis import advice_loader


def test_extract_advice_from_doc() -> None:
    doc = """Summary sentence.\n\nMore details follow."""
    result = advice_loader._extract_advice_from_doc(doc)  # type: ignore[attr-defined]
    assert result == "Summary sentence"


def test_build_advice_maps_contains_known_entries() -> None:
    pattern_map, arch_map = advice_loader.build_advice_maps()
    # Expect common names to be present (detectors registered in registry)
    assert "Factory Method" in pattern_map or "Factory" in pattern_map
    assert any(k in arch_map for k in ("MVC", "Hexagonal Architecture", "Layered Architecture"))
