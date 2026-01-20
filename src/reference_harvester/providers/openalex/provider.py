from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

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
        ]

        inventory = {
            "provider": "openalex",
            "exported_at": exported_at,
            "api_base": OPENALEX_API_BASE,
            "docs_base": OPENALEX_DOCS_BASE,
            "endpoints": endpoints,
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
            "",
            "## Endpoints",
            "",
        ]
        for ep in endpoints:
            md_lines.append(
                f"- {ep['method']} {ep['path']} — " f"{ep.get('description', '')}"
            )
        (artifacts_dir / "inventory.md").write_text(
            "\n".join(md_lines) + "\n",
            encoding="utf-8",
        )

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
        html_dir = provider_root / "html"
        html_dir.mkdir(parents=True, exist_ok=True)

        harvested_at = datetime.now(timezone.utc).isoformat()
        manifest: list[dict[str, Any]] = []

        for idx, url in enumerate(seeds[:max_pages]):
            if throttle_seconds > 0 and idx:
                time.sleep(throttle_seconds)
            try:
                resp = _http_get(
                    url,
                    headers=_build_headers(email, user_agent),
                    timeout=timeout_s,
                )
                resp.raise_for_status()
                content_type = resp.headers.get("content-type")
                filename = _url_to_filename(url, content_type)
                path = html_dir / filename
                path.write_bytes(resp.content)
                manifest.append(
                    {
                        "url": url,
                        "status_code": resp.status_code,
                        "content_type": content_type,
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

        (provider_root / "manifest.json").write_text(
            json.dumps(
                {
                    "provider": "openalex",
                    "harvested_at": harvested_at,
                    "seeds": seeds,
                    "items": manifest,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

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
        ris_lines.append(f"TI  - OpenAlex Works Search ({len(raw_records)} records)")
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
