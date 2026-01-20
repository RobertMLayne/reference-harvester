"""Provider exports for Reference Harvester."""

from typing import TYPE_CHECKING, Any

from .base import ProviderContext, ProviderPlugin
from .registry import (
    ProviderCapabilities,
    ProviderEntry,
    ProviderInfo,
    ProviderRegistry,
    register_default_providers,
    registry,
)

if TYPE_CHECKING:
    from .openalex.provider import OpenAlexProvider
    from .template import TemplateProvider
    from .uspto.provider import USPTOProvider


def __getattr__(name: str) -> Any:
    if name == "USPTOProvider":
        from .uspto.provider import USPTOProvider

        return USPTOProvider
    if name == "OpenAlexProvider":
        from .openalex.provider import OpenAlexProvider

        return OpenAlexProvider
    if name == "TemplateProvider":
        from .template import TemplateProvider

        return TemplateProvider
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(
        list(globals().keys())
        + ["OpenAlexProvider", "USPTOProvider", "TemplateProvider"]
    )


__all__ = [
    "ProviderContext",
    "ProviderPlugin",
    "ProviderRegistry",
    "ProviderCapabilities",
    "ProviderEntry",
    "ProviderInfo",
    "register_default_providers",
    "registry",
    "OpenAlexProvider",
    "USPTOProvider",
    "TemplateProvider",
]
