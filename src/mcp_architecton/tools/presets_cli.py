from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, cast


def _presets_path() -> Path:
    # Resolve repo-root relative to this file
    return Path(__file__).resolve().parents[3] / "data" / "prompt_presets.json"


def _load() -> Dict[str, List[Mapping[str, Any]]]:
    p = _presets_path()
    try:
        raw_obj: object = json.loads(p.read_text())
        typed_raw: Dict[str, Any] = (
            cast(Dict[str, Any], raw_obj) if isinstance(raw_obj, dict) else {}
        )
        prompts_obj: object = typed_raw.get("prompts", [])
        subruns_obj: object = typed_raw.get("subruns", [])

        # normalize to list of mappings
        def _coerce(lst_obj: object) -> List[Mapping[str, Any]]:
            if isinstance(lst_obj, list):
                items: List[object] = cast(List[object], lst_obj)
                result: List[Mapping[str, Any]] = []
                for x_obj in items:
                    if isinstance(x_obj, Mapping):
                        result.append(cast(Mapping[str, Any], x_obj))
                return result
            return []

        return {"prompts": _coerce(prompts_obj), "subruns": _coerce(subruns_obj)}
    except Exception:
        return {"prompts": [], "subruns": []}


def cmd_list(args: argparse.Namespace) -> int:
    data = _load()
    kind: str = args.kind
    items: List[Mapping[str, Any]] = data.get(kind, [])
    for it in items:
        _id = str(it.get("id", ""))
        name = str(it.get("name", ""))
        print(f"{_id}\t{name}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    data = _load()
    kind: str = args.kind
    target_id: str = args.id
    for it in data.get(kind, []):
        if str(it.get("id", "")) == target_id:
            print(str(it.get("body", "")))
            return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="architecton-presets", add_help=True)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List prompt or subrun presets")
    p_list.add_argument("kind", choices=["prompts", "subruns"], help="Preset kind")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Print a preset body by id")
    p_show.add_argument("kind", choices=["prompts", "subruns"], help="Preset kind")
    p_show.add_argument("id", help="Preset id")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
