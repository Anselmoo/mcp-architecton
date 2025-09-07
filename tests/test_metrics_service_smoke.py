from __future__ import annotations

from mcp_architecton.services import metrics as metrics_service

SAMPLE = """\n# sample code\n\n def trivial():\n    return 42\n"""


def test_metrics_service_code() -> None:
    data = metrics_service.analyze_metrics_impl(code=SAMPLE)
    assert isinstance(data, dict)
    assert "results" in data
