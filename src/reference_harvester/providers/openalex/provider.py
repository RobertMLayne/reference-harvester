from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib import robotparser

import httpx

from reference_harvester.canonicalizer import canonicalize_batch
from reference_harvester.endnote_xml import write_reference_type_table
from reference_harvester.log_utils import write_jsonl
from reference_harvester.providers.base import ProviderContext, ProviderPlugin
from reference_harvester.providers.registry import (
    ProviderCapabilities,
    ProviderInfo,
)
from reference_harvester.registry import load_registry
from reference_harvester.sidecars import (
    build_sidecar_envelope,
    sha256_hex,
    write_sidecar_json,
)

from .local_constants import (
    OPENALEX_API_BASE,
    OPENALEX_DEFAULT_SEEDS,
    OPENALEX_DOCS_BASE,
    OPENALEX_PROVIDER_ID,
)


def _default_registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "registry" / "openalex_fields.yaml"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            records.append(obj)
    return records


def _openalex_id_from_url(value: Any) -> str:
    url = str(value or "")
    if not url:
        return ""
    # OpenAlex IDs look like https://openalex.org/W123...
    return url.rstrip("/").rsplit("/", 1)[-1]


def _build_headers(email: str | None, user_agent: str) -> dict[str, str]:
    headers = {"User-Agent": user_agent}
    if email:
        headers["User-Agent"] = f"{user_agent} (mailto:{email})"
        headers["From"] = email
    return headers


_http_get: Callable[..., httpx.Response] = httpx.get


def _safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return cleaned or "item"


