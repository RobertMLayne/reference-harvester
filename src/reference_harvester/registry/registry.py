from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]


@dataclass
class CanonicalField:
    name: str
    raw_keys: list[str]
    type_hint: str | None = None
    description: str | None = None
    passthrough: bool = False


@dataclass
class FieldRegistry:
    canonical_provider: str
    fields: dict[str, CanonicalField]


def load_registry(path: str | Path) -> FieldRegistry:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    fields: dict[str, CanonicalField] = {}
    for name, cfg in data.get("fields", {}).items():
        fields[name] = CanonicalField(
            name=name,
            raw_keys=list(cfg.get("raw_keys", [])),
            type_hint=cfg.get("type"),
            description=cfg.get("description"),
            passthrough=bool(cfg.get("passthrough", False)),
        )
    return FieldRegistry(
        canonical_provider=str(data.get("canonical_provider", "")),
        fields=fields,
    )


def canonical_fields(registry: FieldRegistry) -> list[str]:
    return list(registry.fields.keys())


def raw_key_lookup(registry: FieldRegistry) -> dict[str, str]:
    """Return reverse lookup raw_key -> canonical."""

    reverse: dict[str, str] = {}
    for canonical, field in registry.fields.items():
        for raw in field.raw_keys:
            reverse[raw] = canonical
    return reverse


__all__ = [
    "CanonicalField",
    "FieldRegistry",
    "canonical_fields",
    "load_registry",
    "raw_key_lookup",
]
