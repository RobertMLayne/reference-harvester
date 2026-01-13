import importlib
from importlib import resources
from pathlib import Path
from typing import Any, cast

canonicalizer_mod = importlib.import_module(
    "reference_harvester.canonicalizer"
)
registry_mod = importlib.import_module("reference_harvester.registry")
canonicalize_payload = cast(Any, canonicalizer_mod).canonicalize_payload
load_registry = cast(Any, registry_mod).load_registry


def _registry():
    packaged = resources.files("reference_harvester.registry").joinpath(
        "uspto_fields.yaml"
    )
    return load_registry(Path(str(packaged)))


def test_manifest_entry_maps_core_fields():
    payload = {
        "url": "https://data.uspto.gov/docs/foo.html",
        "local_path": "raw/harvester/uspto/foo.html",
        "status_code": 200,
        "fetched_at": "2024-01-01T00:00:00Z",
        "sha256": "abc",
        "content_type": "text/html",
        "_manifest": "uspto/mirror/manifest.json",
        "documentURL": "https://data.uspto.gov/docs/foo.html",
        "applicationNumber": "12345",
    }

    record, diag = canonicalize_payload(payload, _registry())

    assert record.canonical["url"] == payload["url"]
    assert record.canonical["local_path"] == payload["local_path"]
    assert record.canonical["status_code"] == payload["status_code"]
    assert record.canonical["harvester_manifest"] == payload["_manifest"]
    assert record.canonical["application_number"] == "12345"
    assert record.canonical["document_url"] == payload["documentURL"]
    assert record.extras == {}
    assert diag.unknown_keys == []


def test_unknown_fields_fall_into_extras():
    payload = {
        "url": "https://data.uspto.gov/docs/bar.json",
        "local_path": "raw/harvester/uspto/bar.json",
        "status_code": 200,
        "mysteryField": "value",
    }

    record, diag = canonicalize_payload(payload, _registry())

    assert "mystery_field" in record.extras
    assert "mysteryField" in diag.unknown_keys


def test_collisions_and_coercions_recorded():
    payload = {
        "url": "https://data.uspto.gov/docs/baz.json",
        "local_path": "raw/harvester/uspto/baz.json",
        "status_code": "200",
        "sha256": "abc",
        "applicationNumber": "12345",
        "applicationFilingDate": "2024-01-02",
        "documentURL": "https://data.uspto.gov/docs/baz.json",
        "status_code_duplicate": 200,
    }

    record, diag = canonicalize_payload(payload, _registry())

    # First mapping wins, duplicate should register a collision
    assert record.canonical["status_code"] == "200"
    assert diag.collisions["status_code"] == ["status_code_duplicate"]

    # Coercion of status_code from str -> int should be logged when hinted
    assert "status_code" in diag.coercions


def test_nested_mapping_keys_are_flattened():
    payload = {
        "trialMetaData": {
            "trialStatusCategory": "Pending",
            "trialTypeCode": "IPR",
        },
        "patentOwnerData": {"patentNumber": "123"},
        "trialNumber": "IPR2026-00001",
    }

    record, diag = canonicalize_payload(payload, _registry())

    assert record.canonical["status"] == "Pending"
    assert record.canonical["type"] == "IPR"
    assert record.canonical["owner_patent_number"] == "123"
    assert diag.unknown_keys == []
