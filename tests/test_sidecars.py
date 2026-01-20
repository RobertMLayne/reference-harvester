from __future__ import annotations

import json
from pathlib import Path

from reference_harvester.sidecars import (
    SIDECAR_SCHEMA,
    build_sidecar_envelope,
    write_sidecar_json,
)


def test_write_sidecar_json_is_deterministic(tmp_path: Path) -> None:
    sidecars_dir = tmp_path / "sidecars"

    envelope = build_sidecar_envelope(
        provider="test",
        kind="record",
        stable_id="abc",
        exported_at="2026-01-01T00:00:00+00:00",
        data={"b": 2, "a": 1},
    )

    sha1, path1 = write_sidecar_json(
        sidecars_dir=sidecars_dir,
        envelope=envelope,
    )
    sha2, path2 = write_sidecar_json(
        sidecars_dir=sidecars_dir,
        envelope=envelope,
    )

    assert sha1 == sha2
    assert path1 == path2
    assert path1.name == f"{sha1}.json"

    loaded = json.loads(path1.read_text(encoding="utf-8"))
    assert loaded["schema"] == SIDECAR_SCHEMA
    assert loaded["provider"] == "test"
    assert loaded["kind"] == "record"
    assert loaded["stable_id"] == "abc"
    assert loaded["data"] == {"a": 1, "b": 2}
