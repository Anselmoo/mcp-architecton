from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_architecton.analysis.ast_utils import analyze_code_for_patterns
from mcp_architecton.detectors import registry


def find(res: list[dict[str, Any]], name: str) -> bool:
    return any(r.get("name") == name for r in res)


essential = (
    ("Layered Architecture", "tests/samples/architecture_layered_good.py"),
    ("Hexagonal Architecture", "tests/samples/architecture_hexagonal_good.py"),
    ("Clean Architecture", "tests/samples/architecture_clean_good.py"),
    ("Repository", "tests/samples/architecture_repository_good.py"),
    ("Unit of Work", "tests/samples/architecture_unit_of_work_good.py"),
    ("Service Layer", "tests/samples/architecture_service_layer_good.py"),
    ("Message Bus", "tests/samples/architecture_message_bus_good.py"),
    ("Domain Events", "tests/samples/architecture_domain_events_good.py"),
    ("CQRS", "tests/samples/architecture_cqrs_good.py"),
)


def test_detect_architectures_minimals():
    for name, path in essential:
        code = Path(path).read_text()
        res = analyze_code_for_patterns(code, registry)
        assert find(res, name), f"Expected to detect {name}"
