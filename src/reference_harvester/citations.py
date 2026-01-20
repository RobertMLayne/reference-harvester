from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from reference_harvester.models import ensure_parent


@dataclass(frozen=True)
class CitationRecord:
    provider: str
    identifier: str
    canonical: dict[str, Any]


def _first(canonical: dict[str, Any], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = canonical.get(key)
        if value:
            return str(value)
    return None


def _authors_list(canonical: dict[str, Any]) -> list[str]:
    value = canonical.get("authors") or canonical.get("inventors")
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if value:
        return [str(value)]
    return []


def _year(canonical: dict[str, Any]) -> str | None:
    date_val = _first(canonical, ["year", "publication_date", "pub_date", "date"])
    if not date_val:
        return None
    # Accept YYYY or YYYY-MM-DD; truncate if needed.
    if len(date_val) >= 4:
        return str(date_val)[:4]
    return str(date_val)


def _hash_key(provider: str, identifier: str) -> str:
    h = hashlib.sha1(f"{provider}:{identifier}".encode("utf-8"))
    return h.hexdigest()[:12]


def to_ris(records: Iterable[CitationRecord]) -> str:
    lines: list[str] = []
    for rec in records:
        canon = rec.canonical
        lines.append("TY  - GEN")
        title = _first(canon, ["title", "name"]) or "Untitled"
        lines.append(f"TI  - {title}")
        for author in _authors_list(canon):
            lines.append(f"AU  - {author}")
        year = _year(canon)
        if year:
            lines.append(f"PY  - {year}")
        doi = _first(canon, ["doi"])
        if doi:
            lines.append(f"DO  - {doi}")
        url = _first(canon, ["url", "link", "landing_page"])
        if url:
            lines.append(f"UR  - {url}")
        abstract = _first(canon, ["abstract", "description"])
        if abstract:
            lines.append(f"AB  - {abstract}")
        lines.append("ER  - ")
    return "\n".join(lines) + ("\n" if lines else "")


def to_bibtex(records: Iterable[CitationRecord]) -> str:
    entries: list[str] = []
    for rec in records:
        canon = rec.canonical
        key = _hash_key(rec.provider, rec.identifier)
        title = _first(canon, ["title", "name"]) or "Untitled"
        authors = " and ".join(_authors_list(canon))
        year = _year(canon) or ""
        url = _first(canon, ["url", "link", "landing_page"]) or ""
        doi = _first(canon, ["doi"]) or ""
        abstract = _first(canon, ["abstract", "description"]) or ""
        parts = [
            f"@misc{{{rec.provider}-{key},",
            f"  title = {{{title}}},",
        ]
        if authors:
            parts.append(f"  author = {{{authors}}},")
        if year:
            parts.append(f"  year = {{{year}}},")
        if url:
            parts.append(f"  url = {{{url}}},")
        if doi:
            parts.append(f"  doi = {{{doi}}},")
        if abstract:
            parts.append(f"  note = {{{abstract}}},")
        parts.append("}")
        entries.append("\n".join(parts))
    return "\n\n".join(entries) + ("\n" if entries else "")


def write_ris(path: Path, records: Iterable[CitationRecord]) -> None:
    ensure_parent(path)
    path.write_text(to_ris(records), encoding="utf-8")


def write_bibtex(path: Path, records: Iterable[CitationRecord]) -> None:
    ensure_parent(path)
    path.write_text(to_bibtex(records), encoding="utf-8")


__all__ = [
    "CitationRecord",
    "to_ris",
    "to_bibtex",
    "write_ris",
    "write_bibtex",
]
