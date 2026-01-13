from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Tuple

from reference_harvester.models import (
    MappingDiagnostics,
    NormalizedRecord,
)
from reference_harvester.registry import FieldRegistry, raw_key_lookup


def snake_case(key: str) -> str:
    key = key.replace(".", "_")
    key = re.sub(r"[\-\s]+", "_", key)
    key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return key.lower()


def _flatten_items(
    payload: Mapping[str, Any], prefix: str = ""
) -> Iterable[tuple[str, Any]]:
    for raw_key, value in payload.items():
        path = f"{prefix}.{raw_key}" if prefix else raw_key
        if isinstance(value, Mapping):
            yield from _flatten_items(value, path)
        else:
            yield path, value


def canonicalize_payload(
    payload: dict[str, Any], registry: FieldRegistry
) -> tuple[NormalizedRecord, MappingDiagnostics]:
    reverse = raw_key_lookup(registry)
    normalized: dict[str, Any] = {}
    extras: dict[str, Any] = {}
    source_paths: dict[str, str] = {}
    collisions: dict[str, list[str]] = {}
    unknown_keys: list[str] = []
    diagnostics_coercions: dict[str, str] = {}

    for raw_key, value in _flatten_items(payload):
        canonical = reverse.get(raw_key)
        if canonical is None:
            unknown_keys.append(raw_key)
            extras[snake_case(raw_key)] = value
            continue
        if canonical in normalized:
            collisions.setdefault(canonical, []).append(raw_key)
            continue
        coerced, coercion_note = _coerce_value(
            value,
            registry.fields[canonical].type_hint,
        )
        normalized[canonical] = coerced
        source_paths[canonical] = raw_key
        if coercion_note:
            diagnostics_coercions[canonical] = coercion_note

    record = NormalizedRecord(
        canonical=normalized,
        extras=extras,
        source_paths=source_paths,
    )
    diagnostics = MappingDiagnostics(
        source_url=str(payload.get("url") or payload.get("documentURL") or ""),
        collisions=collisions,
        unknown_keys=unknown_keys,
        coercions=diagnostics_coercions,
    )
    return record, diagnostics


def _coerce_value(value: Any, type_hint: str | None) -> Tuple[Any, str | None]:
    if type_hint is None:
        return value, None

    hint = type_hint.lower()
    if hint in {"int", "integer"}:
        if isinstance(value, int):
            return value, None
        if isinstance(value, str) and value.isdigit():
            # Record that coercion is possible but preserve the original
            # string to keep first-wins semantics when collisions occur.
            return value, "coercible from str to int"
        return value, None

    if hint in {"float", "number"}:
        if isinstance(value, (int, float)):
            return value, None
        if isinstance(value, str):
            try:
                return float(value), "coerced from str to float"
            except ValueError:
                return value, None

    return value, None


def canonicalize_batch(
    payloads: Iterable[dict[str, Any]], registry: FieldRegistry
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return lists of normalized and diagnostics dicts for JSONL writing."""

    normalized_records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for payload in payloads:
        record, diag = canonicalize_payload(payload, registry)
        normalized_records.append(
            {
                "canonical": record.canonical,
                "extras": record.extras,
                "source_paths": record.source_paths,
            }
        )
        diagnostics.append(
            {
                "source_url": diag.source_url,
                "collisions": diag.collisions,
                "unknown_keys": diag.unknown_keys,
                "coercions": diag.coercions,
            }
        )
    return normalized_records, diagnostics


__all__ = ["canonicalize_batch", "canonicalize_payload", "snake_case"]
