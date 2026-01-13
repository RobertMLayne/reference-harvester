from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

from .local_constants import USPTO_PROVIDER_ID


class StorePaths:
    def __init__(self, out_root: Path) -> None:
        self.out_root = out_root

    def artifacts_root(self, provider_id: str = USPTO_PROVIDER_ID) -> Path:
        base = self.out_root
        # Avoid duplicating the provider segment when out_root already ends
        # with it.
        if base.name.lower() != provider_id.lower():
            base = base / provider_id
        path = base / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path


def path_for_url(root: Path, url: str) -> Path:
    parsed = urlparse(url)
    host_part = parsed.netloc or ""
    path_parts = [p for p in parsed.path.split("/") if p]

    if not host_part:
        # Fallback when URL is missing a netloc; avoid empty join.
        host_part = "unknown-host"

    # Always treat the host as a directory to prevent collisions between
    # a root page ("host") and deeper assets ("host/assets/...").
    dest = root.joinpath(*([host_part] + path_parts))
    last_segment = path_parts[-1] if path_parts else ""
    has_extension = "." in last_segment and not last_segment.endswith(".")

    # If the URL path is empty, ends with a slash, or the last segment has no
    # extension, store content as an index.html under that directory. This
    # avoids later collisions when writing child assets beneath the same path.
    if not path_parts or parsed.path.endswith("/") or not has_extension:
        dest = dest / "index.html"

    return dest


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


__all__ = ["StorePaths", "path_for_url", "sha256_bytes", "sha256_file"]
