from __future__ import annotations

import sys
from pathlib import Path

import pytest

from reference_harvester.providers import harvester_import as hi


def _reset_caches() -> None:
    hi.clear_harvester_import_caches()


def test_env_override_and_sys_path(monkeypatch, tmp_path: Path) -> None:
    harv_root = tmp_path / "harvester"
    harv_root.mkdir()

    monkeypatch.setenv("REFERENCE_HARVESTER_PATH", str(harv_root))
    monkeypatch.setattr(sys, "path", sys.path.copy())

    _reset_caches()
    resolved = hi.resolve_harvester_root()
    assert resolved == harv_root

    before = list(sys.path)
    added = hi.ensure_harvester_on_path()
    assert added == harv_root
    assert sys.path[0] == str(harv_root)
    assert len([p for p in sys.path if p == str(harv_root)]) == 1
    assert sys.path[1:] == before

    _reset_caches()
    monkeypatch.delenv("REFERENCE_HARVESTER_PATH", raising=False)


def test_missing_path_raises_runtimeerror(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    monkeypatch.setattr(
        hi,
        "_candidate_harvester_paths",
        lambda _here: [missing],
    )
    _reset_caches()

    with pytest.raises(RuntimeError):
        hi.resolve_harvester_root()


def test_cache_clear_refreshes_resolution(monkeypatch, tmp_path: Path) -> None:
    path_one = tmp_path / "one"
    path_two = tmp_path / "two"
    path_one.mkdir()
    path_two.mkdir()

    monkeypatch.setattr(
        hi,
        "_candidate_harvester_paths",
        lambda _here: [path_one, path_two],
    )
    _reset_caches()
    assert hi.resolve_harvester_root() == path_one

    monkeypatch.setattr(
        hi,
        "_candidate_harvester_paths",
        lambda _here: [path_two],
    )
    assert hi.resolve_harvester_root() == path_one

    _reset_caches()
    assert hi.resolve_harvester_root() == path_two


def test_ensure_harvester_on_path_inserts_once(
    monkeypatch, tmp_path: Path
) -> None:
    target = tmp_path / "harv"
    target.mkdir()

    monkeypatch.setattr(hi, "resolve_harvester_root", lambda: target)
    monkeypatch.setattr(sys, "path", ["orig"])

    first = hi.ensure_harvester_on_path()
    second = hi.ensure_harvester_on_path()

    assert first == target
    assert second == target
    assert sys.path[0] == str(target)
    assert sys.path[1:] == ["orig"]
    assert len([p for p in sys.path if p == str(target)]) == 1
