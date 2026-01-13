# Output layout and contracts

Run outputs live under `out/{providerName}/{domainOrDataset}/{runId}/` with a clear split between canonical and derived artifacts.

## Canonical artifacts (always captured)

- `manifest.jsonl` — event log of fetch/mirror steps with status, URLs, hashes, and local paths.
- `raw_provider.jsonl` — full provider payloads plus HTTP metadata (status, headers, request URL, retrieval timestamps).
- `normalized_canonical.jsonl` — payloads mapped into canonical snake_case fields (USPTO-shaped) with `extras` holding unmapped data.
- `mapping_diagnostics.jsonl` — per-record provenance: source paths, collisions, coercions, unknown keys.

## Derived artifacts (may be re-generated)

- `inventories/` — OpenAPI bundles, endpoint inventories, diffs.
- `exports/` — Markdown/HTML conversions, citations.
- `endnote/` — RIS plus attachments folder for import.
- `reports/` — summaries, validation results.

## Folder conventions

- `mirror/` — mirrored docs/specs/assets (LFS by default).
- `downloads/` — binary payloads and headers (LFS by default).
- `logs/` — JSONL artifacts above; text overrides keep them diffable.
- `derived/` — optional recomputable views (indexes, summaries, GUI caches).

Keep `out/` tracked in Git with LFS applied to binaries and mirror/download content; text overrides keep JSON/CSV/Markdown diffable.
