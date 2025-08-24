# MCP Architecton

An MCP server that analyzes Python code for design patterns and software architecture signals, and can scaffold pattern introductions.

### Boilerplate header (scaffold guardrails)

Generated scaffolds prepend a compact module docstring that enforces safe, minimal-diff integration:

- Steps 1–5: role mapping → interface extraction → implementation → wiring via a small seam → validate and commit minimal diffs
- Contract: states inputs/outputs invariants (e.g., public inputs unchanged; behavior unchanged)
- Validation: toolset used to sanity-check edits (ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile)
- Complexity: low/medium/high hint using LOC and top-level defs, with cues like Strangler Fig / Branch-by-Abstraction
- Cross-ref: up to two links for the pattern/architecture and refactoring techniques (from `data/patterns/catalog.json`)
- Prompt: one-line hint; may come from catalog’s `prompt_hint` when available

Complexity heuristic (approx.):

- low: <300 LOC and <15 top-level defs
- medium: 300–799 LOC or 15–39 defs
- high: ≥800 LOC or ≥40 defs

This header is guidance only—the generator emits boilerplate scaffolds, not automatic refactors.

See also:

- `data/prompt_presets.json` for 5 prompts and 5 CI subrun recipes
- `docs/prompt_templates.md` for copyable header and CI subrun templates

### Prompt presets CLI

List presets and print bodies:

```shell
uv run architecton-presets list prompts
uv run architecton-presets list subruns
uv run architecton-presets show prompts minimal-seam-integration
```

## Quick start

- Requires Python 3.10+
- Uses `uv` for tooling

### Install (editable)

```shell
uv sync --dev
```

### Run the server

```shell
uv run mcp-architecton
```

### Optional toggles: ast-grep and rope

Runtime features are gated by environment variables and mirrored CLI flags:

- ARCHITECTON_ENABLE_ASTGREP: enables ast-grep heuristics (top-level defs, long parameter lists, repeated literals). Default: enabled.
- ARCHITECTON_ENABLE_ROPE: enables rope sanity parse and a dry-run rename preview validator in enforcement (hits scope). Default: enabled.

You can set them via CLI flags when starting the server:

```shell
# enable/disable ast-grep
uv run mcp-architecton --enable-astgrep
uv run mcp-architecton --disable-astgrep

# enable/disable rope
uv run mcp-architecton --enable-rope
uv run mcp-architecton --disable-rope
```

Or with environment variables:

```shell
set -x ARCHITECTON_ENABLE_ASTGREP 0  # fish shell example
set -x ARCHITECTON_ENABLE_ROPE 1
uv run mcp-architecton
```

### VS Code MCP config (user settings JSON)

```json
{
  "mcp": {
    "servers": {
      "architecton": {
        "command": "uvx",
        "args": ["mcp-architecton"]
      }
    }
  }
}
```

Alternatively, add `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "architecton": {
        "command": "uvx",
        "args": ["mcp-architecton"]
      }
    }
  }
}
```

## Tools

- propose-architecture: unified proposal that runs detectors, Radon metrics, Ruff, and ranked enforcement to suggest top patterns/architectures with tailored prompts
- propose-patterns: like propose-architecture but filters suggestions to patterns only
- analyze-metrics: Radon (CC/MI/LOC) plus Ruff rule counts (Ruff only; Vulture removed)
- thresholded-enforcement: anti-pattern indicators + ranked suggestions with reasons
- analyze-patterns: detect patterns in code
- analyze-architectures: detect architecture signals
- suggest-refactor: propose changes towards canonical implementations (patterns)
- suggest-architecture-refactor: targeted advice per architecture
- introduce-pattern: transform-first; falls back to scaffold; returns unified diff. Supports {dry_run, out_path}
- analyze-paths: scan files/dirs/globs for findings; optional metrics per file

### Examples

```shell
# Unified proposal for a file or code snippet
uv run mcp-architecton  # then call tool propose_architecture with {"files": ["path/to/file.py"]}

# Metrics + Ruff counts
uv run mcp-architecton  # then call tool analyze_metrics with {"files": ["src/**/*.py"]}

# Pattern-only proposal
uv run mcp-architecton  # then call tool propose_patterns with {"files": ["module.py"]}

# Introduce a Strategy into a file without writing (dry-run)
uv run mcp-architecton  # then call tool introduce_pattern with {"name": "strategy", "module_path": "demo/demo_file_large.py", "dry_run": true}

# Refactor-as-new: write the change to a different path and get the diff
uv run mcp-architecton  # then call tool introduce_pattern with {"name": "strategy", "module_path": "demo/demo_file_large.py", "out_path": "demo/refactored_demo_file_large.py"}
```

### Notes

- Ruff-only: Dead-code scanning via Vulture has been removed for speed; we keep Ruff integrated in metrics.
- Introduce tools apply generic AST-family transforms both before and after scaffolding to normalize imports and future annotations and always return a unified diff.
- Overlap clarification: propose-architecture gives prioritized, ranked suggestions using indicators and advice; suggest-architecture-refactor is a lighter, direct advice emitter for already detected architectures.

## License

MIT
