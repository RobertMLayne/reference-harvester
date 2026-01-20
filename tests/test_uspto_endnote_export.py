from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

provider_mod = importlib.import_module("reference_harvester.providers.uspto.provider")
sidecars_mod = importlib.import_module("reference_harvester.sidecars")


def test_export_endnote_writes_sidecar_and_ris(tmp_path: Path):
    prov = provider_mod.USPTOProvider()

    out_dir = tmp_path / "out" / "uspto"
    provider_home = out_dir / "raw" / "harvester" / provider_mod.USPTO_PROVIDER_ID
    provider_home.mkdir(parents=True, exist_ok=True)

    # Minimal manifest entry; exporter will canonicalize best-effort.
    manifest_text = (
        "["
        '{"url": "https://example.test/doc", '
        '"documentURL": "https://example.test/doc"}'
        "]\n"
    )
    (provider_home / "manifest.json").write_text(
        manifest_text,
        encoding="utf-8",
    )

    ctx = SimpleNamespace(name="uspto", out_dir=out_dir)
    prov.export_endnote(ctx)

    endnote_dir = out_dir / "endnote"
    assert (endnote_dir / "reference_type_table.xml").exists()

    ris_path = endnote_dir / "uspto.ris"
    assert ris_path.exists()

    sidecars_dir = endnote_dir / "sidecars"
    assert sidecars_dir.exists()

    sidecars = sorted(sidecars_dir.glob("*.json"))
    # One bulk-manifest sidecar + one per-record sidecar.
    assert len(sidecars) == 2

    ris_text = ris_path.read_text(encoding="utf-8")

    # Bulk manifest should include a URL and endpoint summary keywords.
    assert "TI  - USPTO Bulk Manifest" in ris_text
    assert "UR  - " in ris_text
    assert "KW  - endpoint:" in ris_text

    # Bulk sidecar should include the richer manifest fields.
    bulk_sidecar_path = None
    for p in sidecars:
        envelope = json.loads(p.read_text(encoding="utf-8"))
        if envelope.get("kind") == "bulk_manifest":
            bulk_sidecar_path = p
            bulk_envelope = envelope
            break

    assert bulk_sidecar_path is not None
    assert bulk_envelope["schema"] == sidecars_mod.SIDECAR_SCHEMA
    assert bulk_envelope["provider"] == "uspto"
    assert bulk_envelope["stable_id"].startswith("bulk:")
    bulk_payload = bulk_envelope["data"]
    assert bulk_payload.get("url")
    assert "observed_date_min" in bulk_payload
    assert "observed_date_max" in bulk_payload
    assert isinstance(bulk_payload.get("endpoint_counts"), dict)
    assert isinstance(bulk_payload.get("bulk_artifacts"), list)

    # Ensure RIS references both sidecars and that each C8 matches its file.
    l1_lines = [line for line in ris_text.splitlines() if line.startswith("L1  - ")]
    assert len(l1_lines) == 2
    referenced_stems: set[str] = set()
    for line in l1_lines:
        rel = line.split("-", 1)[1].strip()
        assert rel.startswith("sidecars/")
        referenced = endnote_dir / rel
        assert referenced.exists()
        referenced_stems.add(referenced.stem)

    c8_lines = [line for line in ris_text.splitlines() if line.startswith("C8  - ")]
    assert len(c8_lines) == 2
    c8_values = {line.split("-", 1)[1].strip() for line in c8_lines}
    assert referenced_stems == c8_values

    # Bulk manifest + at least one record reference.
    an_lines = [line for line in ris_text.splitlines() if line.startswith("AN  - ")]
    assert len(an_lines) == 2
    an_values = [line.split("-", 1)[1].strip() for line in an_lines]
    assert any(v.startswith("uspto:bulk:") for v in an_values)
    assert any(
        v.startswith("uspto:") and not v.startswith("uspto:bulk:") for v in an_values
    )
