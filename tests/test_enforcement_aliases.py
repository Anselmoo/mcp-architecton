from __future__ import annotations

from mcp_architecton.analysis.enforcement import ranked_enforcement_targets


def test_aliases_match_recommendations_to_architecture():
    indicators = []
    recs = ["Consider MVC for separation of concerns"]
    pattern_advice = {}
    arch_advice = {"Model-View-Controller (MVC)": "Separate concerns via MVC."}
    name_aliases = {"mvc": "Model-View-Controller (MVC)"}

    results = ranked_enforcement_targets(
        indicators, recs, pattern_advice, arch_advice, name_aliases
    )

    assert any(n == "Model-View-Controller (MVC)" for (n, _c, _w, _r) in results)
    rec_reasons = {n: r for (n, _c, _w, r) in results}
    assert "recommendation" in rec_reasons["Model-View-Controller (MVC)"]
