from __future__ import annotations

from pathlib import Path

from mcp_architecton.generators.refactor_generator import introduce_impl


def test_header_uses_prompt_hint_and_contract_from_catalog(tmp_path: Path) -> None:
    target = tmp_path / "adapter_scaffold.py"
    # Introduce Adapter; catalog contains prompt_hint and contract
    res = introduce_impl(name="adapter", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    assert target.exists(), "scaffold file should be created"
    text = target.read_text()

    # Prompt hint should be present
    assert "Prompt: Stabilize client API with an adapter" in text

    # Contract line should reflect catalog overrides (not the default)
    assert (
        "Contract: inputs=Stable Target interface; client calls unchanged; outputs=Same behavior via Adaptee; no observable changes"
        in text
    )


def test_header_contains_refactoring_refs_and_validation_tools(tmp_path: Path) -> None:
    target = tmp_path / "strategy_scaffold.py"
    res = introduce_impl(name="strategy", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    text = target.read_text()

    # Cross-ref Refactoring should include at least one known fallback link
    assert "Cross-ref Refactoring: https://refactoring.guru/refactoring/techniques" in text or (
        "https://refactoring.com/catalog/" in text
    )

    # Validation tools line should include a few tools
    assert "Validation: ast, parso, libcst" in text


def test_composite_header_uses_prompt_hint(tmp_path: Path) -> None:
    target = tmp_path / "composite_scaffold.py"
    res = introduce_impl(name="composite", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    text = target.read_text()
    assert "Prompt: Unify Leaf and Composite under Component" in text


def test_bridge_header_uses_prompt_hint(tmp_path: Path) -> None:
    target = tmp_path / "bridge_scaffold.py"
    res = introduce_impl(name="bridge", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    text = target.read_text()
    assert "Prompt: Separate Abstraction from Implementor" in text


def test_clean_architecture_header_uses_prompt_hint(tmp_path: Path) -> None:
    target = tmp_path / "clean_arch_scaffold.py"
    res = introduce_impl(name="clean", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    text = target.read_text()
    assert "Prompt: Entities/use-cases/adapters" in text


def test_three_tier_header_uses_prompt_hint(tmp_path: Path) -> None:
    target = tmp_path / "three_tier_scaffold.py"
    res = introduce_impl(name="three_tier", module_path=str(target), dry_run=False)
    assert res.get("status") == "ok"
    text = target.read_text()
    assert "Prompt: Presentation, logic, data tiers" in text
