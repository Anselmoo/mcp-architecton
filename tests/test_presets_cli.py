from __future__ import annotations

import io
from contextlib import redirect_stdout

from mcp_architecton.tools import presets_cli


def test_presets_cli_list_prompts():
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = presets_cli.main(["list", "prompts"])  # uses repository JSON file
    assert exit_code == 0
    out = buf.getvalue().strip().splitlines()
    # should list at least one id and name separated by tab
    assert any("minimal-seam-integration" in line for line in out)


def test_presets_cli_show_prompt():
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = presets_cli.main(["show", "prompts", "minimal-seam-integration"])
    assert exit_code == 0
    body = buf.getvalue()
    assert "minimal seam" in body.lower()
