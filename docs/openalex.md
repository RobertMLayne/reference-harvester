# OpenAlex provider

The `openalex` provider supports:

- `inventory`: writes a local inventory of key API endpoints and `robots.txt` snapshots.
- `harvest`: mirrors a small set of OpenAlex/OpenAlex Docs pages (HTML) into `out/` with a manifest.
- `fetch`: queries OpenAlex `/works` using the `search` parameter and stores raw + canonical JSONL logs.
- `endnote`: exports `openalex.ris` plus lossless JSON sidecars.

## Polite usage (recommended)

OpenAlex does not require an API key, but it is good practice to identify yourself.

- Set `OPENALEX_EMAIL=you@example.com` in your environment, or pass `--email you@example.com`.
- The provider uses `mailto` (query param where applicable) and `From`/`User-Agent` headers.

## Commands

Inventory:

- `reference-harvester inventory openalex`

Harvest (mirror docs seeds):

- `reference-harvester harvest openalex --email you@example.com --max-pages 4`

Fetch works:

- `reference-harvester fetch openalex --query "ptab" --per-page 25 --max-pages 2 --email you@example.com`

EndNote export:

- `reference-harvester endnote openalex`

## Outputs

All outputs are written under `out/openalex/...` or `out/openalex/runs/<run-id>/...`.

Note: `out/` is generated output and is ignored by default in Git.

Key files/folders:

- `raw/harvester/openalex/artifacts/inventory.{json,md}`
- `raw/harvester/openalex/artifacts/robots_inventory.{json,jsonl}`
- `raw/harvester/openalex/html/` (mirrored pages)
- `raw/harvester/openalex/manifest.json` (mirror manifest)
- `raw/harvester/openalex/logs/mirror_manifest.{json,jsonl}`
- `raw/harvester/openalex/logs/raw_provider.jsonl` (OpenAlex work payloads)
- `raw/harvester/openalex/logs/normalized_canonical.jsonl`
- `endnote/openalex.ris`
- `endnote/sidecars/*.json` (lossless sidecar envelope per record + query manifest)
