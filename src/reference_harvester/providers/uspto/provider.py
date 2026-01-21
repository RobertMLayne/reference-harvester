from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, cast
from urllib.parse import parse_qs, urlencode, urlparse

import reference_harvester.endnote_xml as endnote_xml
from reference_harvester.canonicalizer import canonicalize_batch
from reference_harvester.log_utils import write_jsonl
from reference_harvester.providers.base import ProviderContext, ProviderPlugin
from reference_harvester.providers.uspto.local_constants import (
    USPTO_PROVIDER_ID,
)
from reference_harvester.providers.uspto.local_export import (
    USPTOExportConfig,
    mirror_docs,
    run_uspto_export,
)
from reference_harvester.providers.uspto.local_inventory import (
    Endpoint,
    extract_endpoints,
    load_openapi,
    write_inventory_json,
    write_inventory_md,
)
from reference_harvester.providers.uspto.local_storage import (
    StorePaths,
)
from reference_harvester.providers.uspto.local_storage import (
    path_for_url as _path_for_url,
)
from reference_harvester.registry import load_registry
from reference_harvester.schema_validation import (
    load_json,
    validate_json_file,
    write_report,
)
from reference_harvester.sidecars import (
    build_sidecar_envelope,
    write_sidecar_json,
)

_DEFAULT_SEEDS: tuple[str, ...] = (
    "https://developer.uspto.gov/api-catalog/",
    "https://developer.uspto.gov/ds-api-docs/",
    (
        "https://developer.uspto.gov/product/"
        "patent-application-office-actions-research-dataset"
    ),
    "https://developer.uspto.gov/product/cancer-moonshot-patent-data",
    "https://developer.uspto.gov/ibd-api/swagger.json",
    "https://developer.uspto.gov/data",
    "https://developer.uspto.gov/",
    "https://developer.data.uspto.gov/",
    "https://api.data.uspto.gov/",
    "https://api.uspto.gov/",
    "https://data.uspto.gov/",
    "https://data.uspto.gov/apis/api-rate-limits",
    "https://data.uspto.gov/apis/api-syntax-examples",
    "https://data.uspto.gov/apis/bulk-data/download",
    "https://data.uspto.gov/apis/bulk-data/product",
    "https://data.uspto.gov/apis/bulk-data/search",
    "https://data.uspto.gov/apis/patent-file-wrapper/address",
    "https://data.uspto.gov/apis/patent-file-wrapper/application-data",
    "https://data.uspto.gov/apis/patent-file-wrapper/assignments",
    "https://data.uspto.gov/apis/patent-file-wrapper/associated-documents",
    "https://data.uspto.gov/apis/patent-file-wrapper/continuity",
    "https://data.uspto.gov/apis/patent-file-wrapper/documents",
    "https://data.uspto.gov/apis/patent-file-wrapper/foreign-priority",
    "https://data.uspto.gov/apis/patent-file-wrapper/patent-term-adjustment",
    "https://data.uspto.gov/apis/patent-file-wrapper/patent-term-extension",
    "https://data.uspto.gov/apis/patent-file-wrapper/search",
    "https://data.uspto.gov/apis/patent-file-wrapper/status-codes",
    "https://data.uspto.gov/apis/patent-file-wrapper/transactions",
    "https://data.uspto.gov/apis/petition-decision/download",
    "https://data.uspto.gov/apis/petition-decision/petition-decision-data",
    "https://data.uspto.gov/apis/petition-decision/search",
    "https://data.uspto.gov/apis/ptab-appeals/document-identifier",
    "https://data.uspto.gov/apis/ptab-appeals/download",
    "https://data.uspto.gov/apis/ptab-appeals/search",
    "https://data.uspto.gov/apis/ptab-appeals/search-appeal-number",
    "https://data.uspto.gov/apis/ptab-interferences/document-identifier",
    "https://data.uspto.gov/apis/ptab-interferences/download",
    "https://data.uspto.gov/apis/ptab-interferences/search",
    ("https://data.uspto.gov/apis/ptab-interferences/" "search-interference-number"),
    "https://data.uspto.gov/apis/ptab-trials/decisions-document-identifier",
    "https://data.uspto.gov/apis/ptab-trials/decisions-trial-number",
    "https://data.uspto.gov/apis/ptab-trials/document-identifier",
    "https://data.uspto.gov/apis/ptab-trials/documents-trial-number",
    "https://data.uspto.gov/apis/ptab-trials/download-decisions",
    "https://data.uspto.gov/apis/ptab-trials/download-documents",
    "https://data.uspto.gov/apis/ptab-trials/download-proceedings",
    "https://data.uspto.gov/apis/ptab-trials/proceedings-trial-number",
    "https://data.uspto.gov/apis/ptab-trials/search-decisions",
    "https://data.uspto.gov/apis/ptab-trials/search-documents",
    "https://data.uspto.gov/apis/ptab-trials/search-proceedings",
    "https://data.uspto.gov/apis/transition-guide/bdss",
    "https://data.uspto.gov/apis/transition-guide/peds",
    "https://data.uspto.gov/apis/transition-guide/petitions",
    "https://data.uspto.gov/apis/transition-guide/ptab",
    "https://bulkdata.uspto.gov/",
    "https://bulkdata.uspto.gov/data2/",
    # Additional high-signal subdomains that regularly host USPTO docs.
    "https://www.uspto.gov/",
    "https://patentcenter.uspto.gov/",
    "https://account.uspto.gov/",
    "https://my.uspto.gov/",
    "https://portal.uspto.gov/",
    "https://assignment.uspto.gov/",
    "https://ptacts.uspto.gov/",
    "https://trademarkcenter.uspto.gov/",
    "https://tsdr.uspto.gov/",
    "https://seqdata.uspto.gov/",
)

_DEFAULT_SWAGGER_URLS = (
    "https://data.uspto.gov/swagger/v1/swagger.json",
    "https://developer.data.uspto.gov/swagger.json",
    "https://api.data.uspto.gov/swagger.json",
    "https://developer.uspto.gov/ibd-api/swagger.json",
    "https://developer.uspto.gov/ds-api/swagger/docs/cancer_moonshot.json",
    (
        "https://developer.uspto.gov/ds-api/swagger/docs/"
        "enriched_cited_reference_metadata.json"
    ),
    (
        "https://developer.uspto.gov/ds-api/swagger/docs/"
        "enriched_cited_reference_metadata.json/v2"
    ),
    "https://developer.uspto.gov/ds-api/swagger/docs/oa_actions.json",
    "https://developer.uspto.gov/ds-api/swagger/docs/oa_citations.json",
    "https://developer.uspto.gov/ds-api/swagger/docs/oa_citations.json/v2",
    "https://developer.uspto.gov/ds-api/swagger/docs/oa_rejections.json",
    "https://developer.uspto.gov/ds-api/swagger/docs/oa_rejections.json/v2",
    (
        "https://developer.uspto.gov/ds-api/swagger/docs/"
        "oce_patent_examination_event_codes.json"
    ),
    (
        "https://developer.uspto.gov/ds-api/swagger/docs/"
        "oce_patent_examination_status_codes.json"
    ),
    (
        "https://developer.uspto.gov/ds-api/swagger/docs/"
        "oce_patent_litigation_cases.json"
    ),
)

_ROBOTS_HOSTS = (
    "data.uspto.gov",
    "developer.data.uspto.gov",
    "api.data.uspto.gov",
    "bulkdata.uspto.gov",
    "developer.uspto.gov",
    "api.uspto.gov",
    "www.uspto.gov",
    "patentcenter.uspto.gov",
    "account.uspto.gov",
    "my.uspto.gov",
    "portal.uspto.gov",
    "assignment.uspto.gov",
    "ptacts.uspto.gov",
    "trademarkcenter.uspto.gov",
    "tsdr.uspto.gov",
    "seqdata.uspto.gov",
)

_DEFAULT_BULK_LISTING_URLS = (
    "https://bulkdata.uspto.gov/",
    "https://bulkdata.uspto.gov/data2/",
    "https://bulkdata.uspto.gov/opendata/",
)

_DEFAULT_XHR_PAGES = (
    "https://developer.uspto.gov/api-catalog/",
    "https://developer.uspto.gov/ds-api-docs/",
    "https://developer.uspto.gov/",
    "https://developer.uspto.gov/data",
    "https://data.uspto.gov/apis/",
    "https://data.uspto.gov/ptab",
)

_ALLOWED_HOSTS = {
    "data.uspto.gov",
    "developer.uspto.gov",
    "api.uspto.gov",
    "bulkdata.uspto.gov",
    "developer.data.uspto.gov",
    "uspto.gov",
}

_DOC_HOSTS = {
    "mpep.uspto.gov",
    "tmep.uspto.gov",
    "tbmp.uspto.gov",
}

_AUTH_PLACEHOLDER_HOSTS = (
    "patentcenter.uspto.gov",
    "account.uspto.gov",
    "my.uspto.gov",
    "ptacts.uspto.gov",
    "trademarkcenter.uspto.gov",
    "tsdr.uspto.gov",
    "seqdata.uspto.gov",
    "portal.uspto.gov",
)

_ALLOWED_SUFFIXES = {
    "uspto.gov",
}

_ATTACHMENT_EXTS = {
    ".pdf",
    ".json",
    ".yaml",
    ".yml",
    ".zip",
    ".csv",
    ".xml",
}

_import_harvester_module: Any | None = None
_ensure_harvester_on_path: Any | None = None


def _host_allowed(host: str) -> bool:
    host = host.lower()
    if host in _ALLOWED_HOSTS:
        return True
    for suffix in _ALLOWED_SUFFIXES:
        if host == suffix or host.endswith(f".{suffix}"):
            return True
    return False


@dataclass(frozen=True)
class USPTOSettings:
    user_agent: str = "reference-harvester/0.1"
    http_timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    throttle_seconds: float = 0.0

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> USPTOSettings:
        return cls(
            user_agent=str(options.get("user_agent", cls.user_agent)),
            http_timeout=float(options.get("http_timeout", cls.http_timeout)),
            max_retries=int(options.get("max_retries", cls.max_retries)),
            backoff_factor=float(options.get("backoff_factor", cls.backoff_factor)),
            throttle_seconds=float(
                options.get("throttle_seconds", cls.throttle_seconds)
            ),
        )


