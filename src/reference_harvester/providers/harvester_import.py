from __future__ import annotations

import os
import sys
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Iterable


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered


def _candidate_harvester_paths(here: Path) -> list[Path]:
    env = os.environ.get("REFERENCE_HARVESTER_PATH")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))

    for parent in here.parents:
        candidates.extend(
            [
                parent / "harvester",
                parent / "fetch-uspto" / "harvester",
                parent / "ingest" / "fetch-uspto" / "harvester",
            ]
        )

    return _dedupe(candidates)


def harvester_root_candidates() -> list[Path]:
    """Return candidate harvester roots in search order (env-first, deduped)."""

    here = Path(__file__).resolve()
    return _candidate_harvester_paths(here)


@lru_cache(maxsize=1)
def resolve_harvester_root() -> Path:
    """Locate the harvester root from env or common sibling locations."""

    here = Path(__file__).resolve()
    for candidate in _candidate_harvester_paths(here):
        if candidate.is_dir():
            return candidate
    raise RuntimeError(
        "Unable to locate 'harvester' package; set REFERENCE_HARVESTER_PATH"
    )


def ensure_harvester_on_path() -> Path:
    root = resolve_harvester_root()
    root_str = str(root)
    if root_str not in sys.path:
        # Prepend so the resolved harvester wins over unrelated site packages.
        sys.path.insert(0, root_str)
    return root


@lru_cache(maxsize=None)
def import_harvester_module(module_path: str):
    ensure_harvester_on_path()
    return import_module(module_path)


def clear_harvester_import_caches() -> None:
    resolve_harvester_root.cache_clear()
    import_harvester_module.cache_clear()


__all__ = [
    "clear_harvester_import_caches",
    "ensure_harvester_on_path",
    "harvester_root_candidates",
    "import_harvester_module",
    "resolve_harvester_root",
]
