from __future__ import annotations

import ast
from pathlib import Path

from mcp_architecton.detectors.patterns import factory, adapter, builder

SIMPLE_FACTORY = (
    """\nclass A:\n    pass\n\nclass B:\n    pass\n\ndef factory():\n    return A()\n"""
)


def test_factory_detector_smoke() -> None:
    tree = ast.parse(SIMPLE_FACTORY)
    res = factory.detect(tree, SIMPLE_FACTORY)
    assert any(f.get("name") == "Factory" for f in res)


def test_other_detectors_no_crash() -> None:
    # Load a couple of example files to pass through detectors (adapter, builder) for minimal coverage
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    sample = (examples_dir / "non_pythonic_small.py").read_text()
    tree = ast.parse(sample)
    adapter.detect(tree, sample)
    builder.detect(tree, sample)
