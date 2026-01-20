from __future__ import annotations

import json
from pathlib import Path

from reference_harvester.schema_validation import validate_json_file


def test_validate_json_file_catches_type_mismatch(tmp_path: Path) -> None:
    schema = {
        "type": "object",
        "properties": {"count": {"type": "integer"}},
    }
    doc = {"count": "not-an-int"}

    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema) + "\n", encoding="utf-8")

    doc_path = tmp_path / "doc.json"
    doc_path.write_text(json.dumps(doc) + "\n", encoding="utf-8")

    loaded_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = validate_json_file(doc_path, loaded_schema)
    assert errors
    assert any("Expected type integer" in err.message for err in errors)


def test_validate_json_file_allows_tuple_items_singleton_list(
    tmp_path: Path,
) -> None:
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                # Draft-04 tuple validation; singleton list should behave
                # like a uniform items schema.
                "items": [{"type": "string"}],
            }
        },
    }

    doc = {"items": ["a", "b"]}

    doc_path = tmp_path / "doc.json"
    doc_path.write_text(json.dumps(doc) + "\n", encoding="utf-8")

    errors = validate_json_file(doc_path, schema)
    assert errors == []
