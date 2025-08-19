from typing import cast

from mcp_architecton.snippets.catalog import CatalogEntry
from mcp_architecton.snippets.generators import gen_catalog, gen_factory, gen_registry


def test_gen_catalog_enriched_with_catalog_entry():
    entry = cast(
        CatalogEntry,
        {
            "name": "Catalog",
            "category": "Other",
            "intent": "Maintain a keyed collection of items.",
            "description": "",
            "refs": ["https://example.com/catalog"],
        },
    )
    code = gen_catalog("catalog", entry) or ""
    assert "Maintain a keyed collection" in code
    assert "References:" in code and "https://example.com/catalog" in code
    assert "class Catalog" in code and "def add(" in code and "def get(" in code


def test_gen_registry_enriched_defaults_without_entry():
    code = gen_registry("registry", None) or ""
    assert "class Registry" in code
    assert "def register(" in code and "def get(" in code


def test_gen_factory_includes_protocol_and_concrete_examples():
    entry = cast(
        CatalogEntry,
        {
            "name": "Factory",
            "category": "Creational",
            "description": "Provide a method to create objects without exposing the creation logic.",
            "refs": ["https://refactoring.guru/design-patterns/factory-method"],
        },
    )
    code = gen_factory("factory", entry) or ""
    assert "class Factory" in code and "def create(" in code
    assert "class ConcreteA" in code and "class ConcreteB" in code
    assert "References:" in code
