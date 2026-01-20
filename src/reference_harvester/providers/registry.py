from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, cast

from reference_harvester.providers.base import ProviderPlugin


@dataclass(frozen=True)
class ProviderCapabilities:
    supports_inventory: bool = False
    supports_harvest: bool = False
    supports_fetch: bool = False
    supports_endnote: bool = False
    supports_citations: bool = False
    supports_browser_fallback: bool = False


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    title: str
    description: str
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    credentials: list[str] = field(default_factory=list)
    default_seeds: list[str] = field(default_factory=list)
    homepage: str | None = None


@dataclass
class ProviderEntry:
    plugin: ProviderPlugin
    info: ProviderInfo


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ProviderEntry] = {}

    def register(
        self,
        name: str,
        plugin: ProviderPlugin,
        info: ProviderInfo | None = None,
    ) -> None:
        resolved = info
        if resolved is None:
            resolved = getattr(plugin, "provider_info", None)
        if resolved is None:
            resolved = ProviderInfo(
                name=name,
                title=name,
                description=f"Provider {name}",
                capabilities=ProviderCapabilities(
                    supports_inventory=hasattr(plugin, "refresh_inventory"),
                    supports_harvest=hasattr(plugin, "mirror_sources"),
                    supports_fetch=hasattr(plugin, "fetch_references"),
                    supports_endnote=hasattr(plugin, "export_endnote"),
                    supports_citations=True,
                ),
            )
        self._providers[name] = ProviderEntry(plugin=plugin, info=resolved)

    def get(self, name: str) -> ProviderPlugin:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name].plugin

    def info(self, name: str) -> ProviderInfo:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name].info

    def entry(self, name: str) -> ProviderEntry:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name]

    def available(self) -> list[str]:
        return sorted(self._providers)

    def entries(self) -> list[ProviderEntry]:
        return [self._providers[name] for name in self.available()]


registry = ProviderRegistry()


def register_default_providers() -> None:
    """Register built-in providers (idempotent)."""

    from reference_harvester.providers.openalex.provider import (
        OpenAlexProvider,
    )
    from reference_harvester.providers.uspto.provider import (
        USPTOProvider,
    )

    if "uspto" not in registry.available():
        registry.register(
            "uspto",
            cast(ProviderPlugin, USPTOProvider()),
            ProviderInfo(
                name="uspto",
                title="USPTO Open Data",
                description="USPTO open data, swagger, and bulk assets",
                capabilities=ProviderCapabilities(
                    supports_inventory=True,
                    supports_harvest=True,
                    supports_fetch=True,
                    supports_endnote=True,
                    supports_citations=True,
                    supports_browser_fallback=True,
                ),
                credentials=["USPTO_ODP_API"],
                homepage="https://developer.uspto.gov/",
            ),
        )

    if "openalex" not in registry.available():
        registry.register(
            "openalex",
            cast(ProviderPlugin, OpenAlexProvider()),
            ProviderInfo(
                name="openalex",
                title="OpenAlex",
                description="OpenAlex works metadata (no API key)",
                capabilities=ProviderCapabilities(
                    supports_inventory=True,
                    supports_harvest=True,
                    supports_fetch=True,
                    supports_endnote=True,
                ),
                credentials=["OPENALEX_EMAIL"],
                homepage="https://openalex.org/",
            ),
        )


__all__ = [
    "ProviderCapabilities",
    "ProviderEntry",
    "ProviderInfo",
    "ProviderRegistry",
    "register_default_providers",
    "registry",
]
