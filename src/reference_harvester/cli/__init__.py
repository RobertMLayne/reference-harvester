"""CLI entry points for Reference Harvester."""

import importlib
from typing import Any, cast

_cli_mod = importlib.import_module("reference_harvester.cli.app")
app = cast(Any, _cli_mod).app
endnote = cast(Any, _cli_mod).endnote
fetch = cast(Any, _cli_mod).fetch
gui = cast(Any, _cli_mod).gui
harvest = cast(Any, _cli_mod).harvest
inventory = cast(Any, _cli_mod).inventory
run = cast(Any, _cli_mod).run

__all__ = [
    "app",
    "endnote",
    "fetch",
    "gui",
    "harvest",
    "inventory",
    "run",
]
