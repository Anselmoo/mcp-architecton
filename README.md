# MCP Architecton

An MCP server that analyzes Python code for design patterns and software architecture signals, and can scaffold pattern introductions.

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
- introduce-pattern: scaffold a chosen pattern
- analyze-paths: scan files/dirs/globs for findings; optional metrics per file

### Examples

```shell
# Unified proposal for a file or code snippet
uv run mcp-architecton  # then call tool propose_architecture with {"files": ["path/to/file.py"]}

# Metrics + Ruff counts
uv run mcp-architecton  # then call tool analyze_metrics with {"files": ["src/**/*.py"]}

# Pattern-only proposal
uv run mcp-architecton  # then call tool propose_patterns with {"files": ["module.py"]}
```

### Notes

- Ruff-only: Dead-code scanning via Vulture has been removed for speed; we keep Ruff integrated in metrics.
- Overlap clarification: propose-architecture gives prioritized, ranked suggestions using indicators and advice; suggest-architecture-refactor is a lighter, direct advice emitter for already detected architectures.

## License

MIT
