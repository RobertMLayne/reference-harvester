# USPTO fetch report (2026-01-13)

## Runs performed

- Two smoke fetches: `--max-pages 5 --max-assets 5 --max-depth 2 --throttle-seconds 0.1` (same `out/uspto` root).
- One full fetch with defaults (`--out-root out`).

## Dedupe/resume evidence

- `out/uspto/manifest.jsonl` shows repeated HTML responses marked `"deduped_by_hash": true` with consistent `host` and `depth` (see first five entries around the PTAB/FDW endpoints).
- Subsequent run reused hashes; no duplicate downloads beyond the first capture.

## Coverage / swagger artifacts

- Packaged swagger fallback emitted placeholder endpoint: `GET /` with empty host because the packaged spec has no server URL.
- `out/uspto/raw/harvester/uspto/artifacts/coverage.json` contains that single implemented endpoint; `coverage.md` mirrors it.
- Source coverage: `coverage_sources.md` lists 7 discovered URLs (6 OK on data.uspto.gov, 1 404 on developer.uspto.gov); summary JSON confirms the same.

## Run totals

- From `run_manifest_summary.json`: `additional_pages=6`, `additional_assets=1`, `api_samples=0`, `bulk_artifacts=0`, `total=7`.

## Notes

- Outputs under `out/` are ignored via `.gitignore`; this report lives under `docs/reports/` for versioned tracking.
- Git LFS is initialized; binaries such as zip/pdf are covered by `.gitattributes` (though `out/` is ignored).
