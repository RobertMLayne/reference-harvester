from __future__ import annotations

import json
from pathlib import Path


def launch_gui(
    inventory_dir: Path | None = None,
    options: dict | None = None,
) -> None:
    """Launch a minimal GUI scaffold.

    Primary: NiceGUI; fallback: Streamlit. Keeps soft dependency to avoid
    forcing GUI installs for CLI-only users.
    """

    try:
        from nicegui import ui  # type: ignore
    except ImportError:
        _launch_streamlit_fallback(options)
        return

    ui.label("Reference Harvester GUI (scaffold)")
    ui.label(f"Inventory dir: {inventory_dir or 'not provided'}")
    if options is not None:
        ui.label(f"Options: {json.dumps(options, ensure_ascii=False)}")
    ui.run()


def _launch_streamlit_fallback(options: dict | None = None) -> None:
    try:
        import streamlit as st  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "GUI extras not installed; install with `pip install .[gui]`"
        ) from exc

    st.title("Reference Harvester GUI (scaffold)")
    st.write("Install NiceGUI for the primary experience.")
    if options is not None:
        st.write(json.dumps(options, ensure_ascii=False))


__all__ = ["launch_gui"]
