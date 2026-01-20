# PTAB Interferences API pages (2026-01-14)

Location: docs/inputs/odp/2026-01-14/ptab-interferences

## Files

- data.uspto.gov-apis-ptab-interferences-document-identifier-\*.json (doc page for decision lookups by document identifier; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-interferences-search-\*.json (doc page for general search; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-interferences-search-interference-number-\*.json (doc page for lookups by interference number; statuses 200/400/403/404/413/500)
- data.uspto.gov-apis-ptab-interferences-download-\*.json (doc page for search result download; statuses 200/400/403/404/413/500)

## Source and provenance

- User-supplied captures from data.uspto.gov PTAB Interferences API docs, copied intact on 2026-01-14.
- Text is the on-page narrative plus example JSON snippets from the USPTO portal.

## Handling guidance

- Treat these as source reference; do not rewrite content. If annotating, add separate notes instead of editing originals.
- Some pages contain minor formatting quirks (e.g., spaces in URL schemes like `https: //` or truncated sample payloads). Preserve as-is for fidelity; normalize only in derived outputs if needed.
- When parsing, note these files are not strict JSON responses—they mix prose with example payloads. Downstream tooling should treat them as documentation artifacts, not machine-validated schemas.
