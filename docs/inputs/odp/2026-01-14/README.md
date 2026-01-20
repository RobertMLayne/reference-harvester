# ODP inputs (2026-01-14)

Location: docs/inputs/odp/2026-01-14

## Files

- Simplified Query Syntax Open Data Portal API.pdf (source binary)
- Simplified Query Syntax Open Data Portal API.md (text extract for quick reference)
- ODP Patent Trial and Appeal Board (PTAB) Decisions.pdf (source binary)
- ODP Patent Trial and Appeal Board (PTAB) Decisions.md (text extract for quick reference)
- bulkdata-response-schema.json (schema response payload, kept as raw JSON)
- PTAB Interferences API doc pages (24 JSON doc captures) in [docs/inputs/odp/2026-01-14/ptab-interferences](docs/inputs/odp/2026-01-14/ptab-interferences/README.md)
- PTAB Appeals API doc pages (24 JSON doc captures) in [docs/inputs/odp/2026-01-14/ptab-appeals](docs/inputs/odp/2026-01-14/ptab-appeals/README.md)
- PTAB Trials API doc pages (66 JSON doc captures) in [docs/inputs/odp/2026-01-14/ptab-trials](docs/inputs/odp/2026-01-14/ptab-trials/README.md)
- Bulk Datasets API doc pages (11 JSON doc captures) in [docs/inputs/odp/2026-01-14/bulk-data](docs/inputs/odp/2026-01-14/bulk-data/README.md)
- Patent File Wrapper API doc pages (61 JSON doc captures) in [docs/inputs/odp/2026-01-14/patent-file-wrapper](docs/inputs/odp/2026-01-14/patent-file-wrapper/README.md)
- Petition Decisions API doc pages (12 JSON doc captures) in [docs/inputs/odp/2026-01-14/petition-decisions](docs/inputs/odp/2026-01-14/petition-decisions/README.md)
- Patent File Wrapper schema assets (ODP patent-data-schema.json from USPTO + sample search response) in [docs/inputs/odp/2026-01-14/pfw-schemas](docs/inputs/odp/2026-01-14/pfw-schemas/README.md)
- ODP reference guides, mappings, and downloaded PDFs in [docs/inputs/odp/2026-01-14/odp-guides](docs/inputs/odp/2026-01-14/odp-guides/README.md)

## Source and provenance

- Provided by user (local Desktop), copied intact on 2026-01-14.
- Content originates from USPTO Open Data Portal (public documentation/portal pages).

## Handling guidance

- Keep the PDFs as the source of truth; extracts are for searchability only.
- The JSON schema should remain as JSON (best practice: store machine-readable schema verbatim). If you add annotations or notes, place them in a separate README rather than editing the schema itself.
- When generating further derived outputs (e.g., CSV/MD summaries), link back to these originals and avoid embedding large excerpts in code comments or tests.