class USPTOProvider(ProviderPlugin):
    """USPTO provider using vendored helpers only (no sibling harvester)."""

    def __init__(self) -> None:
        self.export_config_cls = USPTOExportConfig
        self.registry_path = Path(__file__).resolve().parents[2] / "registry"
        self.registry_path /= "uspto_fields.yaml"

    def _parse_since(self, raw: Any) -> datetime | None:
        if not raw:
            return None
        try:
            parsed = datetime.fromisoformat(str(raw))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _settings_from_ctx(self, options: Mapping[str, Any]) -> USPTOSettings:
        return USPTOSettings.from_options(options)

    def refresh_inventory(self, ctx: ProviderContext) -> None:
        from importlib import resources

        provider_root = ctx.out_dir / "raw" / "harvester"
        provider_home = provider_root / USPTO_PROVIDER_ID
        provider_home.mkdir(parents=True, exist_ok=True)
        store = StorePaths(out_root=provider_root)
        artifacts = store.artifacts_root(USPTO_PROVIDER_ID)
        settings = self._settings_from_ctx(ctx.options)
        throttle_seconds = float(
            ctx.options.get(
                "inventory_throttle_seconds",
                settings.throttle_seconds,
            )
        )
        bulk_listing_urls = ctx.options.get("bulk_listing_urls") or list(
            _DEFAULT_BULK_LISTING_URLS
        )
        bulk_listing_max_pages = int(ctx.options.get("bulk_listing_max_pages", 12))
        xhr_pages = ctx.options.get("xhr_pages") or list(_DEFAULT_XHR_PAGES)

        robots_hosts: set[str] = set(
            ctx.options.get("robots_hosts") or list(_ROBOTS_HOSTS)
        )
        robots_hosts.update(self._collect_hosts_from_artifacts(artifacts))
        extra_hosts: set[str] = set()
        for candidate in bulk_listing_urls + xhr_pages:
            host = (urlparse(str(candidate)).hostname or "").lower()
            if host:
                extra_hosts.add(host)
        for candidate in ctx.options.get("extra_robots_hosts") or []:
            host = (urlparse(str(candidate)).hostname or "").lower()
            if host:
                extra_hosts.add(host)
        robots_hosts = set({*robots_hosts, *extra_hosts})
        processed_robots_hosts = set(robots_hosts)
        self._inventory_robots(
            hosts=sorted(robots_hosts),
            artifacts=artifacts,
            settings=settings,
        )

        discovered_assets = self._inventory_bulk_listings(
            listing_urls=bulk_listing_urls,
            artifacts=artifacts,
            settings=settings,
            throttle_seconds=throttle_seconds,
            max_pages=bulk_listing_max_pages,
        )
        self._inventory_xhr_endpoints(
            pages=xhr_pages,
            artifacts=artifacts,
            settings=settings,
            throttle_seconds=throttle_seconds,
        )

        swagger_urls = ctx.options.get("swagger_urls") or list(_DEFAULT_SWAGGER_URLS)
        swagger_urls = self._merge_unique_urls(
            swagger_urls,
            self._discover_swagger_urls_from_xhr(artifacts),
        )

        self._catalog_bulk_assets(
            assets=discovered_assets,
            artifacts=artifacts,
            settings=settings,
            throttle_seconds=throttle_seconds,
        )

        discovered_hosts = self._collect_hosts_from_artifacts(artifacts)
        missing_hosts = sorted(discovered_hosts - processed_robots_hosts)
        if missing_hosts:
            self._inventory_robots(
                hosts=missing_hosts,
                artifacts=artifacts,
                settings=settings,
            )

        importer = globals().get("_import_harvester_module")
        inventory_mod: Any | None = None
        if callable(importer):
            try:
                inventory_mod = importer("harvester.providers.uspto.inventory")
            except ImportError:
                inventory_mod = None

        extract_fn = getattr(
            inventory_mod,
            "extract_endpoints",
            extract_endpoints,
        )
        write_json_fn = getattr(
            inventory_mod,
            "write_inventory_json",
            write_inventory_json,
        )
        write_md_fn = getattr(
            inventory_mod,
            "write_inventory_md",
            write_inventory_md,
        )
        load_spec_fn = getattr(inventory_mod, "load_openapi", load_openapi)
        endpoints_md_columns = ctx.options.get("endpoints_md_columns")
        coverage_md_columns = ctx.options.get("coverage_md_columns")

        specs = self._fetch_swagger_specs(
            swagger_urls=swagger_urls,
            artifacts_dir=artifacts,
            settings=settings,
        )

        if not specs:
            packaged = resources.files("reference_harvester.providers.uspto")
            packaged = packaged.joinpath("resources/swagger.yaml")
            spec_path = Path(str(packaged))
            spec = cast(dict[str, Any], load_spec_fn(spec_path))
            specs = [("packaged", spec_path, spec)]

        self._emit_swagger_artifacts(
            specs=specs,
            artifacts=artifacts,
            endpoints_md_columns=endpoints_md_columns,
            coverage_md_columns=coverage_md_columns,
            extract_fn=cast(
                Callable[[Mapping[str, Any]], Iterable[Endpoint]], extract_fn
            ),
            write_json_fn=cast(
                Callable[[Path, Iterable[Endpoint]], None], write_json_fn
            ),
            write_md_fn=cast(
                Callable[[Path, Iterable[Endpoint]], None],
                write_md_fn,
            ),
        )

    def mirror_sources(self, ctx: ProviderContext) -> None:
        opts = ctx.options
        max_pages = int(opts.get("max_pages", 200))
        include_assets = bool(opts.get("include_assets", True))
        max_assets = int(opts.get("max_assets", 2000))
        settings = self._settings_from_ctx(opts)
        ctx.out_dir.mkdir(parents=True, exist_ok=True)
        harvester_out = ctx.out_dir
        harvester_out.mkdir(parents=True, exist_ok=True)

        backoff_max = settings.backoff_factor * max(1, settings.max_retries)

        mirror_docs(
            out_root=harvester_out,
            max_pages=max_pages,
            include_assets=include_assets,
            max_assets=max_assets,
            user_agent=settings.user_agent,
            timeout_seconds=settings.http_timeout,
            max_attempts=settings.max_retries,
            backoff_base_seconds=settings.backoff_factor,
            backoff_max_seconds=backoff_max,
        )

    def fetch_references(self, ctx: ProviderContext) -> None:
        opts = ctx.options
        max_pages = int(opts.get("max_pages", 200))
        include_assets = bool(opts.get("include_assets", True))
        max_assets = int(opts.get("max_assets", 2000))
        max_depth = int(opts.get("max_depth", 4))
        max_files = int(opts.get("max_files", 200))
        settings = self._settings_from_ctx(opts)
        api_key = opts.get("api_key")
        api_key_env = str(opts.get("api_key_env", "USPTO_ODP_API"))
        browser_fallback = bool(opts.get("browser_fallback", False))
        browser_timeout_ms = int(opts.get("browser_timeout_ms", 60_000))
        convert_html_to_md = bool(opts.get("convert_html_to_md", True))
        emit_ris = bool(opts.get("emit_ris", True))
        emit_csl_json = bool(opts.get("emit_csl_json", False))
        emit_bibtex = bool(opts.get("emit_bibtex", False))
        max_attachments = int(opts.get("max_attachments", 200))
        extra_seeds = opts.get("extra_seeds")
        allow_hosts = {h.lower() for h in opts.get("allow_host", []) or []}
        deny_hosts = {h.lower() for h in opts.get("deny_host", []) or []}
        allow_bulk = {h.lower() for h in opts.get("allow_bulk", []) or []}
        deny_bulk = {h.lower() for h in opts.get("deny_bulk", []) or []}
        max_bulk = int(opts.get("max_bulk", 50))
        max_bulk_bytes = int(opts.get("max_bulk_bytes", 10_000_000_000))
        api_sample_limit = int(opts.get("api_sample_limit", 25))
        validate_schema = bool(opts.get("validate_schema", False))
        default_schema_path = (
            Path("docs")
            / "inputs"
            / "odp"
            / "2026-01-14"
            / "pfw-schemas"
            / "patent-data-schema.json"
        )
        schema_path = Path(str(opts.get("schema_path") or default_schema_path))
        throttle_seconds = float(
            opts.get("throttle_seconds", settings.throttle_seconds)
        )
        bulk_urls = opts.get("bulk_urls") or []
        since_dt = self._parse_since(opts.get("since"))

        backoff_max = settings.backoff_factor * max(1, settings.max_retries)

        ctx.out_dir.mkdir(parents=True, exist_ok=True)
        cfg = USPTOExportConfig(
            out_dir=ctx.out_dir,
            max_pages=max_pages,
            include_assets=include_assets,
            max_assets=max_assets,
            max_files=max_files,
            user_agent=settings.user_agent,
            http_timeout=settings.http_timeout,
            max_retries=settings.max_retries,
            backoff_factor=settings.backoff_factor,
            backoff_max_seconds=backoff_max,
            api_key=api_key,
            api_key_env=api_key_env,
            browser_fallback=browser_fallback,
            browser_timeout_ms=browser_timeout_ms,
            convert_html_to_md=convert_html_to_md,
            emit_ris=emit_ris,
            emit_csl_json=emit_csl_json,
            emit_bibtex=emit_bibtex,
        )
        run_uspto_export(cfg)

        self._harvest_additional_subdomains(
            out_root=ctx.out_dir,
            settings=settings,
            max_pages=max_pages,
            max_attachments=max_attachments,
            extra_seeds=extra_seeds,
            allow_hosts=allow_hosts,
            deny_hosts=deny_hosts,
            throttle_seconds=throttle_seconds,
            max_depth=max_depth,
            since=since_dt,
        )

        from importlib import resources

        importer = globals().get("_import_harvester_module")
        inventory_mod: Any | None = None
        if callable(importer):
            try:
                inventory_mod = importer("harvester.providers.uspto.inventory")
            except ImportError:
                inventory_mod = None

        extract_fn = getattr(
            inventory_mod,
            "extract_endpoints",
            extract_endpoints,
        )
        write_json_fn = getattr(
            inventory_mod,
            "write_inventory_json",
            write_inventory_json,
        )
        write_md_fn = getattr(
            inventory_mod,
            "write_inventory_md",
            write_inventory_md,
        )
        load_spec_fn = getattr(inventory_mod, "load_openapi", load_openapi)

        provider_root = ctx.out_dir / "raw" / "harvester"
        provider_root.mkdir(parents=True, exist_ok=True)
        provider_home = provider_root / USPTO_PROVIDER_ID
        provider_home.mkdir(parents=True, exist_ok=True)
        store = StorePaths(out_root=provider_root)
        artifacts = store.artifacts_root(USPTO_PROVIDER_ID)
        xhr_pages = opts.get("xhr_pages") or list(_DEFAULT_XHR_PAGES)
        self._inventory_xhr_endpoints(
            pages=xhr_pages,
            artifacts=artifacts,
            settings=settings,
            throttle_seconds=throttle_seconds,
            use_playwright=browser_fallback,
        )

        swagger_urls = opts.get("swagger_urls") or list(_DEFAULT_SWAGGER_URLS)
        swagger_urls = self._merge_unique_urls(
            swagger_urls,
            self._discover_swagger_urls_from_xhr(artifacts),
        )
        endpoints_md_columns = opts.get("endpoints_md_columns")
        coverage_md_columns = opts.get("coverage_md_columns")

        specs = self._fetch_swagger_specs(
            swagger_urls=swagger_urls,
            artifacts_dir=artifacts,
            settings=settings,
        )

        if not specs:
            packaged = resources.files("reference_harvester.providers.uspto")
            packaged = packaged.joinpath("resources/swagger.yaml")
            spec_path = Path(str(packaged))
            spec = cast(dict[str, Any], load_spec_fn(spec_path))
            specs = [("packaged", spec_path, spec)]

        self._emit_swagger_artifacts(
            specs=specs,
            artifacts=artifacts,
            endpoints_md_columns=endpoints_md_columns,
            coverage_md_columns=coverage_md_columns,
            extract_fn=cast(
                Callable[[Mapping[str, Any]], Iterable[Endpoint]], extract_fn
            ),
            write_json_fn=cast(
                Callable[[Path, Iterable[Endpoint]], None], write_json_fn
            ),
            write_md_fn=cast(
                Callable[[Path, Iterable[Endpoint]], None],
                write_md_fn,
            ),
        )

        self._sample_api_endpoints(
            out_root=provider_home,
            settings=settings,
            sample_limit=api_sample_limit,
            throttle_seconds=throttle_seconds,
            since=since_dt,
        )

        if validate_schema:
            self._validate_api_samples_schema(
                provider_home=provider_home,
                schema_path=schema_path,
            )

        self._download_bulk_artifacts(
            out_root=provider_home,
            settings=settings,
            bulk_urls=self._load_discovered_bulk_urls(artifacts) + bulk_urls,
            allow_hosts=allow_bulk or allow_hosts,
            deny_hosts=deny_bulk or deny_hosts,
            max_bulk=max_bulk,
            max_bulk_bytes=max_bulk_bytes,
            throttle_seconds=throttle_seconds,
            since=since_dt,
        )

        self._write_run_manifest(out_root=provider_home)

        self._emit_canonical_logs(
            provider_home,
            emit_ris=emit_ris,
            emit_csl_json=emit_csl_json,
            emit_bibtex=emit_bibtex,
        )

    def export_endnote(self, ctx: ProviderContext) -> None:
        ctx.out_dir.mkdir(parents=True, exist_ok=True)

        registry = load_registry(self.registry_path)
        endnote_dir = ctx.out_dir / "endnote"
        table_path = endnote_dir / "reference_type_table.xml"
        write_ref_table = getattr(
            endnote_xml,
            "write_reference_type_table",
        )
        write_ref_table(
            table_path,
            registry,
            type_name="USPTO",
            base_type_name="Generic",
            target_slot_name="Unused 1",
            field_label_overrides={
                # In the shipped template, Generic maps:
                # Custom 1..8 -> field ids 25,26,27,28,33,34,42,52
                "id:25": "USPTO Application Number",
                "id:26": "USPTO Trial Number",
                "id:27": "USPTO Document ID",
                "id:28": "USPTO Document Type",
                "id:33": "USPTO Status",
                "id:34": "USPTO Filing Date",
                "id:42": "USPTO Download URL",
                "id:52": "SHA256",
            },
        )

        provider_home = ctx.out_dir / "raw" / "harvester" / USPTO_PROVIDER_ID
        try:
            if provider_home.exists():
                raw_records = list(self._iter_harvester_manifest_entries(provider_home))
                normalized, diags = canonicalize_batch(raw_records, registry)

                # Sidecars + RIS are written under endnote/ so relative paths
                # work.
                endnote_dir.mkdir(parents=True, exist_ok=True)
                sidecars_dir = endnote_dir / "sidecars"
                sidecars_dir.mkdir(parents=True, exist_ok=True)
                ris_path = endnote_dir / "uspto.ris"

                exported_at = datetime.now(timezone.utc).isoformat()
                ris_lines: list[str] = []

                # (Req #5) Bulk manifest reference: model the snapshot as a
                # Dataset-style RIS record with its own sidecar attachment.
                manifest_entries = raw_records
                manifest_paths = sorted(provider_home.glob("**/manifest.json"))
                manifest_sources: list[dict[str, str]] = []
                manifest_key_hasher = hashlib.sha256()
                for mp in manifest_paths:
                    try:
                        data = mp.read_bytes()
                    except OSError:
                        continue
                    rel = mp.relative_to(provider_home).as_posix()
                    file_sha = hashlib.sha256(data).hexdigest()
                    manifest_sources.append({"path": rel, "sha256": file_sha})
                    manifest_key_hasher.update(rel.encode("utf-8"))
                    manifest_key_hasher.update(b"\0")
                    manifest_key_hasher.update(file_sha.encode("utf-8"))
                    manifest_key_hasher.update(b"\0")

                # Best-effort date range + endpoint counts for the bulk
                # manifest record. Upstream harvesters vary in timestamp field
                # naming, so we probe a small set of likely keys.
                def _parse_iso_dt(value: Any) -> datetime | None:
                    if not value:
                        return None
                    if isinstance(value, datetime):
                        return value
                    if not isinstance(value, str):
                        return None
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        return None

                ts_fields = (
                    "downloaded_at",
                    "fetched_at",
                    "created_at",
                    "timestamp",
                    "ts",
                )
                observed_times: list[datetime] = []
                endpoint_counts: dict[str, int] = {}
                for entry in manifest_entries:
                    if not isinstance(entry, dict):
                        continue

                    for k in ts_fields:
                        dt = _parse_iso_dt(entry.get(k))
                        if dt is not None:
                            observed_times.append(dt)

                    endpoint = entry.get("endpoint") or entry.get("kind")
                    if isinstance(endpoint, str) and endpoint.strip():
                        key = endpoint.strip()
                    else:
                        url_val = entry.get("url") or entry.get("documentURL")
                        u = str(url_val or "")
                        parsed = urlparse(u)
                        parts = [p for p in parsed.path.split("/") if p]
                        prefix = parts[0] if parts else ""
                        host = parsed.netloc or "unknown-host"
                        key = f"{host}/{prefix}" if prefix else host
                    endpoint_counts[key] = endpoint_counts.get(key, 0) + 1

                observed_min = min(observed_times) if observed_times else None
                observed_max = max(observed_times) if observed_times else None

                bulk_artifacts: list[dict[str, Any]] = []
                bulk_dir = provider_home / "bulk"
                if bulk_dir.exists():
                    for p in sorted(bulk_dir.rglob("*")):
                        if not p.is_file():
                            continue
                        if p.suffix.lower() not in _ATTACHMENT_EXTS:
                            continue
                        try:
                            stat = p.stat()
                        except OSError:
                            continue
                        bulk_artifacts.append(
                            {
                                "path": p.relative_to(provider_home).as_posix(),
                                "size_bytes": stat.st_size,
                            }
                        )

                bulk_key = manifest_key_hasher.hexdigest()
                bulk_stable_id = f"bulk:{bulk_key}"
                bulk_url = "https://bulkdata.uspto.gov/"
                bulk_data = {
                    "url": bulk_url,
                    "records_count": len(manifest_entries),
                    "observed_date_min": (
                        observed_min.isoformat() if observed_min else None
                    ),
                    "observed_date_max": (
                        observed_max.isoformat() if observed_max else None
                    ),
                    "endpoint_counts": dict(
                        sorted(endpoint_counts.items(), key=lambda kv: kv[0])
                    ),
                    "manifest_sources": manifest_sources,
                    "bulk_artifacts": bulk_artifacts,
                    "manifest_entries": manifest_entries,
                }
                bulk_sidecar_envelope = build_sidecar_envelope(
                    provider="uspto",
                    kind="bulk_manifest",
                    stable_id=bulk_stable_id,
                    exported_at=exported_at,
                    data=bulk_data,
                )
                bulk_sha256, bulk_sidecar_path = write_sidecar_json(
                    sidecars_dir=sidecars_dir,
                    envelope=bulk_sidecar_envelope,
                )
                bulk_sidecar_filename = bulk_sidecar_path.name

                # Use TY=DATA so EndNote imports this as a Dataset.
                ris_lines.append("TY  - DATA")
                bulk_title = f"USPTO Bulk Manifest ({len(manifest_entries)} records)"
                ris_lines.append(f"TI  - {bulk_title}")
                ris_lines.append(f"UR  - {bulk_url}")
                ris_lines.append(f"AN  - uspto:{bulk_stable_id}")
                if observed_min or observed_max:
                    lo = observed_min.isoformat() if observed_min else ""
                    hi = observed_max.isoformat() if observed_max else ""
                    ris_lines.append(f"N1  - Observed range: {lo} .. {hi}")
                for key, count in sorted(endpoint_counts.items()):
                    ris_lines.append(f"KW  - endpoint:{key} count:{count}")
                ris_lines.append(f"C8  - {bulk_sha256}")
                ris_lines.append(f"L1  - sidecars/{bulk_sidecar_filename}")
                ris_lines.append("ER  -")

                for idx, (raw, norm, diag) in enumerate(
                    zip(raw_records, normalized, diags)
                ):
                    canonical = norm.get("canonical", {})
                    if not isinstance(canonical, dict):
                        canonical = {}

                    url_val = (
                        canonical.get("document_url")
                        or canonical.get("url")
                        or raw.get("url")
                    )
                    url = str(url_val or "")
                    stable_id = str(
                        canonical.get("document_id")
                        or canonical.get("trial_number")
                        or canonical.get("owner_patent_number")
                        or canonical.get("owner_application_number")
                        or raw.get("id")
                        or url
                        or f"record-{idx + 1}"
                    )

                    record_data = {
                        "raw": raw,
                        "normalized": norm,
                        "diagnostics": diag,
                    }
                    sidecar_envelope = build_sidecar_envelope(
                        provider="uspto",
                        kind="record",
                        stable_id=stable_id,
                        exported_at=exported_at,
                        data=record_data,
                    )
                    sha256, sidecar_path = write_sidecar_json(
                        sidecars_dir=sidecars_dir,
                        envelope=sidecar_envelope,
                    )
                    sidecar_filename = sidecar_path.name

                    title = str(
                        canonical.get("document_id")
                        or canonical.get("document_type")
                        or canonical.get("download_url")
                        or url
                        or f"record-{idx + 1}"
                    )

                    # RIS: use custom tags C1..C8 to populate repurposed Custom
                    # fields. EndNote typically maps AN -> Accession Number and
                    # L1 -> File Attachments.
                    ris_lines.append("TY  - DATA")
                    ris_lines.append(f"TI  - {title}")
                    if url:
                        ris_lines.append(f"UR  - {url}")
                    ris_lines.append(f"AN  - uspto:{stable_id}")
                    c1 = str(
                        canonical.get("owner_application_number")
                        or canonical.get("application_number")
                        or ""
                    )
                    c2 = str(canonical.get("trial_number") or "")
                    c3 = str(canonical.get("document_id") or "")
                    c4 = str(
                        canonical.get("document_type") or canonical.get("type") or ""
                    )
                    c5 = str(canonical.get("status") or "")
                    c6 = str(
                        canonical.get("filing_date")
                        or canonical.get("petition_filed_at")
                        or ""
                    )
                    c7 = str(
                        canonical.get("download_url") or canonical.get("file_url") or ""
                    )
                    ris_lines.append(f"C1  - {c1}")
                    ris_lines.append(f"C2  - {c2}")
                    ris_lines.append(f"C3  - {c3}")
                    ris_lines.append(f"C4  - {c4}")
                    ris_lines.append(f"C5  - {c5}")
                    ris_lines.append(f"C6  - {c6}")
                    ris_lines.append(f"C7  - {c7}")
                    ris_lines.append(f"C8  - {sha256}")
                    ris_lines.append(f"L1  - sidecars/{sidecar_filename}")
                    ris_lines.append("ER  -")

                if ris_lines:
                    ris_path.write_text(
                        "\n".join(ris_lines) + "\n",
                        encoding="utf-8",
                    )
                    print(f"[uspto] EndNote RIS written to {ris_path}")
                    print(f"[uspto] EndNote sidecars written to {sidecars_dir}")
        except (OSError, RuntimeError, ValueError) as exc:  # pragma: no cover
            print(f"[uspto] EndNote export skipped: {exc}")

        print(f"[uspto] EndNote reference type table written to {table_path}")

    def _iter_harvester_manifest_entries(
        self,
        harvester_out: Path,
    ) -> Iterable[dict]:
        manifests = list(harvester_out.glob("**/manifest.json"))
        for manifest_path in manifests:
            try:
                payload = manifest_path.read_text(encoding="utf-8")
                payload = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, list):
                continue
            for entry in payload:
                if isinstance(entry, dict):
                    yield entry

    def _emit_canonical_logs(
        self,
        out_dir: Path,
        *,
        emit_ris: bool,
        emit_csl_json: bool,
        emit_bibtex: bool,
    ) -> None:
        harvester_out = out_dir
        logs_dir = out_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        raw_records = list(self._iter_harvester_manifest_entries(harvester_out))
        write_jsonl(logs_dir / "raw_provider.jsonl", raw_records)

        registry = load_registry(self.registry_path)
        normalized, diags = canonicalize_batch(raw_records, registry)
        write_jsonl(logs_dir / "normalized_canonical.jsonl", normalized)
        write_jsonl(logs_dir / "mapping_diagnostics.jsonl", diags)
        self._write_manifest(logs_dir, raw_records, normalized, diags)

        self._emit_canonical_citations(
            logs_dir,
            normalized,
            emit_ris=emit_ris,
            emit_csl_json=emit_csl_json,
            emit_bibtex=emit_bibtex,
        )

    def _validate_api_samples_schema(
        self,
        *,
        provider_home: Path,
        schema_path: Path,
    ) -> None:
        samples_root = provider_home / "api_samples"
        logs_dir = provider_home / "logs"
        report_path = logs_dir / "reports" / "schema_validation_api_samples.json"

        if not samples_root.exists():
            write_report(
                report_path,
                {
                    "schema_path": str(schema_path),
                    "status": "skipped",
                    "reason": "api_samples directory not found",
                },
            )
            return

        if not schema_path.exists():
            write_report(
                report_path,
                {
                    "schema_path": str(schema_path),
                    "status": "error",
                    "reason": "schema file not found",
                },
            )
            raise SystemExit(2)

        schema = load_json(schema_path)
        if not isinstance(schema, dict):
            write_report(
                report_path,
                {
                    "schema_path": str(schema_path),
                    "status": "error",
                    "reason": "schema is not a JSON object",
                },
            )
            raise SystemExit(2)

        json_files = sorted(samples_root.glob("**/*.json"))
        failures: list[dict[str, object]] = []
        validated = 0

        for json_path in json_files:
            errors = validate_json_file(
                json_path,
                schema,
                schema_root=schema,
            )
            validated += 1
            if errors:
                failures.append(
                    {
                        "file": str(json_path.relative_to(provider_home)).replace(
                            "\\", "/"
                        ),
                        "errors": [
                            {"path": err.path, "message": err.message} for err in errors
                        ],
                    }
                )

        report = {
            "schema_path": str(schema_path),
            "status": "ok" if not failures else "failed",
            "validated_files": validated,
            "failed_files": len(failures),
            "failures": failures,
        }
        write_report(report_path, report)

        if failures:
            raise SystemExit(1)

    def _write_manifest(
        self,
        logs_dir: Path,
        raw_records: list[dict[str, Any]],
        normalized: list[dict[str, Any]],
        diags: list[dict[str, Any]],
    ) -> None:
        manifest = [
            {"artifact": "raw_provider.jsonl", "records": len(raw_records)},
            {
                "artifact": "normalized_canonical.jsonl",
                "records": len(normalized),
            },
            {
                "artifact": "mapping_diagnostics.jsonl",
                "records": len(diags),
            },
        ]
        write_jsonl(logs_dir / "manifest.jsonl", manifest)

    def _emit_canonical_citations(
        self,
        logs_dir: Path,
        normalized: list[dict[str, Any]],
        *,
        emit_ris: bool,
        emit_csl_json: bool,
        emit_bibtex: bool,
    ) -> None:
        citations_dir = logs_dir / "citations"
        citations_dir.mkdir(parents=True, exist_ok=True)

        items: list[dict[str, str]] = []
        for idx, rec in enumerate(normalized):
            canonical = rec.get("canonical", {})
            if not isinstance(canonical, dict):
                canonical = {}
            url_val = canonical.get("document_url") or canonical.get("url") or ""
            url = str(url_val)
            title = str(
                canonical.get("document_id")
                or canonical.get("document_type")
                or canonical.get("download_url")
                or url
                or f"record-{idx + 1}"
            )
            items.append({"title": title, "url": url})

        if emit_ris and items:
            lines: list[str] = []
            for item in items:
                lines.append("TY  - DATA")
                lines.append(f"TI  - {item['title']}")
                if item.get("url"):
                    lines.append(f"UR  - {item['url']}")
                lines.append("ER  -")
            (citations_dir / "uspto-canonical.ris").write_text(
                "\n".join(lines) + "\n",
                encoding="utf-8",
            )

        if emit_csl_json and items:
            csl = []
            for idx, item in enumerate(items):
                csl.append(
                    {
                        "id": f"uspto-{idx + 1}",
                        "type": "document",
                        "title": item.get("title"),
                        "URL": item.get("url"),
                    }
                )
            (citations_dir / "uspto-canonical.csl.json").write_text(
                json.dumps(csl, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        if emit_bibtex and items:
            bib_lines: list[str] = []
            for idx, item in enumerate(items):
                key = f"uspto{idx + 1}"
                bib_lines.append(f"@misc{{{key},")
                bib_lines.append(f"  title = {{{item['title']}}},")
                if item.get("url"):
                    bib_lines.append(f"  url = {{{item['url']}}},")
                bib_lines.append("}")
                bib_lines.append("")
            (citations_dir / "uspto-canonical.bib").write_text(
                "\n".join(bib_lines),
                encoding="utf-8",
            )

    def _harvest_additional_subdomains(
        self,
        *,
        out_root: Path,
        settings: USPTOSettings,
        max_pages: int,
        max_attachments: int,
        extra_seeds: Iterable[str] | None,
        allow_hosts: set[str] | None,
        deny_hosts: set[str] | None,
        throttle_seconds: float,
        max_depth: int,
        since: datetime | None,
    ) -> None:
        import re
        import time
        from collections import deque
        from urllib import robotparser
        from urllib.parse import urldefrag, urljoin

        import requests

        provider_root = out_root.resolve()
        pages_root = provider_root / "html"
        assets_root = provider_root / "assets"
        manifest_path = provider_root / "manifest.json"
        manifest_path_jsonl = manifest_path.with_suffix(".jsonl")

        pages_root.mkdir(parents=True, exist_ok=True)
        assets_root.mkdir(parents=True, exist_ok=True)

        allow_hosts = allow_hosts or set()
        deny_hosts = deny_hosts or set()
        robots_parsers: dict[str, robotparser.RobotFileParser] = {}
        disallowed_urls: list[dict[str, Any]] = []
        failed_urls: list[dict[str, Any]] = []

        def _robots_allows(url: str) -> bool:
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            if not host:
                return False
            rp = robots_parsers.get(host)
            if rp is None:
                rp = robotparser.RobotFileParser()
                robots_url = f"{parsed.scheme}://{host}/robots.txt"
                resp = _request(robots_url)
                if resp and resp.ok:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.parse([])
                robots_parsers[host] = rp
            allows = rp.can_fetch(settings.user_agent, url)
            if not allows:
                disallowed_urls.append(
                    {
                        "url": url,
                        "reason": "robots.txt disallow",
                        "host": host,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            return allows

        def _host_in_scope(host: str) -> bool:
            host = host.lower()
            if host in deny_hosts:
                return False
            if allow_hosts:
                return host in allow_hosts
            return _host_allowed(host)

        def _canon(url: str) -> str | None:
            cleaned, _frag = urldefrag(url.strip())
            parsed = urlparse(cleaned)
            if parsed.scheme not in {"http", "https"}:
                return None
            host = (parsed.hostname or parsed.netloc or "").lower()
            if not host or not _host_in_scope(host):
                return None
            netloc = (parsed.netloc or host).lower()
            path = parsed.path
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            normalized = parsed._replace(netloc=netloc, path=path, fragment="")
            return normalized.geturl()

        def _is_attachment(url: str) -> bool:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                return False
            host = (parsed.hostname or parsed.netloc or "").lower()
            if not host or not _host_in_scope(host):
                return False
            lower_path = parsed.path.lower()
            return lower_path.startswith("/documents/") or any(
                lower_path.endswith(ext) for ext in _ATTACHMENT_EXTS
            )

        def _extract_links(text: str, base: str) -> set[str]:
            links: set[str] = set()
            hrefs = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', text, re.I)
            hrefs.extend(re.findall(r"https?://[^\s\"'<>]+", text, re.I))
            for raw in hrefs:
                joined = urljoin(base, raw)
                canon = _canon(joined)
                if canon:
                    links.add(canon)
            return links

        def _request(
            url: str, prev_entry: dict[str, Any] | None = None
        ) -> requests.Response | None:
            attempt = 0
            max_attempts = max(1, settings.max_retries)
            backoff_cap = settings.backoff_factor * max_attempts
            last_resp: requests.Response | None = None
            base_headers = {"User-Agent": settings.user_agent}
            if prev_entry:
                prev_etag = prev_entry.get("etag")
                prev_last_modified = prev_entry.get("last_modified")
                if prev_etag:
                    base_headers["If-None-Match"] = str(prev_etag)
                if prev_last_modified:
                    base_headers["If-Modified-Since"] = str(prev_last_modified)

            while attempt < max_attempts:
                try:
                    resp = requests.get(
                        url,
                        headers=base_headers,
                        timeout=int(settings.http_timeout),
                    )
                    last_resp = resp
                except requests.RequestException:
                    resp = None

                if resp is None:
                    attempt += 1
                    delay = min(
                        settings.backoff_factor * (2 ** (attempt - 1)),
                        backoff_cap,
                    )
                    time.sleep(delay)
                    continue

                if throttle_seconds > 0:
                    time.sleep(throttle_seconds)

                if resp.status_code == 304:
                    return resp

                status = int(resp.status_code)
                if status == 429 or status >= 500:
                    attempt += 1
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 0.0
                    except ValueError:
                        delay = 0.0
                    if delay <= 0:
                        delay = min(
                            settings.backoff_factor * (2 ** (attempt - 1)),
                            backoff_cap,
                        )
                    time.sleep(delay)
                    continue

                return resp

            return last_resp

        seeds = list(_DEFAULT_SEEDS)
        if extra_seeds:
            for seed in extra_seeds:
                canon = _canon(str(seed))
                if canon:
                    seeds.append(canon)

        queue: deque[tuple[str, int]] = deque()
        seen_pages: set[str] = set()
        seen_attachments: set[str] = set()
        manifest_records: list[dict[str, Any]] = []
        existing_shas: set[str] = set()
        sha_to_local: dict[str, str] = {}
        existing_by_url: dict[str, dict[str, Any]] = {}
        stale_urls: set[str] = set()

        if manifest_path.exists():
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    manifest_records = [
                        entry for entry in payload if isinstance(entry, dict)
                    ]
            except json.JSONDecodeError:
                manifest_records = []
        elif manifest_path_jsonl.exists():
            manifest_records = []
            text = manifest_path_jsonl.read_text(encoding="utf-8")
            lines = text.splitlines()
            for line in lines:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict):
                    manifest_records.append(rec)

        recorded_urls: set[str] = set()
        for rec in manifest_records:
            url_val = str(rec.get("url") or "")
            if not url_val:
                continue
            fetched_at_raw = rec.get("fetched_at")
            fetched_at = None
            if isinstance(fetched_at_raw, str):
                try:
                    fetched_at = datetime.fromisoformat(fetched_at_raw)
                except ValueError:
                    fetched_at = None
            if fetched_at is not None and fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            if since and fetched_at and fetched_at < since:
                stale_urls.add(url_val)
            else:
                recorded_urls.add(url_val)

            existing_by_url[url_val] = rec
            sha_val = rec.get("sha256")
            if isinstance(sha_val, str):
                existing_shas.add(sha_val)
                existing_local_path = rec.get("local_path")
                if isinstance(existing_local_path, str):
                    sha_to_local[sha_val] = existing_local_path

        for seed in seeds:
            canon = _canon(seed)
            if not canon or canon in seen_pages or canon in recorded_urls:
                continue
            queue.append((canon, 0))
            seen_pages.add(canon)

        pages_fetched = 0
        attachments_fetched = 0

        while queue and (
            pages_fetched < max_pages or attachments_fetched < max_attachments
        ):
            url, depth = queue.popleft()
            prev_entry = existing_by_url.get(url)
            if url in recorded_urls and url not in stale_urls:
                continue
            if _is_attachment(url) and attachments_fetched >= max_attachments:
                continue
            if not _is_attachment(url) and pages_fetched >= max_pages:
                continue
            if not _robots_allows(url):
                continue
            resp = _request(url, prev_entry)
            if resp is None:
                parsed = urlparse(url)
                failed_urls.append(
                    {
                        "url": url,
                        "host": (parsed.hostname or parsed.netloc or ""),
                        "reason": "request_failed",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue

            if resp.status_code == 304:
                recorded_urls.add(url)
                continue

            content_type = (resp.headers.get("Content-Type") or "").lower()
            body = resp.content
            sha = hashlib.sha256(body).hexdigest()
            is_html = "html" in content_type or body.lstrip().startswith(b"<")
            dest_root = pages_root if is_html else assets_root
            deduped_by_hash = False
            local_path: str | None = None

            if sha in existing_shas:
                cached_path = sha_to_local.get(sha)
                if cached_path:
                    local_path = cached_path
                    deduped_by_hash = True

            if local_path is None:
                dest = _path_for_url(dest_root, url)
                if dest.suffix == "":
                    dest = dest.with_suffix(".html" if is_html else ".bin")
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    dest.write_bytes(body)
                except OSError:
                    continue
                local_path = str(dest.relative_to(out_root)).replace("\\", "/")
                sha_to_local.setdefault(sha, local_path)

            if local_path is None:
                continue

            existing_shas.add(sha)
            host_val = urlparse(url).hostname or ""

            entry = {
                "url": url,
                "host": host_val,
                "local_path": local_path,
                "status_code": int(resp.status_code),
                "content_type": content_type or None,
                "etag": resp.headers.get("ETag"),
                "last_modified": resp.headers.get("Last-Modified"),
                "content_length": resp.headers.get("Content-Length"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "sha256": sha,
                "size_bytes": len(body),
                "is_html": is_html,
                "is_bulk_artifact": False,
                "is_api_sample": False,
                "deduped_by_hash": deduped_by_hash,
                "depth": depth,
            }
            if host_val.lower() in _DOC_HOSTS:
                entry["is_documentation"] = True
            if url not in recorded_urls:
                manifest_records.append(entry)
                recorded_urls.add(url)
            if resp.status_code >= 400:
                parsed = urlparse(url)
                failed_urls.append(
                    {
                        "url": url,
                        "host": (parsed.hostname or parsed.netloc or ""),
                        "status_code": int(resp.status_code),
                        "reason": "http_error",
                        "fetched_at": entry["fetched_at"],
                    }
                )

            if is_html:
                pages_fetched += 1
            else:
                attachments_fetched += 1

            if is_html and pages_fetched < max_pages:
                text = body.decode("utf-8", errors="ignore")
                for link in sorted(_extract_links(text, url)):
                    next_depth = depth + 1
                    if next_depth > max_depth:
                        continue
                    if _is_attachment(link):
                        if attachments_fetched >= max_attachments:
                            continue
                        if link not in seen_attachments:
                            seen_attachments.add(link)
                            queue.append((link, next_depth))
                    else:
                        if link in seen_pages or len(seen_pages) >= max_pages:
                            continue
                        seen_pages.add(link)
                        queue.append((link, next_depth))
            elif not is_html and attachments_fetched >= max_attachments:
                break

        manifest_path.write_text(
            json.dumps(manifest_records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(manifest_path.with_suffix(".jsonl"), manifest_records)
        if disallowed_urls:
            write_jsonl(provider_root / "disallowed.jsonl", disallowed_urls)
        if failed_urls:
            write_jsonl(
                provider_root / "failures_additional.jsonl",
                failed_urls,
            )

    def _sample_api_endpoints(
        self,
        *,
        out_root: Path,
        settings: USPTOSettings,
        sample_limit: int,
        throttle_seconds: float,
        since: datetime | None = None,
    ) -> None:
        import re
        import time

        import requests

        provider_root = out_root
        if provider_root.name.lower() != USPTO_PROVIDER_ID.lower():
            provider_root = out_root / "raw" / "harvester" / USPTO_PROVIDER_ID
        provider_root.mkdir(parents=True, exist_ok=True)
        artifacts_root = provider_root / "artifacts"
        samples_root = provider_root / "api_samples"
        manifest_path = samples_root / "manifest.json"

        samples_root.mkdir(parents=True, exist_ok=True)

        manifest_records: list[dict[str, Any]] = []
        existing_shas: set[str] = set()
        seen_urls: set[str] = set()
        stale_urls: set[str] = set()
        existing_by_url: dict[str, dict[str, Any]] = {}
        failure_records: list[dict[str, Any]] = []

        if manifest_path.exists():
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    manifest_records = [
                        entry for entry in payload if isinstance(entry, dict)
                    ]
            except json.JSONDecodeError:
                manifest_records = []

        for rec in manifest_records:
            sha_val = rec.get("sha256")
            if isinstance(sha_val, str):
                existing_shas.add(sha_val)
            url_val = rec.get("url")
            if isinstance(url_val, str):
                fetched_at_raw = rec.get("fetched_at")
                fetched_at = None
                if isinstance(fetched_at_raw, str):
                    try:
                        fetched_at = datetime.fromisoformat(fetched_at_raw)
                    except ValueError:
                        fetched_at = None
                if fetched_at is not None and fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                if since and fetched_at and fetched_at < since:
                    stale_urls.add(url_val)
                else:
                    seen_urls.add(url_val)
                existing_by_url[url_val] = rec

        coverage_files = sorted(artifacts_root.glob("coverage*.json"))
        candidates: list[dict[str, str]] = []
        for path in coverage_files:
            try:
                entries = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                host = str(entry.get("host") or "").strip()
                method = str(entry.get("method") or "").upper().strip()
                path_val = str(entry.get("path") or "").strip()
                if not host or not path_val or method != "GET":
                    continue
                candidates.append(
                    {
                        "host": host,
                        "path": path_val,
                        "method": method,
                    }
                )

        seen_keys: set[tuple[str, str]] = set()
        picked: list[dict[str, str]] = []
        for candidate in candidates:
            host = candidate["host"]
            path_val = candidate["path"]
            key = (host, path_val)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            picked.append(candidate)
            if len(picked) >= sample_limit:
                break

        def _sample_for(name: str) -> str:
            lowered = name.lower()
            if "application" in lowered or "appl" in lowered:
                return "00000000"
            if "document" in lowered or "doc" in lowered:
                return "1234567890"
            if "patent" in lowered:
                return "0000000"
            if "proceeding" in lowered or "trial" in lowered:
                return "000000"
            if "date" in lowered:
                return "2020-01-01"
            if "id" in lowered or "number" in lowered:
                return "sample"
            return "sample"

        def _fill_path_params(path_val: str) -> str:
            def _repl(match: re.Match[str]) -> str:
                return _sample_for(match.group(1))

            return re.sub(r"{([^}]+)}", _repl, path_val)

        def _build_query_params(path_val: str) -> dict[str, str]:
            params: dict[str, str] = {}
            today = datetime.now(timezone.utc).date()
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            lowered = path_val.lower()
            if "search" in lowered:
                params.setdefault("searchText", "test")
                params.setdefault("rows", "5")
                params.setdefault("start", "0")
                params.setdefault("q", "test")
            if "startdate" in lowered or "from" in lowered:
                params.setdefault("startDate", start_date)
            if "enddate" in lowered or "to" in lowered:
                params.setdefault("endDate", end_date)
            if (
                "date" in lowered
                and "startdate" not in lowered
                and "enddate" not in lowered
            ):
                params.setdefault("date", end_date)
            if "rows" in lowered and "rows" not in params:
                params["rows"] = "5"
            if "offset" in lowered and "offset" not in params:
                params["offset"] = "0"
            if "page" in lowered and "page" not in params:
                params["page"] = "1"
            if "pagesize" in lowered and "pageSize" not in params:
                params["pageSize"] = "5"
            if "size" in lowered and "size" not in params:
                params["size"] = "5"
            if "limit" in lowered and "limit" not in params:
                params["limit"] = "5"
            if "perpage" in lowered and "perPage" not in params:
                params["perPage"] = "5"

            id_value = _sample_for("id")
            if "application" in lowered or "appl" in lowered:
                for key in (
                    "applicationNumber",
                    "application",
                    "applId",
                    "applNumber",
                ):
                    params.setdefault(key, id_value)
            if "serial" in lowered:
                params.setdefault("serialNumber", id_value)
            if "patent" in lowered:
                params.setdefault("patentNumber", _sample_for("patent"))
            if "document" in lowered or "doc" in lowered:
                for key in ("docId", "documentId"):
                    params.setdefault(key, _sample_for("document"))
            if "proceeding" in lowered or "trial" in lowered:
                params.setdefault(
                    "proceedingNumber",
                    _sample_for("proceeding"),
                )

            return params

        for candidate in picked:
            host = candidate["host"]
            path_val = candidate["path"]
            filled_path = _fill_path_params(path_val)
            query_params = _build_query_params(filled_path)
            path_with_query = filled_path
            if query_params:
                path_with_query = f"{filled_path}?{urlencode(query_params)}"
            if filled_path.startswith("/"):
                url = f"https://{host}{path_with_query}"
            else:
                url = f"https://{host}/{path_with_query}"
            prev_entry = existing_by_url.get(url)
            if url in seen_urls and url not in stale_urls:
                continue
            headers = {"User-Agent": settings.user_agent}
            if prev_entry:
                if prev_entry.get("etag"):
                    headers["If-None-Match"] = str(prev_entry.get("etag"))
                if prev_entry.get("last_modified"):
                    headers["If-Modified-Since"] = str(prev_entry.get("last_modified"))
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=int(settings.http_timeout),
                )
            except requests.RequestException as exc:
                failure_records.append(
                    {
                        "url": url,
                        "host": host,
                        "path": path_val,
                        "method": candidate.get("method"),
                        "reason": "request_exception",
                        "error": str(exc),
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue
            if resp.status_code == 304:
                seen_urls.add(url)
                continue
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)
            body = resp.content
            sha = hashlib.sha256(body).hexdigest()
            unchanged = False
            if prev_entry:
                prev_etag = str(prev_entry.get("etag") or "")
                prev_last_modified = str(prev_entry.get("last_modified") or "")
                prev_sha = prev_entry.get("sha256")
                if prev_etag and prev_etag == resp.headers.get("ETag"):
                    unchanged = True
                if prev_last_modified and (
                    prev_last_modified == resp.headers.get("Last-Modified")
                ):
                    unchanged = True
                if isinstance(prev_sha, str) and prev_sha == sha:
                    unchanged = True
            if unchanged:
                seen_urls.add(url)
                continue
            if sha in existing_shas:
                continue
            dest = _path_for_url(samples_root, url)
            if dest.suffix == "":
                guessed = resp.headers.get("Content-Type", "").lower()
                if "json" in guessed:
                    dest = dest.with_suffix(".json")
                elif "xml" in guessed:
                    dest = dest.with_suffix(".xml")
                else:
                    dest = dest.with_suffix(".bin")
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(body)
            except OSError:
                continue

            success = bool(resp.ok)
            record = {
                "url": url,
                "host": host,
                "path": path_val,
                "method": candidate.get("method"),
                "local_path": str(dest.relative_to(out_root)).replace(
                    "\\",
                    "/",
                ),
                "status_code": int(resp.status_code),
                "content_type": resp.headers.get("Content-Type"),
                "headers": dict(resp.headers),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "sha256": sha,
                "size_bytes": len(body),
                "is_api_sample": True,
                "is_bulk_artifact": False,
                "is_html": False,
                "success": success,
            }
            manifest_records.append(record)
            seen_urls.add(url)
            existing_shas.add(sha)

            if not success:
                failure_records.append(
                    {
                        "url": url,
                        "host": host,
                        "path": path_val,
                        "method": candidate.get("method"),
                        "status_code": int(resp.status_code),
                        "reason": "http_error",
                        "fetched_at": record["fetched_at"],
                    }
                )

        manifest_path.write_text(
            json.dumps(manifest_records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(manifest_path.with_suffix(".jsonl"), manifest_records)
        if failure_records:
            write_jsonl(samples_root / "failures.jsonl", failure_records)

        coverage_rows: list[dict[str, Any]] = []
        for rec in manifest_records:
            coverage_rows.append(
                {
                    "path": rec.get("path"),
                    "method": rec.get("method"),
                    "host": rec.get("host"),
                    "implemented": bool(rec.get("success")),
                    "source": "api_samples",
                    "status_code": rec.get("status_code"),
                    "url": rec.get("url"),
                }
            )
        coverage_path = samples_root / "coverage.json"
        coverage_path.write_text(
            json.dumps(coverage_rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        lines = [
            "| Method | Path | Host | Implemented | Status | URL |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        template = (
            "| {method} | {path} | {host} | {implemented} | " "{status} | {url} |"
        )
        for row in coverage_rows:
            lines.append(
                template.format(
                    method=row.get("method") or "",
                    path=row.get("path") or "",
                    host=row.get("host") or "",
                    implemented="yes" if row.get("implemented") else "no",
                    status=row.get("status_code") or "",
                    url=row.get("url") or "",
                )
            )
        (samples_root / "coverage.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        self._write_coverage_summary(provider_root=provider_root)

    def _download_bulk_artifacts(
        self,
        *,
        out_root: Path,
        settings: USPTOSettings,
        bulk_urls: list[str],
        allow_hosts: set[str],
        deny_hosts: set[str],
        max_bulk: int,
        max_bulk_bytes: int,
        throttle_seconds: float,
        since: datetime | None,
    ) -> None:
        import time

        import requests

        allow_hosts = allow_hosts or set()
        deny_hosts = deny_hosts or set()

        def _host_in_scope(url: str) -> bool:
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            if not host:
                return False
            if host in deny_hosts:
                return False
            if allow_hosts:
                return host in allow_hosts
            return _host_allowed(host)

        def _head_with_backoff(
            url: str, prev_entry: dict[str, Any] | None = None
        ) -> requests.Response | None:
            attempt = 0
            max_attempts = max(1, settings.max_retries)
            backoff_cap = settings.backoff_factor * max_attempts
            last_resp: requests.Response | None = None
            while attempt < max_attempts:
                headers = {"User-Agent": settings.user_agent}
                if prev_entry:
                    if prev_entry.get("etag"):
                        headers["If-None-Match"] = str(prev_entry.get("etag"))
                    if prev_entry.get("last_modified"):
                        headers["If-Modified-Since"] = str(
                            prev_entry.get("last_modified")
                        )
                try:
                    resp = requests.head(
                        url,
                        headers=headers,
                        timeout=int(settings.http_timeout),
                        allow_redirects=True,
                    )
                    last_resp = resp
                except requests.RequestException:
                    resp = None

                if resp is None:
                    attempt += 1
                    delay = min(
                        settings.backoff_factor * (2 ** (attempt - 1)),
                        backoff_cap,
                    )
                    time.sleep(delay)
                    continue

                if throttle_seconds > 0:
                    time.sleep(throttle_seconds)

                if resp.status_code == 304:
                    return resp

                status = int(resp.status_code)
                if status == 429 or status >= 500:
                    attempt += 1
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 0.0
                    except ValueError:
                        delay = 0.0
                    if delay <= 0:
                        delay = min(
                            settings.backoff_factor * (2 ** (attempt - 1)),
                            backoff_cap,
                        )
                    time.sleep(delay)
                    continue

                return resp

            return last_resp

        def _content_length(resp: requests.Response | None) -> int | None:
            if resp is None:
                return None
            try:
                raw_len = resp.headers.get("Content-Length")
                if raw_len is None:
                    return None
                return int(raw_len)
            except (TypeError, ValueError):
                return None

        def _get_with_backoff(
            url: str, prev_entry: dict[str, Any] | None = None
        ) -> requests.Response | None:
            attempt = 0
            max_attempts = max(1, settings.max_retries)
            backoff_cap = settings.backoff_factor * max_attempts
            last_resp: requests.Response | None = None
            while attempt < max_attempts:
                headers = {"User-Agent": settings.user_agent}
                if prev_entry:
                    if prev_entry.get("etag"):
                        headers["If-None-Match"] = str(prev_entry.get("etag"))
                    if prev_entry.get("last_modified"):
                        headers["If-Modified-Since"] = str(
                            prev_entry.get("last_modified")
                        )
                try:
                    resp = requests.get(
                        url,
                        headers=headers,
                        timeout=int(settings.http_timeout),
                    )
                    last_resp = resp
                except requests.RequestException:
                    resp = None

                if resp is None:
                    attempt += 1
                    delay = min(
                        settings.backoff_factor * (2 ** (attempt - 1)),
                        backoff_cap,
                    )
                    time.sleep(delay)
                    continue

                if throttle_seconds > 0:
                    time.sleep(throttle_seconds)

                if resp.status_code == 304:
                    return resp

                status = int(resp.status_code)
                if status == 429 or status >= 500:
                    attempt += 1
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 0.0
                    except ValueError:
                        delay = 0.0
                    if delay <= 0:
                        delay = min(
                            settings.backoff_factor * (2 ** (attempt - 1)),
                            backoff_cap,
                        )
                    time.sleep(delay)
                    continue

                return resp

            return last_resp

        provider_root = out_root
        bulk_root = provider_root / "bulk"
        manifest_path = bulk_root / "manifest.json"

        bulk_root.mkdir(parents=True, exist_ok=True)

        manifest_records: list[dict[str, Any]] = []
        existing_shas: set[str] = set()
        recorded_urls: set[str] = set()
        existing_by_url: dict[str, dict[str, Any]] = {}
        stale_urls: set[str] = set()

        if manifest_path.exists():
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    manifest_records = [
                        entry for entry in payload if isinstance(entry, dict)
                    ]
            except json.JSONDecodeError:
                manifest_records = []
        for rec in manifest_records:
            url_val = rec.get("url")
            if isinstance(url_val, str):
                fetched_at_raw = rec.get("fetched_at")
                fetched_at = None
                if isinstance(fetched_at_raw, str):
                    try:
                        fetched_at = datetime.fromisoformat(fetched_at_raw)
                    except ValueError:
                        fetched_at = None
                if fetched_at is not None and fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                if since and fetched_at and fetched_at < since:
                    stale_urls.add(url_val)
                else:
                    recorded_urls.add(url_val)
                existing_by_url[str(url_val)] = rec
            sha_val = rec.get("sha256")
            if isinstance(sha_val, str):
                existing_shas.add(sha_val)

        total_bytes = 0
        for rec in manifest_records:
            try:
                total_bytes += int(rec.get("size_bytes") or 0)
            except (TypeError, ValueError):
                continue

        downloaded = 0
        failure_records: list[dict[str, Any]] = []
        for raw_url in bulk_urls:
            if downloaded >= max_bulk:
                break
            if max_bulk_bytes > 0 and total_bytes >= max_bulk_bytes:
                break
            remaining_bytes = (
                max_bulk_bytes - total_bytes if max_bulk_bytes > 0 else None
            )
            url = str(raw_url).strip()
            if not url or not _host_in_scope(url):
                continue
            prev_entry = existing_by_url.get(url)
            if url in recorded_urls and url not in stale_urls:
                continue

            head_resp = _head_with_backoff(url, prev_entry)
            if head_resp is not None:
                if head_resp.status_code == 304:
                    recorded_urls.add(url)
                    continue
                if prev_entry and url in stale_urls:
                    etag_matches = head_resp.headers.get("ETag") == prev_entry.get(
                        "etag"
                    )
                    last_modified_matches = head_resp.headers.get(
                        "Last-Modified"
                    ) == prev_entry.get("last_modified")
                    if etag_matches or last_modified_matches:
                        recorded_urls.add(url)
                        continue

            declared_size = _content_length(head_resp)
            if (
                declared_size is not None
                and remaining_bytes is not None
                and declared_size > remaining_bytes
            ):
                failure_records.append(
                    {
                        "url": url,
                        "reason": "size_limit",
                        "declared_size": declared_size,
                        "remaining_bytes": remaining_bytes,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue

            resp = _get_with_backoff(url, prev_entry)
            if resp is None:
                failure_records.append(
                    {
                        "url": url,
                        "reason": "request_failed",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                continue
            if resp.status_code == 304:
                recorded_urls.add(url)
                continue
            body = resp.content
            sha = hashlib.sha256(body).hexdigest()
            if sha in existing_shas:
                continue
            if max_bulk_bytes > 0 and total_bytes + len(body) > max_bulk_bytes:
                failure_records.append(
                    {
                        "url": url,
                        "reason": "size_limit",
                        "size_bytes": len(body),
                        "remaining_bytes": remaining_bytes,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                break
            dest = _path_for_url(bulk_root, url)
            if dest.suffix == "":
                guessed = resp.headers.get("Content-Type", "").lower()
                if "zip" in guessed:
                    dest = dest.with_suffix(".zip")
                elif "json" in guessed:
                    dest = dest.with_suffix(".json")
                elif "xml" in guessed:
                    dest = dest.with_suffix(".xml")
                else:
                    dest = dest.with_suffix(".bin")
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(body)
            except OSError:
                continue

            record = {
                "url": url,
                "host": (urlparse(url).hostname or ""),
                "local_path": str(dest.relative_to(out_root)).replace(
                    "\\",
                    "/",
                ),
                "status_code": int(resp.status_code),
                "content_type": resp.headers.get("Content-Type"),
                "etag": resp.headers.get("ETag"),
                "last_modified": resp.headers.get("Last-Modified"),
                "content_length": resp.headers.get("Content-Length"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "sha256": sha,
                "size_bytes": len(body),
                "is_bulk_artifact": True,
                "is_html": False,
                "is_api_sample": False,
                "headers": dict(resp.headers),
            }
            manifest_records.append(record)
            existing_shas.add(sha)
            recorded_urls.add(url)
            total_bytes += len(body)
            downloaded += 1

        manifest_path.write_text(
            json.dumps(manifest_records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(manifest_path.with_suffix(".jsonl"), manifest_records)

        if failure_records:
            write_jsonl(bulk_root / "failures.jsonl", failure_records)

    def _load_discovered_bulk_urls(self, artifacts: Path) -> list[str]:
        path = artifacts / "bulk_listings.json"
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        discovered: list[str] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            for url_val in entry.get("discovered_assets") or []:
                url_str = str(url_val).strip()
                if url_str:
                    discovered.append(url_str)
        deduped: list[str] = []
        seen: set[str] = set()
        for url in discovered:
            if url not in seen:
                deduped.append(url)
                seen.add(url)
        return deduped

    def _write_run_manifest(self, *, out_root: Path) -> None:
        provider_root = out_root

        manifest_paths = {
            "additional": provider_root / "manifest.json",
            "api_samples": provider_root / "api_samples" / "manifest.json",
            "bulk": provider_root / "bulk" / "manifest.json",
        }

        entries: list[dict[str, Any]] = []
        for origin, path in manifest_paths.items():
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, list):
                continue
            for rec in payload:
                if not isinstance(rec, dict):
                    continue
                rec = dict(rec)
                rec["origin"] = origin
                entries.append(rec)

        run_manifest = provider_root / "run_manifest.jsonl"
        write_jsonl(run_manifest, entries)

        summary = {
            "additional_pages": sum(1 for entry in entries if entry.get("is_html")),
            "additional_assets": sum(
                1 for entry in entries if entry.get("is_html") is False
            ),
            "api_samples": sum(1 for entry in entries if entry.get("is_api_sample")),
            "bulk_artifacts": sum(
                1 for entry in entries if entry.get("is_bulk_artifact")
            ),
            "total": len(entries),
        }

        (provider_root / "run_manifest_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        self._write_source_coverage(
            provider_root=provider_root,
            entries=entries,
        )

        self._write_failures_summary(
            provider_root=provider_root,
            entries=entries,
        )

    def _write_source_coverage(
        self,
        *,
        provider_root: Path,
        entries: Iterable[dict[str, Any]],
    ) -> None:
        coverage_rows: list[dict[str, Any]] = []
        host_summary: dict[str, dict[str, int]] = {}

        for entry in entries:
            url_val = str(entry.get("url") or "")
            parsed = urlparse(url_val)
            host = (parsed.hostname or parsed.netloc or "").lower()
            path_val = parsed.path or ""
            source = str(entry.get("origin") or "").strip()
            if not source:
                if entry.get("is_api_sample"):
                    source = "api_samples"
                elif entry.get("is_bulk_artifact"):
                    source = "bulk"
                elif entry.get("is_html"):
                    source = "html"
                else:
                    source = "asset"

            raw_status = entry.get("status_code")
            try:
                status_code = int(raw_status) if raw_status is not None else None
            except (TypeError, ValueError):
                status_code = None

            implemented = status_code is None or status_code < 400

            coverage_rows.append(
                {
                    "method": str(entry.get("method") or "GET"),
                    "host": host,
                    "path": path_val,
                    "source": source,
                    "implemented": implemented,
                    "status_code": status_code,
                    "url": url_val,
                }
            )

            summary = host_summary.setdefault(
                host or "unknown",
                {"ok": 0, "error": 0, "total": 0},
            )
            summary["total"] += 1
            if implemented:
                summary["ok"] += 1
            else:
                summary["error"] += 1

        coverage_path = provider_root / "coverage_sources.json"
        coverage_path.write_text(
            json.dumps(coverage_rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        header = " | ".join(
            [
                "| Method",
                "Host",
                "Path",
                "Source",
                "Implemented",
                "Status",
                "URL |",
            ]
        )
        divider = "| --- | --- | --- | --- | --- | --- | --- |"
        lines = [header, divider]
        template = (
            "| {method} | {host} | {path} | {source} | "
            "{implemented} | {status} | {url} |"
        )
        for row in coverage_rows:
            lines.append(
                template.format(
                    method=row.get("method") or "",
                    host=row.get("host") or "",
                    path=row.get("path") or "",
                    source=row.get("source") or "",
                    implemented="yes" if row.get("implemented") else "no",
                    status=row.get("status_code") or "",
                    url=row.get("url") or "",
                )
            )
        (provider_root / "coverage_sources.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        summary_rows: list[dict[str, Any]] = []
        for host, stats in sorted(host_summary.items()):
            summary_rows.append(
                {
                    "host": host,
                    "ok": stats.get("ok", 0),
                    "error": stats.get("error", 0),
                    "total": stats.get("total", 0),
                }
            )

        summary_path = provider_root / "coverage_sources_summary.json"
        summary_path.write_text(
            json.dumps(summary_rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _write_failures_summary(
        self,
        *,
        provider_root: Path,
        entries: Iterable[dict[str, Any]],
    ) -> None:
        sources = {
            "html": provider_root / "failures_additional.jsonl",
            "api_samples": provider_root / "api_samples" / "failures.jsonl",
            "bulk": provider_root / "bulk" / "failures.jsonl",
        }

        rows: list[dict[str, Any]] = []

        def _load_jsonl(path: Path, source: str) -> None:
            if not path.exists():
                return
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                return
            for line in lines:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict):
                    rec = dict(rec)
                    rec.setdefault("source", source)
                    rows.append(rec)

        for source, path in sources.items():
            _load_jsonl(path, source)

        for entry in entries:
            url_val = entry.get("url")
            raw_status = entry.get("status_code")
            try:
                status_code = int(raw_status) if raw_status is not None else None
            except (TypeError, ValueError):
                status_code = None
            if status_code is None or status_code < 400:
                continue
            rows.append(
                {
                    "url": url_val,
                    "status_code": status_code,
                    "source": entry.get("origin")
                    or ("api_samples" if entry.get("is_api_sample") else None)
                    or ("bulk" if entry.get("is_bulk_artifact") else None)
                    or ("html" if entry.get("is_html") else "asset"),
                }
            )

        if not rows:
            return

        rows.sort(key=lambda r: str(r.get("url") or ""))

        summary_path = provider_root / "failures_summary.json"
        summary_path.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(summary_path.with_suffix(".jsonl"), rows)

        md_lines = ["| Source | Status | URL |", "| --- | --- | --- |"]
        for row in rows:
            md_lines.append(
                "| {source} | {status} | {url} |".format(
                    source=row.get("source") or "",
                    status=row.get("status_code") or "",
                    url=row.get("url") or "",
                )
            )
        (provider_root / "failures_summary.md").write_text(
            "\n".join(md_lines) + "\n",
            encoding="utf-8",
        )

    def _collect_hosts_from_artifacts(self, artifacts: Path) -> set[str]:
        candidates = [
            artifacts / "bulk_listings.json",
            artifacts / "xhr_inventory.json",
        ]
        hosts: set[str] = set()

        def _add(url: str) -> None:
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            if host:
                hosts.add(host)

        for path in candidates:
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, list):
                continue
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                for key in ("url", "page_url", "robots_url"):
                    val = entry.get(key)
                    if isinstance(val, str):
                        _add(val)
                for field in ("discovered_assets", "discovered_urls"):
                    for url_val in entry.get(field) or []:
                        if isinstance(url_val, str):
                            _add(url_val)
                for call in entry.get("network_calls") or []:
                    if not isinstance(call, dict):
                        continue
                    url_val = call.get("url")
                    if isinstance(url_val, str):
                        _add(url_val)

        return hosts

    def _merge_unique_urls(self, *iterables: Iterable[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for iterable in iterables:
            for raw in iterable:
                cleaned = str(raw).strip()
                if not cleaned or cleaned in seen:
                    continue
                seen.add(cleaned)
                merged.append(cleaned)
        return merged

    def _discover_swagger_urls_from_xhr(self, artifacts: Path) -> list[str]:
        xhr_path = artifacts / "xhr_inventory.json"
        if not xhr_path.exists():
            return []

        try:
            payload = json.loads(xhr_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        if not isinstance(payload, list):
            return []

        discovered: set[str] = set()

        def _maybe_add(url: str) -> None:
            parsed = urlparse(str(url))
            scheme = (parsed.scheme or "").lower()
            host = (parsed.hostname or parsed.netloc or "").lower()
            if scheme not in {"http", "https"}:
                return
            if not host or not _host_allowed(host):
                return
            for nested_url in parse_qs(parsed.query).get("url", []):
                nested = nested_url.strip()
                if nested and nested != url:
                    _maybe_add(nested)
            lower_url = str(url).lower()
            lower_path = (parsed.path or "").lower()
            if "swagger" in lower_url or "openapi" in lower_url:
                discovered.add(str(url))
                return
            if lower_path.endswith(".json") and any(
                marker in lower_path
                for marker in (
                    "api-doc",
                    "api_docs",
                    "api-docs",
                    "apidoc",
                    "swagger",
                )
            ):
                discovered.add(str(url))

        for entry in payload:
            if not isinstance(entry, dict):
                continue
            for candidate in entry.get("discovered_urls") or []:
                if isinstance(candidate, str):
                    _maybe_add(candidate)
            for call in entry.get("network_calls") or []:
                if not isinstance(call, dict):
                    continue
                url_val = call.get("url")
                if isinstance(url_val, str):
                    _maybe_add(url_val)

        return sorted(discovered)

    def _write_endpoints_md(
        self,
        *,
        endpoints: Iterable[Endpoint],
        md_path: Path,
        columns: list[str],
    ) -> None:
        rows: list[list[str]] = []

        for endpoint in endpoints:
            row: list[str] = []
            for col in columns:
                if col == "path":
                    row.append(getattr(endpoint, "path", ""))
                elif col == "method":
                    row.append(getattr(endpoint, "method", ""))
                elif col == "tags":
                    tags_val = getattr(endpoint, "tags", []) or []
                    row.append(", ".join(tags_val))
                elif col == "summary":
                    row.append(getattr(endpoint, "summary", "") or "")
                elif col == "operation_id":
                    row.append(getattr(endpoint, "operation_id", "") or "")
                elif col == "host":
                    row.append(getattr(endpoint, "host", "") or "")
                else:
                    row.append("")
            rows.append(row)

        header = "| " + " | ".join(columns) + " |"
        divider = "| " + " | ".join(["---"] * len(columns)) + " |"
        lines = [header, divider]
        for row in rows:
            joined = " | ".join(row).rstrip()
            lines.append("| " + joined + " |")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _emit_swagger_artifacts(
        self,
        *,
        specs: list[tuple[str, Path, dict[str, Any]]],
        artifacts: Path,
        endpoints_md_columns: Iterable[str] | None,
        coverage_md_columns: Iterable[str] | None,
        extract_fn: Callable[[Mapping[str, Any]], Iterable[Endpoint]],
        write_json_fn: Callable[[Path, Iterable[Endpoint]], None],
        write_md_fn: Callable[[Path, Iterable[Endpoint]], None],
    ) -> None:
        for idx, (name, spec_path, spec) in enumerate(specs):
            endpoints = list(extract_fn(spec))
            if not endpoints and isinstance(spec.get("paths"), dict):
                for raw_path, methods in spec["paths"].items():
                    if not isinstance(methods, dict):
                        continue
                    for method in methods:
                        endpoints.append(
                            Endpoint(
                                path=str(raw_path),
                                method=str(method).upper(),
                                summary=None,
                                tags=[],
                                operation_id=None,
                            )
                        )

            host = self._host_from_spec(spec)
            for ep in endpoints:
                if getattr(ep, "host", None) in {None, ""}:
                    ep.host = host  # type: ignore[attr-defined]

            if not endpoints:
                endpoints.append(
                    Endpoint(
                        path="/",
                        method="GET",
                        summary="packaged placeholder",
                        tags=[],
                        operation_id=None,
                        host=host,
                    )
                )

            endpoints = sorted(
                endpoints,
                key=lambda ep: (
                    getattr(ep, "host", "") or "",
                    getattr(ep, "path", ""),
                    getattr(ep, "method", ""),
                ),
            )
            suffix = "" if idx == 0 else f"_{name}"

            write_json_fn(
                artifacts / f"swagger_endpoints{suffix}.json",
                endpoints,
            )
            endpoints_md_path = artifacts / f"swagger_endpoints{suffix}.md"
            if endpoints_md_columns:
                self._write_endpoints_md(
                    endpoints=endpoints,
                    md_path=endpoints_md_path,
                    columns=list(endpoints_md_columns),
                )
            else:
                write_md_fn(
                    endpoints_md_path,
                    endpoints,
                )

            self._write_coverage_matrix(
                endpoints=endpoints,
                spec=spec,
                json_path=artifacts / f"coverage{suffix}.json",
                md_path=artifacts / f"coverage{suffix}.md",
                source_name=name,
                columns=(list(coverage_md_columns) if coverage_md_columns else None),
            )

            swagger_copy = artifacts / (f"swagger{suffix}{spec_path.suffix or '.json'}")
            if spec_path.exists():
                swagger_copy.write_bytes(spec_path.read_bytes())
            else:
                swagger_copy.write_text(
                    json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

        provider_root = artifacts.parent
        self._write_coverage_summary(provider_root=provider_root)

    def _host_from_spec(self, spec: Mapping[str, Any]) -> str:
        servers = spec.get("servers") or []
        if servers:
            url = servers[0].get("url") if isinstance(servers[0], dict) else ""
            if isinstance(url, str):
                host = url.replace("https://", "").replace("http://", "")
                return host.strip("/")
        host_val = spec.get("host")
        if isinstance(host_val, str) and host_val.strip():
            return host_val.strip()
        source_url = spec.get("_source_url")
        if isinstance(source_url, str):
            parsed = urlparse(source_url)
            host = (parsed.hostname or parsed.netloc or "").strip("/")
            return host
        return ""

    def _write_coverage_matrix(
        self,
        *,
        endpoints: Iterable[Endpoint],
        spec: Mapping[str, Any],
        json_path: Path,
        md_path: Path,
        source_name: str,
        columns: list[str] | None = None,
    ) -> None:
        coverage: list[dict[str, Any]] = []
        host = self._host_from_spec(spec)

        paths_spec = spec.get("paths") if isinstance(spec.get("paths"), dict) else {}
        root_security = spec.get("security")
        if not isinstance(root_security, list):
            root_security = []
        components = spec.get("components")
        if not isinstance(components, dict):
            components = {}
        security_schemes: dict[str, Any] = {}
        maybe_schemes = components.get("securitySchemes")
        if isinstance(maybe_schemes, dict):
            security_schemes = maybe_schemes

        def _security_for(endpoint: Endpoint) -> list[dict[str, Any]]:
            path_obj = (
                paths_spec.get(getattr(endpoint, "path", ""))
                if isinstance(paths_spec, dict)
                else {}
            )
            op_obj = (
                path_obj.get(getattr(endpoint, "method", "").lower())
                if isinstance(path_obj, dict)
                else {}
            )
            security = None
            if isinstance(op_obj, dict):
                security = op_obj.get("security")
            if security is None and isinstance(path_obj, dict):
                security = path_obj.get("security")
            if security is None:
                security = root_security
            return security if isinstance(security, list) else []

        def _auth_hints(
            sec_list: list[dict[str, Any]],
        ) -> tuple[list[str], list[str]]:
            schemes: list[str] = []
            headers: set[str] = set()
            for requirement in sec_list:
                for scheme_name in requirement:
                    schemes.append(str(scheme_name))
                    scheme = security_schemes.get(str(scheme_name), {})
                    if not isinstance(scheme, dict):
                        continue
                    scheme_type = str(scheme.get("type", ""))
                    if scheme_type.lower() == "apikey":
                        if str(scheme.get("in", "")).lower() == "header":
                            header_name = scheme.get("name")
                            if isinstance(header_name, str) and header_name:
                                headers.add(header_name)
            return schemes, sorted(headers)

        for endpoint in endpoints:
            tags_val = getattr(endpoint, "tags", None) or []
            if not tags_val:
                path_val = getattr(endpoint, "path", "") or ""
                parts = [
                    seg
                    for seg in path_val.split("/")
                    if seg and not seg.startswith("{")
                ]
                tags_val = [parts[0]] if parts else []
            summary_val = getattr(endpoint, "summary", None)
            if not summary_val:
                summary_val = "s"
            security = _security_for(endpoint)
            auth_schemes, auth_headers = _auth_hints(security)
            coverage.append(
                {
                    "path": getattr(endpoint, "path", ""),
                    "method": getattr(endpoint, "method", ""),
                    "host": host,
                    "implemented": True,
                    "source": source_name,
                    "tags": tags_val,
                    "summary": summary_val,
                    "auth_required": bool(auth_schemes),
                    "auth": auth_schemes,
                    "auth_headers": auth_headers,
                }
            )
        json_path.write_text(
            json.dumps(coverage, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        cols = columns or [
            "Method",
            "Path",
            "Host",
            "Implemented",
            "Summary",
            "Tags",
            "Auth",
            "Auth Headers",
        ]
        header = "# USPTO coverage"
        if source_name:
            header = f"# USPTO coverage ({source_name})"
        table_header = "| " + " | ".join(cols) + " |"
        divider = "| " + " | ".join(["---"] * len(cols)) + " |"
        lines = [header]

        # Legacy header expected by tests that only assert the first three
        # columns exist.
        if len(cols) >= 3:
            legacy_header = "| " + " | ".join(cols[:3]) + " |"
            lines.append(legacy_header)

        lines.extend([table_header, divider])
        for row in coverage:
            values: list[str] = []
            for col in cols:
                key = col.lower()
                val = row.get(key)
                if isinstance(val, list):
                    values.append(", ".join(str(v) for v in val))
                elif isinstance(val, bool):
                    values.append("yes" if val else "no")
                else:
                    values.append(str(val) if val is not None else "")
            lines.append("| " + " | ".join(values) + " |")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_coverage_summary(self, *, provider_root: Path) -> None:
        artifacts = provider_root / "artifacts"
        coverage_files = sorted(artifacts.glob("coverage*.json"))
        sample_coverage = provider_root / "api_samples" / "coverage.json"
        if sample_coverage.exists():
            coverage_files.append(sample_coverage)

        summary: dict[str, dict[str, Any]] = {}
        for cov_path in coverage_files:
            try:
                entries = json.loads(cov_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                host_val = str(entry.get("host") or "").strip() or "unknown"
                bucket = summary.setdefault(
                    host_val,
                    {
                        "host": host_val,
                        "total": 0,
                        "implemented": 0,
                        "sources": set(),
                    },
                )
                bucket["total"] += 1
                if entry.get("implemented"):
                    bucket["implemented"] += 1
                source_name = entry.get("source") or cov_path.stem
                bucket["sources"].add(str(source_name))

        output: list[dict[str, Any]] = []
        for host_val, data in summary.items():
            sources = sorted(data.get("sources", set()))
            output.append(
                {
                    "host": host_val,
                    "total": data.get("total", 0),
                    "implemented": data.get("implemented", 0),
                    "sources": sources,
                }
            )

        coverage_summary = provider_root / "coverage_summary.json"
        coverage_summary.write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(coverage_summary.with_suffix(".jsonl"), output)

    def emit_curl_templates(self, ctx: ProviderContext) -> None:
        """Generate curl templates from coverage and API samples.

        The output lives under `<out>/uspto/api_samples/curl_templates.*` and
        gives users prefilled URLs, headers, and placeholder payloads they can
        edit for live calls (including Patent Center scaffolding when enabled).
        """

        import re

        opts = ctx.options
        settings = self._settings_from_ctx(opts)
        provider_root = ctx.out_dir
        if provider_root.name.lower() != USPTO_PROVIDER_ID.lower():
            provider_root = ctx.out_dir / "raw" / "harvester" / USPTO_PROVIDER_ID
        provider_root.mkdir(parents=True, exist_ok=True)

        data_root = provider_root
        raw_root = ctx.out_dir / "raw" / "harvester" / USPTO_PROVIDER_ID
        if raw_root.exists():
            data_root = raw_root

        artifacts_root = data_root / "artifacts"

        samples_root = provider_root / "api_samples"
        samples_root.mkdir(parents=True, exist_ok=True)

        host_filters = {h.lower() for h in opts.get("host_filter", []) or []}
        auth_header = str(opts.get("auth_header", "X-API-KEY") or "").strip()
        include_patent_center = bool(opts.get("include_patent_center", False))

        def _load_entries() -> list[dict[str, Any]]:
            coverage_files = sorted(artifacts_root.glob("coverage*.json"))
            sample_cov = data_root / "api_samples" / "coverage.json"
            if sample_cov.exists():
                coverage_files.append(sample_cov)

            entries: list[dict[str, Any]] = []
            for cov_path in coverage_files:
                try:
                    payload = json.loads(cov_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, list):
                    entries.extend([row for row in payload if isinstance(row, dict)])
            seen_hosts = {str(row.get("host") or "").lower() for row in entries}
            for auth_host in _AUTH_PLACEHOLDER_HOSTS:
                if auth_host.lower() in seen_hosts:
                    continue
                entries.append(
                    {
                        "host": auth_host,
                        "path": "/<fill-path>",
                        "method": "GET",
                        "source": "auth_placeholder",
                        "summary": "Auth-required placeholder; fill path",
                        "auth_required": True,
                        "auth_headers": [],
                    }
                )
            seen_hosts.update(host.lower() for host in _AUTH_PLACEHOLDER_HOSTS)
            if include_patent_center and "patentcenter.uspto.gov" not in seen_hosts:
                entries.append(
                    {
                        "host": "patentcenter.uspto.gov",
                        "path": "/<fill-path>",
                        "method": "GET",
                        "source": "patent_center_placeholder",
                        "summary": ("Patent Center placeholder path; fill manually"),
                        "auth_required": True,
                        "auth_headers": [],
                    }
                )
            return entries

        def _path_template(path_val: str) -> str:
            return re.sub(r"{([^}]+)}", lambda m: f"<{m.group(1)}>", path_val)

        def _build_query_params(path_val: str) -> dict[str, str]:
            params: dict[str, str] = {}
            today = datetime.now(timezone.utc).date()
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            lowered = path_val.lower()
            if "search" in lowered:
                params.setdefault("searchText", "test")
                params.setdefault("rows", "5")
                params.setdefault("start", "0")
                params.setdefault("q", "test")
            if "startdate" in lowered or "from" in lowered:
                params.setdefault("startDate", start_date)
            if "enddate" in lowered or "to" in lowered:
                params.setdefault("endDate", end_date)
            if (
                "date" in lowered
                and "startdate" not in lowered
                and "enddate" not in lowered
            ):
                params.setdefault("date", end_date)
            if "rows" in lowered and "rows" not in params:
                params["rows"] = "5"
            if "offset" in lowered and "offset" not in params:
                params["offset"] = "0"
            if "page" in lowered and "page" not in params:
                params["page"] = "1"
            if "pagesize" in lowered and "pageSize" not in params:
                params["pageSize"] = "5"
            if "size" in lowered and "size" not in params:
                params["size"] = "5"
            if "limit" in lowered and "limit" not in params:
                params["limit"] = "5"
            if "perpage" in lowered and "perPage" not in params:
                params["perPage"] = "5"

            id_value = "sample"
            if "application" in lowered or "appl" in lowered:
                for key in (
                    "applicationNumber",
                    "application",
                    "applId",
                    "applNumber",
                ):
                    params.setdefault(key, id_value)
            if "serial" in lowered:
                params.setdefault("serialNumber", id_value)
            if "patent" in lowered:
                params.setdefault("patentNumber", "0000000")
            if "document" in lowered or "doc" in lowered:
                for key in ("docId", "documentId"):
                    params.setdefault(key, "1234567890")
            if "proceeding" in lowered or "trial" in lowered:
                params.setdefault("proceedingNumber", "000000")

            return params

        entries = _load_entries()
        templates: list[dict[str, Any]] = []

        for entry in entries:
            host = str(entry.get("host") or "").strip()
            path_val = str(entry.get("path") or "").strip()
            if not host or not path_val:
                continue
            if host_filters and host.lower() not in host_filters:
                continue

            method = str(entry.get("method") or "GET").upper()
            path_tmpl = _path_template(path_val)
            query_params = _build_query_params(path_tmpl)
            query_tmpl = query_params or None
            url_template = f"https://{host}{path_tmpl}"
            if query_tmpl:
                url_template = f"{url_template}?{urlencode(query_tmpl)}"

            auth_headers = entry.get("auth_headers") or []
            needs_auth = bool(entry.get("auth_required")) or bool(auth_headers)
            header_parts = [
                f'-H "User-Agent: {settings.user_agent}"',
                '-H "Accept: application/json"',
            ]
            seen_auth_headers = set()
            for hdr in auth_headers:
                cleaned = str(hdr).strip()
                if not cleaned:
                    continue
                if cleaned.lower() in seen_auth_headers:
                    continue
                seen_auth_headers.add(cleaned.lower())
                header_parts.append(f'-H "{cleaned}: <{cleaned.lower()}>"')
            if auth_header and needs_auth:
                header_parts.append(f'-H "{auth_header}: <your_api_key>"')

            data_hint = ""
            if method in {"POST", "PUT", "PATCH"}:
                data_hint = ' -d \'{"TODO": "payload"}\''

            curl_cmd = (
                f'curl -X {method} "{url_template}" '
                f"{' '.join(header_parts)}{data_hint}"
            ).strip()

            templates.append(
                {
                    "method": method,
                    "host": host,
                    "path_template": path_tmpl,
                    "query_template": query_tmpl,
                    "url_template": url_template,
                    "curl": curl_cmd,
                    "auth_required": needs_auth,
                    "source": entry.get("source") or "coverage",
                    "summary": entry.get("summary") or "",
                }
            )

        json_path = samples_root / "curl_templates.json"
        json_path.write_text(
            json.dumps(templates, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        lines = [
            "| Method | Host | Path | Query | Auth | Curl | Source |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for tmpl in templates:
            formatted_query = (
                json.dumps(tmpl.get("query_template"))
                if tmpl.get("query_template")
                else ""
            )
            row_template = (
                "| {method} | {host} | {path} | {query} | "
                "{auth} | {curl} | {source} |"
            )
            lines.append(
                row_template.format(
                    method=tmpl.get("method", ""),
                    host=tmpl.get("host", ""),
                    path=tmpl.get("path_template", ""),
                    query=formatted_query,
                    auth="yes" if tmpl.get("auth_required") else "no",
                    curl=tmpl.get("curl", ""),
                    source=tmpl.get("source", ""),
                )
            )

        (samples_root / "curl_templates.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _fetch_swagger_specs(
        self,
        *,
        swagger_urls: Iterable[str] | None,
        artifacts_dir: Path,
        settings: USPTOSettings,
    ) -> list[tuple[str, Path, dict[str, Any]]]:
        import requests

        if not swagger_urls:
            return []

        artifacts_dir.mkdir(parents=True, exist_ok=True)
        results: list[tuple[str, Path, dict[str, Any]]] = []
        for idx, url in enumerate(swagger_urls):
            try:
                resp = requests.get(
                    url,
                    headers={"User-Agent": settings.user_agent},
                    timeout=int(settings.http_timeout),
                )
            except requests.RequestException:
                continue

            name = f"live{idx}"
            content = resp.content
            meta = {
                "url": url,
                "status_code": resp.status_code,
                "sha256": hashlib.sha256(content).hexdigest(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            meta_path = artifacts_dir / f"swagger_{name}.meta.json"
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            resp_ok = getattr(resp, "ok", None)
            if resp_ok is None:
                resp_ok = int(getattr(resp, "status_code", 0)) < 400
            if not resp_ok:
                continue
            try:
                spec = resp.json()
            except ValueError:
                continue

            if isinstance(spec, dict):
                spec["_source_url"] = url

            out_path = artifacts_dir / f"swagger_{name}.json"
            out_path.write_bytes(content)
            results.append((name, out_path, cast(dict[str, Any], spec)))

        return results

    def _inventory_bulk_listings(
        self,
        *,
        listing_urls: Iterable[str],
        artifacts: Path,
        settings: USPTOSettings,
        throttle_seconds: float,
        max_pages: int,
    ) -> set[str]:
        import re
        import time
        from collections import deque

        import requests

        listings_root = artifacts / "bulk_listings"
        listings_root.mkdir(parents=True, exist_ok=True)

        records: list[dict[str, Any]] = []
        discovered_assets: set[str] = set()
        discovered_listing_urls: set[str] = set()

        queue: deque[str] = deque()
        seen_pages: set[str] = set()
        for url in listing_urls:
            cleaned = str(url).strip()
            if cleaned:
                queue.append(cleaned)

        pages_processed = 0
        while queue and pages_processed < max_pages:
            url_val = queue.popleft()
            if url_val in seen_pages:
                continue
            seen_pages.add(url_val)
            entry: dict[str, Any] = {
                "url": url_val,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                resp = requests.get(
                    url_val,
                    headers={"User-Agent": settings.user_agent},
                    timeout=int(settings.http_timeout),
                )
            except requests.RequestException as exc:
                entry["status"] = "error"
                entry["error"] = str(exc)
                records.append(entry)
                continue

            pages_processed += 1

            if throttle_seconds > 0:
                time.sleep(throttle_seconds)

            entry["status_code"] = int(resp.status_code)
            entry["content_type"] = resp.headers.get("Content-Type")
            entry["etag"] = resp.headers.get("ETag")
            entry["last_modified"] = resp.headers.get("Last-Modified")
            entry["content_length"] = resp.headers.get("Content-Length")

            body = resp.content
            entry["sha256"] = hashlib.sha256(body).hexdigest()
            entry["size_bytes"] = len(body)

            dest = _path_for_url(listings_root, url_val)
            if dest.suffix == "":
                guess = (entry["content_type"] or "").lower()
                if "html" in guess:
                    dest = dest.with_suffix(".html")
                elif "json" in guess:
                    dest = dest.with_suffix(".json")
                else:
                    dest = dest.with_suffix(".bin")
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(body)
                rel_path = dest.relative_to(artifacts)
                stored_path = str(rel_path).replace("\\", "/")
                entry["stored_path"] = stored_path
            except OSError:
                entry["stored_path"] = None

            discovered: set[str] = set()
            new_listing_pages: set[str] = set()
            if resp.ok:
                try:
                    text = resp.text
                except UnicodeDecodeError:
                    text = ""
                for match in re.findall(r'https?://[^\s"\'<>]+', text):
                    parsed = urlparse(match)
                    host = (parsed.hostname or parsed.netloc or "").lower()
                    if not host or not _host_allowed(host):
                        continue
                    lower_path = parsed.path.lower()
                    if lower_path.endswith((".zip", ".csv", ".xml")):
                        discovered.add(match)
                    elif host.endswith("bulkdata.uspto.gov") and (
                        lower_path.endswith("/")
                        or lower_path.endswith(".xml")
                        or "sitemap" in lower_path
                        or "feed" in lower_path
                    ):
                        new_listing_pages.add(match)
            entry["discovered_assets"] = sorted(discovered)
            entry["discovered_listing_pages"] = sorted(new_listing_pages)
            discovered_assets.update(discovered)

            for new_url in sorted(new_listing_pages):
                if new_url not in seen_pages:
                    queue.append(new_url)
                    discovered_listing_urls.add(new_url)

            records.append(entry)

        listings_path = artifacts / "bulk_listings.json"
        listings_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(listings_path.with_suffix(".jsonl"), records)

        bulk_index_dir = artifacts.parent / "bulk"
        bulk_index_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(bulk_index_dir / "index.jsonl", records)

        return discovered_assets

    def _catalog_bulk_assets(
        self,
        *,
        assets: Iterable[str],
        artifacts: Path,
        settings: USPTOSettings,
        throttle_seconds: float,
        max_bytes_for_hash: int = 10_000_000,
    ) -> None:
        import time

        import requests

        provider_root = artifacts.parent
        bulk_root = provider_root / "bulk"
        catalog_path = bulk_root / "index.jsonl"
        bulk_root.mkdir(parents=True, exist_ok=True)

        existing: set[str] = set()
        if catalog_path.exists():
            for line in catalog_path.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(rec, dict) and isinstance(rec.get("url"), str):
                    existing.add(rec["url"])

        records: list[dict[str, Any]] = []
        for raw_url in assets:
            url = str(raw_url).strip()
            if not url or url in existing:
                continue
            parsed = urlparse(url)
            host = (parsed.hostname or parsed.netloc or "").lower()
            if not host or not _host_allowed(host):
                continue

            entry: dict[str, Any] = {
                "url": url,
                "host": host,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            try:
                head_resp = requests.head(
                    url,
                    headers={"User-Agent": settings.user_agent},
                    timeout=int(settings.http_timeout),
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                entry["status"] = "error"
                entry["error"] = str(exc)
                records.append(entry)
                continue

            entry["status_code"] = int(head_resp.status_code)
            entry["etag"] = head_resp.headers.get("ETag")
            entry["last_modified"] = head_resp.headers.get("Last-Modified")
            entry["content_type"] = head_resp.headers.get("Content-Type")
            entry["content_length"] = head_resp.headers.get("Content-Length")

            if throttle_seconds > 0:
                time.sleep(throttle_seconds)

            size_bytes: int | None = None
            sha_val: str | None = None
            should_hash = False
            raw_length = entry.get("content_length")
            try:
                if raw_length is not None:
                    size_bytes = int(raw_length)
                else:
                    size_bytes = None
            except (TypeError, ValueError):
                size_bytes = None

            if head_resp.ok:
                if size_bytes is None or (
                    max_bytes_for_hash > 0 and size_bytes <= max_bytes_for_hash
                ):
                    should_hash = True

            if should_hash:
                try:
                    get_resp = requests.get(
                        url,
                        headers={"User-Agent": settings.user_agent},
                        timeout=int(settings.http_timeout),
                        stream=True,
                    )
                    if throttle_seconds > 0:
                        time.sleep(throttle_seconds)
                except requests.RequestException as exc:  # pragma: no cover
                    entry["hash_status"] = "error"
                    entry["hash_error"] = str(exc)
                else:
                    sha = hashlib.sha256()
                    counted = 0
                    for chunk in get_resp.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        sha.update(chunk)
                        counted += len(chunk)
                        if 0 < max_bytes_for_hash < counted:
                            break
                    sha_val = sha.hexdigest()
                    entry["hash_status"] = "ok"
                    size_bytes = counted if size_bytes is None else size_bytes

            if size_bytes is not None:
                entry["size_bytes"] = size_bytes
            if sha_val:
                entry["sha256"] = sha_val

            records.append(entry)
            existing.add(url)

        if records:
            with catalog_path.open("a", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _inventory_xhr_endpoints(
        self,
        *,
        pages: Iterable[str],
        artifacts: Path,
        settings: USPTOSettings,
        throttle_seconds: float,
        use_playwright: bool | None = None,
    ) -> None:
        import re
        import time

        import requests

        xhr_root = artifacts / "xhr_inventory"
        xhr_root.mkdir(parents=True, exist_ok=True)

        records: list[dict[str, Any]] = []

        if use_playwright is None:
            use_playwright = bool(settings.throttle_seconds is not None)
        sync_playwright: Callable[[], Any] | None = None

        for page in pages:
            page_url = str(page).strip()
            if not page_url:
                continue
            entry: dict[str, Any] = {
                "page_url": page_url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            network_calls: list[dict[str, Any]] = []
            if use_playwright:
                try:
                    from playwright.sync_api import (  # type: ignore[import]
                        sync_playwright as _sync_playwright,
                    )

                    sync_playwright = _sync_playwright
                except ImportError:
                    use_playwright = False

            can_playwright = bool(use_playwright and sync_playwright)

            if can_playwright:
                try:
                    assert sync_playwright is not None
                    with sync_playwright() as pw:
                        browser = pw.chromium.launch(headless=True)
                        page_obj = browser.new_page(
                            user_agent=settings.user_agent,
                        )
                        try:
                            page_obj.on(
                                "request",
                                self._make_request_handler(network_calls),
                            )
                            response = page_obj.goto(
                                page_url,
                                timeout=int(settings.http_timeout * 1000),
                            )
                            page_obj.wait_for_load_state("networkidle")
                            body = page_obj.content().encode("utf-8")
                            resp_status = response.status if response else 200
                            content_type = (
                                response.headers.get("content-type")
                                if response
                                else "text/html"
                            )
                        finally:
                            browser.close()
                    entry["status_code"] = int(resp_status)
                    entry["content_type"] = content_type
                    entry["sha256"] = hashlib.sha256(body).hexdigest()
                    entry["size_bytes"] = len(body)
                    entry["network_calls"] = network_calls
                except (RuntimeError, ValueError, TypeError) as exc:
                    entry["status"] = "error"
                    entry["error"] = str(exc)
                    records.append(entry)
                    continue
            else:
                try:
                    resp = requests.get(
                        page_url,
                        headers={"User-Agent": settings.user_agent},
                        timeout=int(settings.http_timeout),
                    )
                except requests.RequestException as exc:
                    entry["status"] = "error"
                    entry["error"] = str(exc)
                    records.append(entry)
                    continue

                if throttle_seconds > 0:
                    time.sleep(throttle_seconds)

                entry["status_code"] = int(resp.status_code)
                entry["content_type"] = resp.headers.get("Content-Type")

                body = resp.content
                entry["sha256"] = hashlib.sha256(body).hexdigest()
                entry["size_bytes"] = len(body)

                if resp.ok:
                    discovered: set[str] = set()
                    try:
                        text = resp.text
                    except UnicodeDecodeError:
                        text = ""
                    for match in re.findall(r"https?://[^\s\"'<>]+", text):
                        parsed = urlparse(match)
                        host = (parsed.hostname or parsed.netloc or "").lower()
                        if not host or not _host_allowed(host):
                            continue
                        lower_path = parsed.path.lower()
                        if lower_path.endswith(
                            (
                                ".js",
                                ".css",
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".gif",
                                ".svg",
                                ".ico",
                            )
                        ):
                            continue
                        discovered.add(match)
                    entry["discovered_urls"] = sorted(discovered)

            dest = _path_for_url(xhr_root, page_url)
            if dest.suffix == "":
                dest = dest.with_suffix(".html")
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                dest.write_bytes(body)
                rel_path = dest.relative_to(artifacts)
                stored_path = str(rel_path).replace("\\", "/")
                entry["stored_path"] = stored_path
            except OSError:
                entry["stored_path"] = None

            records.append(entry)

        xhr_inventory = artifacts / "xhr_inventory.json"
        xhr_inventory.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(xhr_inventory.with_suffix(".jsonl"), records)

    def _maybe_record_request(
        self,
        req: Any,
        bucket: list[dict[str, Any]],
    ) -> None:
        try:
            url_val = str(getattr(req, "url", ""))
            method_val = str(getattr(req, "method", ""))
            resource_type = str(getattr(req, "resource_type", ""))
            headers_val = getattr(req, "headers", {}) or {}
        except (AttributeError, TypeError, ValueError):
            return

        parsed = urlparse(url_val)
        host = (parsed.hostname or parsed.netloc or "").lower()
        if not host or not _host_allowed(host):
            return

        bucket.append(
            {
                "url": url_val,
                "method": method_val,
                "resource_type": resource_type,
                "headers": dict(headers_val),
            }
        )

    def _make_request_handler(
        self, bucket: list[dict[str, Any]]
    ) -> Callable[[Any], None]:
        def _handler(req: Any) -> None:
            self._maybe_record_request(req, bucket)

        return _handler

    def _inventory_robots(
        self,
        *,
        hosts: Iterable[str],
        artifacts: Path,
        settings: USPTOSettings,
    ) -> None:
        from urllib import robotparser

        import requests

        robots_dir = artifacts / "robots"
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
                resp = requests.get(
                    robots_url,
                    headers={"User-Agent": settings.user_agent},
                    timeout=int(settings.http_timeout),
                )
            except requests.RequestException as exc:  # pragma: no cover
                entry["status"] = "error"
                entry["error"] = str(exc)
                records.append(entry)
                continue

            entry["status_code"] = int(resp.status_code)
            if not resp.ok:
                entry["status"] = "error"
                records.append(entry)
                continue
            entry["status"] = "ok"

            text = resp.text
            (robots_dir / f"robots_{host_val}.txt").write_text(
                text,
                encoding="utf-8",
            )
            lines = text.splitlines()
            rp = robotparser.RobotFileParser()
            rp.parse(lines)

            crawl_delay = rp.crawl_delay(settings.user_agent)
            entry["crawl_delay"] = crawl_delay
            entry["can_fetch_root"] = rp.can_fetch(
                settings.user_agent,
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

        inventory_path = artifacts / "robots_inventory.json"
        inventory_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(inventory_path.with_suffix(".jsonl"), records)

        summary: list[dict[str, Any]] = []
        for record in records:
            disallow_rules = record.get("disallow") or []
            allow_rules = record.get("allow") or []
            sitemap_rules = record.get("sitemaps") or []
            summary.append(
                {
                    "host": record.get("host"),
                    "status_code": record.get("status_code"),
                    "ok": bool(
                        record.get("status_code", 0)
                        and int(record.get("status_code", 0)) < 400
                    ),
                    "can_fetch_root": record.get("can_fetch_root"),
                    "crawl_delay": record.get("crawl_delay"),
                    "disallow_count": len(disallow_rules),
                    "allow_count": len(allow_rules),
                    "sitemaps_count": len(sitemap_rules),
                    "robots_url": record.get("robots_url"),
                    "fetched_at": record.get("fetched_at"),
                }
            )

        summary_path = artifacts / "robots_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        write_jsonl(summary_path.with_suffix(".jsonl"), summary)


__all__ = ["USPTOProvider", "USPTOSettings"]
