from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import typer

from reference_harvester.citations import (
    CitationRecord,
    write_bibtex,
    write_ris,
)
from reference_harvester.endnote_xml import write_reference_type_table
from reference_harvester.models import JobRequest
from reference_harvester.providers.base import ProviderContext
from reference_harvester.providers.registry import (
    ProviderEntry,
    register_default_providers,
    registry,
)
from reference_harvester.registry import load_registry

app = typer.Typer(
    help="Spec-driven, multi-provider harvesting and reference export",
)


def _ctx(
    provider: str,
    out_root: Path,
    *,
    run_id: str | None = None,
    **options: Any,
) -> ProviderContext:
    # Normalize to an absolute provider-scoped output dir to avoid accidental
    # path duplication when the CLI is invoked from a nested working directory
    # (e.g., running inside an existing out_root). Avoid double-appending the
    # provider segment if the caller already supplied it.
    base = out_root
    if base.name.lower() != provider.lower():
        base = base / provider
    if run_id:
        base = base / "runs" / run_id
    ctx = ProviderContext(name=provider, out_dir=base.resolve())
    opts: Any = getattr(ctx, "options", None)
    if isinstance(opts, dict):
        if run_id:
            opts.setdefault("run_id", run_id)
        opts.update(options)
    return ctx


def build_ctx(
    provider: str,
    out_root: Path,
    *,
    run_id: str | None = None,
    **options: Any,
) -> ProviderContext:
    """Public wrapper for building ProviderContext used by the CLI."""

    return _ctx(provider, out_root, run_id=run_id, **options)


def _ensure_providers(names: Iterable[str]) -> list[ProviderEntry]:
    register_default_providers()
    entries: list[ProviderEntry] = []
    for name in names:
        entries.append(registry.entry(name))
    return entries


def _emit_citations(
    out_dir: Path,
    provider: str,
    records: list[dict[str, Any]],
    emit_ris: bool,
    emit_bibtex_flag: bool,
) -> None:
    citations: list[CitationRecord] = []
    for rec in records:
        ident = str(rec.get("id") or rec.get("identifier") or rec.get("url", ""))
        citations.append(
            CitationRecord(provider=provider, identifier=ident, canonical=rec)
        )

    if emit_ris:
        write_ris(out_dir / "citations" / f"{provider}.ris", citations)
    if emit_bibtex_flag:
        write_bibtex(out_dir / "citations" / f"{provider}.bib", citations)


@app.command()
def inventory(
    provider: str = typer.Argument(..., help="Provider slug (e.g., uspto)"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    run_id: str | None = typer.Option(
        None,
        help="Optional run id (writes under out/<provider>/runs/<run-id>/)",
    ),
    swagger_url: list[str] = typer.Option(
        None,
        help="Override swagger/OpenAPI URLs (can be passed multiple times)",
    ),
) -> None:
    """Inspect or refresh inventories/spec bundles for a provider."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.refresh_inventory(
        build_ctx(
            provider,
            out_root,
            run_id=run_id,
            swagger_urls=swagger_url or None,
        )
    )


@app.command()
def harvest(
    provider: str = typer.Argument(..., help="Provider slug (e.g., uspto)"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    run_id: str | None = typer.Option(
        None,
        help="Optional run id (writes under out/<provider>/runs/<run-id>/)",
    ),
    email: str | None = typer.Option(
        None,
        help=("Contact email for polite requests " "(e.g., OpenAlex mailto/from)"),
    ),
    max_pages: int = typer.Option(200, help="Max pages to mirror"),
    include_assets: bool = typer.Option(
        True,
        help="Mirror same-origin assets",
    ),
    max_assets: int = typer.Option(2000, help="Max assets to fetch"),
    user_agent: str = typer.Option(
        "reference-harvester/0.1",
        help="User-Agent for HTTP requests",
    ),
    seed: list[str] = typer.Option(None, help="Extra seed URLs (multi)"),
) -> None:
    """Mirror docs/specs/assets/downloadables for a provider."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.mirror_sources(
        build_ctx(
            provider,
            out_root,
            run_id=run_id,
            email=email,
            max_pages=max_pages,
            include_assets=include_assets,
            max_assets=max_assets,
            user_agent=user_agent,
            extra_seeds=seed or None,
        )
    )


