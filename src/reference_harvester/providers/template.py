from __future__ import annotations

from pathlib import Path
from typing import Any

from reference_harvester.providers.base import ProviderContext, ProviderPlugin
from reference_harvester.registry import FieldRegistry


class TemplateProvider(ProviderPlugin):
    """Skeleton provider illustrating required hooks.

    Implementations should:
    - refresh_inventory: bundle swagger/specs and emit inventories/diffs
    - mirror_sources: crawl docs/assets within allowlisted domains
        - fetch_references: plan/download payloads, then emit canonical logs
        - export_endnote: produce EndNote-ready artifacts
            (RIS/CSL/BibTeX/attachments)
    """

    def __init__(
        self,
        name: str,
        registry_path: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.registry_path = registry_path
        self.options = options or {}

    def refresh_inventory(self, ctx: ProviderContext) -> None:
        raise NotImplementedError  # pragma: no cover - template

    def mirror_sources(self, ctx: ProviderContext) -> None:
        raise NotImplementedError  # pragma: no cover - template

    def fetch_references(self, ctx: ProviderContext) -> None:
        raise NotImplementedError  # pragma: no cover - template

    def export_endnote(self, ctx: ProviderContext) -> None:
        raise NotImplementedError  # pragma: no cover - template


def registry_for_template(registry: FieldRegistry) -> FieldRegistry:
    """Return the canonical registry for template-based providers.

    This function exists to mirror the pattern used by concrete providers
    that adopt the USPTO-shaped canonical field set.
    """

    return registry


__all__ = ["TemplateProvider", "registry_for_template"]
