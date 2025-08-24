# Prompt templates

## Module header (copyable template)

"""
Boilerplate Scaffold: {Name} ({Category})

1. Map roles to your code (Target/Adapter/etc.)
2. Extract/define the client-facing interface (keep API stable)
3. Implement and delegate to existing impl
4. Wire via a small seam; avoid broad rewrites
5. Run unit tests and ruff; commit minimal diffs
   Contract: inputs={inputs}; outputs={outputs}
   Validation: ast, parso, libcst, astroid, RedBaron, tree-sitter, py_compile
   Complexity: {level} (LOC={loc}; defs={defs})
   Cross-ref Pattern: {pattern_refs}
   Cross-ref Refactoring: {refactor_refs}
   Prompt: {prompt_hint}
   """

Notes:

- Keep to ~12 lines; prefer concise wording to avoid overflow.
- pattern_refs/refactor_refs should list 1–2 links each.

## CI subrun (micro-refactor)

Instructions:

- Pick exactly one technique from the catalog for the target: {technique_candidates}
- Propose a tiny patch plan and show only 3–5 line diff chunks.
- No public API changes allowed; include a rollback snippet.
- Run tests + ruff + ast/libcst + py_compile; stop if any fail.
- Stop if diff exceeds ~{diff_budget} lines and return NO-CHANGE.

Output:

- Decision: PASS | FAIL | NO-CHANGE
- Diffs: minimal chunks
- Tests/Parsers: summary
- Rollback: snippet
