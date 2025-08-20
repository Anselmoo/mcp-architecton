from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

from mcp_architecton.refactors import transform_code as _strategy_transform
from mcp_architecton.snippets.aliases import NAME_ALIASES as _name_aliases
from mcp_architecton.snippets.api import get_snippet
from mcp_architecton.snippets.api import transform_code as _snippet_transform


def _canonical_pattern_name(name: str | None) -> str:
    raw = (name or "").strip().lower()
    return _name_aliases.get(raw, raw)


def _apply_to_text(name: str, text: str) -> Tuple[bool, str]:
    # Enhanced: Try intelligent refactoring first
    try:
        from mcp_architecton.analysis.refactoring_engine import intelligent_refactor
        
        # Attempt intelligent refactoring
        refactor_result = intelligent_refactor(text, name)
        transformation_result = refactor_result.get("transformation_result", {})
        
        if (transformation_result.get("success") and 
            transformation_result.get("transformed_code") and
            transformation_result["transformed_code"] != text):
            return True, transformation_result["transformed_code"]
    
    except ImportError:
        # Fall back to existing logic if intelligent refactoring not available
        pass
    
    # Try strategy transform first (existing logic)
    if _strategy_transform is not None:
        try:
            out = _strategy_transform(name, text)
            if isinstance(out, str) and out != text:
                return True, out
        except Exception:
            pass
    # Then snippets transform
    if _snippet_transform is not None:
        try:
            out = _snippet_transform(name, text)
            if isinstance(out, str) and out != text:
                return True, out
        except Exception:
            pass
    return False, text


def _append_snippet_if_missing(name: str, text: str) -> Tuple[bool, str]:
    try:
        key = _canonical_pattern_name(name)
    except Exception:
        key = (name or "").strip().lower()
    marker = f"# --- mcp-architecton snippet: {key} ---"
    if marker in text:
        return False, text
    try:
        snippet = get_snippet(name)
    except Exception:
        snippet = None
    if not snippet:
        return False, text
    appended = (
        text.rstrip() + "\n\n" + marker + "\n" + snippet.rstrip() + "\n# --- end snippet ---\n"
    )
    # Cleanup with best available transform
    changed, out = _apply_to_text(name, appended)
    return True, (out if changed else appended)


def _diff(a: str, b: str, fname: str) -> str:
    try:
        import difflib

        return "".join(
            difflib.unified_diff(
                a.splitlines(True), b.splitlines(True), fromfile=fname, tofile=fname
            )
        )
    except Exception:
        return ""


def introduce_impl(
    *,
    name: str,
    module_path: str,
    dry_run: bool = False,
    out_path: str | None = None,
) -> dict[str, Any]:
    base = Path(module_path)
    if not base.exists():
        return {"status": "error", "error": f"Path not found: {module_path}"}

    if base.is_dir():
        changes: list[dict[str, Any]] = []
        for p in sorted(base.rglob("*.py")):
            try:
                before = p.read_text()
            except (FileNotFoundError, PermissionError, OSError) as exc:
                changes.append({"file": str(p), "error": str(exc)})
                continue
            changed, after = _apply_to_text(name, before)
            if not changed:
                appended, after2 = _append_snippet_if_missing(name, after)
                if appended:
                    changed, after = True, after2
            entry: dict[str, Any] = {"file": str(p), "changed": changed}
            if changed:
                entry["diff"] = _diff(before, after, str(p))
            if changed and not dry_run:
                if out_path:
                    outp = Path(out_path) / p.relative_to(base)
                    outp.parent.mkdir(parents=True, exist_ok=True)
                    outp.write_text(after)
                    entry["written_to"] = str(outp)
                else:
                    p.write_text(after)
            changes.append(entry)
        return {
            "status": "ok",
            "mode": "transformed-dir",
            "dry_run": dry_run,
            "target": str(base),
            "changes": changes,
        }

    # Single file
    try:
        before = base.read_text()
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return {"status": "error", "error": str(exc), "target": str(base)}
    changed, after = _apply_to_text(name, before)
    if not changed:
        appended, after2 = _append_snippet_if_missing(name, after)
        if appended:
            changed, after = True, after2
    res: dict[str, Any] = {
        "status": "ok",
        "mode": "transformed-file",
        "dry_run": dry_run,
        "target": str(base),
        "changed": changed,
    }
    if changed:
        res["diff"] = _diff(before, after, str(base))
        if not dry_run:
            if out_path:
                outp = Path(out_path)
                outp.parent.mkdir(parents=True, exist_ok=True)
                outp.write_text(after)
                res["written_to"] = str(outp)
            else:
                base.write_text(after)
    return res