def _url_to_filename(url: str, content_type: str | None) -> str:
    base = _safe_slug(url.rstrip("/").rsplit("/", 1)[-1] or "index")
    ext = "txt"
    ct = (content_type or "").split(";", 1)[0].strip().lower()
    if ct == "text/html":
        ext = "html"
    elif ct in {"application/json", "application/ld+json"}:
        ext = "json"
    return f"{base}.{ext}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class OpenAlexProvider(ProviderPlugin):
    provider_info = ProviderInfo(
        name="openalex",
        title="OpenAlex",
        description="OpenAlex works metadata (no API key; mailto supported)",
        capabilities=ProviderCapabilities(
            supports_inventory=True,
            supports_harvest=True,
            supports_fetch=True,
            supports_endnote=True,
            supports_citations=False,
        ),
        credentials=[],
        homepage="https://openalex.org/",
    )

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    def refresh_inventory(self, ctx: ProviderContext) -> None:
        opts = dict(self.options)
        opts.update(ctx.options or {})

        provider_root = ctx.out_dir / "raw" / "harvester" / OPENALEX_PROVIDER_ID
        artifacts_dir = provider_root / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        exported_at = datetime.now(timezone.utc).isoformat()

        endpoints: list[dict[str, Any]] = [
            {
                "method": "GET",
                "path": "/works",
                "base": OPENALEX_API_BASE,
                "description": ("Search works via ?search=...&per-page=...&page=..."),
            },
            {
                "method": "GET",
                "path": "/works/{id}",
                "base": OPENALEX_API_BASE,
                "description": "Fetch a single work (W...) by id",
            },
            {
                "method": "GET",
                "path": "/authors",
                "base": OPENALEX_API_BASE,
                "description": "Search authors",
            },
            {
                "method": "GET",
                "path": "/authors/{id}",
                "base": OPENALEX_API_BASE,
                "description": "Fetch a single author (A...) by id",
            },
            {
                "method": "GET",
                "path": "/sources",
                "base": OPENALEX_API_BASE,
                "description": "Search sources (journals/venues)",
            },
            {
                "method": "GET",
                "path": "/sources/{id}",
                "base": OPENALEX_API_BASE,
                "description": "Fetch a single source (S...) by id",
            },
            {
                "method": "GET",
                "path": "/institutions",
                "base": OPENALEX_API_BASE,
                "description": "Search institutions",
            },
            {
                "method": "GET",
                "path": "/institutions/{id}",
                "base": OPENALEX_API_BASE,
                "description": "Fetch a single institution (I...) by id",
            },
            {
                "method": "GET",
                "path": "/concepts",
                "base": OPENALEX_API_BASE,
                "description": "Search concepts",
            },
            {
                "method": "GET",
                "path": "/concepts/{id}",
                "base": OPENALEX_API_BASE,
                "description": "Fetch a single concept (C...) by id",
            },
        ]

        email = (
            str(opts.get("email") or opts.get("mailto") or "").strip()
            or os.environ.get("OPENALEX_EMAIL")
            or None
        )
        user_agent = str(opts.get("user_agent") or "reference-harvester/0.1")
        timeout_s = float(opts.get("timeout_s") or 30.0)

        robots_hosts = [
            "openalex.org",
            "api.openalex.org",
            "docs.openalex.org",
        ]
        robots_inventory = self._inventory_robots(
            artifacts_dir=artifacts_dir,
            hosts=robots_hosts,
            email=email,
            user_agent=user_agent,
            timeout_s=timeout_s,
        )

        inventory = {
            "provider": "openalex",
            "exported_at": exported_at,
            "api_base": OPENALEX_API_BASE,
            "docs_base": OPENALEX_DOCS_BASE,
            "endpoints": endpoints,
            "robots": {
                "hosts": robots_hosts,
                "items": robots_inventory,
            },
            "notes": (
                "OpenAlex does not require an API key; include a contact "
                "email via mailto + From/User-Agent for polite usage."
            ),
        }

        (artifacts_dir / "inventory.json").write_text(
            json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (artifacts_dir / "endpoints.json").write_text(
            json.dumps(endpoints, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        md_lines = [
            "# OpenAlex inventory",
            "",
            f"- API base: {OPENALEX_API_BASE}",
            f"- Docs: {OPENALEX_DOCS_BASE}",
            "- Robots inventory: artifacts/robots_inventory.json",
            "",
            "## Endpoints",
            "",
        ]
        for ep in endpoints:
            md_lines.append(
                f"- {ep['method']} {ep['path']} — {ep.get('description', '')}"
            )
        (artifacts_dir / "inventory.md").write_text(
            "\n".join(md_lines) + "\n",
            encoding="utf-8",
        )

    def _inventory_robots(
        self,
        *,
        artifacts_dir: Path,
        hosts: list[str],
        email: str | None,
        user_agent: str,
        timeout_s: float,
    ) -> list[dict[str, Any]]:
        robots_dir = artifacts_dir / "robots"
        robots_dir.mkdir(parents=True, exist_ok=True)

        records: list[dict[str, Any]] = []
        for host in hosts:
            host_val = str(host).strip().lower()
            if not host_val:
                continue

            robots_url = f"https://{host_val}/robots.txt"
            entry: dict[str, Any] = {
                "host": host_val,
                "robots_url": robots_url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                resp = _http_get(
                    robots_url,
                    headers=_build_headers(email, user_agent),
                    timeout=timeout_s,
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover
                entry["status"] = "error"
                entry["error"] = str(exc)
                records.append(entry)
                continue

            entry["status"] = "ok"
            entry["status_code"] = int(getattr(resp, "status_code", 0) or 0)

            text = getattr(resp, "text", "")
            stored = robots_dir / f"robots_{host_val}.txt"
            stored.write_text(text, encoding="utf-8")
            stored_path = str(stored.relative_to(artifacts_dir))
            entry["stored_path"] = stored_path.replace("\\", "/")

            lines = text.splitlines()
            rp = robotparser.RobotFileParser()
            rp.parse(lines)

            crawl_delay = rp.crawl_delay(user_agent)
            entry["crawl_delay"] = crawl_delay
            entry["can_fetch_root"] = rp.can_fetch(
                user_agent,
                f"https://{host_val}/",
            )

            disallow: list[str] = []
            allow: list[str] = []
            sitemaps: list[str] = []
            for raw in lines:
                lower = raw.lower().strip()
                if lower.startswith("disallow:"):
                    disallow.append(raw.split(":", 1)[1].strip())
                elif lower.startswith("allow:"):
                    allow.append(raw.split(":", 1)[1].strip())
                elif lower.startswith("sitemap:"):
                    sitemaps.append(raw.split(":", 1)[1].strip())
                elif lower.startswith("crawl-delay:") and crawl_delay is None:
                    try:
                        entry["crawl_delay"] = float(raw.split(":", 1)[1].strip())
                    except ValueError:
                        entry["crawl_delay"] = None
            entry["disallow"] = disallow
            entry["allow"] = allow
            entry["sitemaps"] = sitemaps
            records.append(entry)

        robots_inventory_path = artifacts_dir / "robots_inventory.json"
        robots_inventory_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(robots_inventory_path.with_suffix(".jsonl"), records)

        summary: list[dict[str, Any]] = []
        for record in records:
            disallow_rules = record.get("disallow") or []
            allow_rules = record.get("allow") or []
            sitemap_rules = record.get("sitemaps") or []
            status_code = int(record.get("status_code", 0) or 0)
            summary.append(
                {
                    "host": record.get("host"),
                    "status_code": status_code,
                    "ok": bool(status_code and status_code < 400),
                    "can_fetch_root": record.get("can_fetch_root"),
                    "crawl_delay": record.get("crawl_delay"),
                    "disallow_count": len(disallow_rules),
                    "allow_count": len(allow_rules),
                    "sitemaps_count": len(sitemap_rules),
                }
            )
        robots_summary_path = artifacts_dir / "robots_summary.json"
        robots_summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(robots_summary_path.with_suffix(".jsonl"), summary)

        return records

    def mirror_sources(self, ctx: ProviderContext) -> None:
        opts = dict(self.options)
        opts.update(ctx.options or {})

        max_pages = int(opts.get("max_pages") or 25)
        timeout_s = float(opts.get("timeout_s") or 30.0)
        throttle_seconds = float(opts.get("throttle_seconds") or 0.0)
        seeds = list(opts.get("extra_seeds") or [])
        if not seeds:
            seeds = list(OPENALEX_DEFAULT_SEEDS)

        email = (
            str(opts.get("email") or opts.get("mailto") or "").strip()
            or os.environ.get("OPENALEX_EMAIL")
            or None
        )
        user_agent = str(opts.get("user_agent") or "reference-harvester/0.1")

        provider_root = ctx.out_dir / "raw" / "harvester" / OPENALEX_PROVIDER_ID
        logs_dir = provider_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        html_dir = provider_root / "html"
        html_dir.mkdir(parents=True, exist_ok=True)

        harvested_at = datetime.now(timezone.utc).isoformat()
        manifest: list[dict[str, Any]] = []

        for idx, url in enumerate(seeds[:max_pages]):
            if throttle_seconds > 0 and idx:
                time.sleep(throttle_seconds)
            try:
                fetched_at = datetime.now(timezone.utc).isoformat()
                resp = _http_get(
                    url,
                    headers=_build_headers(email, user_agent),
                    timeout=timeout_s,
                )
                resp.raise_for_status()
                headers = getattr(resp, "headers", {})
                content_type = (
                    headers.get("content-type") if hasattr(headers, "get") else None
                )
                filename = _url_to_filename(url, content_type)
                path = html_dir / filename
                content = getattr(resp, "content", b"")
                if isinstance(content, str):
                    content = content.encode("utf-8")
                path.write_bytes(content)

                sha256 = _sha256_bytes(content)
                etag = headers.get("etag") if hasattr(headers, "get") else None
                last_modified = (
                    headers.get("last-modified") if hasattr(headers, "get") else None
                )
                content_length = (
                    headers.get("content-length") if hasattr(headers, "get") else None
                )

                final_url = str(getattr(resp, "url", "") or "")

                manifest.append(
                    {
                        "url": url,
                        "final_url": final_url or url,
                        "fetched_at": fetched_at,
                        "status_code": resp.status_code,
                        "content_type": content_type,
                        "content_length": content_length,
                        "etag": etag,
                        "last_modified": last_modified,
                        "sha256": sha256,
                        "path": str(path.relative_to(provider_root)),
                    }
                )
            except (httpx.HTTPError, OSError) as exc:  # pragma: no cover
                manifest.append(
                    {
                        "url": url,
                        "error": str(exc),
                    }
                )

        mirror_manifest = {
            "provider": "openalex",
            "kind": "mirror",
            "harvested_at": harvested_at,
            "seeds": seeds,
            "items": manifest,
        }

        (provider_root / "manifest.json").write_text(
            json.dumps(mirror_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (logs_dir / "mirror_manifest.json").write_text(
            json.dumps(mirror_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(logs_dir / "mirror_manifest.jsonl", manifest)

    def fetch_references(self, ctx: ProviderContext) -> None:
        opts = dict(self.options)
        opts.update(ctx.options or {})

        query = str(opts.get("query") or "patent trial and appeal board")
        per_page = int(opts.get("per_page") or 25)
        max_pages = int(opts.get("max_pages") or 1)
        timeout_s = float(opts.get("timeout_s") or 30.0)

        email = (
            str(opts.get("email") or opts.get("mailto") or "").strip()
            or os.environ.get("OPENALEX_EMAIL")
            or None
        )
        user_agent = str(opts.get("user_agent") or "reference-harvester/0.1")

        provider_home = ctx.out_dir / "raw" / "harvester" / OPENALEX_PROVIDER_ID
        logs_dir = provider_home / "logs"
        api_samples_dir = provider_home / "api_samples" / "openalex"
        logs_dir.mkdir(parents=True, exist_ok=True)
        api_samples_dir.mkdir(parents=True, exist_ok=True)

        fetched_at = datetime.now(timezone.utc).isoformat()

        all_works: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            params: dict[str, Any] = {
                "search": query,
                "per-page": per_page,
                "page": page,
            }
            if email:
                params["mailto"] = email

            url = f"{OPENALEX_API_BASE}/works"
            resp = _http_get(
                url,
                params=params,
                headers=_build_headers(email, user_agent),
                timeout=timeout_s,
            )
            resp.raise_for_status()
            payload = resp.json()

            (api_samples_dir / f"works_search_page_{page}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            results = payload.get("results")
            if not isinstance(results, list):
                continue

            for work in results:
                if not isinstance(work, dict):
                    continue
                work_id = work.get("id")
                openalex_id = _openalex_id_from_url(work_id)
                enriched = dict(work)
                enriched.setdefault("url", str(work_id or ""))
                enriched.setdefault("openalex_id", openalex_id)
                enriched.setdefault("fetched_at", fetched_at)
                enriched.setdefault("query", query)
                all_works.append(enriched)

        registry = load_registry(_default_registry_path())
        normalized, diags = canonicalize_batch(all_works, registry)

        write_jsonl(logs_dir / "raw_provider.jsonl", all_works)
        write_jsonl(logs_dir / "normalized_canonical.jsonl", normalized)
        write_jsonl(logs_dir / "mapping_diagnostics.jsonl", diags)
        write_jsonl(
            logs_dir / "manifest.jsonl",
            [
                {
                    "provider": "openalex",
                    "query": query,
                    "fetched_at": fetched_at,
                    "records": len(all_works),
                    "files": {
                        "raw_provider.jsonl": len(all_works),
                        "normalized_canonical.jsonl": len(normalized),
                        "mapping_diagnostics.jsonl": len(diags),
                    },
                }
            ],
        )

    def export_endnote(self, ctx: ProviderContext) -> None:
        provider_home = ctx.out_dir / "raw" / "harvester" / OPENALEX_PROVIDER_ID
        logs_dir = provider_home / "logs"
        raw_path = logs_dir / "raw_provider.jsonl"

        if not raw_path.exists():
            print("[openalex] EndNote export skipped: no raw_provider.jsonl")
            return

        raw_records = _read_jsonl(raw_path)
        registry = load_registry(_default_registry_path())
        normalized, diags = canonicalize_batch(raw_records, registry)

        endnote_dir = ctx.out_dir / "endnote"
        endnote_dir.mkdir(parents=True, exist_ok=True)
        sidecars_dir = endnote_dir / "sidecars"
        ris_path = endnote_dir / "openalex.ris"

        # Type table for an OpenAlex bucket in Unused 2.
        table_path = endnote_dir / "reference_type_table.xml"
        write_reference_type_table(
            table_path,
            registry,
            type_name="OpenAlex",
            base_type_name="Generic",
            target_slot_name="Unused 2",
            field_label_overrides={
                "id:25": "OpenAlex ID",
                "id:26": "DOI",
                "id:27": "Publication Date",
                "id:28": "Work Type",
                "id:33": "Host Venue",
                "id:52": "SHA256",
            },
        )

        exported_at = datetime.now(timezone.utc).isoformat()
        ris_lines: list[str] = []

        # Query manifest record: describes the fetch that produced this set.
        query = str(raw_records[0].get("query") or "") if raw_records else ""
        manifest_data = {
            "query": query,
            "records_count": len(raw_records),
        }
        manifest_envelope = build_sidecar_envelope(
            provider="openalex",
            kind="query_manifest",
            stable_id="query:" + sha256_hex(query)[:12],
            exported_at=exported_at,
            data=manifest_data,
        )
        manifest_sha, manifest_path = write_sidecar_json(
            sidecars_dir=sidecars_dir,
            envelope=manifest_envelope,
        )
        ris_lines.append("TY  - DATA")
        title = f"OpenAlex Works Search ({len(raw_records)} records)"
        ris_lines.append(f"TI  - {title}")
        ris_lines.append(f"UR  - {OPENALEX_API_BASE}/works")
        if query:
            ris_lines.append(f"N1  - query: {query}")
        ris_lines.append(f"AN  - openalex:{manifest_envelope['stable_id']}")
        ris_lines.append(f"C8  - {manifest_sha}")
        ris_lines.append(f"L1  - sidecars/{manifest_path.name}")
        ris_lines.append("ER  -")

        for idx, (raw, norm, diag) in enumerate(zip(raw_records, normalized, diags)):
            canonical = norm.get("canonical", {})
            if not isinstance(canonical, dict):
                canonical = {}

            work_id = raw.get("id") or raw.get("url")
            openalex_id = raw.get("openalex_id") or _openalex_id_from_url(work_id)
            stable_id = str(openalex_id or f"record-{idx + 1}")

            title = str(canonical.get("title") or raw.get("title") or stable_id)
            url = str(
                canonical.get("url")
                or raw.get("primary_location", {}).get("landing_page_url")
                or raw.get("url")
                or raw.get("id")
                or ""
            )
            doi = str(canonical.get("doi") or raw.get("doi") or "")
            pub_date = str(
                canonical.get("publication_date") or raw.get("publication_date") or ""
            )
            work_type = str(canonical.get("work_type") or raw.get("type") or "")
            host_venue = str(canonical.get("host_venue") or "")

            record_data = {
                "raw": raw,
                "normalized": norm,
                "diagnostics": diag,
            }
            envelope = build_sidecar_envelope(
                provider="openalex",
                kind="record",
                stable_id=stable_id,
                exported_at=exported_at,
                data=record_data,
            )
            sha256, sidecar_path = write_sidecar_json(
                sidecars_dir=sidecars_dir,
                envelope=envelope,
            )

            # Prefer built-in types for shape; JOUR is generally acceptable.
            ris_lines.append("TY  - JOUR")
            ris_lines.append(f"TI  - {title}")
            if url:
                ris_lines.append(f"UR  - {url}")
            ris_lines.append(f"AN  - openalex:{stable_id}")
            ris_lines.append(f"C1  - {openalex_id}")
            ris_lines.append(f"C2  - {doi}")
            ris_lines.append(f"C3  - {pub_date}")
            ris_lines.append(f"C4  - {work_type}")
            ris_lines.append(f"C5  - {host_venue}")
            ris_lines.append(f"C8  - {sha256}")
            ris_lines.append(f"L1  - sidecars/{sidecar_path.name}")
            ris_lines.append("ER  -")

        ris_path.write_text("\n".join(ris_lines) + "\n", encoding="utf-8")
        print(f"[openalex] EndNote RIS written to {ris_path}")
        print(f"[openalex] EndNote sidecars written to {sidecars_dir}")


__all__ = ["OpenAlexProvider"]
