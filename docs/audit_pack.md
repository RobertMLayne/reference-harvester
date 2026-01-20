# Audit Pack: Reference Harvester

This document is a repo-wide “audit pack” focused on:

- Entry points and end-to-end data flow
- Output contracts vs current implementation
- Data contracts and schema enforcement
- EndNote interoperability requirements
- A prioritized fix list with testable acceptance criteria

## 1) Entrypoints and call graph (current)

### CLI

Primary CLI is defined in `src/reference_harvester/cli/app.py`.

- `inventory` → `ProviderPlugin.refresh_inventory(ctx)`
- `harvest` → `ProviderPlugin.mirror_sources(ctx)`
- `fetch` → `ProviderPlugin.fetch_references(ctx)`
- `endnote` → `ProviderPlugin.export_endnote(ctx)`
- `endnote-xml` → `reference_harvester.endnote_xml.write_reference_type_table(...)`

Provider output root normalization happens in `_ctx(...)` (CLI only): it ensures output is written to `out_root/<provider>/...` even if the user passes `--out-root out`.

Reference docs:

- Project goals and promises: `README.md`
- Intended architecture (including run-id layout): `docs/PLAN.md`

### GUI

GUI lives in `src/reference_harvester/gui/app.py`.

- NiceGUI path is the primary UI (Streamlit is fallback).
- The GUI executes `JobRequest` via an internal `_execute_job(job)`.

Important: Prior to this audit pack, the GUI and CLI did not agree on how `ProviderContext.out_dir` should be scoped. The CLI scopes it by provider (e.g. `out/uspto`), while the GUI passed `out/` directly.

## 2) Data contracts and terminology

### “Canonical” vs “manifest metadata”

This repo uses both terms intentionally:

- **Manifest metadata**: crawl/download bookkeeping entries (URLs, local paths, hashes, HTTP status/headers when available). This is what is currently treated as “raw provider records” for canonicalization.
- **Canonical**: the normalized, snake_case field dictionary produced by mapping manifest entries via the YAML registry.

Today, the canonical pipeline is “manifest-entry-centric” because many upstream sources are files/pages rather than a single uniform JSON API payload.

### Core data models

Data contracts are declared in `src/reference_harvester/models.py`:

- `RawRecord`: a _true_ HTTP capture contract (URL/status/headers/payload/retrieved_at). This is the conceptual “raw payload” contract.
- `NormalizedRecord`: `canonical` + `extras` + `source_paths` (reversible mapping support).
- `MappingDiagnostics`: collisions, unknown keys, coercions.

Note: the USPTO provider does not currently serialize `RawRecord` directly; instead it serializes a union of manifest-entry dicts.

Canonicalization is implemented in `src/reference_harvester/canonicalizer.py`:

- Flattened key paths (e.g. `trialMetaData.trialStatusCategory`) are matched against a YAML registry (`src/reference_harvester/registry/uspto_fields.yaml`) via `raw_key_lookup(...)`.
- Known fields map into `NormalizedRecord.canonical`.
- Unknown fields are preserved (losslessly) under `NormalizedRecord.extras` with `snake_case(...)` keys.
- Collisions are tracked in `MappingDiagnostics.collisions` (“first wins” semantics).

This supports the “no-loss” approach as long as raw payloads are retained somewhere (currently: `raw_provider.jsonl`).

### Citation/export utilities

Citation serialization is in `src/reference_harvester/citations.py`:

- `CitationRecord` is a lightweight wrapper around a provider name, stable identifier, and canonical dict.
- `write_ris(...)` and `write_bibtex(...)` emit provider-normalized citations. The default RIS type emitted is `GEN` (generic).

## 3) Output contracts vs implementation

The desired output contract is documented in `docs/outputs.md`.

What the current code does today (USPTO provider):

- `fetch_references` produces provider outputs and writes canonical logs under:
  - `out/<provider>/raw/harvester/uspto/logs/raw_provider.jsonl`
  - `out/<provider>/raw/harvester/uspto/logs/normalized_canonical.jsonl`
  - `out/<provider>/raw/harvester/uspto/logs/mapping_diagnostics.jsonl`
  - `out/<provider>/raw/harvester/uspto/logs/manifest.jsonl`

