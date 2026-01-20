from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any

from reference_harvester.models import JobRequest
from reference_harvester.providers.base import ProviderContext
from reference_harvester.providers.registry import (
    register_default_providers,
    registry,
)

DEFAULT_OPTIONS: dict[str, Any] = {
    "mode": "fetch",
    "max_pages": 200,
    "max_depth": 4,
    "max_files": 200,
    "include_assets": True,
    "max_assets": 2000,
    "browser_fallback": False,
    "browser_timeout_ms": 60_000,
    "convert_html_to_md": True,
    "emit_ris": True,
    "emit_bibtex": False,
    "emit_csl_json": False,
    "user_agent": "reference-harvester/0.1",
}


def _execute_job(job: JobRequest) -> None:
    register_default_providers()
    for provider in job.providers:
        entry = registry.entry(provider)
        out_dir = job.out_root
        if out_dir.name.lower() != provider.lower():
            out_dir = out_dir / provider
        ctx = ProviderContext(
            name=provider,
            out_dir=out_dir.resolve(),
            options=dict(job.options),
        )
        plugin = entry.plugin
        if job.mode == "inventory":
            plugin.refresh_inventory(ctx)
        elif job.mode in {"harvest", "mirror"}:
            plugin.mirror_sources(ctx)
        elif job.mode in {"fetch", "reference-docs"}:
            plugin.fetch_references(ctx)
        elif job.mode == "endnote":
            plugin.export_endnote(ctx)
        else:
            raise ValueError(f"Unsupported mode: {job.mode}")


def launch_gui(
    inventory_dir: Path | None = None,
    options: dict | None = None,
) -> None:
    """Launch a minimal GUI with the shared fetch/harvest flags."""

    opts = {**DEFAULT_OPTIONS, **(options or {})}
    try:
        from nicegui import ui  # type: ignore
    except ImportError:
        _launch_streamlit_fallback(opts)
        return

    register_default_providers()
    provider_names = registry.available()

    ui.label("Reference Harvester GUI")
    ui.label(f"Inventory dir: {inventory_dir or 'not provided'}")

    if not hasattr(ui, "select"):
        ui.label(f"Options: {opts}")
        ui.run()
        return

    selected = ui.select(provider_names, multiple=True, value=provider_names)
    mode = ui.select(
        ["inventory", "harvest", "fetch", "endnote"],
        value=opts.get("mode", "fetch"),
        label="Mode",
    )
    out_root = ui.input("Output root", value=str(Path("out")))
    max_pages = ui.number("Max pages", value=opts["max_pages"])
    max_depth = ui.number("Max depth", value=opts["max_depth"])
    max_files = ui.number("Max files", value=opts["max_files"])
    include_assets = ui.checkbox(
        "Include assets",
        value=opts["include_assets"],
    )
    max_assets = ui.number("Max assets", value=opts["max_assets"])
    browser_fallback = ui.checkbox(
        "Browser fallback",
        value=opts["browser_fallback"],
    )
    browser_timeout_ms = ui.number(
        "Browser timeout (ms)", value=opts["browser_timeout_ms"]
    )
    convert_html_to_md = ui.checkbox(
        "Convert HTML to Markdown", value=opts["convert_html_to_md"]
    )
    emit_ris = ui.checkbox("Emit RIS", value=opts["emit_ris"])
    emit_bibtex = ui.checkbox("Emit BibTeX", value=opts["emit_bibtex"])
    emit_csl_json = ui.checkbox("Emit CSL-JSON", value=opts["emit_csl_json"])

    status = ui.label("Idle")

    async def on_run() -> None:
        status.text = "Running..."
        job = JobRequest(
            providers=list(selected.value) or provider_names,
            mode=str(mode.value),
            out_root=Path(str(out_root.value)),
            options={
                "max_pages": int(max_pages.value),
                "max_depth": int(max_depth.value),
                "max_files": int(max_files.value),
                "include_assets": bool(include_assets.value),
                "max_assets": int(max_assets.value),
                "browser_fallback": bool(browser_fallback.value),
                "browser_timeout_ms": int(browser_timeout_ms.value),
                "convert_html_to_md": bool(convert_html_to_md.value),
                "emit_ris": bool(emit_ris.value),
                "emit_bibtex": bool(emit_bibtex.value),
                "emit_csl_json": bool(emit_csl_json.value),
            },
        )
        await ui.run_worker(partial(_execute_job, job))
        status.text = "Done"

    ui.button("Run", on_click=on_run)
    ui.run()


def _launch_streamlit_fallback(options: dict[str, Any]) -> None:
    try:
        import streamlit as st  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "GUI extras not installed; install with `pip install .[gui]`"
        ) from exc

    register_default_providers()
    provider_names = registry.available()

    st.title("Reference Harvester GUI (fallback)")
    selected = st.multiselect(
        "Providers",
        provider_names,
        default=provider_names,
    )
    mode = st.selectbox(
        "Mode",
        ["inventory", "harvest", "fetch", "endnote"],
        index=2,
    )
    out_root = Path(st.text_input("Output root", "out"))
    st.write("Options below mirror the CLI flags.")
    max_pages = st.number_input("Max pages", value=int(options["max_pages"]))
    max_depth = st.number_input("Max depth", value=int(options["max_depth"]))
    max_files = st.number_input("Max files", value=int(options["max_files"]))
    include_assets = st.checkbox(
        "Include assets", value=bool(options["include_assets"])
    )
    max_assets = st.number_input(
        "Max assets",
        value=int(options["max_assets"]),
    )
    browser_fallback = st.checkbox(
        "Browser fallback", value=bool(options["browser_fallback"])
    )
    browser_timeout_ms = st.number_input(
        "Browser timeout (ms)", value=int(options["browser_timeout_ms"])
    )
    convert_html_to_md = st.checkbox(
        "Convert HTML to Markdown", value=bool(options["convert_html_to_md"])
    )
    emit_ris = st.checkbox("Emit RIS", value=bool(options["emit_ris"]))
    emit_bibtex = st.checkbox(
        "Emit BibTeX",
        value=bool(options["emit_bibtex"]),
    )
    emit_csl_json = st.checkbox(
        "Emit CSL-JSON",
        value=bool(options["emit_csl_json"]),
    )

    if st.button("Run"):
        job = JobRequest(
            providers=selected or provider_names,
            mode=str(mode),
            out_root=out_root,
            options={
                "max_pages": int(max_pages),
                "max_depth": int(max_depth),
                "max_files": int(max_files),
                "include_assets": bool(include_assets),
                "max_assets": int(max_assets),
                "browser_fallback": bool(browser_fallback),
                "browser_timeout_ms": int(browser_timeout_ms),
                "convert_html_to_md": bool(convert_html_to_md),
                "emit_ris": bool(emit_ris),
                "emit_bibtex": bool(emit_bibtex),
                "emit_csl_json": bool(emit_csl_json),
            },
        )
        _execute_job(job)
        st.success("Completed")


__all__ = ["launch_gui"]
