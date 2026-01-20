from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class SchemaValidationError:
    path: str
    message: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_instance_of_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        # bool is a subclass of int, so exclude it explicitly
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def _resolve_ref(
    schema_root: dict[str, Any],
    ref: str,
) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None

    parts = [p for p in ref[2:].split("/") if p]
    cur: Any = schema_root
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    if isinstance(cur, dict):
        return cur
    return None


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    schema_root: dict[str, Any] | None = None,
    path: str = "$",
    max_errors: int = 200,
) -> list[SchemaValidationError]:
    """Validate a JSON-like instance against a JSON Schema (draft-04 subset).

    Supported keywords:
    - $ref (internal refs only: #/...)
    - type
    - properties
    - required
    - additionalProperties (bool or schema)
    - items (schema or list-of-schemas; if list length==1, treat as uniform)
    - enum

    This is intentionally minimal and aims to be dependency-free.
    """

    root = schema_root or schema

    if "$ref" in schema and isinstance(schema["$ref"], str):
        resolved = _resolve_ref(root, schema["$ref"])
        if resolved is None:
            return [
                SchemaValidationError(
                    path=path,
                    message=f"Unsupported $ref: {schema['$ref']}",
                )
            ]
        return validate_instance(
            instance,
            resolved,
            schema_root=root,
            path=path,
            max_errors=max_errors,
        )

    errors: list[SchemaValidationError] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        if not _is_instance_of_type(instance, expected_type):
            return [
                SchemaValidationError(
                    path=path,
                    message=(
                        "Expected type " f"{expected_type}, got {_type_name(instance)}"
                    ),
                )
            ]

    enum_vals = schema.get("enum")
    if isinstance(enum_vals, list):
        if instance not in enum_vals:
            errors.append(
                SchemaValidationError(
                    path=path,
                    message="Value not in enum",
                )
            )
            return errors

    if isinstance(instance, dict):
        props = schema.get("properties")
        if isinstance(props, dict):
            required = schema.get("required")
            if isinstance(required, list):
                for key in required:
                    if isinstance(key, str) and key not in instance:
                        errors.append(
                            SchemaValidationError(
                                path=f"{path}.{key}",
                                message="Missing required property",
                            )
                        )
                        if len(errors) >= max_errors:
                            return errors

            for key, subschema in props.items():
                if key not in instance:
                    continue
                if not isinstance(subschema, dict):
                    continue
                errors.extend(
                    validate_instance(
                        instance[key],
                        subschema,
                        schema_root=root,
                        path=f"{path}.{key}",
                        max_errors=max_errors - len(errors),
                    )
                )
                if len(errors) >= max_errors:
                    return errors

        additional = schema.get("additionalProperties", True)
        if additional is False and isinstance(props, dict):
            allowed = set(props.keys())
            for key in instance.keys():
                if key not in allowed:
                    errors.append(
                        SchemaValidationError(
                            path=f"{path}.{key}",
                            message="Additional property not allowed",
                        )
                    )
                    if len(errors) >= max_errors:
                        return errors
        elif isinstance(additional, dict) and isinstance(props, dict):
            allowed = set(props.keys())
            for key, value in instance.items():
                if key in allowed:
                    continue
                errors.extend(
                    validate_instance(
                        value,
                        additional,
                        schema_root=root,
                        path=f"{path}.{key}",
                        max_errors=max_errors - len(errors),
                    )
                )
                if len(errors) >= max_errors:
                    return errors

    if isinstance(instance, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for idx, value in enumerate(instance):
                errors.extend(
                    validate_instance(
                        value,
                        items,
                        schema_root=root,
                        path=f"{path}[{idx}]",
                        max_errors=max_errors - len(errors),
                    )
                )
                if len(errors) >= max_errors:
                    return errors
        elif isinstance(items, list) and items:
            # draft-04 tuple validation. Many USPTO schemas use a single-item
            # list even when the intent is uniform array items.
            if len(items) == 1 and isinstance(items[0], dict):
                uniform = items[0]
                for idx, value in enumerate(instance):
                    errors.extend(
                        validate_instance(
                            value,
                            uniform,
                            schema_root=root,
                            path=f"{path}[{idx}]",
                            max_errors=max_errors - len(errors),
                        )
                    )
                    if len(errors) >= max_errors:
                        return errors
            else:
                for idx, subschema in enumerate(items):
                    if idx >= len(instance):
                        break
                    if not isinstance(subschema, dict):
                        continue
                    errors.extend(
                        validate_instance(
                            instance[idx],
                            subschema,
                            schema_root=root,
                            path=f"{path}[{idx}]",
                            max_errors=max_errors - len(errors),
                        )
                    )
                    if len(errors) >= max_errors:
                        return errors

    return errors


def validate_json_file(
    json_path: Path,
    schema: dict[str, Any],
    *,
    schema_root: dict[str, Any] | None = None,
    max_errors: int = 200,
) -> list[SchemaValidationError]:
    try:
        instance = load_json(json_path)
    except json.JSONDecodeError as exc:
        return [
            SchemaValidationError(
                path="$",
                message=f"Invalid JSON: {exc}",
            )
        ]

    if not isinstance(schema, dict):
        return [
            SchemaValidationError(
                path="$",
                message="Schema must be a JSON object",
            )
        ]

    return validate_instance(
        instance,
        schema,
        schema_root=schema_root,
        path="$",
        max_errors=max_errors,
    )


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def iter_json_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".json":
            yield path
