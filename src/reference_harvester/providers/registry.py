from __future__ import annotations

from typing import Dict, cast

from reference_harvester.providers.base import ProviderPlugin


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ProviderPlugin] = {}

    def register(self, name: str, plugin: ProviderPlugin) -> None:
        self._providers[name] = plugin

    def get(self, name: str) -> ProviderPlugin:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' is not registered")
        return self._providers[name]

    def available(self) -> list[str]:
        return sorted(self._providers)


registry = ProviderRegistry()


def register_default_providers() -> None:
    """Register built-in providers (idempotent)."""

    from reference_harvester.providers.uspto.provider import (
        USPTOProvider,
    )

    if "uspto" not in registry.available():
        registry.register("uspto", cast(ProviderPlugin, USPTOProvider()))


__all__ = [
    "ProviderRegistry",
    "register_default_providers",
    "registry",
]
