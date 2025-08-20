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
- suggest-refactor: **ENHANCED** - now provides intelligent refactoring suggestions with context-aware analysis, step-by-step instructions, and code transformation
- suggest-architecture-refactor: **ENHANCED** - targeted architectural advice with existing code structure analysis
- introduce-pattern: **ENHANCED** - intelligent transformation-first approach; analyzes existing code and transforms appropriately rather than blind appending; returns unified diff. Supports {dry_run, out_path}
- analyze-paths: scan files/dirs/globs for findings; optional metrics per file

### Enhanced Intelligent Refactoring Features

The suggest-refactor and introduce-pattern commands now include:
- **Context-aware analysis**: Understands existing code structure before suggesting patterns
- **Intelligent transformation**: Modifies existing code rather than appending templates
- **Step-by-step instructions**: Detailed refactoring guidance for LLMs/Copilot
- **Risk assessment**: Identifies potential issues with proposed refactoring
- **Integration points**: Shows where patterns should connect with existing code
- **Before/after comparisons**: Clear diff-based suggestions
- **Validation framework**: Steps to verify refactored code works correctly

### Examples

```shell
# Unified proposal for a file or code snippet with intelligent analysis
uv run mcp-architecton  # then call tool propose_architecture with {"files": ["path/to/file.py"]}

# Intelligent pattern refactoring with step-by-step instructions
uv run mcp-architecton  # then call tool suggest_refactor with {"code": "class MyClass: ..."}

# Metrics + Ruff counts
uv run mcp-architecton  # then call tool analyze_metrics with {"files": ["src/**/*.py"]}

# Pattern-only proposal with refactoring opportunities
uv run mcp-architecton  # then call tool propose_patterns with {"files": ["module.py"]}

# Intelligent pattern introduction - analyzes and transforms existing code
uv run mcp-architecton  # then call tool introduce_pattern with {"name": "strategy", "module_path": "demo/demo_file_large.py", "dry_run": true}

# Refactor-as-new: write intelligent transformation to different path with diff
uv run mcp-architecton  # then call tool introduce_pattern with {"name": "singleton", "module_path": "demo/demo_file_large.py", "out_path": "demo/refactored_demo_file_large.py"}
```

### Notes

- **Intelligent Refactoring**: The introduce and suggest-refactor tools now analyze existing code structure and provide context-aware transformations rather than simple template appending. This addresses the issue of LLMs blindly appending boilerplate code.
- **Ruff-only**: Dead-code scanning via Vulture has been removed for speed; we keep Ruff integrated in metrics.
- **Transform-first approach**: Introduce tools apply intelligent AST-based analysis and transformations, with step-by-step instructions for LLMs, before falling back to scaffolding. Always returns unified diff.
- **Enhanced suggestions**: suggest-refactor commands now provide detailed refactoring plans, risk assessments, and integration guidance for better LLM interaction.

## License

MIT
