from __future__ import annotations

import importlib
import inspect
from types import SimpleNamespace

import mcp_architecton.analysis.advice_loader as advice_loader


def test_build_advice_maps_fallback_import_and_precedence(monkeypatch):
    # Prepare fake detectors and override registry to a tiny mapping
    def fake_detector_pattern(node, code):  # noqa: ARG001
        return []

    def fake_detector_arch(node, code):  # noqa: ARG001
        return []

    monkeypatch.setattr(
        advice_loader,
        "detector_registry",
        {"My Pattern": fake_detector_pattern, "MVC": fake_detector_arch},
        raising=True,
    )

    # Force inspect.getmodule to return None for our fake detectors so fallback import logic runs
    real_getmodule = inspect.getmodule

    def _fake_getmodule(obj):  # pragma: no cover - small guard fallback
        if obj in (fake_detector_pattern, fake_detector_arch):
            return None
        return real_getmodule(obj)

    monkeypatch.setattr(inspect, "getmodule", _fake_getmodule, raising=True)

    # Stub importlib.import_module to return modules based on expected candidate paths
    def _fake_import_module(name: str):
        if name == "mcp_architecton.detectors.patterns.my_pattern":
            # ADVICE should take precedence over any docstrings
            return SimpleNamespace(
                ADVICE="Prefer Strategy-like encapsulation for variable behavior.",
                __doc__="Ignored.",
            )
        if name == "mcp_architecton.detectors.architecture.mvc":
            # No ADVICE, fall back to docstring, first sentence
            return SimpleNamespace(__doc__="Model-View-Controller separates concerns. More text.")
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module, raising=True)

    pattern_map, arch_map = advice_loader.build_advice_maps()

    assert pattern_map["My Pattern"].startswith("Prefer Strategy-like encapsulation")
    assert arch_map["MVC"] == "Model-View-Controller separates concerns"
