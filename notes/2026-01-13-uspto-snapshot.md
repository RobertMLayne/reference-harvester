# USPTO snapshot – 2026-01-13

Tag: `uspto-2026-01-13`

## Commits

- d192e29: Ingest USPTO fetch 2026-01-13 (data snapshot under data/uspto-2026-01-13)
- 0a2cc8f: Add USPTO bulk byte cap (expose max_bulk_bytes flag, guard bulk fetch by declared size and running total, refresh seed/robots lists, normalize .gitattributes)

## Notes

- Data: bulk manifests, HTML captures, assets, coverage/failure summaries under data/uspto-2026-01-13.
- CLI: use --max-bulk-bytes to cap total bulk download volume per run (default 10 GB).
