from __future__ import annotations

import importlib
from pathlib import Path

cli_app = importlib.import_module("reference_harvester.cli.app")


def test_ctx_applies_run_id(tmp_path: Path) -> None:
    ctx = cli_app.build_ctx("uspto", tmp_path, run_id="r1")
    assert ctx.out_dir == (tmp_path / "uspto" / "runs" / "r1").resolve()


def test_ctx_does_not_duplicate_provider_segment(tmp_path: Path) -> None:
    provider_root = tmp_path / "uspto"
    ctx = cli_app.build_ctx("uspto", provider_root, run_id="r2")
    assert ctx.out_dir == (provider_root / "runs" / "r2").resolve()
