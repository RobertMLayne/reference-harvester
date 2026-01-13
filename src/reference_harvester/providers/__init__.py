"""Provider exports for Reference Harvester."""

import importlib
from typing import Any, cast

from .base import ProviderContext, ProviderPlugin
from .registry import ProviderRegistry, register_default_providers, registry

USPTOProvider = cast(
    Any,
    importlib.import_module("reference_harvester.providers.uspto.provider"),
).USPTOProvider
TemplateProvider = cast(
    Any,
    importlib.import_module("reference_harvester.providers.template"),
).TemplateProvider

__all__ = [
    "ProviderContext",
    "ProviderPlugin",
    "ProviderRegistry",
    "register_default_providers",
    "registry",
    "USPTOProvider",
    "TemplateProvider",
]
