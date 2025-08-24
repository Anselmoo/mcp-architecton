#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Local runner for the MCP server (keeps editable installs handy).

    Note: CLI flags are parsed in mcp_architecton.server.main; we just ensure src on sys.path
    and delegate. This keeps a single source of truth for flags like --enable-astgrep/rope.
    """
    # Ensure local 'src' is importable
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # Import and run server (parses CLI flags itself)
    from mcp_architecton.server import main as server_main

    server_main()


if __name__ == "__main__":  # pragma: no cover
    main()
