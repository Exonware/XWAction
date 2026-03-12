from __future__ import annotations
import sys
from pathlib import Path
from typing import Any


def _find_monorepo_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / "xwaction").is_dir() and (p / "xwsystem").is_dir():
            return p
    return start


def _add_monorepo_src_paths() -> None:
    monorepo_root = _find_monorepo_root(Path(__file__).resolve())
    for pkg in ("xwaction", "xwsystem", "xwschema", "xwdata", "xwnode", "xwformats", "xwsyntax", "xwquery"):
        src = monorepo_root / pkg / "src"
        if src.is_dir():
            sys.path.insert(0, str(src))
_add_monorepo_src_paths()
from exonware.xwaction import XWAction  # noqa: E402
from exonware.xwsystem.io.serialization import get_serialization_registry  # noqa: E402


def load_catalog(path: Path) -> dict[str, Any]:
    registry = get_serialization_registry()
    serializer = registry.detect_from_file(path)
    if serializer is None:
        raise RuntimeError(f"No serializer found for: {path}")
    data = serializer.load_file(path)
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict from {path}, got {type(data).__name__}")
    # XML outputs are commonly wrapped in a single root element (e.g. {"xwaction_actions": {...}})
    if len(data) == 1:
        only_val = next(iter(data.values()))
        if isinstance(only_val, dict):
            data = only_val
    return data


def reconstruct_actions(catalog: dict[str, Any]) -> dict[str, list[XWAction]]:
    actions_native = catalog.get("actions_native_by_entity", {})
    if not isinstance(actions_native, dict):
        raise TypeError("catalog['actions_native_by_entity'] must be a dict")
    out: dict[str, list[XWAction]] = {}
    for entity, action_dicts in actions_native.items():
        if not isinstance(entity, str):
            continue
        if not isinstance(action_dicts, list):
            continue
        out[entity] = []
        for action_dict in action_dicts:
            if not isinstance(action_dict, dict):
                continue
            out[entity].append(XWAction.from_native(action_dict))  # type: ignore[arg-type]
    return out


def print_summary(path: Path, actions: dict[str, list[XWAction]]) -> None:
    total = sum(len(v) for v in actions.values())
    print(f"\nLoaded: {path.name}")
    print(f"- entities: {sorted(actions.keys())}")
    print(f"- total actions: {total}")
    for entity, acts in actions.items():
        sample = ", ".join(a.api_name for a in acts[:5])
        print(f"  - {entity}: {len(acts)} ({sample}{'...' if len(acts) > 5 else ''})")


def main() -> None:
    out_dir = Path(__file__).parent / "out"
    files = [
        out_dir / "actions.json",
        out_dir / "actions.yaml",
        out_dir / "actions.toml",
        out_dir / "actions.xml",
    ]
    for f in files:
        catalog = load_catalog(f)
        actions = reconstruct_actions(catalog)
        print_summary(f, actions)
if __name__ == "__main__":
    main()
