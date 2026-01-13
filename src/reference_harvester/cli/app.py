from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from reference_harvester.providers.base import ProviderContext
from reference_harvester.providers.registry import (
    register_default_providers,
    registry,
)

app = typer.Typer(
    help="Spec-driven, multi-provider harvesting and reference export",
)


def _ctx(provider: str, out_root: Path, **options: Any) -> ProviderContext:
    # Normalize to an absolute provider-scoped output dir to avoid accidental
    # path duplication when the CLI is invoked from a nested working directory
    # (e.g., running inside an existing out_root). Avoid double-appending the
    # provider segment if the caller already supplied it.
    base = out_root
    if base.name.lower() != provider.lower():
        base = base / provider
    ctx = ProviderContext(name=provider, out_dir=base.resolve())
    opts: Any = getattr(ctx, "options", None)
    if isinstance(opts, dict):
        opts.update(options)
    return ctx


@app.command()
def inventory(
    provider: str = typer.Argument(..., help="Provider slug (e.g., uspto)"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
    swagger_url: list[str] = typer.Option(
        None,
        help="Override swagger/OpenAPI URLs (can be passed multiple times)",
    ),
) -> None:
    """Inspect or refresh inventories/spec bundles for a provider."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.refresh_inventory(
        _ctx(
            provider,
            out_root,
            swagger_urls=swagger_url or None,
        )
    )


@app.command()
def harvest(
    provider: str = typer.Argument(..., help="Provider slug (e.g., uspto)"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
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
        _ctx(
            provider,
            out_root,
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
    api_sample_limit: int = typer.Option(25, help="Max API samples"),
    throttle_seconds: float = typer.Option(
        0.0,
        help="Delay between HTTP calls",
    ),
    swagger_url: list[str] = typer.Option(
        None,
        help="Override swagger/OpenAPI URLs (can be passed multiple times)",
    ),
) -> None:
    """Plan and download references/metadata for a provider."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.fetch_references(
        _ctx(
            provider,
            out_root,
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
            api_sample_limit=api_sample_limit,
            throttle_seconds=throttle_seconds,
            swagger_urls=swagger_url or None,
        )
    )


@app.command()
def endnote(
    provider: str = typer.Argument(..., help="Provider slug"),
    out_root: Path = typer.Option(Path("out"), help="Root output directory"),
) -> None:
    """Export scraped references to EndNote (RIS + attachments)."""

    register_default_providers()
    plugin = registry.get(provider)
    plugin.export_endnote(_ctx(provider, out_root))


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
    "gui",
    "harvest",
    "inventory",
    "run",
]


if __name__ == "__main__":
    run()