Notable gaps/mismatches:

- The contract mentions `out/{provider}/{domainOrDataset}/{runId}/...`; current implementation is provider-centric but does not model run IDs.
- `docs/outputs.md` previously described `raw_provider.jsonl` as “full payloads”. In practice it is a union of **manifest entries** (URLs + local paths), and the payloads live on disk under `html/`, `assets/`, and `api_samples/`.
- `logs/manifest.jsonl` is currently an artifact index (counts), not an event log of the pipeline.
- Schema validation via `docs/inputs/odp/2026-01-14/pfw-schemas/patent-data-schema.json` exists as an **opt-in toggle** (see P1 below); it is not run by default.

## 4) Capability matrix (current)

| Surface | Feature            | Implemented | Notes                                                                               |
| ------- | ------------------ | ----------: | ----------------------------------------------------------------------------------- |
| CLI     | `inventory`        |         Yes | Generates swagger-derived endpoint coverage artifacts for USPTO                     |
| CLI     | `harvest`          |     Partial | Placeholder mirroring scaffolding (dirs only)                                       |
| CLI     | `fetch`            |     Partial | Runs a larger pipeline but includes placeholder export; canonical logs are produced |
| CLI     | `endnote`          |         Yes | Produces EndNote reference type table + a RIS export (bulk manifest + per-record)   |
| CLI     | `endnote-xml`      |         Yes | Template-based RefTypes patching                                                    |
| GUI     | NiceGUI            |         Yes | Minimal UI; can run jobs                                                            |
| GUI     | Streamlit fallback |         Yes | Optional dependency                                                                 |

## 5) EndNote conformance checklist

Goal: import into EndNote 25 with no structural breakage, while remaining lossless.

This checklist is the “definition of done” for the EndNote constraints/strategy described in `docs/endnote_mapping.md`.

- [x] (1) Treat a real EndNote-exported RefTypes template as the ground truth schema (never invent XML)
- [x] (2) Fit within EndNote’s type budget by repurposing `Unused 1/2/3` (no “one endpoint = one type” explosion)
- [x] (3) Relabel by stable Field `id` keys when possible (avoid localization/user-label fragility)
- [~] (4) Export RIS for EndNote import (implemented; mapping still evolving)
- [~] (4) Guarantee lossless round-trip by attaching a canonical sidecar per reference and anchoring it with a stable EndNote field (implemented for USPTO)
- [~] (5) Model bulk datasets as transport/provenance: “bulk manifest” reference + per-record references, each with its own sidecar (implemented for USPTO)
- [x] (6) Standardize provider-neutral core fields + provider-specific sidecar schema; keep EndNote type set stable over time

Notes:

- Sidecars now use a versioned, provider-neutral envelope (`schema`, `schema_version`, `provider`, `kind`, `exported_at`, `stable_id`, `data`) via `reference_harvester.sidecars`.

## 6) Prioritized fixes (with acceptance criteria)

### P0 — GUI output path parity

Problem: GUI and CLI previously disagreed on provider scoping for outputs.

Acceptance criteria:

- Running GUI job for provider `uspto` writes under `out/uspto/...` (same as CLI).
- Add a unit test if/when GUI is expanded beyond the stub-only branch.

### P0 — EndNote export includes RIS

Problem: `endnote` command claimed “RIS + attachments” but only produced a type table.

Acceptance criteria:

- `ProviderPlugin.export_endnote` writes a type table AND a RIS file under `out/<provider>/endnote/`.

Status:

- Implemented for `uspto` when harvest outputs exist: `export_endnote` re-emits canonical logs and copies `logs/citations/uspto-canonical.ris` into `endnote/uspto.ris`.

### P1 — Schema validation toggle

Problem: `docs/inputs/odp/2026-01-14/pfw-schemas/patent-data-schema.json` exists but needs explicit enforcement.

Acceptance criteria (implemented):

