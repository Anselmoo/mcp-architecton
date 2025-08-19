from __future__ import annotations

from mcp_architecton.analysis.advice_loader import (
    _category_for_name,
    _extract_advice_from_doc,
    build_advice_maps,
)


def test_extract_advice_from_doc_uses_first_sentence():
    doc = """
    Use Strategy to encapsulate algorithms. Additional details follow in later sentences.

    More lines below should be ignored by the extractor.
    """
    out = _extract_advice_from_doc(doc)
    assert out == "Use Strategy to encapsulate algorithms"


def test_category_for_name_distinguishes_architecture():
    assert _category_for_name("Hexagonal Architecture") == "Architecture"
    assert _category_for_name("Strategy") == "Pattern"


def test_build_advice_maps_contains_known_items():
    pattern_map, arch_map = build_advice_maps()
    assert isinstance(pattern_map, dict) and isinstance(arch_map, dict)

    # Expect at least these well-known names to be present
    assert "Strategy" in pattern_map
    # The detectors register "Model-View-Controller (MVC)"; advice loader maps "MVC" as architecture marker
    # Ensure at least one architecture key we know is present
    assert "Hexagonal Architecture" in arch_map or any(
        k for k in arch_map if "Architecture" in k or k.startswith("Model-View-Controller")
    )
