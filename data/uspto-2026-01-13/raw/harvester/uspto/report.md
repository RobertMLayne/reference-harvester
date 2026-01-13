# USPTO fetch report (2026-01-13)

- Runs: two small fetches (`--max-pages 5 --max-assets 5 --max-depth 2 --throttle-seconds 0.1`) followed by one full fetch with defaults, all targeting `out/uspto`.
- Dedupe/resume: `out/uspto/manifest.jsonl` entries show repeated HTML hashes marked `"deduped_by_hash": true` with preserved `host` and `depth` (see first five records).
- Coverage (packaged swagger fallback): `coverage.json` contains one placeholder endpoint (`GET /`, host empty) and `coverage.md` reflects the same.
- Source coverage summary: `coverage_sources.md` lists 7 discovered URLs (6 OK on data.uspto.gov, 1 404 on developer.uspto.gov); `coverage_sources_summary.json` mirrors these counts.
- Run manifest summary: `run_manifest_summary.json` totals — additional_pages: 6, additional_assets: 1, api_samples: 0, bulk_artifacts: 0.
