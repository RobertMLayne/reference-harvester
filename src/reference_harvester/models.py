from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from reference_harvester.providers.base import ProviderContext


@dataclass
class RawRecord:
    url: str
    status_code: int
    headers: dict[str, str]
    payload: dict[str, Any]
    retrieved_at: str


@dataclass
class NormalizedRecord:
    canonical: dict[str, Any]
    extras: dict[str, Any] = field(default_factory=dict)
    source_paths: dict[str, str] = field(default_factory=dict)


@dataclass
class MappingDiagnostics:
    source_url: str
    collisions: dict[str, list[str]] = field(default_factory=dict)
    unknown_keys: list[str] = field(default_factory=list)
    coercions: dict[str, str] = field(default_factory=dict)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class JobRequest:
    providers: list[str]
    mode: str
    out_root: Path
    options: dict[str, Any] = field(default_factory=dict)

    def contexts(self) -> Iterable[ProviderContext]:
        for provider in self.providers:
            yield ProviderContext(
                name=provider,
                out_dir=self.out_root,
                options=dict(self.options),
            )


__all__ = [
    "MappingDiagnostics",
    "NormalizedRecord",
    "RawRecord",
    "JobRequest",
    "ensure_parent",
]
