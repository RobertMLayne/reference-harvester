from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import reference_harvester.providers.openalex.provider as openalex_mod
from reference_harvester.providers.base import ProviderContext
from reference_harvester.providers.openalex.provider import OpenAlexProvider


@dataclass
class _FakeResponse:
    payload: dict[str, Any]

    def raise_for_status(self) -> None:
        return

    def json(self) -> dict[str, Any]:
        return self.payload


@dataclass
class _FakeHttpxResponse:
    status_code: int
    content: bytes
    headers: dict[str, str]
    url: str

    def raise_for_status(self) -> None:
        return

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


def test_openalex_fetch_writes_expected_files(tmp_path: Path, monkeypatch: Any) -> None:
    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> _FakeResponse:
        assert url.endswith("/works")
        assert params["search"] == "ptab"
        assert params["per-page"] == 2
        assert params["page"] == 1
        assert params["mailto"] == "me@example.com"
        assert "mailto:me@example.com" in headers.get("User-Agent", "")
        assert timeout > 0

        return _FakeResponse(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "Example Title",
                        "doi": "10.1234/example",
                        "publication_date": "2020-01-01",
                        "type": "journal-article",
                        "host_venue": {"display_name": "Example Venue"},
                    }
                ]
            }
        )

    monkeypatch.setattr(openalex_mod, "_http_get", fake_get)

    ctx = ProviderContext(
        name="openalex",
        out_dir=tmp_path,
        options={
            "query": "ptab",
            "per_page": 2,
            "max_pages": 1,
            "email": "me@example.com",
        },
    )

    OpenAlexProvider().fetch_references(ctx)

    base = tmp_path / "raw" / "harvester" / "openalex"
    assert (base / "logs" / "raw_provider.jsonl").exists()
    assert (base / "logs" / "normalized_canonical.jsonl").exists()
    assert (base / "logs" / "mapping_diagnostics.jsonl").exists()
    assert (base / "logs" / "manifest.jsonl").exists()

    sample = base / "api_samples" / "openalex" / "works_search_page_1.json"
    assert sample.exists()

    raw_lines = (
        (base / "logs" / "raw_provider.jsonl").read_text(encoding="utf-8").splitlines()
    )
    assert len(raw_lines) == 1
    raw = json.loads(raw_lines[0])
    assert raw["openalex_id"] == "W123"
    assert raw["query"] == "ptab"


def test_openalex_endnote_export_writes_ris_and_sidecars(
    tmp_path: Path, monkeypatch: Any
) -> None:
    def fake_get(
        url: str,
        **_kwargs: Any,
    ) -> _FakeResponse:
        assert url.endswith("/works")
        return _FakeResponse(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W999",
                        "title": "Another Title",
                        "doi": "10.9999/example",
                        "publication_date": "2021-12-31",
                        "type": "journal-article",
                        "host_venue": {"display_name": "Venue"},
                    }
                ]
            }
        )

    monkeypatch.setattr(openalex_mod, "_http_get", fake_get)

    ctx = ProviderContext(
        name="openalex",
        out_dir=tmp_path,
        options={
            "query": "ptab",
            "per_page": 1,
            "max_pages": 1,
            "email": "me@example.com",
        },
    )

    provider = OpenAlexProvider()
    provider.fetch_references(ctx)
    provider.export_endnote(ctx)

    ris_path = tmp_path / "endnote" / "openalex.ris"
    assert ris_path.exists()
    ris_text = ris_path.read_text(encoding="utf-8")
    assert "AN  - openalex:W999" in ris_text
    assert "L1  - sidecars/" in ris_text

    sidecars_dir = tmp_path / "endnote" / "sidecars"
    assert sidecars_dir.exists()

    sidecar_files = list(sidecars_dir.glob("*.json"))
    assert len(sidecar_files) >= 2  # query manifest + record

    envelope = json.loads(sidecar_files[0].read_text(encoding="utf-8"))
    assert envelope["provider"] == "openalex"
    assert "schema" in envelope
    assert "schema_version" in envelope
    assert "data" in envelope


def test_openalex_inventory_writes_endpoints_and_robots(
    tmp_path: Path, monkeypatch: Any
) -> None:
    robots_text = """User-agent: *
Disallow: /private
Allow: /
Sitemap: https://docs.openalex.org/sitemap.xml
"""

    def fake_get(url: str, **kwargs: Any) -> _FakeHttpxResponse:
        assert url.endswith("/robots.txt")
        headers = kwargs.get("headers") or {}
        assert "mailto:me@example.com" in headers.get("User-Agent", "")
        assert kwargs.get("timeout")
        return _FakeHttpxResponse(
            status_code=200,
            content=robots_text.encode("utf-8"),
            headers={"content-type": "text/plain"},
            url=url,
        )

    monkeypatch.setattr(openalex_mod, "_http_get", fake_get)

    ctx = ProviderContext(
        name="openalex",
        out_dir=tmp_path,
        options={
            "email": "me@example.com",
            "timeout_s": 1.0,
        },
    )

    OpenAlexProvider().refresh_inventory(ctx)

    artifacts = tmp_path / "raw" / "harvester" / "openalex" / "artifacts"
    inv_path = artifacts / "inventory.json"
    assert inv_path.exists()

    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    endpoints = inventory.get("endpoints") or []
    assert any(ep.get("path") == "/works" for ep in endpoints)
    assert any(ep.get("path") == "/authors" for ep in endpoints)

    robots_inventory = artifacts / "robots_inventory.json"
    assert robots_inventory.exists()
    robots = json.loads(robots_inventory.read_text(encoding="utf-8"))
    assert len(robots) == 3
    assert {r.get("host") for r in robots} == {
        "openalex.org",
        "api.openalex.org",
        "docs.openalex.org",
    }


def test_openalex_mirror_writes_manifest_with_hashes(
    tmp_path: Path, monkeypatch: Any
) -> None:
    def fake_get(url: str, **kwargs: Any) -> _FakeHttpxResponse:
        assert kwargs.get("timeout")
        assert "User-Agent" in (kwargs.get("headers") or {})
        content = f"<html><body>{url}</body></html>".encode("utf-8")
        return _FakeHttpxResponse(
            status_code=200,
            content=content,
            headers={
                "content-type": "text/html",
                "etag": 'W/"abc"',
                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                "content-length": str(len(content)),
            },
            url=url,
        )

    monkeypatch.setattr(openalex_mod, "_http_get", fake_get)

    ctx = ProviderContext(
        name="openalex",
        out_dir=tmp_path,
        options={
            "email": "me@example.com",
            "max_pages": 2,
            "extra_seeds": [
                "https://docs.openalex.org/",
                "https://openalex.org/",
            ],
        },
    )

    OpenAlexProvider().mirror_sources(ctx)

    base = tmp_path / "raw" / "harvester" / "openalex"
    manifest_path = base / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["kind"] == "mirror"
    assert len(manifest["items"]) == 2
    assert "sha256" in manifest["items"][0]

    mirror_jsonl = base / "logs" / "mirror_manifest.jsonl"
    assert mirror_jsonl.exists()
