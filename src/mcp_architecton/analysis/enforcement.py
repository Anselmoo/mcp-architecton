"""Enforcement ranking logic (indicators -> prioritized targets).

Moves ranking out of server and uses shared aliases. Includes all advice entries
with baseline weights in addition to curated boosts.
"""

from __future__ import annotations

from typing import Any


def _simplify(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _canonical_from_text(
    token_text: str, advice_keys: list[str], aliases: dict[str, str]
) -> set[str]:
    """Find advice keys referenced in free-form text using direct and alias-based matching."""
    text = token_text.lower()
    hits: set[str] = set()
    # direct contains
    for k in advice_keys:
        if k.lower() in text:
            hits.add(k)
    # alias contains
    for alias_key in aliases.keys():
        if alias_key in text:
            # try to map alias to the closest advice key
            alias_val = aliases[alias_key]
            simp_val = _simplify(alias_val)
            for k in advice_keys:
                if _simplify(k) == simp_val or alias_val in k.lower():
                    hits.add(k)
    return hits


def ranked_enforcement_targets(
    indicators: list[dict[str, Any]],
    recs: list[str],
    pattern_advice: dict[str, str],
    arch_advice: dict[str, str],
    name_aliases: dict[str, str],
) -> list[tuple[str, str, int, list[str]]]:
    """Return list of (name, category, weight, reasons) sorted by weight.

    - name: canonical item name (pattern or architecture)
    - category: "Pattern" or "Architecture"
    - weight: aggregated severity score
    - reasons: indicators contributing
    """
    sev: dict[str, int] = {
        "dynamic_eval": 3,
        "high_cc": 3,
        "very_large_function": 3,
        "low_mi": 2,
        "large_file": 2,
        "global_or_any_usage": 2,
        "print_logging": 1,
    }

    # Curated boosts for common mappings. We'll also add a baseline for all advice keys.
    indicator_targets: dict[str, list[tuple[str, int]]] = {
        "high_cc": [
            ("Strategy", 3),
            ("Template Method", 2),
            ("Chain of Responsibility", 2),
            ("State", 2),
            ("Command", 2),
            ("Mediator", 1),
            ("Visitor", 1),
            ("Facade", 1),
            ("Borg", 1),  # encourage shared-state consolidation when complexity is global
        ],
        "very_large_function": [
            ("Template Method", 3),
            ("Strategy", 2),
            ("Chain of Responsibility", 1),
            ("Command", 1),
            ("Borg", 1),
        ],
        "low_mi": [
            ("Facade", 2),
            ("Strategy", 2),
            ("Mediator", 1),
            ("Observer", 1),
            ("Hexagonal Architecture", 1),
            ("Clean Architecture", 1),
            ("Singleton", 1),
        ],
        "large_file": [
            ("Layered Architecture", 3),
            ("Model-View-Controller (MVC)", 2),
            ("Hexagonal Architecture", 2),
            ("Clean Architecture", 2),
            ("Three-Tier Architecture", 2),
            ("Facade", 1),
            ("Borg", 1),
        ],
        "global_or_any_usage": [
            ("Dependency Injection", 3),
            ("Facade", 2),
            ("Hexagonal Architecture", 1),
            ("Service Layer", 1),
            ("Singleton", 2),
            ("Borg", 2),
        ],
        "dynamic_eval": [
            ("Factory Method", 3),
            ("Abstract Factory", 2),
            ("Strategy", 1),
            ("Command", 1),
            ("Proxy", 1),
            ("Visitor", 1),
        ],
        "print_logging": [
            ("Hexagonal Architecture", 2),
            ("Facade", 1),
            ("Observer", 1),
        ],
    }

    # Ensure every advice entry is present at least with baseline weight 1 for each indicator type
    all_keys = list(pattern_advice.keys()) + list(arch_advice.keys())
    for itype in sev.keys():
        entries = indicator_targets.setdefault(itype, [])
        present = {name for name, _ in entries}
        for k in all_keys:
            if k not in present:
                entries.append((k, 1))

    def add_target(
        name: str, reasons: list[str], w: int, acc: dict[str, tuple[str, int, set[str]]]
    ) -> None:
        cat = "Pattern" if name in pattern_advice else "Architecture"
        if name not in acc:
            acc[name] = (cat, 0, set())
        cat0, w0, rs = acc[name]
        acc[name] = (cat0, w0 + w, rs.union(reasons))

    acc: dict[str, tuple[str, int, set[str]]] = {}

    for ind in indicators:
        itype = str(ind.get("type", ""))
        base = sev.get(itype, 1)
        for target, bonus in indicator_targets.get(itype, []):
            add_target(target, [itype], max(1, bonus or base), acc)

    # Consider explicit recommendations text
    rec_text = " ".join(r.lower() for r in recs)
    if rec_text:
        for k in _canonical_from_text(rec_text, list(pattern_advice.keys()), name_aliases):
            add_target(k, ["recommendation"], 1, acc)
        for k in _canonical_from_text(rec_text, list(arch_advice.keys()), name_aliases):
            add_target(k, ["recommendation"], 1, acc)

    items: list[tuple[str, str, int, list[str]]] = [
        (name, cat, weight, sorted(list(reasons))) for name, (cat, weight, reasons) in acc.items()
    ]
    items.sort(key=lambda t: (-t[2], t[0]))
    return items


__all__ = ["ranked_enforcement_targets"]
