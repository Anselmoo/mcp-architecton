#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    # Ensure local 'src' is importable
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Import and run server
    from mcp_architecton.server import run  # noqa: WPS433

    run()


if __name__ == "__main__":  # pragma: no cover
    main()
