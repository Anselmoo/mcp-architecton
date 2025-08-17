Checklist for this workspace

- [x] Verify that `.github/copilot-instructions.md` exists.
- [x] Clarify project requirements (Python MCP server; uv; Ruff-only metrics; Radon; pattern/architecture detectors; dynamic advice).
- [x] Scaffold/update project using current directory.
- [x] Customize: unify analysis via `propose_architecture`; add `propose_patterns`; keep Ruff; remove Vulture.
- [x] Install required extensions only if specified elsewhere (none currently).
- [x] Compile/diagnose: `uv run ruff check .` and `uv run -q pytest -q` should pass.
- [x] Create tasks only when needed (not required now).
- [x] Launch via `uv run mcp-architecton` when requested.
- [x] Ensure docs are up to date (README reflects consolidated tools and Ruff-only metrics).

Guidelines

- Use “.” as working directory; avoid creating extra folders.
- Prefer concise, actionable responses; avoid verbose outputs.
- Don’t install extensions unless explicitly requested by setup info.
- When adding features, ensure detectors drive advice (no hard-coded maps; use loader/docstrings/defaults).
