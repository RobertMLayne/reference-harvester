# EndNote 25 mapping strategy (no-loss, no-field-overflow)

This project integrates harvested provider metadata (USPTO/PTAB today, others later) with EndNote Desktop (EndNote 25 / EndNote 2025) by:

1. staying within EndNote’s hard limits for reference types/fields, and
2. guaranteeing lossless round-trip by attaching a canonical sidecar payload to each reference.

## Constraints (hard limits)

EndNote’s Reference Types Table is constrained:

- Reference types are a fixed list with 3 repurposable slots: **Unused 1/Unused 2/Unused 3**.
- Each reference type has a capped field layout: **up to 52 fields per reference, including the reference type name**.
- EndNote provides a fixed pool of field “slots”, including **Custom 1..Custom 8**.

Because of these limits, “one EndNote field per provider key across all endpoints” is not feasible.

Practical rule of thumb used in this repo:

- Treat **≤51 fields/type** as the usable budget, because one “slot” is consumed by the type itself.

## Design goals

- **No-loss**: every harvested record can be reconstructed exactly.
- **No field overflow**: we do not try to flatten every provider key into EndNote fields.
- **Usable in EndNote**: a small set of stable, searchable fields covers day-to-day use.
- **Future-proof**: providers can vary wildly; EndNote types stay stable.

## Recommended representation

### 1) Keep a stable EndNote type taxonomy

Prefer existing built-in EndNote types for the user-facing “shape” of the reference whenever possible:

- Patents: built-in **Patent**
- Court-like decisions: built-in **Case** (or **Report** depending on usage)
- Web captures and HTML/PDF documents: built-in **Web Page**
- Bulk data exports / dataset snapshots: built-in **Dataset**

Use **Unused 1/2/3** only when you truly need a provider-specific “bucket type” (e.g., “USPTO”).

Taxonomy goal: keep the type set stable over time.

- Built-in types are preferred for “shape” (Patent, Case, Web Page, Dataset).
- Repurposed Unused slots are reserved for:
  - provider “buckets” (e.g., USPTO)
  - transport/provenance manifests (bulk snapshots)

### 2) Put the long tail in a sidecar attachment (lossless payload)

For each EndNote reference, attach a sidecar JSON file containing:

- the raw provider payload
- canonicalized fields
- mapping diagnostics
- provenance (URL(s), timestamps, hashes)

This keeps EndNote fields clean while guaranteeing round-trip.

### 3) Anchor the sidecar with stable IDs (searchable)

Use a small number of highly-valuable fields for searching/sorting:

- Title / Short Title: human-friendly name
- Author (or Inventor/Creator): primary entity
- Year and/or Date
- URL
- Keywords
- Accession Number (or Label): stable record key / internal id

Use **Custom 1..8** for the most important provider-specific identifiers and integrity checks.

In this repo, the intended anchoring pattern is:

- A stable identifier stored in an EndNote field that RIS can populate reliably (Accession Number).
- A SHA256 of the sidecar stored in a repurposed Custom field.
- The sidecar file itself attached via the File Attachments field.

This gives you:

- search/sort on the stable identifier
- integrity checks via the hash
- exact lossless reconstruction via the attachment

## Per-type first-class fields (≤51) vs sidecar

EndNote fields fall into two categories:

1. **First-class fields** (searchable/sortable in EndNote)
2. **Sidecar-only fields** (lossless payload; not expected to be searchable in EndNote)

Rule:

- First-class fields are intentionally curated and capped.
- Everything else goes into the sidecar attachment.

Suggested provider-neutral “core” first-class fields:

- Title / Short Title
- Author/Inventor (as applicable)
- Year/Date
- URL
- Abstract/Notes
- Keywords
- Accession Number (stable key)

Provider-specific first-class fields should be limited to a few high-value identifiers and status fields.

## Bulk datasets as transport + provenance (manifest modeling)

Bulk snapshots are not the same as per-record references. The recommended model is:

- One **bulk manifest** reference (Dataset type or a repurposed Unused slot)

  - describes the snapshot: source, date range, counts, hashes
  - attaches a manifest sidecar (or ZIP) containing:
    - bulk file list
    - checksums
    - crawl/download logs

- Separate per-record references (Patent / Case / Web Page / provider bucket)

  - each has its own sidecar attachment

This keeps EndNote usable while preserving provenance and replayability.

## Provider-neutral core + provider-specific sidecar schemas

To support future providers without breaking EndNote:

- Keep a small provider-neutral core field set stable (title/date/url/id/hash).
- Make sidecars provider-specific, but wrap them in a provider-neutral, versioned envelope:
  - `schema` (currently `reference-harvester.sidecar.v1`)
  - `schema_version` (integer)
  - `provider` (e.g., `uspto`)
  - `kind` (e.g., `record`, `bulk_manifest`)
  - `exported_at` (ISO 8601 timestamp string)
  - `stable_id` (provider-scoped stable identifier)
  - `data` (provider-specific payload)

For per-record sidecars, `data` typically contains `raw`, `normalized`, and `diagnostics`.
For bulk-manifest sidecars, `data` contains snapshot/provenance fields (URL, counts, artifacts, entries).

## Implementation notes (this repo)

### Reference Types Table generation

This repo patches a real exported EndNote Reference Types Table XML template (see `endnote_reference_type_table.xml`) and repurposes an `Unused N` slot.

To avoid breaking on localized templates or user-renamed fields, relabel overrides should match by **field id** whenever possible.

In the shipped template, `Generic` defines Custom fields with these EndNote field ids:

- Custom 1 → id 25
- Custom 2 → id 26
- Custom 3 → id 27
- Custom 4 → id 28
- Custom 5 → id 33
- Custom 6 → id 34
- Custom 7 → id 42
- Custom 8 → id 52

### USPTO default relabel plan

When exporting the `USPTO` type (repurposing `Unused 1`), the project relabels those fields as:

- id:25 → USPTO Application Number
- id:26 → USPTO Trial Number
- id:27 → USPTO Document ID
- id:28 → USPTO Document Type
- id:33 → USPTO Status
- id:34 → USPTO Filing Date
- id:42 → USPTO Download URL
- id:52 → SHA256

### Current USPTO EndNote export behavior

The `uspto` provider writes these artifacts under `out/uspto/endnote/`:

- `reference_type_table.xml` (patched from the exported template)
- `uspto.ris`
- `sidecars/<sha256>.json` (bulk manifest + one per record)

RIS tags used by the exporter:

- `AN` — stable identifier (written as `uspto:<stable_id>`)
- `C1..C8` — Custom fields 1..8 (C8 holds the sidecar SHA256)
- `L1` — file attachment path (`sidecars/<sha256>.json` relative to the RIS)

Bulk-manifest record (the first RIS record in the export) also uses:

- `UR` — a stable bulk listing URL (currently `https://bulkdata.uspto.gov/`)
- `N1` — observed timestamp range (best-effort)
- `KW` — endpoint counts (searchable summary)

If EndNote is configured to import file attachments from RIS, the sidecar files become attached automatically.

## Operational warning: the table is global

EndNote Reference Type Tables are a **global per-user preference** on that machine.
Importing a table can overwrite existing customizations.

The safe workflow is:

- export your current RefTypeTable.xml from EndNote
- run `reference-harvester endnote-xml` against that export as a template
- import the patched output back into EndNote
