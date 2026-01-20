from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SIDECAR_SCHEMA = "reference-harvester.sidecar.v1"


def build_sidecar_envelope(
    *,
    provider: str,
    kind: str,
    stable_id: str,
    exported_at: str,
    data: Mapping[str, Any],
    schema: str = SIDECAR_SCHEMA,
    schema_version: int = 1,
) -> dict[str, Any]:
    """Build a provider-neutral, versioned sidecar envelope.

    Contract:
    - Top-level keys are stable across providers.
    - Provider-specific payload lives under `data`.
    """

    return {
        "schema": schema,
        "schema_version": schema_version,
        "provider": provider,
        "kind": kind,
        "exported_at": exported_at,
        "stable_id": stable_id,
        "data": dict(data),
    }


def dump_sidecar_text(envelope: Mapping[str, Any]) -> str:
    """Deterministic JSON serialization for hashing and on-disk storage."""

    return json.dumps(
        envelope,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_sidecar_json(
    *,
    sidecars_dir: Path,
    envelope: Mapping[str, Any],
) -> tuple[str, Path]:
    """Write `envelope` to `sidecars_dir/<sha256>.json`.

    Returns (sha256_hex, sidecar_path).
    """

    sidecars_dir.mkdir(parents=True, exist_ok=True)
    text = dump_sidecar_text(envelope)
    sha256 = sha256_hex(text)
    path = sidecars_dir / f"{sha256}.json"
    if not path.exists():
        path.write_text(text + "\n", encoding="utf-8")
    return sha256, path
