# Reference Harvester (formerly Endpoint Corpus Workbench / api-harvest-studio)

Spec-driven, multi-provider harvesting and reference export. Goals:

- Mirror provider docs/specs/assets/downloadables with explicit domain allowlists and manifests.
- Plan and fetch references/metadata, log full raw payloads, and normalize into a canonical USPTO-shaped snake_case schema with reversible mappings.
- Scrape pages/documents and emit EndNote-importable artifacts (RIS + attachments).
- Provide a spec-driven GUI that adapts to each provider’s endpoints/query terms.
- Track all outputs under `out/`, using Git LFS for binaries while keeping diffable text artifacts in Git.

## Layout

- `src/reference_harvester/` — core package (CLI, providers, registry, logging/helpers).
- `docs/` — architecture notes, output contracts.
- `out/` — run outputs (mirrors, manifests, logs, derived exports).
- `tests/` — unit/integration tests.

## Next actions

1. Flesh out provider plugin interface and copy/refactor USPTO provider pieces (mirror, inventory, download, export).
2. Add canonical field registry generation and JSONL logging at ingestion boundaries.
3. Stub the GUI (NiceGUI primary, Streamlit alt) wired to inventories/spec bundles.
4. Port EndNote export (RIS + attachments) and Scrape→Reference pipeline.
