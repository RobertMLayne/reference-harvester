# Output layout and contracts

Current implementation is **provider-scoped** under `out/<provider>/...`.

The CLI also supports an optional `--run-id` which writes under:

- `out/<provider>/runs/<run-id>/...`

Target architecture (planned, not yet implemented) is run-scoped under `out/<provider>/<domain|dataset>/<run-id>/...`.

## Canonical artifacts (always captured)

- `manifest.jsonl` — artifact index (counts of the JSONL files written in this run).
- `raw_provider.jsonl` — provider-native raw records (either raw API payloads or manifest-style items).
- `normalized_canonical.jsonl` — raw records mapped into canonical snake_case fields (per the provider registry, e.g. `uspto_fields.yaml` or `openalex_fields.yaml`), with `extras` holding unmapped data.
- `mapping_diagnostics.jsonl` — per-record mapping diagnostics: collisions, coercions, and unknown keys.

## Derived artifacts (may be re-generated)

- `artifacts/` — OpenAPI bundles, endpoint inventories, coverage, diffs.
  - OpenAlex adds `robots_inventory.{json,jsonl}` and `robots/*.txt` snapshots.
- `api_samples/` — downloaded API sample payloads plus per-sample manifest.
- `endnote/` — RefTypes XML and RIS exports, plus per-record sidecar attachments.
  - `endnote/uspto.ris` (provider-specific RIS)
  - `endnote/openalex.ris` (provider-specific RIS)
  - `endnote/sidecars/<sha256>.json` (lossless payload: bulk manifest + per-record)
    - Sidecars are JSON envelopes with stable top-level keys (`schema`, `schema_version`, `provider`, `kind`, `exported_at`, `stable_id`) and provider-specific content under `data`.
- `logs/reports/` — validation and summary reports.

## Folder conventions

- `raw/harvester/<provider-id>/html/` — crawled HTML pages.
- `raw/harvester/<provider-id>/assets/` — crawled non-HTML assets.
- `raw/harvester/<provider-id>/api_samples/` — API sample payloads.
- `raw/harvester/<provider-id>/logs/` — JSONL exports and citation artifacts.
  - OpenAlex `harvest` also writes `mirror_manifest.{json,jsonl}` under `logs/`.

`out/` and `raw/harvester/` are generated outputs and are ignored by default in Git.
Commit only curated, human-maintained docs under `docs/` (and optionally small, stable example artifacts).
