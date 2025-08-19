from __future__ import annotations

from pathlib import Path

from mcp_architecton.server import introduce_architecture_impl, introduce_pattern_impl


def test_introduce_pattern_directory_mode_dry_run(tmp_path: Path):
    # Arrange: create a small Python project structure
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "mod.py").write_text("x = 1\n")

    # Act: run in directory mode with dry_run
    res = introduce_pattern_impl("Strategy", str(src), dry_run=True)

    # Assert: structure and mode
    assert res["status"] == "ok"
    assert res["mode"] == "transformed-dir"
    assert isinstance(res.get("changes"), list)


def test_introduce_architecture_directory_mode_dry_run(tmp_path: Path):
    # Arrange: create a small Python project structure
    src = tmp_path / "pkg"
    src.mkdir()
    (src / "service.py").write_text("def run():\n    return 42\n")

    # Act: run in directory mode with dry_run
    res = introduce_architecture_impl("hexagonal", str(src), dry_run=True)

    # Assert: structure and mode
    assert res["status"] == "ok"
    assert res["mode"] == "transformed-dir"
    assert isinstance(res.get("changes"), list)
