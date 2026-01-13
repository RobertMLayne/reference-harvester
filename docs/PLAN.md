# Reference Harvester plan (USPTO-first, multi-provider)

## Repo naming and layout

- Primary: Reference Harvester (formerly Endpoint Corpus Workbench / api-harvest-studio).
- Alternates considered: corpus-harvester, reference-harvester, cite-harvester.
- Python src-layout with modules for providers, mirroring/harvest, inventory/spec, canonical schema/registry, logging, EndNote export, GUI, shared models.

## Output contracts

- Canonical vs derived artifacts under `out/{provider}/{domain|dataset}/{run-id}/`.
- Required manifests/logs: `manifest.jsonl`, `raw_provider.jsonl`, `normalized_canonical.jsonl`, `mapping_diagnostics.jsonl`.

## Canonical schema strategy

- USPTO is the canonical provider schema; other providers map into it.
- FieldRegistry: canonical snake_case keys, raw-key mappings/aliases, type/coercion hints, provenance via `source_paths`.
- Collisions logged; unmapped values live in `extras`.

## Mirroring strategy

- Per-provider Domain Map: allowlisted domains, seeds, discovery roots, robots/offsite/asset policies, newly discovered domain logs.
- OpenAPI bundles and endpoint inventories stored with diffs to keep current.

## Provider plugin architecture

- Provider interface exposes inventory/spec, mirror/harvest, fetch/plan/download, export (EndNote reference export).
- Copy/refactor first from existing workspace projects for these flows; avoid third-party content in committed text.

## GUI approach

- Primary: NiceGUI (Python, dynamic forms from OpenAPI). Alternate: Streamlit.
- GUI reads inventories/specs, builds jobs, runs pipelines, and lets users browse outputs/logs.

## Git LFS policy

- Default LFS for `out/**`; text overrides keep JSON/CSV/Markdown diffable.
- Global binary extensions to LFS; threshold-based exceptions for huge text.

## Execution steps

- Phase 1: skeleton + LFS + output contracts + registry stubs.
- Phase 2: copy/refactor USPTO provider (mirror, inventory, download, export) and add JSONL logging.
- Phase 3: canonical registry + mapping diagnostics + EndNote (RIS + attachments) export pipeline.
- Phase 4: GUI scaffold (spec-driven job builder) and browsing of outputs/logs.
- Phase 5: add second provider to prove extensibility.

## Risks and mitigations

- Schema drift: raw logs + registry updates; additive releases.
- Crawling scope: allowlists + manifesting discovered domains; dry-run mode.
- Performance/rate limits: backoff/retry, resumable downloads, and offline cache of mirrors.