- Optional validation mode (off by default) validates downloaded `api_samples/**/*.json` against a schema.
- Failing validation emits a report under `logs/reports/` and returns non-zero exit code when enabled.

Notes:

- The included schema models raw USPTO payloads; validating canonical logs would require a separate canonical schema.

Tests:

- `tests/test_schema_validation.py` locks the validator behavior (including singleton-list `items` handling).

### P1 — Output contract “run id”

Problem: Outputs aren’t grouped by run id, so repeated runs collide.

Acceptance criteria:

- Introduce a run-id directory (timestamp or UUID) under provider root and write all outputs beneath it.
- Keep a stable “latest” pointer (symlink or text file) if needed.

Status:

- CLI now supports an opt-in `--run-id` that writes under `out/<provider>/runs/<run-id>/...`.
- A `latest` pointer and the full `out/<provider>/<domain|dataset>/<run-id>/` layout are still future work.

Proposed tests:

- Add a test that two runs do not collide (distinct run-id dirs).
- Add a test that a `latest.txt` (or similar) points at the newest run-id directory.

### P1 — EndNote sidecar attachments (lossless round-trip)

Problem: EndNote fields are capped; the project’s “no-loss” promise requires record-level sidecar attachments.

Acceptance criteria:

- For each emitted EndNote reference, emit a sidecar file (JSON or ZIP) containing raw payload + canonical + diagnostics + provenance.
- Store a stable identifier in a dedicated, documented EndNote field (e.g., `Accession Number` or a repurposed Custom field) that can be used to locate/verify the sidecar.
- Add a regression test that the sidecar file hash matches the anchored EndNote hash field (e.g., `SHA256`).

## 7) Regression tests added in this audit pass

- EndNote RefTypes patching: verifies `id:25` relabeling works and that base fields are copied into the repurposed slot.
- URL ingestion: verifies `_harvest_additional_subdomains` writes `manifest.json` and respects allow-host scoping.
- PTAB canonical mapping: validates key PTAB proceeding fields map cleanly with no unknown keys.
- Swagger robustness: validates fetch failure handling and deterministic artifact emission.

## 8) URL ingestion / scraping audit (USPTO)

USPTO uses two distinct URL-ingestion paths:

- Swagger/OpenAPI inventory and coverage emission (`refresh_inventory` + `_fetch_swagger_specs`).
- A lightweight crawler for “additional subdomains” (`_harvest_additional_subdomains`) that:
  - obeys `robots.txt` (best effort)
  - scopes hosts via `allow_host`/`deny_host` and the internal allowlist
  - extracts links via regex over HTML (href/src and absolute URLs)
  - stores HTML under `raw/harvester/uspto/html/` and non-HTML under `raw/harvester/uspto/assets/`
  - records fetches in `raw/harvester/uspto/manifest.json` (+ `.jsonl`)

Gaps vs the intended contract in `docs/outputs.md`:

- The contract describes `mirror/` and `downloads/`; the implementation uses `html/` and `assets/`.
- The contract describes a run-id layout; the crawler writes into a stable provider folder, so repeated runs overwrite/append.
- Link extraction is regex-based (not DOM-based), so it will miss many JS-generated URLs and can include false positives.

Recommended P1 fixes (test-anchored):

- Add a unit test that verifies the crawler:
  - writes `manifest.json` entries for a seed page
  - extracts and enqueues at least one discovered link
  - respects `allow_host` scoping
- Rename/clarify output folders (either update docs or rename folders) to avoid confusion between “mirror” vs “html/assets”.

Status:

- The docs have been aligned to current folder conventions; renaming folders would be a larger breaking change and should come with migration tooling.

## 9) EndNote CLI vs library API (signature parity)

The `endnote-xml` CLI command now calls `write_reference_type_table(...)` using explicit keyword arguments (`type_name`, `template_path`, `base_type_name`, `target_slot_name`, `field_label_overrides`) to match the library signature in `src/reference_harvester/endnote_xml.py`.

If a future mismatch reappears, it should be caught by:

- a lightweight CLI smoke test that runs `reference-harvester endnote-xml --help` and a minimal generation call in a temp directory.
