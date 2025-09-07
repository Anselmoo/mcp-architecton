from __future__ import annotations

import libcst as cst
from libcst import parse_module
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor


class _AddTypeHints(cst.CSTTransformer):
    """Annotate untyped function params and returns with `Any`.

    - Skips parameters named `self` or `cls`.
    - Sets `changed` when any change is made so callers can detect idempotence.
    """

    def __init__(self) -> None:
        super().__init__()
        self.changed = False

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:  # noqa: N802
        if updated_node.annotation is None and updated_node.name.value not in {"self", "cls"}:
            self.changed = True
            return updated_node.with_changes(annotation=cst.Annotation(cst.Name("Any")))
        return updated_node

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        if updated_node.returns is None and updated_node.name.value != "__init__":
            self.changed = True
            return updated_node.with_changes(returns=cst.Annotation(cst.Name("Any")))
        return updated_node


def add_type_hints_to_code(source: str) -> tuple[bool, str]:
    """Return (changed, code) with Any annotations added where missing.

    Preserves formatting and comments. Adds `from typing import Any` when changes occur.
    """
    try:
        mod = parse_module(source)
    except Exception:
        return (False, source)

    transformer = _AddTypeHints()
    new_mod = mod.visit(transformer)
    if not transformer.changed:
        return (False, source)

    # Ensure `Any` import is present
    ctx = CodemodContext()
    AddImportsVisitor.add_needed_import(ctx, "typing", "Any")
    new_mod2 = AddImportsVisitor(ctx).transform_module(new_mod)
    return (True, new_mod2.code)


__all__ = ["add_type_hints_to_code"]
