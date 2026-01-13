from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ProviderContext:
    name: str
    out_dir: Path
    options: dict[str, Any] = field(default_factory=dict)


class ProviderPlugin(Protocol):
    def refresh_inventory(self, ctx: ProviderContext) -> None: ...

    def mirror_sources(self, ctx: ProviderContext) -> None: ...

    def fetch_references(self, ctx: ProviderContext) -> None: ...

    def export_endnote(self, ctx: ProviderContext) -> None: ...


__all__ = ["ProviderContext", "ProviderPlugin"]
