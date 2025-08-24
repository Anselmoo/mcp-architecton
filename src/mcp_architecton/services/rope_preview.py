from __future__ import annotations
# ruff: noqa: I001

from pathlib import Path
from typing import Any


def rope_preview_rename_impl(
    project_root: str,
    resource_path: str,
    offset: int,
    new_name: str,
) -> dict[str, Any]:
    """Preview a rename refactor using rope without applying changes.

    - project_root: base folder of the project
    - resource_path: file path relative to project_root
    - offset: character offset of the symbol to rename
    - new_name: new symbol name

    Returns dict with 'changes': list of file diffs or an 'error' on failure.
    """
    try:
        import rope.base.project  # type: ignore
        import rope.base.libutils  # type: ignore
        import rope.refactor.rename  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"error": f"rope not available: {exc}"}

    root = Path(project_root)
    if not root.exists():
        return {"error": f"project_root not found: {project_root}"}

    full_path = root / resource_path
    if not full_path.exists():
        return {"error": f"resource not found: {resource_path}"}

    project = None
    try:
        project = rope.base.project.Project(str(root))  # type: ignore[attr-defined]
        resource = project.get_file(str(full_path))  # type: ignore[attr-defined]
        rope.base.libutils.get_string_module(project, resource.read())  # type: ignore[attr-defined]
        name_finder = rope.base.libutils.get_name_at(project, resource, offset)  # type: ignore[attr-defined]
        if not name_finder:
            return {"error": "Could not resolve symbol at offset"}
        renamer = rope.refactor.rename.Rename(project, name_finder)  # type: ignore[attr-defined]
        changes = renamer.get_changes(new_name)  # type: ignore[attr-defined]
        # Extract change descriptions; we won't perform them
        result: list[dict[str, Any]] = []
        for ch in getattr(changes, "changes", []) or []:
            try:
                result.append(
                    {
                        "file": getattr(getattr(ch, "resource", None), "path", None),
                        "diff": getattr(ch, "get_description", lambda: "")(),
                    }
                )
            except Exception:  # noqa: BLE001
                continue
        return {"changes": result}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    finally:
        try:
            if project is not None:
                project.close()  # type: ignore[attr-defined]
        except Exception:
            pass


__all__ = ["rope_preview_rename_impl"]
