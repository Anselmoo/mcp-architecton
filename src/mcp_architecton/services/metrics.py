from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast


def analyze_metrics_impl(code: str | None = None, files: list[str] | None = None) -> dict[str, Any]:
    """Compute code metrics (CC/MI/LOC) using radon and include Ruff results.

    Accepts either a code string or a list of file paths.
    Returns a dict with per-source metrics and linter analyses.
    """
    try:
        from radon.complexity import cc_visit  # type: ignore
        from radon.metrics import mi_visit  # type: ignore
        from radon.raw import analyze as raw_analyze  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"error": f"radon not available: {exc}"}

    if not code and not files:
        return {"error": "Provide 'code' or 'files'"}

    texts: list[tuple[str, str]] = []
    if code:
        texts.append(("<input>", code))
    if files:
        for f in files:
            p = Path(f)
            try:
                texts.append((str(p), p.read_text()))
            except Exception as exc:  # noqa: BLE001
                texts.append((str(p), f"<read-error: {exc}>"))

    results: list[dict[str, Any]] = []
    for label, text in texts:
        try:
            cc_objs: list[Any] = list(cc_visit(text))  # type: ignore[misc]
            cc: list[dict[str, Any]] = []
            for obj in cc_objs:
                cc.append(
                    {
                        "name": getattr(obj, "name", ""),
                        "type": getattr(obj, "kind", ""),
                        "complexity": getattr(obj, "complexity", None),
                        "lineno": getattr(obj, "lineno", None),
                    },
                )

            mi: Any = mi_visit(text, multi=True)  # type: ignore[misc]
            raw_val = raw_analyze(text)  # type: ignore[misc]
            raw = cast("Any", raw_val)
            results.append(
                {
                    "source": label,
                    "cyclomatic_complexity": cc,
                    "maintainability_index": mi,
                    "raw": {
                        "loc": getattr(raw, "loc", None),
                        "lloc": getattr(raw, "lloc", None),
                        "sloc": getattr(raw, "sloc", None),
                        "comments": getattr(raw, "comments", None),
                        "multi": getattr(raw, "multi", None),
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001
            results.append({"source": label, "error": str(exc)})

    # Ruff analysis (aggregated per file)
    ruff_exe = shutil.which("ruff")
    ruff_out: dict[str, Any] = {"error": "ruff CLI not available in PATH"}
    if ruff_exe:
        tmp_dir: str | None = None
        targets: list[str] = []
        try:
            if code:
                tmp_dir = tempfile.mkdtemp(prefix="ruff_")
                p = Path(tmp_dir) / "input.py"
                p.write_text(code)
                targets.append(str(p))
            if files:
                for f in files:
                    try:
                        if Path(f).is_file():
                            targets.append(f)
                    except Exception:
                        pass
            if targets:
                proc = subprocess.run(
                    [ruff_exe, "check", "--output-format", "json", *targets],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if proc.returncode in (0, 1):  # 1 indicates lint findings
                    try:
                        data = json.loads(proc.stdout or "[]")
                        # Aggregate by file path and rule code
                        agg: dict[str, dict[str, int]] = {}
                        items_list: list[dict[str, Any]] = (
                            cast("list[dict[str, Any]]", data) if isinstance(data, list) else []
                        )
                        for item in items_list:
                            try:
                                fpath = str(item.get("filename", ""))
                                code_key = str(item.get("code", ""))
                                if fpath and code_key:
                                    counts_for_file = agg.setdefault(fpath, {})
                                    counts_for_file[code_key] = counts_for_file.get(code_key, 0) + 1
                            except Exception:
                                continue
                        ruff_out = {
                            "results": [
                                {"file": fp, "counts": counts} for fp, counts in sorted(agg.items())
                            ],
                        }
                    except Exception as exc:  # noqa: BLE001
                        ruff_out = {"error": f"ruff parse error: {exc}"}
                else:
                    ruff_out = {"error": proc.stderr.strip() or "ruff failed"}
        finally:
            if tmp_dir:
                try:
                    shutil.rmtree(tmp_dir)
                except Exception:
                    pass

    return {"results": results, "ruff": ruff_out}
