import importlib
import json
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


def _sample_records():
    sample_path = Path(__file__).parent / "fixtures" / "ptab_proceedings.json"
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    return data["patentTrialProceedingDataBag"]


def test_ptab_primary_mapping():
    record, diag = canonicalize_payload(_sample_records()[0], _registry())
    canonical = record.canonical

    assert canonical["trial_number"] == "IPR2026-00195"
    assert canonical["type"] == "IPR"
    assert canonical["status"] == "Pending"
    assert canonical["petition_filed_at"] == "2026-01-09"
    assert canonical["file_url"].endswith("IPR2026-00195.zip")
    assert canonical["owner_patent_number"] == "10250877"
    assert canonical["owner_application_number"] == "14372021"
    assert canonical["owner_inventor"] == "Philippe Bordes et al"
    assert canonical["tc"] == "2400"
    assert canonical["art_unit"] == "2486"
    assert canonical["grant_date"] == "2019-04-02"
    assert canonical["petitioner_rpi"] == "Amazon.com, Inc. et al."
    assert canonical["petitioner_counsel"] == "Kaiser, Jessicaet al"
    assert canonical["last_modified_at"] == "2026-01-13T00:58:22"
    assert canonical["last_modified_date"] == "2026-01-09"
    assert diag.unknown_keys == []


def test_ptab_optional_fields():
    record, diag = canonicalize_payload(_sample_records()[1], _registry())
    canonical = record.canonical

    assert canonical["accorded_filing_date"] == "2026-01-05"
    assert canonical["petition_filed_at"] == "2026-01-05"
    assert canonical["file_url"].endswith("IPR2026-00192.zip")
    assert diag.unknown_keys == []


def test_ptab_owner_rpi_and_counsel():
    record, diag = canonicalize_payload(_sample_records()[2], _registry())
    canonical = record.canonical

    assert canonical["owner_rpi"] == "Sandpiper CDN, LLC"
    assert canonical["owner_counsel"] == "Eisenberg, Jasonet al"
    assert canonical["petitioner_rpi"] == "Microsoft Corporation"
    assert canonical["petitioner_counsel"] == "Kaiser, Jessicaet al"
    assert diag.unknown_keys == []
