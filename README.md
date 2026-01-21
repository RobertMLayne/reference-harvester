# Reference Harvester (formerly Endpoint Corpus Workbench / api-harvest-studio)

Spec-driven, multi-provider harvesting and reference export. Goals:

- Mirror provider docs/specs/assets/downloadables with explicit domain allowlists and manifests.
- Plan and fetch references/metadata, log full raw payloads, and normalize into a canonical USPTO-shaped snake_case schema with reversible mappings.
- Scrape pages/documents and emit EndNote-importable artifacts (RIS + attachments).
- Provide a spec-driven GUI that adapts to each provider’s endpoints/query terms.
- Write all run outputs under `out/` (generated; ignored by default in Git).

EndNote reference type table constraints and the project’s no-loss mapping approach are documented in [docs/endnote_mapping.md](docs/endnote_mapping.md).

## Layout

- `src/reference_harvester/` — core package (CLI, providers, registry, logging/helpers).
- `docs/` — architecture notes, output contracts.
- `out/` — run outputs (mirrors, manifests, logs, derived exports); not committed.
- `tests/` — unit/integration tests.

## Providers

- `uspto` — USPTO Open Data (swagger + bulk assets)
- `openalex` — OpenAlex works search + light docs mirroring (no API key; supports polite `mailto`)

Example (OpenAlex):

- Inventory: `reference-harvester inventory openalex`
- Harvest docs seeds: `reference-harvester harvest openalex --email you@example.com --max-pages 4`
  - Or set `OPENALEX_EMAIL` in your environment.
- Fetch: `reference-harvester fetch openalex --query "ptab" --per-page 25 --max-pages 1 --email you@example.com`
- Export EndNote: `reference-harvester endnote openalex`

See [docs/openalex.md](docs/openalex.md) for inventory/harvest outputs and options.

## Next actions

1. Document provider-specific inventories/mirroring and their seed lists.
2. Expand the GUI scaffolding (NiceGUI primary, Streamlit alt) wired to inventories.
3. Add additional providers and/or richer citation exports.
