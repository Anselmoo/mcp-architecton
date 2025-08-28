# MCP Architecton for Python 🏛️🐍

An MCP server that analyzes Python code for design patterns and architecture signals, proposes prioritized refactors, and can scaffold safe boilerplate intros with guarded headers.

> [!caution]
>
> **Disclaimer** — Experimental / Early Stage: This project uses third‑party libraries and optional integrations (Radon, Ruff, ast-grep, rope) that evolve quickly. Treat outputs as recommendations and verify against official docs and your tests before production use. Scaffolds are boilerplate helpers, not automatic refactors. Optional features are gated by env/CLI toggles and should be enabled deliberately.

## Table of Contents

- [MCP Architecton for Python 🏛️🐍](#mcp-architecton-for-python-️)
  - [Table of Contents](#table-of-contents)
  - [Why Architecton?](#why-architecton)
  - [📋 Features](#-features)
  - [🚀 Quick Start](#-quick-start)
    - [VS Code Integration (Manual)](#vs-code-integration-manual)
  - [🔧 MCP Client Configuration](#-mcp-client-configuration)
  - [CLI Flags and Env Toggles](#cli-flags-and-env-toggles)
  - [Repo Scan Script](#repo-scan-script)
  - [🛠️ Available Tools](#️-available-tools)
    - [Examples](#examples)
    - [Linked Examples](#linked-examples)
  - [🧩 Boilerplate Header Guardrails](#-boilerplate-header-guardrails)
    - [Prompt presets CLI (optional)](#prompt-presets-cli-optional)
  - [🧪 Development](#-development)
  - [📚 Documentation](#-documentation)
    - [Key Pattern \& Architecture References](#key-pattern--architecture-references)
  - [🤝 Contributing](#-contributing)
  - [📝 License](#-license)

## Why Architecton?

Architecton focuses on pattern/architecture guidance with actionable prompts and minimal diffs. It unifies detectors, metrics, and ranked enforcement so you can move from “what’s wrong” to “what to do next” quickly.

## 📋 Features

- Pattern and architecture detection with tailored advice from a curated catalog
- Unified proposals: Radon metrics (CC/MI/LOC), Ruff-only rule counts, and ranked enforcement prompts
- Safe scaffolding: guarded module header with contract, validation gauntlet (ast/parso/libcst/astroid/RedBaron/tree-sitter/py_compile), complexity hint, and cross-refs
- Optional integrations (gated):
  - ast-grep-py heuristics (top-level defs, long parameter lists, repeated literals)
  - rope dry-run rename validator in enforcement (hits scope) and sanity parse
- FastMCP-based server; minimal tool surface; catalog-driven prompt hints

## 🚀 Quick Start

Requires Python 3.10+ and uses uv.

Install (editable):

```shell
uv sync --dev
```

Run the server:

```shell
uv run mcp-architecton
```

### VS Code Integration (Manual)

Add this to User Settings (JSON) or `.vscode/mcp.json`:

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

## 🔧 MCP Client Configuration

User Settings (JSON) example using `uvx` (same as above). Alternatively, add `.vscode/mcp.json` with the same block to share in a workspace.

## CLI Flags and Env Toggles

Runtime features are gated by environment variables and mirrored flags:

- ARCHITECTON_ENABLE_ASTGREP: enables ast-grep heuristics (default: enabled)
- ARCHITECTON_ENABLE_ROPE: enables rope checks and dry-run validator (default: enabled)

Flags (equivalent to setting env vars):

```shell
uv run mcp-architecton --enable-astgrep
uv run mcp-architecton --disable-astgrep
uv run mcp-architecton --enable-rope
uv run mcp-architecton --disable-rope
```

Fish shell env example:

```fish
set -x ARCHITECTON_ENABLE_ASTGREP 0
set -x ARCHITECTON_ENABLE_ROPE 1
uv run mcp-architecton
```

## Repo Scan Script

Run a quick indicator summary and ranked suggestions across a repo:

```shell
uv run python scripts/scan_repo.py --dir .
```

Toggles also apply here:

```shell
uv run python scripts/scan_repo.py --enable-astgrep --disable-rope --dir .
```

## 🛠️ Available Tools

- propose-architecture: unified proposal using detectors, Radon, Ruff, and ranked enforcement prompts
- propose-patterns: pattern-focused filtering of the unified proposal
- analyze-metrics: Radon (CC/MI/LOC) and Ruff rule counts (Ruff-only; Vulture removed)
- thresholded-enforcement: anti-pattern indicators + ranked prompts with reasons
- analyze-patterns: detect design patterns
- analyze-architectures: detect architecture styles
- suggest-refactor-patterns: advice for detected patterns
- suggest-architecture-refactor: advice for detected architectures
- introduce-pattern / introduce-architecture: transformation-first; scaffold fallback; return unified diff (supports {dry_run, out_path})
- analyze-paths: scan files/dirs/globs with optional per-file metrics

### Examples

```shell
# Unified proposal for file(s)
uv run mcp-architecton  # call propose_architecture with {"files": ["path/to/file.py"]}

# Metrics + Ruff counts
uv run mcp-architecton  # call analyze_metrics with {"files": ["src/**/*.py"]}

# Pattern-only proposal
uv run mcp-architecton  # call propose_patterns with {"files": ["module.py"]}

# Introduce Strategy (dry-run)
uv run mcp-architecton  # call introduce_pattern with {"name": "strategy", "module_path": "demo/demo_file_large.py", "dry_run": true}

# Refactor-as-new path
uv run mcp-architecton  # call introduce_pattern with {"name": "strategy", "module_path": "demo/demo_file_large.py", "out_path": "demo/refactored_demo_file_large.py"}
```

### Linked Examples

- Header scaffold preview: [examples/preview-header.md](examples/preview-header.md)
- ast-grep indicators: [examples/preview-astgrep.md](examples/preview-astgrep.md)
- rope preview rename: [examples/preview-rope.md](examples/preview-rope.md)

## 🧩 Boilerplate Header Guardrails

Generated scaffolds prepend a compact module docstring to enforce safe integration:

- Steps 1–5: role mapping → interface extraction → implementation → seam wiring → validate and commit minimal diffs
- Contract: inputs/outputs invariants (behavior unchanged)
- Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
- Complexity: low/medium/high via LOC/top-level defs, with Strangler Fig/Branch-by-Abstraction cues
- Cross-refs: links for pattern/architecture and refactoring techniques (catalog-driven)
- Prompt: one-line hint from the catalog when available

This header is guidance only—the generator emits safe boilerplate, not automatic refactors.

### Prompt presets CLI (optional)

If you use the bundled presets tool:

```shell
uv run architecton-presets list prompts
uv run architecton-presets list subruns
uv run architecton-presets show prompts minimal-seam-integration
```

## 🧪 Development

```shell
# Install
uv sync --dev

# Lint
uv run ruff check .

# Test
uv run -q pytest -q
```

## 📚 Documentation

- MCP Specification: https://modelcontextprotocol.io/
- FastMCP Framework: https://gofastmcp.com/

### Key Pattern & Architecture References

- Design Patterns (overview): https://refactoring.guru/design-patterns
- Python patterns (examples): https://github.com/faif/python-patterns
- Presentation/Domain/Data layering: https://martinfowler.com/bliki/PresentationDomainDataLayering.html
- Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture/
- Clean Architecture: https://8thlight.com/blog/uncle-bob/2012/08/13/the-clean-architecture.html
- Microservices: https://martinfowler.com/articles/microservices.html
- Event-Driven Architecture: https://martinfowler.com/articles/201701-event-driven.html
- CQRS: https://martinfowler.com/bliki/CQRS.html

Full curated catalog used by the server: [data/patterns/catalog.json](data/patterns/catalog.json)

## 🤝 Contributing

Contributions welcome. Please keep changes typed, linted (Ruff), and include tests for behavior changes.

By contributing, you agree your contributions are licensed under the project’s [MIT License](LICENSE). No Contributor License Agreement (CLA) is required at this time.

## 📝 License

[MIT](LICENSE)
