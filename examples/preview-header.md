# Header Scaffold Example

Below is a compact, generated module docstring that the scaffolder prepends to new snippets. It’s guidance-only and aims for minimal diffs.

```python
"""
Boilerplate Scaffold: Adapter (Pattern)
1) Map roles to your code (Target/Adapter/etc.)
2) Extract/define the client-facing interface (keep API stable)
3) Implement adapter and delegate to existing impl
4) Wire via a small seam; avoid broad rewrites
5) Run unit tests and ruff; commit minimal diffs
Contract: inputs=Public inputs unchanged; outputs=Behavior unchanged
Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
Complexity: low (LOC=?, defs=?) — prefer small seams; consider Strangler Fig/Branch-by-Abstraction
Prompt: Keep public API stable, propose minimal seam, limit diff; validate with tests + ast/libcst/py_compile
Cross-ref Pattern: https://refactoring.guru/design-patterns/adapter
Cross-ref Refactoring: https://refactoring.com/catalog/extractFunction.html
"""
```
