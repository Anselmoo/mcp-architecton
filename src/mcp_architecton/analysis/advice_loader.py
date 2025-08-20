from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from mcp_architecton.analysis.advice_defaults import (
    ARCHITECTURE_REFACTOR_ADVICE_DEFAULTS,
    PATTERN_REFACTOR_ADVICE_DEFAULTS,
)
from mcp_architecton.detectors import registry as detector_registry


@dataclass(frozen=True)
class Advice:
    name: str
    category: str  # Pattern | Architecture
    text: str


def _category_for_name(name: str) -> str:
    # Heuristic: detectors registry mixes patterns and architectures; architecture names are known.
    arch_markers = {
        "Layered Architecture",
        "Hexagonal Architecture",
        "Clean Architecture",
        "MVC",
        "Front Controller",
        "Three-Tier Architecture",
        "Repository",
        "Service Layer",
        "Unit of Work",
        "Message Bus",
        "Domain Events",
        "CQRS",
    }
    return "Architecture" if name in arch_markers else "Pattern"


def _load_module_for_detector(name: str, detector: Any):
    # Try to resolve the module the detector function comes from
    mod = inspect.getmodule(detector)
    if mod is not None:
        return mod
    # Fallback: import by best-effort from known packages
    slug = name.lower().replace(" ", "_").replace("-", "_")
    candidates = [
        f"mcp_architecton.detectors.{slug}",
        f"mcp_architecton.detectors.patterns.{slug}",
        f"mcp_architecton.detectors.architecture.{slug}",
    ]
    for mname in candidates:
        try:
            return importlib.import_module(mname)
        except (ImportError, ModuleNotFoundError):
            continue
    return None


def _extract_advice_from_doc(doc: str | None) -> str | None:
    """Return a concise advice line from a docstring, if possible.

    Uses the first non-empty line or first sentence, trimmed.
    """
    if not doc:
        return None
    text = doc.strip()
    if not text:
        return None
    # Prefer first sentence up to ~220 chars
    first_line = text.splitlines()[0].strip()
    first_sentence = first_line.split(".")[0].strip()
    candidate = first_sentence or first_line
    candidate = candidate.strip()
    if not candidate:
        return None
    return candidate[:220]


def build_advice_maps() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Build pattern and architecture advice maps dynamically.

    Priority per name:
    1. Detector module attribute ADVICE (string) if present.
    2. Defaults from advice_defaults.
    Names and categories are derived from the detectors registry.
    """
    pattern_map: Dict[str, str] = dict(PATTERN_REFACTOR_ADVICE_DEFAULTS)
    arch_map: Dict[str, str] = dict(ARCHITECTURE_REFACTOR_ADVICE_DEFAULTS)

    for name, detector in detector_registry.items():
        category = _category_for_name(name)
        mod = _load_module_for_detector(name, detector)
        if mod is None:
            continue
        advice_text = getattr(mod, "ADVICE", None)
        if isinstance(advice_text, str) and advice_text.strip():
            if category == "Architecture":
                arch_map[name] = advice_text.strip()
            else:
                pattern_map[name] = advice_text.strip()
            continue
        # Fallback to docstrings
        doc_text = _extract_advice_from_doc(getattr(mod, "__doc__", None))
        if not doc_text:
            doc_text = _extract_advice_from_doc(getattr(detector, "__doc__", None))
        if doc_text:
            if category == "Architecture":
                arch_map[name] = doc_text
            else:
                pattern_map[name] = doc_text
    return pattern_map, arch_map
