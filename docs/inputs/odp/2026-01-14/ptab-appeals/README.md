# PTAB Appeals API pages (2026-01-14)

Location: docs/inputs/odp/2026-01-14/ptab-appeals

## Files

- data.uspto.gov-apis-ptab-appeals-document-identifier-\*.json (doc page for decision lookups by document identifier; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-appeals-search-\*.json (doc page for general search; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-appeals-search-appeal-number-\*.json (doc page for search by appeal number; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-appeals-download-\*.json (doc page for search result download; statuses 200/400/403/404/413/500)

## Source and provenance

- User-supplied captures from data.uspto.gov PTAB Appeals API docs, copied intact on 2026-01-14.
- Text is the on-page narrative plus example JSON snippets from the USPTO portal.

## Handling guidance

- Treat these as source reference; do not rewrite content. If annotating, add separate notes instead of editing originals.
- Some pages contain formatting quirks (e.g., spaces in URL schemes like `https: //` or truncated sample payloads). Preserve as-is for fidelity; normalize only in derived outputs if needed.
- These are documentation artifacts, not strict JSON responses; downstream parsing should be tolerant.
