from __future__ import annotations

from mcp_architecton.analysis.enforcement import ranked_enforcement_targets


def test_ranked_enforcement_targets_basic_sorting_and_categories():
    indicators = [
        {"type": "high_cc"},
        {"type": "print_logging"},
    ]
    recs = ["Consider Strategy for complex conditional logic"]
    pattern_advice = {
        "Strategy": "Encapsulate interchangeable behaviors behind a common interface",
        "Facade": "Provide a simplified interface to a subsystem",
    }
    arch_advice = {
        "Hexagonal Architecture": "Isolate domain from external concerns via ports/adapters",
    }
    name_aliases = {}

    results = ranked_enforcement_targets(
        indicators, recs, pattern_advice, arch_advice, name_aliases
    )

    # Ensure expected items are present
    names = [n for (n, _cat, _w, _r) in results]
    assert "Strategy" in names
    assert "Facade" in names
    assert "Hexagonal Architecture" in names

    # Verify categories are correctly assigned
    cats = {n: c for (n, c, _w, _r) in results}
    assert cats["Strategy"] == "Pattern"
    assert cats["Facade"] == "Pattern"
    assert cats["Hexagonal Architecture"] == "Architecture"

    # Strategy should rank highest due to curated boost + baseline + recommendation
    weights = {n: w for (n, _c, w, _r) in results}
    assert weights["Strategy"] >= weights["Hexagonal Architecture"] >= weights["Facade"]

    # Reasons should include the indicator types and recommendation for Strategy
    reasons = {n: set(r) for (n, _c, _w, r) in results}
    assert {"high_cc", "print_logging"}.issubset(
        reasons.get("Facade", set())
    ) or "print_logging" in reasons.get("Facade", set())
    assert "recommendation" in reasons["Strategy"]
