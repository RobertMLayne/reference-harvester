# Simplified Query Syntax – Open Data Portal API (extract)

Source: Simplified Query Syntax Open Data Portal API.pdf (USPTO Open Data Portal), ingested 2026-01-14.

## Contents (as extracted)

- API syntax overview (q, filters, rangeFilters, sort, fields, pagination, facets)
- Reserved words and OpenSearch operators
- POST search request example and parameters
- q parameter modes (free-form, simple query string) with examples
- filters parameter rules and examples
- rangeFilters rules and examples
- sort parameter rules and examples
- fields parameter rules and examples
- Pagination rules
- facets parameter examples
- GET search request notes, URL encoding hints

## Snippets

### Reserved words and operators

- q: search across multiple fields or simple query string
- filters: filter search results
- rangeFilters: range-based filters
- sort, fields, limit, offset, facets
- OpenSearch operators: AND, OR, NOT, wildcard `*`/`?`, quoted phrases, comparison operators

### POST search example (truncated)

```json
{
  "q": "applicationMetaData.applicationTypeLabelName:Utility",
  "filters": [
    {
      "name": "applicationMetaData.applicationStatusDescriptionText",
      "value": ["Patented Case"]
    }
  ],
  "rangeFilters": [
    {
      "field": "applicationMetaData.grantDate",
      "valueFrom": "2010-08-04",
      "valueTo": "2022-08-04"
    }
  ],
  "sort": [{ "field": "applicationMetaData.filingDate", "order": "desc" }],
  "fields": [
    "applicationNumberText",
    "correspondenceAddressBag",
    "applicationMetaData.filingDate"
  ],
  "pagination": { "offset": 0, "limit": 25 },
  "facets": [
    "applicationMetaData.applicationTypeLabelName",
    "applicationMetaData.applicationStatusCode"
  ]
}
```

### q parameter examples (selected)

- Free form: `q=Design` (search all searchable fields)
- Phrase: `q="Patented Case"`
- Fielded OR: `applicationMetaData.applicationTypeLabelName:(Design OR Plant)`
- Fielded AND: `applicationMetaData.applicationStatusDescriptionText:"Patented Case" AND applicationMetaData.entityStatusData.businessEntityStatusCategory:Micro`
- Wildcards: `applicationMetaData.firstApplicantName:Technolog*`, `applicationMetaData.examinerNameText:ANDERS?N`
- Ranges: `applicationMetaData.applicationStatusDate:>=2024-02-20`, `applicationMetaData.filingDate:[2024-01-01 TO 2024-08-30]`

### Filters / rangeFilters rules (high level)

- Optional; multiple filters are ANDed; multiple values per field allowed.
- rangeFilters require `valueFrom` and `valueTo`; inclusive; date/number fields only.

### GET query hints

- Encode reserved characters (space `%20`, quote `%22`, `#` `%23`, `%` `%25`, `<` `%3C`, `>` `%3E`, `|` `%7C`).

---

This extract is for reference; consult the PDF for full formatting and context.
