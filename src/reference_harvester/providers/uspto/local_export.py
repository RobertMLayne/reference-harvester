from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .local_constants import USPTO_PROVIDER_ID


@dataclass(frozen=True)
class USPTOExportConfig:
    out_dir: Path
    max_pages: int = 200
    include_assets: bool = True
    max_assets: int = 2000
    max_files: int = 200
    user_agent: str = "reference-harvester/0.1"
    http_timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    backoff_max_seconds: float = 1.5
    api_key: str | None = None
    api_key_env: str = "USPTO_ODP_API"
    browser_fallback: bool = False
    browser_timeout_ms: int = 60000
    convert_html_to_md: bool = True
    emit_ris: bool = True
    emit_csl_json: bool = False
    emit_bibtex: bool = False


def mirror_docs(
    *,
    out_root: Path,
    max_pages: int,
    include_assets: bool,
    max_assets: int,
    user_agent: str,
    timeout_seconds: float,
    max_attempts: int,
    backoff_base_seconds: float,
    backoff_max_seconds: float,
) -> None:
    # Minimal placeholder: ensure expected directories exist.
    provider_dir = out_root / USPTO_PROVIDER_ID
    assets = provider_dir / "assets"
    provider_dir.mkdir(parents=True, exist_ok=True)
    assets.mkdir(parents=True, exist_ok=True)


def run_uspto_export(cfg: USPTOExportConfig) -> None:
    # Minimal placeholder: create output directories for downstream steps.
    raw_root = cfg.out_dir
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "manifest.json").write_text("[]\n", encoding="utf-8")

    if cfg.emit_ris:
        (cfg.out_dir / "logs").mkdir(parents=True, exist_ok=True)


__all__ = ["USPTOExportConfig", "mirror_docs", "run_uspto_export"]