@app.command()
def fetch(
    provider: str = typer.Argument(..., help="Provider slug"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    run_id: str | None = typer.Option(
        None,
        help="Optional run id (writes under out/<provider>/runs/<run-id>/)",
    ),
    query: str | None = typer.Option(
        None,
        help=("Provider query/search string " "(e.g., OpenAlex works search query)"),
    ),
    per_page: int | None = typer.Option(
        None,
        help=("Provider page size (e.g., OpenAlex per-page for works search)"),
    ),
    email: str | None = typer.Option(
        None,
        help=("Contact email for polite requests " "(e.g., OpenAlex mailto/from)"),
    ),
    max_pages: int = typer.Option(200, help="Max pages to mirror"),
    include_assets: bool = typer.Option(
        True,
        help="Mirror same-origin assets",
    ),
    max_assets: int = typer.Option(2000, help="Max assets to fetch"),
    max_depth: int = typer.Option(4, help="Max crawl depth from seeds"),
    max_files: int = typer.Option(200, help="Max files to download"),
    user_agent: str = typer.Option(
        "reference-harvester/0.1",
        help="User-Agent for HTTP requests",
    ),
    api_key: str | None = typer.Option(
        None, help="API key for authenticated endpoints"
    ),
    api_key_env: str = typer.Option(
        "USPTO_ODP_API", help="Env var name for API key fallback"
    ),
    browser_fallback: bool = typer.Option(
        False, help="Enable browser-based download fallback"
    ),
    browser_timeout_ms: int = typer.Option(
        60_000, help="Browser fallback timeout (ms)"
    ),
    convert_html_to_md: bool = typer.Option(
        True, help="Convert HTML pages to Markdown"
    ),
    emit_ris: bool = typer.Option(True, help="Emit RIS citations"),
    emit_csl_json: bool = typer.Option(False, help="Emit CSL-JSON citations"),
    emit_bibtex: bool = typer.Option(False, help="Emit BibTeX citations"),
    max_attachments: int = typer.Option(200, help="Max attachment downloads"),
    seed: list[str] = typer.Option(None, help="Extra seed URLs (multi)"),
    allow_host: list[str] = typer.Option(
        None,
        help="Allow-listed hosts (multi)",
    ),
    deny_host: list[str] = typer.Option(
        None,
        help="Deny-listed hosts (multi)",
    ),
    allow_bulk: list[str] = typer.Option(
        None,
        help="Allow-listed bulk hosts",
    ),
    deny_bulk: list[str] = typer.Option(
        None,
        help="Deny-listed bulk hosts",
    ),
    bulk_url: list[str] = typer.Option(
        None,
        help="Bulk download URLs (multi)",
    ),
    max_bulk: int = typer.Option(50, help="Max bulk downloads"),
    max_bulk_bytes: int = typer.Option(
        10_000_000_000,
        help="Total bulk bytes cap per run",
    ),
    api_sample_limit: int = typer.Option(25, help="Max API samples"),
    throttle_seconds: float = typer.Option(
        0.0,
        help="Delay between HTTP calls",
    ),
    swagger_url: list[str] = typer.Option(
        None,
        help="Override swagger/OpenAPI URLs (can be passed multiple times)",
    ),
    validate_schema: bool = typer.Option(
        False,
        help=(
            "Validate downloaded API sample JSON files against a JSON schema "
            "and emit a report under logs/reports/"
        ),
    ),
    schema_path: Path = typer.Option(
        Path("docs")
        / "inputs"
        / "odp"
        / "2026-01-14"
        / "pfw-schemas"
        / "patent-data-schema.json",
        help="Path to a JSON Schema (draft-04 supported subset)",
    ),
) -> None:
    """Plan and download references/metadata for a provider."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.fetch_references(
        build_ctx(
            provider,
            out_root,
            run_id=run_id,
            query=query,
            per_page=per_page,
            email=email,
            max_pages=max_pages,
            include_assets=include_assets,
            max_assets=max_assets,
            max_depth=max_depth,
            max_files=max_files,
            user_agent=user_agent,
            api_key=api_key,
            api_key_env=api_key_env,
            browser_fallback=browser_fallback,
            browser_timeout_ms=browser_timeout_ms,
            convert_html_to_md=convert_html_to_md,
            emit_ris=emit_ris,
            emit_csl_json=emit_csl_json,
            emit_bibtex=emit_bibtex,
            max_attachments=max_attachments,
            extra_seeds=seed or None,
            allow_host=allow_host or None,
            deny_host=deny_host or None,
            allow_bulk=allow_bulk or None,
            deny_bulk=deny_bulk or None,
            bulk_urls=bulk_url or None,
            max_bulk=max_bulk,
            max_bulk_bytes=max_bulk_bytes,
            api_sample_limit=api_sample_limit,
            throttle_seconds=throttle_seconds,
            swagger_urls=swagger_url or None,
            validate_schema=validate_schema,
            schema_path=str(schema_path),
        )
    )


@app.command("run")
def run_job(
    provider: list[str] = typer.Option(
        ["uspto"],
        "--provider",
        "-p",
        help="Provider(s) to run",
    ),
    mode: str = typer.Option(
        "fetch",
        help="Mode: inventory | harvest | fetch | endnote",
    ),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    run_id: str | None = typer.Option(
        None,
        help=(
            "Optional run id (writes under out/<provider>/runs/<run-id>/); "
            "applies to all providers in this run"
        ),
    ),
    query: str | None = typer.Option(
        None,
        help=("Provider query/search string " "(e.g., OpenAlex works search query)"),
    ),
    per_page: int | None = typer.Option(
        None,
        help=("Provider page size (e.g., OpenAlex per-page for works search)"),
    ),
    email: str | None = typer.Option(
        None,
        help=("Contact email for polite requests " "(e.g., OpenAlex mailto/from)"),
    ),
    max_pages: int = typer.Option(200, help="Max pages to mirror"),
    include_assets: bool = typer.Option(
        True,
        help="Mirror same-origin assets",
    ),
    max_assets: int = typer.Option(2000, help="Max assets to fetch"),
    max_depth: int = typer.Option(4, help="Max crawl depth from seeds"),
    max_files: int = typer.Option(200, help="Max files to download"),
    user_agent: str = typer.Option(
        "reference-harvester/0.1",
        help="User-Agent for HTTP requests",
    ),
    api_key: str | None = typer.Option(
        None, help="API key for authenticated endpoints"
    ),
    api_key_env: str = typer.Option(
        "USPTO_ODP_API", help="Env var name for API key fallback"
    ),
    browser_fallback: bool = typer.Option(
        False, help="Enable browser-based download fallback"
    ),
    browser_timeout_ms: int = typer.Option(
        60_000, help="Browser fallback timeout (ms)"
    ),
    convert_html_to_md: bool = typer.Option(
        True, help="Convert HTML pages to Markdown"
    ),
    emit_ris: bool = typer.Option(True, help="Emit RIS citations"),
    emit_csl_json: bool = typer.Option(False, help="Emit CSL-JSON citations"),
    emit_bibtex: bool = typer.Option(False, help="Emit BibTeX citations"),
    max_attachments: int = typer.Option(200, help="Max attachment downloads"),
    seed: list[str] = typer.Option(None, help="Extra seed URLs (multi)"),
    allow_host: list[str] = typer.Option(
        None,
        help="Allow-listed hosts (multi)",
    ),
    deny_host: list[str] = typer.Option(
        None,
        help="Deny-listed hosts (multi)",
    ),
    allow_bulk: list[str] = typer.Option(None, help="Allow-listed bulk hosts"),
    deny_bulk: list[str] = typer.Option(None, help="Deny-listed bulk hosts"),
    bulk_url: list[str] = typer.Option(
        None,
        help="Bulk download URLs (multi)",
    ),
    max_bulk: int = typer.Option(50, help="Max bulk downloads"),
    max_bulk_bytes: int = typer.Option(
        10_000_000_000, help="Total bulk bytes cap per run"
    ),
    api_sample_limit: int = typer.Option(25, help="Max API samples"),
    throttle_seconds: float = typer.Option(
        0.0,
        help="Delay between HTTP calls",
    ),
    swagger_url: list[str] = typer.Option(
        None,
        help="Override swagger/OpenAPI URLs (can be passed multiple times)",
    ),
    validate_schema: bool = typer.Option(
        False,
        help=(
            "Validate downloaded API sample JSON files against a JSON schema "
            "and emit a report under logs/reports/"
        ),
    ),
    schema_path: Path = typer.Option(
        Path("docs")
        / "inputs"
        / "odp"
        / "2026-01-14"
        / "pfw-schemas"
        / "patent-data-schema.json",
        help="Path to a JSON Schema (draft-04 supported subset)",
    ),
) -> None:
    """Run one or more providers with shared options."""

    entries = _ensure_providers(provider)
    job = JobRequest(
        providers=provider,
        mode=mode,
        out_root=out_root,
        options={
            "query": query,
            "per_page": per_page,
            "email": email,
            "max_pages": max_pages,
            "include_assets": include_assets,
            "max_assets": max_assets,
            "max_depth": max_depth,
            "max_files": max_files,
            "user_agent": user_agent,
            "api_key": api_key,
            "api_key_env": api_key_env,
            "browser_fallback": browser_fallback,
            "browser_timeout_ms": browser_timeout_ms,
            "convert_html_to_md": convert_html_to_md,
            "emit_ris": emit_ris,
            "emit_csl_json": emit_csl_json,
            "emit_bibtex": emit_bibtex,
            "max_attachments": max_attachments,
            "extra_seeds": seed or None,
            "allow_host": allow_host or None,
            "deny_host": deny_host or None,
            "allow_bulk": allow_bulk or None,
            "deny_bulk": deny_bulk or None,
            "bulk_urls": bulk_url or None,
            "max_bulk": max_bulk,
            "max_bulk_bytes": max_bulk_bytes,
            "api_sample_limit": api_sample_limit,
            "throttle_seconds": throttle_seconds,
            "swagger_urls": swagger_url or None,
            "validate_schema": validate_schema,
            "schema_path": str(schema_path),
        },
    )

    for entry in entries:
        ctx = build_ctx(
            entry.info.name,
            out_root,
            run_id=run_id,
            **job.options,
        )
        plugin = entry.plugin
        if mode == "inventory":
            plugin.refresh_inventory(ctx)
        elif mode in {"harvest", "mirror"}:
            plugin.mirror_sources(ctx)
        elif mode in {"fetch", "reference-docs"}:
            plugin.fetch_references(ctx)
        elif mode == "endnote":
            plugin.export_endnote(ctx)
        else:
            raise typer.BadParameter(f"Unsupported mode: {mode}")


@app.command("curl-templates")
def curl_templates(
    provider: str = typer.Argument(..., help="Provider slug"),
    out_root: Path = typer.Option(
        Path("out"),
        "--out-root",
        "--out",
        help="Root output directory",
    ),
    host: list[str] = typer.Option(None, help="Filter to specific hosts"),
    auth_header: str = typer.Option(
        "X-API-KEY",
        help="Auth header placeholder to inject when auth is required",
    ),
    include_patent_center: bool = typer.Option(
        False,
        help="Include Patent Center placeholder templates",
    ),
) -> None:
    """Emit curl templates derived from coverage and API samples."""

    register_default_providers()
    plugin = registry.get(provider)
    emit = getattr(plugin, "emit_curl_templates", None)
    if not callable(emit):  # pragma: no cover - optional provider support
        typer.echo("Provider does not support curl template emission")
        raise SystemExit(1)

    emit(
        build_ctx(
            provider,
            out_root,
            host_filter=host or None,
            auth_header=auth_header,
            include_patent_center=include_patent_center,
        )
    )


@app.command()
def endnote(
    provider: str = typer.Argument(..., help="Provider slug"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    run_id: str | None = typer.Option(
        None,
        help=("Optional run id (out/<provider>/runs/<run-id>/)"),
    ),
) -> None:
    """Export scraped references to EndNote (RIS + attachments)."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.export_endnote(build_ctx(provider, out_root, run_id=run_id))


@app.command("endnote-xml")
def endnote_xml(
    registry_path: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "registry" / "uspto_fields.yaml",
        help="Canonical field registry YAML",
    ),
    template_path: Path | None = typer.Option(
        None,
        help=(
            "Path to an exported EndNote Reference Types Table XML "
            "(RefTypeTable export). If omitted, the tool looks for "
            "endnote_reference_type_table.xml (preferred: "
            "src/reference_harvester/endnote_reference_type_table.xml)."
        ),
    ),
    out_path: Path = typer.Option(
        Path("out/endnote/reference-harvester.xml"),
        help="Destination EndNote type table XML",
    ),
    type_name: str = typer.Option(
        "ReferenceHarvester",
        help="EndNote reference type name",
    ),
    base_type_name: str = typer.Option(
        "Generic",
        help="Base EndNote reference type to copy field layout from",
    ),
    target_slot_name: str = typer.Option(
        "Unused 1",
        help="Which EndNote reference type slot to repurpose",
    ),
    field_label_override: list[str] = typer.Option(
        None,
        help=(
            "Override field label text, e.g. 'Custom 1=Application Number'. "
            "The left-hand side may be an existing label (e.g., 'Custom 1') "
            "or a stable field id (e.g., 'id:25' or '25'). "
            "May be passed multiple times."
        ),
    ),
) -> None:
    """Generate an EndNote reference type table from the canonical registry."""

    registry_def = load_registry(registry_path)
    overrides: dict[str, str] | None = None
    if field_label_override:
        overrides = {}
        for entry in field_label_override:
            if "=" not in entry:
                raise typer.BadParameter(
                    "field_label_override must be in the form 'Old=New'"
                )
            old, new = entry.split("=", 1)
            overrides[old.strip()] = new.strip()
    write_reference_type_table(
        out_path,
        registry_def,
        type_name=type_name,
        template_path=template_path,
        base_type_name=base_type_name,
        target_slot_name=target_slot_name,
        field_label_overrides=overrides,
    )
    typer.echo(f"Wrote EndNote type table to {out_path}")


@app.command("providers")
def providers() -> None:
    """List registered providers and capabilities."""

    entries = _ensure_providers(registry.available() or ["uspto"])
    for entry in entries:
        caps = entry.info.capabilities
        typer.echo(
            " - {name}: {title} | inventory={inventory} harvest={harvest} "
            "fetch={fetch} endnote={endnote}".format(
                name=entry.info.name,
                title=entry.info.title,
                inventory=caps.supports_inventory,
                harvest=caps.supports_harvest,
                fetch=caps.supports_fetch,
                endnote=caps.supports_endnote,
            )
        )


@app.command()
def gui() -> None:
    """Launch the spec-driven GUI (NiceGUI primary, Streamlit fallback)."""

    import importlib

    try:
        gui_mod = importlib.import_module("reference_harvester.gui.app")
        launch_gui = gui_mod.launch_gui
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dep
        typer.echo(f"GUI not available: {exc}")
        raise SystemExit(1) from exc

    launch_gui()


def run() -> None:
    app()


__all__ = [
    "app",
    "endnote",
    "fetch",
    "curl_templates",
    "gui",
    "harvest",
    "inventory",
    "run",
]


if __name__ == "__main__":
    run()
